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

from models.user import User, Role
from models.image import Image, ImageSet
from models.campaign import Campaign, CampaignImage
from models.object import Object
import bcrypt
import datetime


def get_headers(db):
    api_key = "123"
    api_secret = "foobar"
    hashed = bcrypt.hashpw(api_secret.encode(), bcrypt.gensalt())
    user = User(
        email="test@example.com",
        API_KEY=api_key,
        API_SECRET=hashed
    )
    db.session.add(user)

    role = Role(
        role='image-admin',
        user=user
    )
    db.session.add(role)

    db.session.commit()

    headers = {
        'Authentication-Key': api_key,
        'Authentication-Secret': api_secret
    }

    return headers


def add_user(db):
    user = User(
        email="someone@example.com",
        API_KEY="",
        API_SECRET="".encode()
    )
    db.session.add(user)
    db.session.commit()
    return user


def add_labeler_user(db, subject_type, subject_id):
    api_key = "label-key"
    api_secret = "some secret value"
    hashed = bcrypt.hashpw(api_secret.encode(), bcrypt.gensalt())
    user = User(
        email="labeler@example.com",
        API_KEY=api_key,
        API_SECRET=hashed
    )
    db.session.add(user)

    role = Role(
        role='labeler',
        user=user,
        subject_type=subject_type,
        subject_id=subject_id
    )
    db.session.add(role)

    db.session.commit()

    headers = {
        'Authentication-Key': api_key,
        'Authentication-Secret': api_secret
    }

    return headers


def add_imagesets(db, user, now):
    imgset1 = ImageSet(
        id=1,
        title="some-image-set",
        status="created",
        blobstorage_path="/some/otherpath",
        date_created=now,
        created_by=user
    )
    imgset2 = ImageSet(
        id=2,
        title="some-other-image-set",
        status="created",
        blobstorage_path="/some/path",
        date_created=now,
        created_by=user
    )
    imgset3 = ImageSet(
        id=3,
        title="a-third-set",
        status="finished",
        meta_data={
            'note': 'Special Drone footage'
        },
        blobstorage_path="/some/thirdpath",
        date_created=now,
        date_finished=now,
        created_by=user
    )
    db.session.add(imgset1)
    db.session.add(imgset2)
    db.session.add(imgset3)
    db.session.commit()
    return imgset1, imgset2, imgset3


def add_images(db, imgset, now):
    img1 = Image(
        id=1,
        blobstorage_path="/some/path/file1.png",
        type="drone",
        meta_data={'source': 'video1.mp4', 'frame': 1337},
        date_added=now
    )
    img2 = Image(
        id=2,
        blobstorage_path="/some/otherpath/file2.png",
        imageset=imgset,
        type="bridge",
        location_description="Dominican Republic - Bridge A",
        filetype="JPEG",
        filesize=123456,
        width=1920,
        height=1080,
        date_taken=now,
        date_added=now
    )
    img3 = Image(
        id=3,
        blobstorage_path="/some/otherpath/file3.png",
        imageset=imgset,
        type="bridge",
        location_description="Dominican Republic - Bridge A",
        lat=51.920801,
        lon=4.4662474,
        filetype="JPEG",
        filesize=123321,
        width=1920,
        height=1080,
        date_taken=now,
        date_added=now
    )
    db.session.add(img1)
    db.session.add(img2)
    db.session.add(img3)
    return img1, img2, img3


def add_campaigns(db, user, now, yesterday):
    campaign1 = Campaign(
        id=1,
        title="some-campaign",
        meta_data={
            "key": "value"
        },
        status="finished",
        label_translations={"PET": "plastic"},
        date_created=now,
        date_started=now,
        date_completed=now,
        date_finished=now,
        created_by=user
    )
    campaign2 = Campaign(
        id=2,
        title="some-other-campaign",
        status="finished",
        date_created=yesterday,
        date_started=yesterday,
        date_completed=yesterday,
        date_finished=yesterday,
        created_by=user
    )
    campaign3 = Campaign(
        id=3,
        title="a-third-campaign",
        status="created",
        date_created=now,
        date_started=None,
        date_completed=None,
        date_finished=None,
        created_by=user
    )
    db.session.add(campaign1)
    db.session.add(campaign2)
    db.session.add(campaign3)
    db.session.commit()
    return campaign1, campaign2, campaign3


def add_image_to_campaign(db, image, campaign):
    campaign_image = CampaignImage(
        campaign=campaign,
        image=image,
        labeled=True
    )
    db.session.add(campaign_image)
    db.session.commit()
    return campaign_image


def add_object(db, now, campaign_image, label, label_translated, confidence,
               bbox):
    obj = Object(
        campaign_image=campaign_image,
        label_translated=label_translated if label_translated is not None
                         else label,
        label_original=label,
        confidence=confidence,
        x_min=bbox[0],
        x_max=bbox[1],
        y_min=bbox[2],
        y_max=bbox[3],
        date_added=now
    )
    db.session.add(obj)
    db.session.commit()
    return obj


def create_basic_testset(db, obj=True):
    now, yesterday, user, img1, img2, img3, campaign1, campaign2, campaign3 = \
        add_images_campaigns(db)

    ci1 = add_image_to_campaign(db, img1, campaign3)
    ci2 = add_image_to_campaign(db, img2, campaign3)
    ci3 = add_image_to_campaign(db, img3, campaign1)

    if obj:
        obj1 = add_object(db, now, ci1, "label1", None, None, [1, 2, 3, 4])
        obj2 = add_object(db, now, ci1, "label2", None, None, [2, 3, 4, 5])
        obj3 = add_object(db, now, ci2, "label3", "translated_label3", 0.87,
                          [6, 7, 8, 9])

    ci2.labeled = False
    db.session.commit()
    return now, yesterday


def add_images_campaigns(db):
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)
    campaign1, campaign2, campaign3 = add_campaigns(db, user, now, yesterday)
    return now, yesterday, user, img1, img2, img3, campaign1, campaign2, \
        campaign3
