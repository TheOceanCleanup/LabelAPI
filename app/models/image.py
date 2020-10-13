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
        back_populates="images"
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
                              nullable=False)

    created_by = db.relationship(
        "User",
        back_populates="campaigns",
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
