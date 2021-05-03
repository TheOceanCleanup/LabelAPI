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

from common.db import db
from common.azure import AzureWrapper
from common.prometheus import number_of_labeled_images, number_of_bounding_boxes_per_image, number_of_unlabeled_images
from sqlalchemy.dialects.postgresql import JSONB
from models.user import User, Role
from models.image import Image
from models.object import Object
from threading import Thread
from flask import current_app
import logging
import os

logger = logging.getLogger("label-api")


class Campaign(db.Model):
    __tablename__ = "campaign"
    __table_args__ = {"schema": os.environ["DB_SCHEMA"]}
    id = db.Column(db.Integer, primary_key=True, unique=True)
    title = db.Column(db.String(128), nullable=False, unique=True)
    meta_data = db.Column(JSONB, name="metadata", nullable=True)
    status = db.Column(
        db.Enum("created", "active", "completed", "finished",
                name="campaign_status"),
        nullable=False,
        default="created"
    )
    label_translations = db.Column(JSONB)
    date_created = db.Column(db.DateTime, nullable=False,
                             server_default=db.func.now())
    date_started = db.Column(db.DateTime, nullable=True)
    date_completed = db.Column(db.DateTime, nullable=True)
    date_finished = db.Column(db.DateTime, nullable=True)
    created_by_id = db.Column(
        db.Integer, db.ForeignKey(f"{os.environ['DB_SCHEMA']}.user.id"),
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
        return "<Campaign %r>" % self.title

    def to_dict(self):
        return {
            "campaign_id": self.id,
            "title": self.title,
            "status": self.status,
            "progress": {
                "done": len([x for x in self.campaign_images if x.labeled]),
                "total": len(self.campaign_images)
            },
            "metadata": self.meta_data,
            "label_translations": self.label_translations,
            "date_created": self.date_created,
            "date_started": self.date_started,
            "date_completed": self.date_completed,
            "date_finished": self.date_finished,
            "created_by": self.created_by.email
        }

    def give_labeler_access(self, user, commit=True):
        """
        Give a specific user the "labeler" role on this campaign.

        :param user:    The user to give access to.
        :param commit:  Whether to commit directly, or postpone this (when
                        called as part of some other flow).
        :returns:       Boolean indicating succes.
        """
        role = Role(
            role="labeler",
            user=user,
            subject_type="campaign",
            subject_id=self.id
        )
        db.session.add(role)
        if commit:
            db.session.commit()

        logger.info("Added labeler role to %s" % user.email)
        return True

    def add_images(self, images):
        """
        Add images to this campaign. Images could be provided by ID or by
        blobstorage path. Only allow adding images if current status of the
        campaign is "created".

        :params images:     List of images to add. Provided as objects, either
                            with "id" or as "filepath" as sole property.
        :returns boolean:   Success or not
        :returns int:       Status code in case of failure - 404 if image does
                            not exist or 409 if status of campaign != created
        :returns string:    Error message in case of failure
        """
        if self.status != "created":
            logger.warning(f"Trying to add images to {self.status} campaign")
            return False, 409, \
                f'Not allowed to add images while status is "{self.status}"'

        for i in images:
            # Find image.
            # NOTE: Connexion has already validated for us that either id or
            #       filepath exists, hence the simple else statement
            if "id" in i:
                image = Image.query.get(i["id"])
            else:
                image = Image.query\
                        .filter(Image.blobstorage_path == i["filepath"])\
                        .first()

            # Check if image exists
            if image is None:
                db.session.rollback()
                return False, 404, "Unknown image provided"

            # All good, add image to campaign, if not yet added (if it is,
            # simply ignore). Note that this is not commited yet, allowing a
            # rollback in case on of the other images can't be added
            if image not in [x.image for x in self.campaign_images]:
                campaign_image = CampaignImage(campaign_id=self.id,
                                               image_id=image.id)
                db.session.add(campaign_image)

        # Now that everything is done with no errors, we can commit.
        db.session.commit()

        # Update metrics
        number_of_unlabeled_images.inc(len(images))

        return True, None, None

    def add_objects(self, objects):
        """
        Add object to this campaign. Only allow adding images if current status
        of the campaign is "active". If at the end of this, an object is
        provided for each image, set status to complete.

        :params objects:    List of images and the objects in them to add.
        :returns boolean:   Success or not
        :returns int:       Status code in case of failure - 404 if image does
                            not exist (in this campaign) or 409 if status of
                            campaign != active
        :returns string:    Error message in case of failure
        """
        if self.status != "active":
            logger.warning(f"Trying to add objects to {self.status} campaign")
            return False, 409, \
                f'Not allowed to add objects while status is "{self.status}"'

        for item in objects:
            # Find campaign image.
            for x in self.campaign_images:
                if x.image_id == item["image_id"]:
                    campaign_image = x
                    break
            else:
                # No object found, image not in campaign
                db.session.rollback()
                return False, 404, \
                    f"Image {item['image_id']} does not exist or is " \
                    "not part of this campaign"

            # As per definition, we remove all existing labels on the
            # current image
            campaign_image.delete_objects(commit=False)

            # Create label object and add to campaign image object. If a
            # translated label is provided, use this as translated label.
            # Otherwise, use the label for both.
            for o in item["objects"]:
                o = Object(
                    campaign_image=campaign_image,
                    label_translated=o.get("label_translated", o["label"]),
                    label_original=o["label"],
                    confidence=o.get("confidence"),
                    x_min=o["bounding_box"]["xmin"],
                    x_max=o["bounding_box"]["xmax"],
                    y_min=o["bounding_box"]["ymin"],
                    y_max=o["bounding_box"]["ymax"]
                )
                db.session.add(o)

            # Set status to labeled for this campaign image
            campaign_image.labeled = True

        # Now that everything is done with no errors, we can commit.
        db.session.commit()

        # Check if all campaign_images are labeled
        if all([x.labeled for x in self.campaign_images]):
            self.change_status("completed")

        # Update the metrics
        number_of_labeled_images.inc(len(objects))
        number_of_unlabeled_images.inc(-len(objects))
        for o in objects:
            number_of_bounding_boxes_per_image.observe(len(o['objects']))

        return True, None, None

    allowed_status_transitions = {
        "created": ["active"],
        "active": ["completed"],
        "completed": ["active", "finished"],
        "finished": []
    }

    def change_status(self, desired_status):
        """
        Change the status of the current set. Check if this is a valid
        transition first.

        :param desired_status:  The status to go to
        :returns boolean:       Success or not
        """
        if desired_status not in self.allowed_status_transitions[self.status]:
            logger.warning(
                f"Attempting invalid status transition on campaign: "
                f"{self.status} to {desired_status}")
            return False

        self.status = desired_status

        if desired_status == 'active':
            self.date_started = db.func.now()
            self.date_completed = None
            self.date_finished = None
        if desired_status == 'completed':
            self.date_completed = db.func.now()
            self.date_finished = None
        if desired_status == 'finished':
            self.date_finished = db.func.now()
        db.session.commit()

        # Handle finishing actions
        if self.status == "finished":
            t = Thread(
                target=self.finish_campaign,
                args=(
                    current_app._get_current_object(),
                    db,
                    self.id,
                    self.title
                )
            )
            t.daemon = True
            t.start()

        return True

    def finish_campaign(self, app, db, campaign_id, campaign_title):
        """
        The campaign is finished. At this point, we need to export two things
        to Azure ML: The images as <campaign_title>_images and the labels as
        <campaign_title>_labels.

        Is meant to be run as a thread, to allow the API to return.

        TODO: For future improvements, consider detecting the datastore based
              on the container component of the image path. For now this does
              not seem to be necessary, as we'll only use one container.
        """
        logger.info("Started thread for finishing campaign")
        paths = []
        labels = []
        campaign_title = campaign_title.lower().replace(" ", "-")

        with app.app_context():
            campaign_images = CampaignImage.query.filter(
                CampaignImage.campaign_id == campaign_id).all()
            for campaign_image in campaign_images:
                path = campaign_image.image.blobstorage_path
                path = path.lstrip("/")
                filepath = "/".join(path.split("/")[1:])

                paths.append(filepath)

                # Determine all objects and add to list.
                labels.append({
                    "image_url": filepath,
                    "label": [
                        {
                            "label": x.label_translated,
                            "bottomX": x.x_min,
                            "topX": x.x_max,
                            "bottomY": x.y_min,
                            "topY": x.y_max
                        }
                        for x in campaign_image.objects
                    ],
                    "label_confidence": [
                        x.confidence for x in campaign_image.objects
                    ]
                })

            logger.info("Successfully parsed campaign image objects from DB")

            AzureWrapper.export_images_to_ML(
                campaign_title + "_images",
                f"Exported dataset as result of the finishing of labeling " +
                f"campaign {campaign_title}",
                paths
            )
            logger.info(
                f"Exported images to AzureML dataset {campaign_title}_images")

            AzureWrapper.export_labels_to_ML(
                campaign_title + "_labels",
                f"Exported labels as result of the finishing of labeling " +
                f"campaign {campaign_title}",
                labels
            )
            logger.info(
                f"Exported labels to AzureML dataset {campaign_title}_labels")

            logger.info("Thread for finishing campaign set done")

    @staticmethod
    def create(labeler_email, title, created_by, metadata=None,
               label_translations=None):
        """
        Create a new campaign, adding the correct users and roles where
        applicable.

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
        db.session.commit()

        # Add role to user that gives access to the campaign
        campaign.give_labeler_access(user, commit=True)

        response = campaign.to_dict()
        response["access_token"] = {
            "apikey": key,
            "apisecret": secret
        }
        return response


class CampaignImage(db.Model):
    __tablename__ = "campaign_image"
    __table_args__ = {"schema": os.environ["DB_SCHEMA"]}
    id = db.Column(db.Integer, primary_key=True, unique=True)
    campaign_id = db.Column(
        db.Integer, db.ForeignKey(f"{os.environ['DB_SCHEMA']}.campaign.id"),
        nullable=False)
    image_id = db.Column(
        db.Integer, db.ForeignKey(f"{os.environ['DB_SCHEMA']}.image.id"),
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
        return "<CampaignImage %r-%r>" % (self.campaign, self.image)

    def to_dict(self):
        return {
            "campaignimage_id": self.id,
            "campaign_id": self.campaign_id,
            "image_id": self.image_id,
            "labeled": self.labeled
        }

    def delete_objects(self, commit=True):
        """
        Delete all attached objects.
        """
        for o in self.objects:
            db.session.delete(o)

        if commit:
            db.session.commit()
