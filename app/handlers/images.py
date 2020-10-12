def get_image_url(image_id, campaigns=[]):
    """
    GET /images/{image_id}

    Get an image. If authenticated, this will redirect to the actual image in
    blobstorage, with a SAS token for access.
    """
    return "Not Implemented: images.get_image_url"


def get_objects(image_id):
    """
    GET /images/{image_id}/objects

    Show the objects for a certain image
    """
    return "Not Implemented: images.get_objects"
