from common.db import db


class Campaign(db.Model):
    __tablename__ = "campaign"


class CampaignImage(db.Model):
    __tablename__ = "campaign_image"
