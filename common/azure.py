from azure.storage.blob import BlockBlobService, BlobPermissions
from azure.common import AzureException
#from retrying import retry
from datetime import datetime, timedelta
import logging
import os

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
    def get_sas_url(path, expires=datetime.utcnow() + timedelta(days=7),
            permissions=["read"]):
        """
        Generate a download URL with SAS key for a given filepath. Requires
        that the Azure datastore connection string is available in the
        environment.

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
            expiry=expires
        )

        # Use token to generate URL
        return block_blob_service.make_blob_url(
            container,
            filepath,
            protocol="https",
            sas_token=token
        )
