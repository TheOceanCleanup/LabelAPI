from azure.storage.blob import BlockBlobService, BlobPermissions, \
    ContainerPermissions
from azure.common import AzureException
#from retrying import retry
from datetime import datetime, timedelta
import logging
import os
import re

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
    def create_folder(foldername):
        """
        Create a new folder in the upload container. Requires
        that the Azure datastore connection string is available in the
        environment.

        Given that the concept of an directory does not exist in Azure
        blobstorage, the folder is created by writing an empyt file called
        `.` into the storage, which has the path. It will then show as folder
        in the UI.

        Requires the following environment variables to be set:
        AZURE_STORAGE_CONNECTION_STRING
        AZURE_STORAGE_IMAGESET_CONTAINER
        AZURE_STORAGE_IMAGESET_FOLDER

        :param foldername:  Name to give the folder
        :returns:           False in case of failure, full path otherwise
        """
        assert "AZURE_STORAGE_CONNECTION_STRING" in os.environ
        assert "AZURE_STORAGE_IMAGESET_CONTAINER" in os.environ
        assert "AZURE_STORAGE_IMAGESET_FOLDER" in os.environ

        block_blob_service = BlockBlobService(
            connection_string=os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        )

        folderpath = '/'.join([
            os.environ["AZURE_STORAGE_IMAGESET_FOLDER"],
            'imageset_' + foldername
        ])

        container = os.environ["AZURE_STORAGE_IMAGESET_CONTAINER"]

        try:
            block_blob_service.create_blob_from_text(
                container_name=container,
                blob_name='/'.join([
                    folderpath,
                    'placeholder'
                ]),
                text=""
            )
        except AzureException:
            logger.warning(f"Failed to create folder {folderpath} in "
                           f"container {container}")
            return False

        logger.info(f"Created folder {folderpath} in container " +
                    f"{container}")

        return '/'.join([
            os.environ["AZURE_STORAGE_IMAGESET_CONTAINER"],
            folderpath
        ])
