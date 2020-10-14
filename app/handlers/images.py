from common.auth import flask_login


@flask_login.login_required
def list_images(page=1, per_page=10):
    """
    GET /images/{image_id}

    List all images
    """
    return "Not Implemented: images.list_images"


@flask_login.login_required
def get_image_url(image_id, campaigns=[]):
    """
    GET /images/{image_id}

    Get an image. If authenticated, this will redirect to the actual image in
    blobstorage, with a SAS token for access.
    """
    return "Not Implemented: images.get_image_url"


@flask_login.login_required
def get_objects(image_id):
    """
    GET /images/{image_id}/objects

    Show the objects for a certain image
    """
    return "Not Implemented: images.get_objects"
