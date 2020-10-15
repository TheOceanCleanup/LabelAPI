from common.auth import flask_login
from models.campaign import Campaign, CampaignImage
from flask import abort


@flask_login.login_required
def list_campaigns(page=1, per_page=10):
    """
    GET /campaigns

    List all the labeling campaigns in the database
    """
    # Check if logged in user has correct permissions
    if not flask_login.current_user.has_role('image-admin'):
        abort(401)

    campaigns = Campaign.query.order_by(Campaign.id)\
                              .paginate(page=page, per_page=per_page)
    return {
        'pagination': {
            'page': campaigns.page,
            'pages': campaigns.page,
            'total': campaigns.total,
            'per_page': campaigns.per_page,
            'prev': (campaigns.prev_num if campaigns.has_prev else None),
            'next': (campaigns.next_num if campaigns.has_next else None)
        },
        'campaigns': [x.to_dict() for x in campaigns.items]
    }


@flask_login.login_required
def get_metadata(campaign_id):
    """
    GET /campaigns/{campaign_id}

    Get the metadata of a given campaign
    """
    # Check if logged in user has correct permissions
    if not flask_login.current_user.has_role('image-admin'):
        abort(401)

    campaign = Campaign.query.get(campaign_id)
    if campaign is None:
        abort(404)

    return campaign.to_dict()


@flask_login.login_required
def change_status(campaign_id, body):
    """
    PUT /campaigns/{campaign_id}

    Change the status of a campaign
    """
    return "Not Implemented: campaigns.change_status"


@flask_login.login_required
def get_objects(campaign_id, page=1, per_page=1000):
    """
    GET /campaigns/{campaign_id}/objects

    Get a list of all images in a campaign, a download link for the image and
    the objects found in that image.
    """
    # Check if logged in user has correct permissions.
    if not flask_login.current_user.has_role('image-admin'):
        abort(401)

    campaign = Campaign.query.get(campaign_id)
    if campaign is None:
        abort(404)

    # Access to campaign images through query, to allow for pagination
    c_images = CampaignImage.query\
                            .filter(CampaignImage.campaign_id == campaign.id)\
                            .order_by(CampaignImage.id)\
                            .paginate(page=page, per_page=per_page)
    return {
        'pagination': {
            'page': c_images.page,
            'pages': c_images.page,
            'total': c_images.total,
            'per_page': c_images.per_page,
            'prev': (c_images.prev_num if c_images.has_prev else None),
            'next': (c_images.next_num if c_images.has_next else None)
        },
        'images': [
            {
                "image_id": x.image.id,
                "url": x.image.get_api_url(),
                "objects": [
                    y.to_dict()
                    for y in sorted(x.objects, key=lambda y: y.id)
                ]
            }
            for x in c_images.items
        ]
    }


@flask_login.login_required
def get_images(campaign_id, page=1, per_page=1000):
    """
    GET /campaigns/{campaign_id}/images

    Get a list of images for a campaign.
    """
    # Check if logged in user has correct permissions. Can be either
    # image-admin or labeler on the specific campaign
    if not (
            flask_login.current_user.has_role('image-admin') or
            flask_login.current_user.has_role_on_subject(
                'labeler',
                'campaign',
                campaign_id)
            ):
        abort(401)

    campaign = Campaign.query.get(campaign_id)
    if campaign is None:
        abort(404)

    # Access to campaign images through query, to allow for pagination
    c_images = CampaignImage.query\
                            .filter(CampaignImage.campaign_id == campaign.id)\
                            .order_by(CampaignImage.id)\
                            .paginate(page=page, per_page=per_page)
    return {
        'pagination': {
            'page': c_images.page,
            'pages': c_images.page,
            'total': c_images.total,
            'per_page': c_images.per_page,
            'prev': (c_images.prev_num if c_images.has_prev else None),
            'next': (c_images.next_num if c_images.has_next else None)
        },
        'images': [
            {
                "image_id": x.image.id,
                "url": x.image.get_api_url()
            }
            for x in c_images.items
        ]
    }


@flask_login.login_required
def add_campaign(body):
    """
    POST /campaigns

    Create a new campaign

    Note: Check if user already exists. If so use that. Check also if user
    already has a key. If not, create.
    """
    # Check if logged in user has correct permissions.
    if not flask_login.current_user.has_role('image-admin'):
        abort(401)

    # Check if there's already a campaign with this title
    if Campaign.query.filter(Campaign.title == body['title']).first() \
            is not None:
        abort(409, "Another campaign with this name already exists")

    response = Campaign.create(
        body['labeler_email'],
        body['title'],
        flask_login.current_user,
        metadata=body.get('metadata', None),
        label_translations=body.get('label_translations', None)
    )

    return response


@flask_login.login_required
def add_images(campaign_id, body):
    """
    POST /campaigns/{campaign_id}/images

    Add images to a campaign

    Note: Can only add to active set
    """
    return "Not Implemented: campaigns.add_images"


@flask_login.login_required
def add_objects(campaign_id, body):
    """
    PUT /campaigns/{campaign_id}/objects

    Handle the delivery of new labeled objects for a campaign.

    Note: Can only add to active set
    """
    return "Not Implemented: campaigns.add_objects"
