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

from common.auth import flask_login
from common.azure import AzureWrapper
from models.image import ImageSet
from flask import abort
import logging

logger = logging.getLogger('label-api')


@flask_login.login_required
def list_imagesets(page=1, per_page=10):
    """
    GET /image_sets

    Return list of image sets
    """
    # Check if logged in user has correct permissions
    if not flask_login.current_user.has_role("image-admin"):
        logger.warning("User not authorized")
        abort(401)

    imagesets = ImageSet.query\
                        .order_by(ImageSet.id)\
                        .paginate(page=page, per_page=per_page)
    return {
        "pagination": {
            "page": imagesets.page,
            "pages": imagesets.page,
            "total": imagesets.total,
            "per_page": imagesets.per_page,
            "prev": (imagesets.prev_num if imagesets.has_prev else None),
            "next": (imagesets.next_num if imagesets.has_next else None)
        },
        "image_sets": [x.to_dict() for x in imagesets.items]
    }


@flask_login.login_required
def add_imageset(body):
    """
    POST /images_sets

    Create a new image set
    """
    # Check if logged in user has correct permissions
    if not flask_login.current_user.has_role("image-admin"):
        logger.warning("User not authorized")
        abort(401)


    # Check if name is valid (Azure Storage limitations)
    if not AzureWrapper.check_name(body["title"]):
        abort(422, "Name is invalid - must be a valid Azure container name")

    success, sc, response = ImageSet.create(
        flask_login.current_user,
        body["title"],
        metadata=body.get("metadata", None)
    )

    if not success:
        abort(sc, response)
    else:
        return response


@flask_login.login_required
def change_status(imageset_id, body):
    """
    PUT /image_sets/{imageset_id}

    Change the status of an image set
    """
    # Check if logged in user has correct permissions
    if not flask_login.current_user.has_role("image-admin"):
        logger.warning("User not authorized")
        abort(401)

    imageset = ImageSet.query.get(imageset_id)
    if imageset is None:
        abort(404, "Image Set does not exist")

    if imageset.change_status(body["new_status"]):
        return "ok"
    else:
        abort(
            409,
            f'Not allowed to go from "{imageset.status}" to '
            f'"{body["new_status"]}"'
        )


@flask_login.login_required
def get_images(imageset_id, page=1, per_page=10):
    """
    GET /image_sets/{imageset_id}/images

    List all the images in the image set, as ID and download path.
    """
    # Check if logged in user has correct permissions
    if not flask_login.current_user.has_role("image-admin"):
        logger.warning("User not authorized")
        abort(401)

    imageset = ImageSet.query.get(imageset_id)
    if imageset is None:
        abort(404, "Image Set does not exist")

    images = imageset.get_images_paginated(page, per_page)
    return {
        "pagination": {
            "page": images.page,
            "pages": images.page,
            "total": images.total,
            "per_page": images.per_page,
            "prev": (images.prev_num if images.has_prev else None),
            "next": (images.next_num if images.has_next else None)
        },
        "images": [x.to_dict() for x in images.items]
    }


@flask_login.login_required
def add_images(imageset_id, body):
    """
    POST /image_sets/{imageset_id}/images

    Add images to an image set.

    Note: Can only add to "created" status set
    """
    # Check if logged in user has correct permissions
    if not flask_login.current_user.has_role("image-admin"):
        logger.warning("User not authorized")
        abort(401)

    imageset = ImageSet.query.get(imageset_id)
    if imageset is None:
        abort(404, "Image Set does not exist")

    success, sc, msg = imageset.add_images(body)
    if success:
        return "ok"
    else:
        abort(sc, msg)
