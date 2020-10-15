from models.user import User, Role
from models.image import Image, ImageSet
from models.campaign import Campaign, CampaignImage
from models.object import Object
import bcrypt


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
        title="some image set",
        status="created",
        blobstorage_path="/some/otherpath",
        date_created=now,
        created_by=user
    )
    imgset2 = ImageSet(
        id=2,
        title="some other image set",
        status="created",
        blobstorage_path="/some/path",
        date_created=now,
        created_by=user
    )
    imgset3 = ImageSet(
        id=3,
        title="A third set",
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
        location_taken="Dominican Republic - Bridge A",
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
        location_taken="Dominican Republic - Bridge A",
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
        title="Some Campaign",
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
        title="Some other Campaign",
        status="finished",
        date_created=yesterday,
        date_started=yesterday,
        date_completed=yesterday,
        date_finished=yesterday,
        created_by=user
    )
    campaign3 = Campaign(
        id=3,
        title="A third Campaign",
        status="active",
        date_created=now,
        date_started=now,
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
        label_translated=label_translated
                         if label_translated is not None
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
