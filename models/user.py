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
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import validates
import bcrypt
import flask_login
import secrets
import logging
import os

logger = logging.getLogger("label-api")


class User(db.Model, flask_login.UserMixin):
    __tablename__ = "user"
    __table_args__ = {"schema": os.environ["DB_SCHEMA"]}
    id = db.Column(db.Integer, primary_key=True, unique=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    public_key = db.Column(db.Text, unique=True, nullable=True)
    API_KEY = db.Column(db.String(100), nullable=True)
    API_SECRET = db.Column(BYTEA, nullable=True)
    enabled = db.Column(db.Boolean, nullable=False, default=True)

    campaigns = db.relationship("Campaign", back_populates="created_by")
    imagesets = db.relationship("ImageSet", back_populates="created_by")
    roles = db.relationship("Role", back_populates="user")

    def __repr__(self):
        return "<User %r>" % self.email

    @validates("email")
    def validate_email(self, key, value):
        assert value != ""
        return value

    def is_active(self):
        return self.enabled

    def check_password(self, api_secret):
        return bcrypt.checkpw(api_secret.encode(), self.API_SECRET)

    def has_role(self, role):
        """
        Check if a user has a specific role, but only when no subject is set
        for this role (for subject-bound roles, use User.has_role_on_subject).

        :param role:            Name of the role
        :returns:               Boolean indicating access.
        """
        return any([
            x.role == role and x.subject_type is None and x.subject_id is None
            for x in self.roles
        ])

    def has_role_on_subject(self, role, subject_type, subject_id):
        """
        Check if a user has a certain role on a provided subject, by checking
        if any of his roles match.

        :param role:            Name of the role
        :param subject_type:    Type of the role subject (eg "campaign")
        :param subject_id:      ID of the role subject
        :returns:               Boolean indicating access.
        """
        return any([
            x.has_role_on_subject(role, subject_type, subject_id)
            for x in self.roles
        ])

    def has_access_to_image(self, image):
        """
        Validate that this user has access to a given image, by checking
        if the image is part of any campaigns that this user has access to.

        :param image:       The image object to verify
        :returns:           Boolean indicating access.
        """
        return any([
            self.has_role_on_subject(
                "labeler",
                "campaign",
                campaign_image.campaign_id
            )
            for campaign_image in image.campaign_images
        ])

    def generate_api_key(self):
        """
        Generate a new API key and secret for the user. The secret is stored in
        hashed form.

        :returns:       A tuple containing the key and the secret. This is the
                        only time the secret is known as plain text.
        """
        api_key = secrets.token_hex(16)
        api_secret = secrets.token_hex(16)
        hashed = bcrypt.hashpw(api_secret.encode(), bcrypt.gensalt())
        self.API_KEY = api_key
        self.API_SECRET = hashed
        db.session.commit()

        logger.info("Generated new API key for %s" % self.email)

        return api_key, api_secret

    @staticmethod
    def find_or_create(email, commit=True):
        user = User.query.filter(User.email == email).first()
        if user is None:
            user = User(email=email)
            db.session.add(user)
            if commit:
                db.session.commit()

        return user


class Role(db.Model):
    __tablename__ = "roles"
    __table_args__ = {"schema": os.environ["DB_SCHEMA"]}
    id = db.Column(db.Integer, primary_key=True, unique=True)
    role = db.Column(
        db.Enum("image-admin", "labeler", name="role_types"),
        nullable=False
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey(f"{os.environ['DB_SCHEMA']}.user.id"),
        nullable=False)
    subject_type = db.Column(db.String(128))
    subject_id = db.Column(db.Integer)

    user = db.relationship(
        "User",
        back_populates="roles",
        foreign_keys=user_id
    )

    def has_role_on_subject(self, role, subject_type, subject_id):
        """
        Check if a role object has a certain role on a provided subject.

        :param role:            Name of the role
        :param subject_type:    Type of the role subject (eg "campaign")
        :param subject_id:      ID of the role subject
        :returns:               Boolean indicating access.
        """
        return self.subject_type == subject_type \
            and self.subject_id == subject_id \
            and (role is None or role == self.role)
