from common.db import db


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    email = db.Column(db.String(128), nullable=False, unique=True)

    campaigns = db.relationship("Campaign", back_populates="created_by")
    imagesets = db.relationship("ImageSet", back_populates="created_by")
