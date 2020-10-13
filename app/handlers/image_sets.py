def list_imagesets(page=1, per_page=10):
    """
    GET /image_sets

    Return list of image sets
    """
    return "Not Implemented: image_sets.list_imagesets"


def add_imageset(body):
    """
    POST /images_sets

    Create a new image set
    """
    return "Not Implemented: image_sets.add_imageset"


def change_status(imageset_id, body):
    """
    PUT /image_sets/{imageset_id}

    Change the status of an image set
    """
    return "Not Implemented: image_sets.change_status"


def get_images(imageset_id):
    """
    GET /image_sets/{imageset_id}/images

    List all the images in the image set, as ID and download path.
    """
    return "Not Implemented: image_sets.get_images"


def add_images(imageset_id, body):
    """
    POST /image_sets/{imageset_id}/images

    Add images to an image set.
    """
    return "Not Implemented: image_sets.add_images"