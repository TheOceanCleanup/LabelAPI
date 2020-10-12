from common.db import db


class Image(db.Model):
    __tablename__ = "image"


class ImageSet(db.Model):
    __tablename__ = "imageset"
