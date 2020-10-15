from common.auth import flask_login
from flask import abort
from models.image import Image


@flask_login.login_required
def list_images(page=1, per_page=10):
    """
    GET /images

    List all images
    """
    # Check if logged in user has correct permissions
    if not flask_login.current_user.has_role('image-admin'):
        abort(401)

    images = Image.query.order_by(Image.id).paginate(page=page, per_page=per_page)
    return {
        'pagination': {
            'page': images.page,
            'pages': images.page,
            'total': images.total,
            'per_page': images.per_page,
            'prev': (images.prev_num if images.has_prev else None),
            'next': (images.next_num if images.has_next else None)
        },
        'images': [x.to_dict() for x in images.items]
    }


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
