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
from flask import abort, redirect
from models.image import Image
from models.campaign import Campaign
import logging

logger = logging.getLogger("label-api")


@flask_login.login_required
def list_images(page=1, per_page=10):
    """
    GET /images

    List all images
    """
    # Check if logged in user has correct permissions
    if not flask_login.current_user.has_role("image-admin"):
        logger.warning("User not authorized")
        abort(401)

    images = Image.query.order_by(Image.id).paginate(page=page,
                                                     per_page=per_page)
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
def get_image_url(image_id):
    """
    GET /images/{image_id}

    Get an image. If authenticated, this will redirect to the actual image in
    blobstorage, with a SAS token for access.

    NOTE: This is implemented the "user-friendly" way. Alternatively, the
          check if a user has access to the image
          (current_user.has_access_to_image(image)) could return 404 as well,
          preventing a non-authorized user from knowing what images exist.
    """
    # First get image object
    image = Image.query.get(image_id)
    if image is None:
        abort(404, "Image does not exist")

    # Check permissions for the image
    if not (flask_login.current_user.has_role("image-admin")
            or flask_login.current_user.has_access_to_image(image)):
        logger.warning("User not authorized")
        abort(401)

    url = image.get_azure_url()

    return redirect(url, 303)


@flask_login.login_required
def get_objects(image_id, campaigns=[]):
    """
    GET /images/{image_id}/objects

    Show the objects for a certain image. Optionally, a list of campaign IDs
    can be provided. If multiple are provided, objects are returned for the
    first campaign in the list for which objects exist for this image - meaning
    only the objects from exactly one campaign will ever be returned. If no
    campaign is provided, objects from the first finished campaign will be
    returned, prioritized by the most recent campaign.
    """
    # Check if logged in user has correct permissions
    if not flask_login.current_user.has_role("image-admin"):
        logger.warning("User not authorized")
        abort(401)

    image = Image.query.get(image_id)
    if image is None:
        abort(404, "Image does not exist")

    # Find the campaigns requested
    campaign_objs = []
    for campaign_id in campaigns:
        campaign = Campaign.query.get(campaign_id)
        if campaign is None:
            abort(404, f"Unknown campaign {campaign_id}")

        campaign_objs.append(campaign)

    objects = image.get_objects(campaigns=campaign_objs)

    return [
        x.to_dict()
        for x in objects
    ]
