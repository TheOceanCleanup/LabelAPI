# LabelAPI - Server program that provides API to manage training sets for machine learning image recognition models
# Copyright (C) 2020-2021 The Ocean Cleanup™
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from azure.storage.blob import BlockBlobService, BlobPermissions, \
    ContainerPermissions
from azure.storage.common.retry import LinearRetry
from azure.common import AzureException
from azureml.core import Workspace, Dataset, Datastore
from azureml.data.dataset_factory import DataType
from azureml.core.authentication import ServicePrincipalAuthentication
from azureml.exceptions import AzureMLException, UserErrorException, \
    ProjectSystemException
from azureml._restclient.models.error_response import ErrorResponseException
from msrest.exceptions import AuthenticationError
from PIL import Image, UnidentifiedImageError
from retrying import retry
from datetime import datetime, timedelta
from pathlib import Path
import logging
import os
import io
import pandas as pd
import string

logger = logging.getLogger("label-api")


class AzureWrapper:
    @staticmethod
    def check_name(name):
        """
        Check if a name is a valid name for use within Azure.

        :params name:   The name to check.
        :returns:       Boolean indicating if the name is valid.
        """
        # Length must be between 3 and 63. We prepend and append, so take of 10
        if len(name) > 53:
            return False

        # All characters must be lowercase ascii, a number, or a dash (-)
        for c in name:
            if c not in string.ascii_lowercase + string.digits + '-':
                return False

        # Name can't start or end with a dash
        if name[0] == '-' or name[-1] == '-':
            return False

        # Consecutive dashes are not allowed:
        if '--' in name:
            return False

        return True

    @staticmethod
    def _create_permissions(permissions):
        """
        Create azure permissions object based on the provided list of
        permissions. This uses the Azure permissions naming as shown in
        https://docs.microsoft.com/en-us/python/api/azure-storage-blob/azure.storage.blob.models.blobpermissions?view=azure-python-previous

        For normal usage, read and create are most likely to be used.
        """
        return BlobPermissions(
            add="add" in permissions,
            create="create" in permissions,
            delete="delete" in permissions,
            read="read" in permissions,
            write="write" in permissions
        )

    @staticmethod
    def _create_container_permissions(permissions):
        """
        Create azure permissions object based on the provided list of
        permissions. This uses the Azure permissions naming as shown in
        https://docs.microsoft.com/en-us/python/api/azure-storage-blob/azure.storage.blob.models.containerpermissions?view=azure-python-previous
        """
        return ContainerPermissions(
            delete="delete" in permissions,
            list="list" in permissions,
            read="read" in permissions,
            write="write" in permissions
        )

    @staticmethod
    def get_sas_url(path, expires=datetime.utcnow() + timedelta(days=7),
                    permissions=["read"]):
        """
        Generate a download URL with SAS key for a given filepath.

        Requires the following environment variables to be set:
        AZURE_STORAGE_CONNECTION_STRING

        :params path:           Path where the image is located. The first
                                component should be the container it is in.
        :params expires:        Datetime object indicating when the SAS key
                                should expire.
        :params permissions:    List of permissions that the key should give.
                                Should be a subset of ["add", "create",
                                "delete", "read", "write"].
        :returns:               The URL with key for the given image.
        """
        block_blob_service = BlockBlobService(
            connection_string=os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        )

        # Determine container and filepath
        path = path.lstrip("/")
        container = path.split("/")[0]
        filepath = "/".join(path.split("/")[1:])

        token = block_blob_service.generate_blob_shared_access_signature(
            container,
            filepath,
            permission=AzureWrapper._create_permissions(permissions),
            expiry=expires,
            protocol="https"
        )

        logger.info("Created SAS token for " + container + "/" + filepath)

        # Use token to generate URL
        return block_blob_service.make_blob_url(
            container,
            filepath,
            protocol="https",
            sas_token=token
        )

    @staticmethod
    def get_container_sas_url(container_name,
                              expires=datetime.utcnow() + timedelta(days=7),
                              permissions=["read"]):
        """
        Generate an access URL with SAS key for a containers.

        Requires the following environment variables to be set:
        AZURE_STORAGE_CONNECTION_STRING

        :params container_nam:  The container to create a URL for
        :params expires:        Datetime object indicating when the SAS key
                                should expire.
        :params permissions:    List of permissions that the key should give.
                                Should be a subset of ["delete", "list",
                                "read", "write"].
        :returns:               The URL with key for the given image.
        """
        block_blob_service = BlockBlobService(
            connection_string=os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        )

        token = block_blob_service.generate_container_shared_access_signature(
            container_name,
            permission=AzureWrapper._create_container_permissions(permissions),
            expiry=expires,
            protocol="https"
        )

        # Use token to generate URL
        url = block_blob_service.make_container_url(
            container_name,
            protocol="https",
            sas_token=token
        )

        # For some reason, the restype=container parameter is added.
        # This breaks the token. Remove this. (see
        # https://github.com/Azure/azure-storage-python/issues/543)
        url_tmp = url.split("?")
        params = url_tmp[1].split("&")
        if "restype=container" in params:
            params.remove("restype=container")
        url = url_tmp[0] + "?" + "&".join(params)

        logger.info("Created SAS token for " + container_name)
        return url

    @staticmethod
    def create_container(container_name):
        """
        Create a new (temporary) container on Blobstorage. This will be
        used to allow imageset uploads.

        Requires the following environment variables to be set:
        AZURE_STORAGE_CONNECTION_STRING

        :param containername:   Name of the container
        :returns:               False in case of failure, container name
                                otherwise
        """
        block_blob_service = BlockBlobService(
            connection_string=os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        )

        container_name = "dropbox-" + container_name.lower()
        try:
            block_blob_service.create_container(container_name)
        except AzureException:
            logger.warning("Failed to create dropbox container " +
                           container_name)
            return False

        logger.info("Created dropbox container " + container_name)
        return container_name

    @staticmethod
    def copy_contents(source_container, source_folder, target_container,
                      target_folder):
        """
        Copy the contents from one container:folder to another.

        Requires the following environment variables to be set:
        AZURE_STORAGE_CONNECTION_STRING

        :param source_container:    Container to copy from
        :param source_folder:       Folder to copy from, as prefix
        :param target_container:    Container to copy to
        :param target_folder:       Folder to copy to, as prefix
        :returns:                   List of all copied files
        """
        block_blob_service = BlockBlobService(
            connection_string=os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        )

        try:
            files = block_blob_service.list_blobs(source_container,
                                                  source_folder)
        except AzureException as e:
            logger.warning(
                f"Failed to list files in {source_container}/{source_folder}")
            return False

        for f in files:
            if source_folder != "":
                target_name = f.name.replace(source_folder, target_folder)
            else:
                target_name = f"{target_folder}/{f.name}"

            try:
                block_blob_service.copy_blob(
                    target_container,
                    target_name,
                    f"https://{block_blob_service.account_name}.blob." +
                    f"core.windows.net/{source_container}/{f.name}"
                )
            except AzureException as e:
                logger.warning(f"Failed to copy file {f.name}")
                return False

        return files

    @staticmethod
    def delete_container(container):
        """
        Delete a container

        Requires the following environment variables to be set:
        AZURE_STORAGE_CONNECTION_STRING

        :param container:    Container to delete
        :returns:            Boolean indicating success
        """
        block_blob_service = BlockBlobService(
            connection_string=os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        )

        try:
            block_blob_service.delete_container(container)
        except AzureException as e:
            logger.warning(f"Failed to delete container {container}")
            return False

        logger.info("Deleted dropbox container " + container)
        return True

    @staticmethod
    def get_image_information(path):
        """
        Read the filetype and dimensions of an image

        Requires the following environment variables to be set:
        AZURE_STORAGE_CONNECTION_STRING

        :param path:        Path where the image is located. The first
                            component should be the container it is in.
        :returns:           Tuple containing: image type, image width,
                            image height
        """
        block_blob_service = BlockBlobService(
            connection_string=os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        )

        path = path.lstrip("/")
        container = path.split("/")[0]
        filepath = "/".join(path.split("/")[1:])

        try:
            b = block_blob_service.get_blob_to_bytes(
                container,
                filepath
            )
        except AzureException as e:
            logging.warning(
                f"Failed to open file from blob storage: {container}/"
                f"{filepath}"
            )
            return None, None, None

        with io.BytesIO(b.content) as img_data:
            try:
                img = Image.open(img_data)
            except UnidentifiedImageError:
                logging.warning(f"Not a valid image: {container}/{filepath}")
                return None, None, None

            return img.format, img.width, img.height

    @staticmethod
    def _get_workspace(subscription_id, resource_group, workspace_name):
        """
        Load the correct workspace

        :param subscription_id:     Azure subscription
        :param resource_group:      Azure resource group
        :param workspace_name:      Name of the workspace
        :returns:                   Azure ML Workspace object
        """
        service_principal = ServicePrincipalAuthentication(
            tenant_id=os.environ["AZURE_ML_SP_TENANT_ID"],
            service_principal_id=os.environ["AZURE_ML_SP_APPLICATION_ID"],
            service_principal_password=os.environ["AZURE_ML_SP_PASSWORD"],
            _enable_caching=False
        )

        return Workspace(
            subscription_id,
            resource_group,
            workspace_name,
            auth=service_principal
        )

    @staticmethod
    def _get_datastore(workspace, datastore_name):
        """
        Get a Datastore object

        :param workspace:       Azure ML Workspace object
        :param datastore_name:  Name of the datastore to load
        :returns:               Azure ML Datastore object
        """
        return Datastore.get(workspace, datastore_name)

    @staticmethod
    @retry(stop_max_attempt_number=5, wait_exponential_multiplier=1000, wait_exponential_max=10000)
    def _get_file_dataset(paths):
        logger.info("Creating dataset")
        logger.handlers[0].flush()

        try:
            return Dataset.File.from_files(
                path=paths,
                validate=False
            )
        except Exception as e:
            logger.error(e)
            logger.handlers[0].flush()
            raise e

    @staticmethod
    @retry(stop_max_attempt_number=3)
    def _get_tabular_dataset(datastore, filename):
        logger.info("Creating dataset")
        logger.handlers[0].flush()

        try:
            return Dataset.Tabular.from_delimited_files(
                path=[(datastore, (f"label_sets/{filename}.csv"))],
                validate=False,
                infer_column_types=False,
                set_column_types={
                    'image_url': DataType.to_string(),
                    'label': DataType.to_string(),
                    'label_confidence': DataType.to_string()
                }
            )
        except Exception as e:
            logger.error(e)
            logger.handlers[0].flush()
            raise e

    @staticmethod
    def export_images_to_ML(name, description, images):
        """
        Export a list of images to an Azure ML dataset.

        Requires the following environment variables to be set:
        AZURE_STORAGE_CONNECTION_STRING
        AZURE_ML_DATASTORE
        AZURE_ML_SUBSCRIPTION_ID
        AZURE_ML_RESOURCE_GROUP
        AZURE_ML_WORKSPACE_NAME

        :param name:        The name to give to the new dataset
        :param description: Short description to give to the dataset
        :param images:      A list of image paths relative to the datastore
                            object in Azure ML.
        """
        ws = AzureWrapper._get_workspace(
            os.environ["AZURE_ML_SUBSCRIPTION_ID"],
            os.environ["AZURE_ML_RESOURCE_GROUP"],
            os.environ["AZURE_ML_WORKSPACE_NAME"]
        )
        datastore = AzureWrapper._get_datastore(
            ws,
            os.environ["AZURE_ML_DATASTORE"]
        )

        logger.info(f"Got Datastore {datastore}")
        logger.info(images)

        paths = [(datastore, x) for x in images]

        logger.info(paths)

        dataset = AzureWrapper._get_file_dataset(paths)

        logger.info(f"Created Dataset {dataset}")

        dataset.register(
            workspace=ws,
            name=name,
            description=description,
            create_new_version=True
        )

        logger.info(f"Registered Dataset {dataset}")

    @staticmethod
    def export_labels_to_ML(name, description, labels):
        """
        Export a list of labels to an Azure ML dataset.

        Requires the following environment variables to be set:
        AZURE_STORAGE_CONNECTION_STRING
        AZURE_ML_DATASTORE
        AZURE_ML_SUBSCRIPTION_ID
        AZURE_ML_RESOURCE_GROUP
        AZURE_ML_WORKSPACE_NAME

        :param name:        The name to give to the new dataset
        :param description: Short description to give to the dataset
        :param labels:      A list of image paths relative to the datastore
                            object in Azure ML.
        """
        ws = AzureWrapper._get_workspace(
            os.environ["AZURE_ML_SUBSCRIPTION_ID"],
            os.environ["AZURE_ML_RESOURCE_GROUP"],
            os.environ["AZURE_ML_WORKSPACE_NAME"]
        )
        data = []
        for image in labels:
            data.append([
                image["image_url"],
                image["label"],
                image["label_confidence"]
            ])

        columns = ["image_url", "label", "label_confidence"]
        df = pd.DataFrame(data, columns=columns)
        Path("tmp").mkdir(parents=True, exist_ok=True)
        local_path = f"tmp/{name}.csv"
        df.to_csv(local_path, index=False)

        logger.info(f"Created local file")

        datastore = AzureWrapper._get_datastore(
            ws,
            os.environ["AZURE_ML_DATASTORE"]
        )

        logger.info(f"Got Datastore {datastore}")

        # upload the local file from src_dir to the target_path in datastore
        datastore.upload(src_dir="tmp", target_path="label_sets")

        logger.info(
            f'Uploaded labels CSV to {os.environ["AZURE_ML_DATASTORE"]}'
            f'/label_sets/{name}.csv')

        dataset = AzureWrapper._get_tabular_dataset(datastore, name)

        logger.info("Created dataset")

        dataset.register(
            workspace=ws,
            name=name,
            description=description,
            create_new_version=True
        )

        logger.info("Registered dataset")

        os.remove(local_path)

    @staticmethod
    def check_storage_connect():
        """
        Check if a connection can be made to the Blob Service. Use very
        limited retry settings, so we don't take too much time.
        """
        block_blob_service = BlockBlobService(
            connection_string=os.environ["AZURE_STORAGE_CONNECTION_STRING"],
            socket_timeout=0.5
        )
        block_blob_service.retry = LinearRetry(backoff=0.5, max_attempts=1).retry
        try:
            block_blob_service.exists("somecontainer")
        except AzureException:
            logger.error("Failed to connect to Azure Storage")
            return False, "Failed to connect to Azure Storage"

        return True, None

    @staticmethod
    def check_container_exists():
        """
        Check if the required container exists.
        """
        block_blob_service = BlockBlobService(
            connection_string=os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        )
        container_name = os.environ["AZURE_STORAGE_IMAGESET_CONTAINER"]
        if block_blob_service.exists(container_name):
            return True, None
        else:
            logger.error(
                f"Main container for storing images {container_name} does not "
                f"exist")
            return \
                False, \
                f"Main container for images {container_name} does not exist"

        return True, None

    @staticmethod
    def check_create_container():
        container_name = "tmp-container-status-check"
        created_container = AzureWrapper.create_container(container_name)
        if not created_container:
            return False, "Can't create container"

        if not AzureWrapper.delete_container(created_container):
            return False, "Can't delete container"

        return True, None

    @staticmethod
    def check_create_blob():
        block_blob_service = BlockBlobService(
            connection_string=os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        )
        container_name = os.environ["AZURE_STORAGE_IMAGESET_CONTAINER"]
        blob_name = 'tmp-blob-status-check'
        try:
            block_blob_service.create_blob_from_text(
                container_name,
                blob_name,
                "text"
            )
        except AzureException:
            logger.error("Failed to create blob on Azure Storage")
            return False, "Failed to create blob on Azure Storage"

        try:
            block_blob_service.delete_blob(
                container_name,
                blob_name
            )
        except AzureException:
            logger.error("Failed to delete blob on Azure Storage")
            return False, "Failed to delete blob on Azure Storage"

        return True, None

    @staticmethod
    def check_get_workspace():
        try:
            AzureWrapper._get_workspace(
                os.environ["AZURE_ML_SUBSCRIPTION_ID"],
                os.environ["AZURE_ML_RESOURCE_GROUP"],
                os.environ["AZURE_ML_WORKSPACE_NAME"]
            )
        except UserErrorException as e:
            logger.error(
                f"Failed to get workspace - Incorrect subscription or user: " \
                f"{e}")
            return \
                False, \
                f"Failed to get workspace - Incorrect subscription or user: " \
                f"{e}"
        except ProjectSystemException as e:
            logger.error(f"Failed to get workspace - Incorrect name: {e}")
            return False, f"Failed to get workspace - Incorrect name: {e}"
        except AuthenticationError as e:
            logger.error(
                f"Failed to get workspace - Unable to log in with " \
                f"provided credentials: {e}")
            return \
                False, \
                f"Failed to get workspace - Unable to log in with " \
                f"provided credentials: {e}"
        except AzureMLException as e:
            logger.error(f"Failed to get workspace - Unknown error: {e}")
            return False, f"Failed to get workspace - Unknown error: {e}"

        return True, None

    @staticmethod
    def datastore_exists():
        ws = AzureWrapper._get_workspace(
            os.environ["AZURE_ML_SUBSCRIPTION_ID"],
            os.environ["AZURE_ML_RESOURCE_GROUP"],
            os.environ["AZURE_ML_WORKSPACE_NAME"]
        )
        ds_name = os.environ["AZURE_ML_DATASTORE"]
        try:
            ds = AzureWrapper._get_datastore(ws, ds_name)
        except ErrorResponseException as e:
            logger.error(f"Failed to get datastore {ds_name}: {e}")
            return False, f"Failed to get datastore {ds_name}: {e}"

        return True, None