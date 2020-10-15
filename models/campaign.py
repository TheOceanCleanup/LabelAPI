from common.db import db
from sqlalchemy.dialects.postgresql import JSONB
from models.user import User, Role
from models.image import Image


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

    def give_labeler_access(self, user, commit=True):
        role = Role(
            role='labeler',
            user=user,
            subject_type='campaign',
            subject_id=self.id
        )
        db.session.add(role)
        if commit:
            db.session.commit()
        return True

    def add_images(self, images):
        """
        Add images to this campaign. Images could be provided by ID or by
        blobstorage path. Only allow adding images if current status of the
        campaign is "created".

        :params images:     List of images to add. Provided as objects, either
                            with 'id' or as 'filepath' as sole property.
        :returns boolean:   Success or not
        :returns int:       Status code in case of failure - 404 if image does
                            not exist, 400 if invalid request or 409 if status
                            of campaign != created
        :returns string:    Error message in case of failure
        """
        if self.status != 'created':
            return False, 409, \
                f'Not allowed to add images while status is "{self.status}"'

        for i in images:
            # Find image.
            # NOTE: Connexion has already validated for us that either id or
            #       filepath exists, hence the simple else statement
            if 'id' in i:
                image = Image.query.get(i['id'])
            else:
                image = Image.query\
                        .filter(Image.blobstorage_path == i['filepath'])\
                        .first()

            # Check if image exists
            if image is None:
                db.session.rollback()
                return False, 404, "Unknown image provided"

            # All good, add image to campaign, if not yet added (if it is,
            # simply ignore). Note that this is not commited yet, allowing a
            # rollback in case on of the other images can't be added
            if not image in [x.image for x in self.campaign_images]:
                campaign_image = CampaignImage(campaign_id=self.id,
                                               image_id=image.id)
                db.session.add(campaign_image)

        # Now that everything is done with no errors, we can commit.
        db.session.commit()
        return True, None, None

    @staticmethod
    def create(labeler_email, title, created_by, metadata=None,
               label_translations=None):
        """
        Create a new campaign, adding the correct users and roles where
        applicable.

        #TODO: Do we need to add some exception / rollback here?

        :param labeler_email:       E mail address for the labeler user
        :param title:               Title for the campaign. Should be unique
        :param created_by:          User that is creating this campaign
        :param metadata:            Metadata to store with the campaign
        :param label_translations:  Translations between labelers and internal
                                    labels
        :returns:                   Campaign metadata dict, expanded with the
                                    (possibly generated) cretentials
        """
        # Find if a user already exists, otherwise create it
        user = User.find_or_create(labeler_email, commit=False)

        # Check if the user already has an API key
        if user.API_KEY is not None:
            key = user.API_KEY
            secret = None
        else:
            key, secret = user.generate_api_key()

        # Create campaign itself
        campaign = Campaign(
            title=title,
            meta_data=metadata,
            label_translations=label_translations,
            created_by=created_by
        )
        db.session.add(campaign)

        # Add role to user that gives access to the campaign
        campaign.give_labeler_access(user, commit=False)

        db.session.commit()

        response = campaign.to_dict()
        response['access_token'] = {
            "apikey": key,
            "apisecret": secret
        }
        return response


class CampaignImage(db.Model):
    __tablename__ = "campaign_image"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'),
                            nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'),
                         nullable=False)
    labeled = db.Column(db.Boolean, nullable=False, default=False)

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
