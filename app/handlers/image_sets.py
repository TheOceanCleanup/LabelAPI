from common.auth import flask_login
from models.image import ImageSet


@flask_login.login_required
def list_imagesets(page=1, per_page=10):
    """
    GET /image_sets

    Return list of image sets
    """
    # Check if logged in user has correct permissions
    if not flask_login.current_user.is_image_admin():
        abort(401)

    imagesets = ImageSet.query.order_by(ImageSet.id).paginate(page=page, per_page=per_page)
    return {
        'pagination': {
            'page': imagesets.page,
            'pages': imagesets.page,
            'total': imagesets.total,
            'per_page': imagesets.per_page,
            'prev': (imagesets.prev_num if imagesets.has_prev else None),
            'next': (imagesets.next_num if imagesets.has_next else None)
        },
        'image_sets': [x.to_dict() for x in imagesets.items]
    }


@flask_login.login_required
def add_imageset(body):
    """
    POST /images_sets

    Create a new image set
    """
    return "Not Implemented: image_sets.add_imageset"


@flask_login.login_required
def change_status(imageset_id, body):
    """
    PUT /image_sets/{imageset_id}

    Change the status of an image set
    """
    return "Not Implemented: image_sets.change_status"


@flask_login.login_required
def get_images(imageset_id):
    """
    GET /image_sets/{imageset_id}/images

    List all the images in the image set, as ID and download path.
    """
    return "Not Implemented: image_sets.get_images"


@flask_login.login_required
def add_images(imageset_id, body):
    """
    POST /image_sets/{imageset_id}/images

    Add images to an image set.

    Note: Can only add to created set
    """
    return "Not Implemented: image_sets.add_images"
