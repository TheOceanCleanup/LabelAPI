from common.db import db
from sqlalchemy.dialects.postgresql import BYTEA
import bcrypt
import flask_login


class User(db.Model, flask_login.UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    email = db.Column(db.String(128), nullable=False, unique=True)
    API_KEY = db.Column(db.String(100), nullable=False)
    API_SECRET = db.Column(BYTEA, nullable=False)

    campaigns = db.relationship("Campaign", back_populates="created_by")
    imagesets = db.relationship("ImageSet", back_populates="created_by")
    roles = db.relationship("Role", back_populates="user")

    def __repr__(self):
        return '<User %r>' % self.email

    def check_password(self, api_secret):
        return bcrypt.checkpw(api_secret.encode(), self.API_SECRET)

    def is_image_admin(self):
        return any([x.role == 'image-admin' for x in self.roles])


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    role = db.Column(
        db.Enum('image-admin', 'labeler', name="role_types"),
        nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('campaign.id'),
                           name="subject", nullable=True)

    user = db.relationship(
        "User",
        back_populates="roles",
        foreign_keys=user_id
    )
    subject = db.relationship(
        "Campaign",
        back_populates="attached_roles",
        foreign_keys=subject_id
    )
