def list_campaigns(page=1, per_page=10):
    """
    GET /campaigns

    List all the labeling campaigns in the database
    """
    return "Not Implemented: campaigns.list_campaigns"


def get_metadata(campaign_id):
    """
    GET /campaigns/{campaign_id}

    /campaigns/{campaign_id}
    """
    return "Not Implemented: campaigns.get_metadata"


def change_status(campaign_id, body):
    """
    PUT /campaigns/{campaign_id}

    Change the status of a campaign
    """
    return "Not Implemented: campaigns.change_status"


def get_objects(campaign_id):
    """
    GET /campaigns/{campaign_id}/objects

    Get a list of all images in a campaign, a download link for the image and
    the objects found in that image.
    """
    return "Not Implemented: campaigns.get_objects"


def get_images(campaign_id, page=1, per_page=1000):
    """
    GET /campaigns/{campaign_id}/images

    Get a list of images for a campaign.
    """
    return "Not Implemented: campaigns.get_images"


def add_campaign(body):
    """
    POST /campaigns

    Create a new campaign
    """
    return "Not Implemented: campaigns.add_campaign"


def add_images(campaign_id, body):
    """
    POST /campaigns/{campaign_id}/images

    Add images to a campaign
    """
    return "Not Implemented: campaigns.add_images"


def add_objects(campaign_id, body):
    """
    PUT /campaigns/{campaign_id}/objects

    Handle the delivery of new labeled objects for a campaign.
    """
    return "Not Implemented: campaigns.add_objects"
