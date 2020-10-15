from common.auth import flask_login


@flask_login.login_required
def list_campaigns(page=1, per_page=10):
    """
    GET /campaigns

    List all the labeling campaigns in the database
    """
    return "Not Implemented: campaigns.list_campaigns"


@flask_login.login_required
def get_metadata(campaign_id):
    """
    GET /campaigns/{campaign_id}

    /campaigns/{campaign_id}
    """
    return "Not Implemented: campaigns.get_metadata"


@flask_login.login_required
def change_status(campaign_id, body):
    """
    PUT /campaigns/{campaign_id}

    Change the status of a campaign
    """
    return "Not Implemented: campaigns.change_status"


@flask_login.login_required
def get_objects(campaign_id):
    """
    GET /campaigns/{campaign_id}/objects

    Get a list of all images in a campaign, a download link for the image and
    the objects found in that image.
    """
    return "Not Implemented: campaigns.get_objects"


@flask_login.login_required
def get_images(campaign_id, page=1, per_page=1000):
    """
    GET /campaigns/{campaign_id}/images

    Get a list of images for a campaign.
    """
    return "Not Implemented: campaigns.get_images"


@flask_login.login_required
def add_campaign(body):
    """
    POST /campaigns

    Create a new campaign

    Note: Check if user already exists. If so use that. Check also if user
    already has a key. If not, create.
    """
    return "Not Implemented: campaigns.add_campaign"


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
