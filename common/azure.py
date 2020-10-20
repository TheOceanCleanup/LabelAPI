from azure.storage.blob import BlockBlobService, BlobPermissions, \
    ContainerPermissions
from azure.common import AzureException
from azureml.core import Workspace, Dataset, Datastore
#from retrying import retry
from datetime import datetime, timedelta
from PIL import Image, UnidentifiedImageError
import logging
import os
import io

logger = logging.getLogger("label-api")


class AzureWrapper:
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
        assert "AZURE_STORAGE_CONNECTION_STRING" in os.environ

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
        assert "AZURE_STORAGE_CONNECTION_STRING" in os.environ

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
        url_tmp = url.split('?')
        params = url_tmp[1].split('&')
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

        logger.info("Created dropbox container" + container_name)
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
        assert "AZURE_STORAGE_CONNECTION_STRING" in os.environ
        block_blob_service = BlockBlobService(
            connection_string=os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        )

        try:
            files = block_blob_service.list_blobs(source_container, source_folder)
        except AzureException as e:
            logger.warning(
                f"Failed to list files in {source_container} : {source_folder}")
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
        assert "AZURE_STORAGE_CONNECTION_STRING" in os.environ
        block_blob_service = BlockBlobService(
            connection_string=os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        )

        try:
            block_blob_service.delete_container(container)
        except AzureException as e:
            logger.warning(f"Failed to delete container {container}")
            return False

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
        assert "AZURE_STORAGE_CONNECTION_STRING" in os.environ

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
                f"Failed to open file from blob storage: {container} : "
                f"{filepath}"
            )
            return None, None, None

        try:
            img = Image.open(io.BytesIO(b.content))
        except UnidentifiedImageError:
            logging.warning(f"Not a valid image: {container} : {filepath}")
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
        return Workspace(subscription_id, resource_group, workspace_name)

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
        assert "AZURE_STORAGE_CONNECTION_STRING" in os.environ
        assert "AZURE_ML_DATASTORE" in os.environ
        assert "AZURE_ML_SUBSCRIPTION_ID" in os.environ
        assert "AZURE_ML_RESOURCE_GROUP" in os.environ
        assert "AZURE_ML_WORKSPACE_NAME" in os.environ

        ws = AzureWrapper._get_workspace(
            os.environ["AZURE_ML_SUBSCRIPTION_ID"],
            os.environ["AZURE_ML_RESOURCE_GROUP"],
            os.environ["AZURE_ML_WORKSPACE_NAME"]
        )
        datastore = AzureWrapper._get_datastore(
            ws,
            os.environ["AZURE_ML_DATASTORE"]
        )

        paths = [(datastore, x) for x in images]

        dataset = Dataset.File.from_files(
            path=paths
        )
        dataset.register(
            workspace=ws,
            name=name,
            description=description,
            create_new_version=True
        )
