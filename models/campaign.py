from common.db import db
from sqlalchemy.dialects.postgresql import JSONB


class Campaign(db.Model):
    __tablename__ = "campaign"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    title = db.Column(db.String(128), nullable=False, unique=True)
    meta_data = db.Column(JSONB, name="metadata", nullable=True)
    status = db.Column(
        db.Enum('created', 'active', 'completed', 'finished',
                name="campaign_status"),
        nullable=False,
        default='created'
    )
    label_translations = db.Column(JSONB)
    date_created = db.Column(db.DateTime, nullable=False,
                             server_default=db.func.now())
    date_started = db.Column(db.DateTime, nullable=True)
    date_completed = db.Column(db.DateTime, nullable=True)
    date_finished = db.Column(db.DateTime, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                              name="created_by", nullable=False)

    created_by = db.relationship(
        "User",
        back_populates="campaigns",
        foreign_keys=created_by_id
    )
    campaign_images = db.relationship(
        "CampaignImage",
        back_populates="campaign"
    )
    attached_roles = db.relationship(
        "Role",
        back_populates="subject"
    )

    def __repr__(self):
        return '<Campaign %r>' % self.title

    def to_dict(self):
        return {
            'campaign_id': self.id,
            'title': self.title,
            'status': self.status,
            'progress': {
                'done': len([x for x in self.campaign_images if x.labeled]),
                'total': len(self.campaign_images)
            },
            'metadata': self.meta_data,
            'label_translations': self.label_translations,
            'date_created': self.date_created,
            'date_started': self.date_started,
            'date_completed': self.date_completed,
            'date_finished': self.date_finished,
            'created_by': self.created_by.email
        }


class CampaignImage(db.Model):
    __tablename__ = "campaign_image"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'),
                            nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'),
                         nullable=False)
    labeled = db.Column(db.Boolean, nullable=False, default=True)

    campaign = db.relationship(
        "Campaign",
        back_populates="campaign_images",
        foreign_keys=campaign_id
    )
    image = db.relationship(
        "Image",
        back_populates="campaign_images",
        foreign_keys=image_id
    )
    objects = db.relationship(
        "Object",
        back_populates="campaign_image"
    )

    def __repr__(self):
        return '<CampaignImage %r-%r>' % (self.campaign, self.image)

    def to_dict(self):
        return {
            'campaignimage_id': self.id,
            'campaign_id': self.campaign_id,
            'image_id': self.image_id,
            'labeled': self.labeled
        }
