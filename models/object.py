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
import os


class Object(db.Model):
    __tablename__ = "object"
    __table_args__ = {"schema": os.environ["DB_SCHEMA"]}
    id = db.Column(db.Integer, primary_key=True, unique=True)
    campaign_image_id = db.Column(
        db.Integer,
        db.ForeignKey(f"{os.environ['DB_SCHEMA']}.campaign_image.id"),
        nullable=False)
    label_translated = db.Column(db.String(128), nullable=False)
    label_original = db.Column(db.String(128), nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    date_added = db.Column(db.DateTime, nullable=False,
                           server_default=db.func.now())
    x_min = db.Column(db.Integer, nullable=False)
    x_max = db.Column(db.Integer, nullable=False)
    y_min = db.Column(db.Integer, nullable=False)
    y_max = db.Column(db.Integer, nullable=False)

    campaign_image = db.relationship(
        "CampaignImage",
        back_populates="objects",
        foreign_keys=campaign_image_id
    )

    def __repr__(self):
        return "<Object labeled %r in image %r>" % \
            (self.label_translated, self.campaign_image.image)

    def to_dict(self):
        return {
            "object_id": self.id,
            "image_id": self.campaign_image.image.id,
            "campaign_id": self.campaign_image.campaign.id,
            "label": self.label_translated,
            "bounding_box": {
                "xmin": self.x_min,
                "xmax": self.x_max,
                "ymin": self.y_min,
                "ymax": self.y_max
            },
            "confidence": self.confidence,
            "date_added": self.date_added
        }
