from common.db import db
from sqlalchemy.dialects.postgresql import JSONB
from common.azure import AzureWrapper
from datetime import datetime, timedelta
import os
import logging
from flask import current_app
from threading import Thread


logger = logging.getLogger("label-api")


class Image(db.Model):
    __tablename__ = "image"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    blobstorage_path = db.Column(db.String(1024), nullable=False, unique=True)
    imageset_id = db.Column(db.Integer, db.ForeignKey('imageset.id'),
                            nullable=True)
    date_taken = db.Column(db.DateTime, nullable=True)
    location_taken = db.Column(db.String(1024), nullable=True)
    type = db.Column(db.String(128), nullable=True)
    meta_data = db.Column(JSONB, name="metadata", nullable=True)
    tss_id = db.Column(db.String(128), nullable=True)
    filetype = db.Column(db.String(128), nullable=True)
    filesize = db.Column(db.Integer, nullable=True)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    date_added = db.Column(db.DateTime, nullable=False,
                           server_default=db.func.now())

    imageset = db.relationship(
        "ImageSet",
        back_populates="images",
        foreign_keys=imageset_id
    )
    campaign_images = db.relationship(
        "CampaignImage",
        back_populates="image"
    )

    def __repr__(self):
        return '<Image %r>' % self.blobstorage_path

    def to_dict(self):
        if self.imageset is not None:
            imageset = {
                'imageset_id': self.imageset.id,
                'title': self.imageset.title
            }
        else:
            imageset = None

        return {
            'image_id': self.id,
            'blobstorage_path': self.blobstorage_path,
            'imageset': imageset,
            'date_taken': self.date_taken,
            'location_taken': self.location_taken,
            'type': self.type,
            'metadata': self.meta_data,
            'tss_id': self.tss_id,
            'file': {
                'filetype': self.filetype,
                'filesize': self.filesize,
                'dimensions': {
                    'width': self.width,
                    'height': self.height
                }
            }
        }

    def get_api_url(self):
        """
        Return the (relative) url that points towards the redirected download.
        """
        return f"/images/{self.id}"

    def get_azure_url(self):
        """
        Return the Azure direct download URI, including a SAS token for access.
        """
        return AzureWrapper.get_sas_url(
            self.blobstorage_path,
            expires=datetime.utcnow() + \
                timedelta(days=int(os.environ.get("IMAGE_READ_TOKEN_VALID_DAYS",
                                                  7))),
            permissions=["read"]
        )

    def get_objects(self, campaigns=[]):
        """
        Get the objects in this image. If these exist for multiple  campaigns,
        priotize them either by the provided campaigns (in that order) or by
        date of the latest campaign otherwise. In the second case, only labels
        from finished campaigns will be returned.

        :param campaigns:   List of campaign objects to find the objects for,
                            in order.
        :returns:           List of objects in the image
        """
        # Find campaign_image relevant here
        campaign_image = None
        if len(campaigns) > 0:
            for campaign in campaigns:
                # Check if there is a campaign_image object like this, and if
                # it has attached objects
                for ci in self.campaign_images:
                    if ci.campaign == campaign and ci.labeled:
                        campaign_image = ci
                        break
                if campaign_image is not None:
                    break
        else:
            # Find the most recent finished campaign
            finished_campaign_images = [
                x for x in self.campaign_images
                if x.campaign.status == 'finished'
            ]
            if len(finished_campaign_images) > 0:
                campaign_image = sorted(finished_campaign_images,
                                        key=lambda x: x.campaign.date_finished,
                                        reverse=True)[0]

        if campaign_image is not None:
            return sorted(campaign_image.objects, key=lambda x: x.id)
        else:
            return []


