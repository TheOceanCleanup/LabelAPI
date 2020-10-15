from common.db import db
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import validates
import bcrypt
import flask_login


class User(db.Model, flask_login.UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    public_key = db.Column(db.Text, unique=True, nullable=True)
    API_KEY = db.Column(db.String(100), nullable=True)
    API_SECRET = db.Column(BYTEA, nullable=True)

    campaigns = db.relationship("Campaign", back_populates="created_by")
    imagesets = db.relationship("ImageSet", back_populates="created_by")
    roles = db.relationship("Role", back_populates="user")

    def __repr__(self):
        return '<User %r>' % self.email

    @validates('email')
    def validate_email(self, key, value):
        assert value != ''
        return value

    def check_password(self, api_secret):
        return bcrypt.checkpw(api_secret.encode(), self.API_SECRET)

    def has_role(self, role):
        return any([
            x.role == role
            for x in self.roles
        ])

    def has_role_on_subject(self, role, subject_type, subject_id):
        return any([
            x.has_role_on_subject(role, subject_type, subject_id)
            for x in self.roles
        ])


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    role = db.Column(
        db.Enum('image-admin', 'labeler', name="role_types"),
        nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_type = db.Column(db.String(128))
    subject_id = db.Column(db.Integer)

    user = db.relationship(
        "User",
        back_populates="roles",
        foreign_keys=user_id
    )

    def has_role_on_subject(self, role, subject_type, subject_id):
        return self.subject_type == subject_type \
            and self.subject_id == subject_id \
            and (role is None or role == self.role)
