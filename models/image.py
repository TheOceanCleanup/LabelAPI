from common.db import db
from sqlalchemy.dialects.postgresql import JSONB


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
        return True

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