class ImageSet(db.Model):
    __tablename__ = "imageset"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    title = db.Column(db.String(128), nullable=False, unique=True)
    status = db.Column(
        db.Enum('created', 'finished', name="imageset_status"),
        nullable=False,
        default='created'
    )
    meta_data = db.Column(JSONB, name="metadata", nullable=True)
    blobstorage_path = db.Column(db.String(1024), nullable=True, unique=True)
    date_created = db.Column(db.DateTime, nullable=False,
                             server_default=db.func.now())
    date_finished = db.Column(db.DateTime, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                              name="created_by", nullable=False)

    created_by = db.relationship(
        "User",
        back_populates="imagesets",
        foreign_keys=created_by_id
    )
    images = db.relationship(
        "Image",
        back_populates="imageset"
    )

    def __repr__(self):
        return '<ImageSet %r>' % self.title

    def to_dict(self):
        return {
            'imageset_id': self.id,
            'title': self.title,
            'status': self.status,
            'metadata': self.meta_data,
            'blobstorage_path': self.blobstorage_path,
            'date_created': self.date_created,
            'date_finished': self.date_finished,
            'created_by': self.created_by.email
        }

    def get_images_paginated(self, page=1, per_page=10):
        return Image.query\
            .filter(Image.imageset == self)\
            .order_by(Image.id)\
            .paginate(page=page, per_page=per_page)

    allowed_status_transitions = {
        'created': ['finished'],
        'finished': []
    }

    def change_status(self, desired_status):
        """
        Change the status of the current set. Check if this is a valid
        transition first.

        :param desired_status:  The status to go to
        :returns boolean:       Success or not
        """
        if desired_status not in self.allowed_status_transitions[self.status]:
            return False

        self.status = desired_status
        db.session.commit()

        # Handle finishing actions
        if self.status == 'finished':
            t = Thread(
                target=self.finish_set,
                args=(current_app._get_current_object(), db)
            )
            t.start()

        return True

    def finish_set(self, app, db):
        """
        Perform the finishing actions on an image set. This is the following:
        - Copy the files from the temporary dropbox to the final location
        - Add the files into the image table
        - Set the path of the image set to the new storage location
        - Remove the temporary dropbox

        Is meant to be run as a thread, hence the explicit passing of the app
        and DB objects.

        Requires the following environment variables to be set:
        AZURE_STORAGE_IMAGESET_CONTAINER
        AZURE_STORAGE_IMAGESET_FOLDER

        :param app:         The app object this is run as (use
                            flask.current_app._get_current_object())
        :param db:          The database object
        """
        logger.info("Starting thread for finishing image set")

        target_container = os.environ["AZURE_STORAGE_IMAGESET_CONTAINER"]
        folder_name = os.environ["AZURE_STORAGE_IMAGESET_FOLDER"] + "/" + \
                      self.title.lower().replace(" ", "-")

        dropbox = self.blobstorage_path

        # Copy all files from dropbox to final folder
        files = AzureWrapper.copy_contents(
            dropbox,
            "",
            target_container,
            folder_name
        )

        logger.debug("Files copied")

        if not files:
            # Failed to copy
            return

        with app.app_context():
            # Add images to DB
            for f in files:
                path = f"{target_container}/{folder_name}/{f.name}"

                # Determine filetype, width and height
                filetype, width, height = AzureWrapper.get_image_information(
                    path
                )

                img = Image(
                    blobstorage_path=path,
                    imageset=self,
                    filetype=filetype,
                    filesize=f.properties.content_length,
                    width=width,
                    height=height
                )
                db.session.add(img)

            # Change blobstorage path
            self.blobstorage_path = f"{target_container}/{folder_name}"

            db.session.commit()

        logger.debug("Image objects created")

        # Delete dropbox
        AzureWrapper.delete_container(dropbox)

        logger.info("Thread for finishing image set done")

    def add_images(self, images):
        """
        Add images to this set. Images could be provided by ID or by
        blobstorage path. Only allow adding images if current status of the
        image set is "created".

        :params images:     List of images to add. Provided as objects, either
                            with 'id' or as 'filepath' as sole property.
        :returns boolean:   Success or not
        :returns int:       Status code in case of failure - 404 if image does
                            not exist, 400 if invalid request or 409 if status
                            of imageset != created or the image is already
                            attached to another set
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

            # Check if image is not yet assigned to another imageset
            if image.imageset is not None:
                db.session.rollback()
                return False, 409, \
                    f"Image {image.id} ({image.blobstorage_path}) is " \
                    "already assigned to an image set"

            # All good, update image. Note that this is not commited yet,
            # allowing a rollback in case on of the other images can't be added
            image.imageset = self

        # Now that everything is done with no errors, we can commit.
        db.session.commit()
        return True, None, None

    @staticmethod
    def create(created_by, title, metadata=None):
        """
        Create a new image set. Will also create the respective folder on the
        blob storage.

        :param created_by:  User that creates the set
        :param title:       Title of the imageset
        :param metadata:    Optional metadata dict to store with the image set.
        :returns:           Tuple with: success (boolean), status code (int),
                            response (msg in case of error, imageset in case of
                            success).
        """
        # Check if title is still available
        if ImageSet.query.filter(
                    db.func.lower(ImageSet.title) == title.lower()
                ).first() is not None:
            return False, 409, "Image Set title is already taken"

        # Create dropbox container on blobstorage
        created_container = AzureWrapper.create_container(title)
        if not created_container:
            return False, 500, "Failed to create container in Blob Storage"

        imageset = ImageSet(
            title=title,
            meta_data=metadata,
            blobstorage_path=created_container,
            created_by=created_by
        )
        db.session.add(imageset)
        db.session.commit()

        response = imageset.to_dict()
        response["dropbox_url"] = AzureWrapper.get_container_sas_url(
            created_container,
            expires=datetime.utcnow() + \
                    timedelta(days=int(
                        os.environ.get("IMAGESET_UPLOAD_TOKEN_VALID_DAYS", 7))
                    ),
            permissions=["write", "list", "read", "delete"]
        )

        return True, 200, response
