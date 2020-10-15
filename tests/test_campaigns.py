from tests.shared import get_headers, add_user, add_imagesets, add_images, \
    add_campaigns, add_image_to_campaign, add_object, add_labeler_user
from models.campaign import Campaign
from models.user import User, Role
import datetime
import bcrypt


def create_basic_testset(db):
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)
    campaign1, campaign2, campaign3 = add_campaigns(db, user, now, yesterday)
    ci1 = add_image_to_campaign(db, img1, campaign3)
    ci2 = add_image_to_campaign(db, img2, campaign3)
    ci3 = add_image_to_campaign(db, img3, campaign1)

    obj1 = add_object(db, now, ci1, 'label1', None, None, [1, 2, 3, 4])
    obj2 = add_object(db, now, ci1, 'label2', None, None, [2, 3, 4, 5])
    obj3 = add_object(db, now, ci2, 'label3', 'translated_label3', 0.87,
                      [6, 7, 8, 9])

    ci2.labeled = False
    db.session.commit()
    return now, yesterday


def test_list_campaigns(client, app, db, mocker):
    headers = get_headers(db)

    now, yesterday = create_basic_testset(db)

    expected = {
        "pagination": {
            "page": 1,
            "pages": 1,
            "total": 3,
            "per_page": 10,
            "next": None,
            "prev": None
        },
        "campaigns": [
            {
                "campaign_id": 1,
                "title": "Some Campaign",
                "status": "finished",
                "progress": {
                    "total": 1,
                    "done": 1
                },
                "metadata": {"key": "value"},
                "label_translations": {"PET": "plastic"},
                "date_created": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "date_started": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "date_completed": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "date_finished": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "created_by": "someone@example.com"
            },
            {
                "campaign_id": 2,
                "title": "Some other Campaign",
                "status": "finished",
                "progress": {
                    "total": 0,
                    "done": 0
                },
                "metadata": None,
                "label_translations": None,
                "date_created": yesterday.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "date_started": yesterday.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "date_completed": yesterday.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "date_finished": yesterday.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "created_by": "someone@example.com"
            },
            {
                "campaign_id": 3,
                "title": "A third Campaign",
                "status": "active",
                "progress": {
                    "total": 2,
                    "done": 1
                },
                "metadata": None,
                "label_translations": None,
                "date_created": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "date_started": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "date_completed": None,
                "date_finished": None,
                "created_by": "someone@example.com"
            },
        ]
    }

    response = client.get("/api/v1/campaigns", headers=headers)
    assert response.status_code == 200
    assert response.json == expected


def test_list_campaigns_pagination(client, app, db, mocker):
    headers = get_headers(db)

    now, yesterday = create_basic_testset(db)

    expected = {
        "pagination": {
            "page": 2,
            "pages": 2,
            "total": 3,
            "per_page": 2,
            "next": None,
            "prev": 1
        },
        "campaigns": [
            {
                "campaign_id": 3,
                "title": "A third Campaign",
                "status": "active",
                "progress": {
                    "total": 2,
                    "done": 1
                },
                "metadata": None,
                "label_translations": None,
                "date_created": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "date_started": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "date_completed": None,
                "date_finished": None,
                "created_by": "someone@example.com"
            },
        ]
    }

    response = client.get("/api/v1/campaigns?page=2&per_page=2",
                          headers=headers)
    assert response.status_code == 200
    assert response.json == expected


def test_new_campaign(client, app, db, mocker):
    headers = get_headers(db)

    json_payload = {
        "title": "Some test set",
        "labeler_email": "labeler@example.com",
        "metadata": {
            "field1": "value1",
            "field2": {
                "subfield1": "value2",
                "subfield2": 3
            }
        },
        "label_translations": {
            "original_label": "translated_label"
        }
    }

    expected = {
        "campaign_id": 1,
        "title": "Some test set",
        "status": "created",
        "progress": {
            "total": 0,
            "done": 0
        },
        "metadata": {
            "field1": "value1",
            "field2": {
                "subfield1": "value2",
                "subfield2": 3
            }
        },
        "label_translations": {
            "original_label": "translated_label"
        },
        "created_by": "test@example.com",
        "access_token": {
            "apikey": "string",  # Not actual value, checked separately
            "apisecret": "string"  # Not actual value, checked separately
        },
        "date_created": "string",  # Not actual value, checked separately
        "date_started": None,
        "date_completed": None,
        "date_finished": None,
    }

    response = client.post(
        "/api/v1/campaigns", json=json_payload, headers=headers)
    assert response.status_code == 200

    for x in ["campaign_id", "title", "status", "progress", "metadata",
              "label_translations", "date_started", "date_completed",
              "date_finished", "created_by"]:
        assert response.json[x] == expected[x]

    assert response.json["access_token"]["apikey"] is not None
    assert response.json["access_token"]["apisecret"] is not None
    assert response.json["date_created"] is not None

    # Check if actually added to DB
    item = db.session.query(Campaign).first()
    assert item is not None and item.title == "Some test set"

    # Check if user created and role set correctly
    user = db.session.query(User)\
                     .filter(User.email == "labeler@example.com").first()
    assert user is not None
    assert user.API_KEY == response.json["access_token"]["apikey"]
    assert bcrypt.checkpw(
        response.json["access_token"]["apisecret"].encode(),
        user.API_SECRET
    )

    role = db.session.query(Role)\
                     .filter(db.and_(
                         Role.user == user,
                         Role.subject_type == "campaign",
                         Role.subject_id == item.id)
                     )
    assert role is not None


def test_new_campaign_existing_user(client, app, db, mocker):
    headers = get_headers(db)

    # Add user first
    api_key = "label-key"
    api_secret = "some secret value"
    hashed = bcrypt.hashpw(api_secret.encode(), bcrypt.gensalt())
    user = User(
        email="labeler@example.com",
        API_KEY=api_key,
        API_SECRET=hashed
    )
    db.session.add(user)
    db.session.commit()

    json_payload = {
        "title": "Some test set",
        "labeler_email": "labeler@example.com",
        "metadata": {
            "field1": "value1",
            "field2": {
                "subfield1": "value2",
                "subfield2": 3
            }
        },
        "label_translations": {
            "original_label": "translated_label"
        }
    }

    expected = {
        "campaign_id": 1,
        "title": "Some test set",
        "status": "created",
        "progress": {
            "total": 0,
            "done": 0
        },
        "metadata": {
            "field1": "value1",
            "field2": {
                "subfield1": "value2",
                "subfield2": 3
            }
        },
        "label_translations": {
            "original_label": "translated_label"
        },
        "created_by": "test@example.com",
        "access_token": {
            "apikey": "string",  # Not actual value, checked separately
            "apisecret": "string"  # Not actual value, checked separately
        },
        "date_created": "string",  # Not actual value, checked separately
        "date_started": None,
        "date_completed": None,
        "date_finished": None,
    }

    response = client.post(
        "/api/v1/campaigns", json=json_payload, headers=headers)
    assert response.status_code == 200

    for x in ["campaign_id", "title", "status", "progress", "metadata",
              "label_translations", "date_started", "date_completed",
              "date_finished", "created_by"]:
        assert response.json[x] == expected[x]

    # Verify that the secret is not returned, but the correct (existing) key
    # is
    assert response.json["access_token"]["apikey"] == "label-key"
    assert response.json["access_token"]["apisecret"] is None
    assert response.json["date_created"] is not None

    # Check if actually added to DB
    item = db.session.query(Campaign).first()
    assert item is not None and item.title == "Some test set"

    # Check if user created and role set correctly
    user = db.session.query(User)\
                     .filter(User.email == "labeler@example.com").first()
    assert user is not None
    assert user.API_KEY == response.json["access_token"]["apikey"]

    # Assert that previously set secret is still valid
    assert bcrypt.checkpw(
        api_secret.encode(),
        user.API_SECRET
    )

    role = db.session.query(Role)\
                     .filter(db.and_(
                         Role.user == user,
                         Role.subject_type == "campaign",
                         Role.subject_id == item.id)
                     )
    assert role is not None


def test_new_campaign_existing_user_no_key(client, app, db, mocker):
    headers = get_headers(db)

    # Add user first, with no key this time
    user = User(
        email="labeler@example.com"
    )
    db.session.add(user)
    db.session.commit()

    json_payload = {
        "title": "Some test set",
        "labeler_email": "labeler@example.com",
        "metadata": {
            "field1": "value1",
            "field2": {
                "subfield1": "value2",
                "subfield2": 3
            }
        },
        "label_translations": {
            "original_label": "translated_label"
        }
    }

    expected = {
        "campaign_id": 1,
        "title": "Some test set",
        "status": "created",
        "progress": {
            "total": 0,
            "done": 0
        },
        "metadata": {
            "field1": "value1",
            "field2": {
                "subfield1": "value2",
                "subfield2": 3
            }
        },
        "label_translations": {
            "original_label": "translated_label"
        },
        "created_by": "test@example.com",
        "access_token": {
            "apikey": "string",  # Not actual value, checked separately
            "apisecret": "string"  # Not actual value, checked separately
        },
        "date_created": "string",  # Not actual value, checked separately
        "date_started": None,
        "date_completed": None,
        "date_finished": None,
    }

    response = client.post(
        "/api/v1/campaigns", json=json_payload, headers=headers)
    assert response.status_code == 200

    for x in ["campaign_id", "title", "status", "progress", "metadata",
              "label_translations", "date_started", "date_completed",
              "date_finished", "created_by"]:
        assert response.json[x] == expected[x]

    # Verify that a new secret and new key are returned
    assert response.json["access_token"]["apikey"] is not None
    assert response.json["access_token"]["apisecret"] is not None
    assert response.json["date_created"] is not None

    # Check if actually added to DB
    item = db.session.query(Campaign).first()
    assert item is not None and item.title == "Some test set"

    # Check if user created and role set correctly
    user = db.session.query(User)\
                     .filter(User.email == "labeler@example.com").first()
    assert user is not None
    assert user.API_KEY == response.json["access_token"]["apikey"]
    assert bcrypt.checkpw(
        response.json["access_token"]["apisecret"].encode(),
        user.API_SECRET
    )

    role = db.session.query(Role)\
                     .filter(db.and_(
                         Role.user == user,
                         Role.subject_type == "campaign",
                         Role.subject_id == item.id)
                     )
    assert role is not None


def test_new_campaign_duplicate_title(client, app, db, mocker):
    headers = get_headers(db)

    # Add some campaigns already
    create_basic_testset(db)

    json_payload = {
        "title": "Some Campaign",  # This campaign should already exist
        "labeler_email": "labeler@example.com",
        "metadata": {
            "field1": "value1",
            "field2": {
                "subfield1": "value2",
                "subfield2": 3
            }
        },
        "label_translations": {
            "original_label": "translated_label"
        }
    }

    response = client.post(
        "/api/v1/campaigns", json=json_payload, headers=headers)
    assert response.status_code == 409


def test_get_campaign_metadata(client, app, db, mocker):
    headers = get_headers(db)

    now, yesterday = create_basic_testset(db)

    expected = {
        "campaign_id": 3,
        "title": "A third Campaign",
        "status": "active",
        "progress": {
            "total": 2,
            "done": 1
        },
        "metadata": None,
        "label_translations": None,
        "date_created": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        "date_started": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        "date_completed": None,
        "date_finished": None,
        "created_by": "someone@example.com"
    }

    response = client.get("/api/v1/campaigns/3", headers=headers)
    assert response.status_code == 200
    assert response.json == expected


def test_change_campaign_status(client, app, db, mocker):
    headers = get_headers(db)

    # TODO: add some campaign to DB and set ID in url below

    json_payload = {
        'new_status': 'active'
    }

    response = client.put(
        "/api/v1/campaigns/1", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: campaigns.change_status"


def test_add_images_to_campaign_by_id(client, app, db, mocker):
    headers = get_headers(db)

    # TODO: add some campaigns and images to DB and set IDs below

    json_payload = [
        {'id': 1},
        {'id': 2},
        {'id': 5}
    ]

    response = client.post(
        "/api/v1/campaigns/1/images", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: campaigns.add_images"


def test_add_images_to_campaign_by_blobstorage_path(client, app, db, mocker):
    headers = get_headers(db)

    # TODO: add some campaigns and images to DB and set IDs below

    json_payload = [
        {'filepath': '/'},
        {'filepath': '/'},
        {'filepath': '/'}
    ]

    response = client.post(
        "/api/v1/campaigns/1/images", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: campaigns.add_images"


def test_add_images_to_campaign_mixed(client, app, db, mocker):
    headers = get_headers(db)

    # TODO: add some campaigns and images to DB and set IDs below

    json_payload = [
        {'filepath': '/'},
        {'id': 3},
        {'filepath': '/'}
    ]

    response = client.post(
        "/api/v1/campaigns/1/images", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: campaigns.add_images"


def test_get_objects_in_campaign(client, app, db, mocker):
    headers = get_headers(db)

    now, yesterday = create_basic_testset(db)

    expected = {
        "pagination": {
            "page": 1,
            "pages": 1,
            "total": 2,
            "per_page": 1000,
            "next": None,
            "prev": None
        },
        "images": [
            {
                "image_id": 1,
                "url": "/images/1",
                "objects": [
                    {
                        "object_id": 1,
                        "image_id": 1,
                        "campaign_id": 3,
                        "label": "label1",
                        "bounding_box": {
                            "xmin": 1,
                            "xmax": 2,
                            "ymin": 3,
                            "ymax": 4
                        },
                        "confidence": None,
                        "date_added": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                    },
                    {
                        "object_id": 2,
                        "image_id": 1,
                        "campaign_id": 3,
                        "label": "label2",
                        "bounding_box": {
                            "xmin": 2,
                            "xmax": 3,
                            "ymin": 4,
                            "ymax": 5
                        },
                        "confidence": None,
                        "date_added": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                    }
                ]
            },
            {
                "image_id": 2,
                "url": "/images/2",
                "objects": [
                    {
                        "object_id": 3,
                        "image_id": 2,
                        "campaign_id": 3,
                        "label": "translated_label3",
                        "bounding_box": {
                            "xmin": 6,
                            "xmax": 7,
                            "ymin": 8,
                            "ymax": 9
                        },
                        "confidence": 0.87,
                        "date_added": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                    }
                ]
            }
        ]
    }

    response = client.get("/api/v1/campaigns/3/objects", headers=headers)
    assert response.status_code == 200
    assert response.json == expected


def test_get_images_in_campaign_with_campaign_key(client, app, db, mocker):
    now, yesterday = create_basic_testset(db)

    # Add labeling user on campaign 3
    headers = add_labeler_user(db, 'campaign', 3)

    expected = {
        "pagination": {
            "page": 1,
            "pages": 1,
            "total": 2,
            "per_page": 1000,
            "next": None,
            "prev": None
        },
        "images": [
            {
                "image_id": 1,
                "url": "/images/1"
            },
            {
                "image_id": 2,
                "url": "/images/2"
            }
        ]
    }

    response = client.get("/api/v1/campaigns/3/images", headers=headers)
    assert response.status_code == 200
    assert response.json == expected


def test_get_images_in_campaign_with_campaign_key_paginated(
        client, app, db, mocker):
    now, yesterday = create_basic_testset(db)

    # Add labeling user on campaign 3
    headers = add_labeler_user(db, 'campaign', 3)

    expected = {
        "pagination": {
            "page": 2,
            "pages": 2,
            "total": 2,
            "per_page": 1,
            "next": None,
            "prev": 1
        },
        "images": [
            {
                "image_id": 2,
                "url": "/images/2"
            }
        ]
    }

    response = client.get("/api/v1/campaigns/3/images?page=2&per_page=1",
                          headers=headers)
    assert response.status_code == 200
    assert response.json == expected


def test_get_images_in_campaign_with_invalid_campaign_key(
        client, app, db, mocker):
    now, yesterday = create_basic_testset(db)

    # Add labeling user on campaign 3
    headers = add_labeler_user(db, 'campaign', 3)

    # Note the campaign id 2 in the requested link, this user has no role for
    # that
    response = client.get("/api/v1/campaigns/2/images", headers=headers)
    assert response.status_code == 401


def test_images_in_campaign_with_user_key(client, app, db, mocker):
    headers = get_headers(db)
    now, yesterday = create_basic_testset(db)

    # Add labeling user on campaign 3. Dont use the headers though
    add_labeler_user(db, 'campaign', 3)

    expected = {
        "pagination": {
            "page": 1,
            "pages": 1,
            "total": 2,
            "per_page": 1000,
            "next": None,
            "prev": None
        },
        "images": [
            {
                "image_id": 1,
                "url": "/images/1"
            },
            {
                "image_id": 2,
                "url": "/images/2"
            }
        ]
    }

    response = client.get("/api/v1/campaigns/3/images", headers=headers)
    assert response.status_code == 200
    assert response.json == expected


def test_add_objects_to_images_in_campaign_with_campaign_key(client, app, db,
                                                             mocker):
    headers = get_headers(db)  # TODO: Change this to campaign keys

    # TODO: add some campaigns and images to DB and set IDs below

    json_payload = [
        {
            'image_id': 1,
            'objects': [
                {
                    'bounding_box': {
                        'xmin': 123, 'xmax': 256, 'ymin': 187, 'ymax': 231
                    },
                    'label': "PET"
                },
                {
                    'bounding_box': {
                        'xmin': 234, 'xmax': 324, 'ymin': 564, 'ymax': 765
                    },
                    'label': "Organic"
                }
            ]
        },
        {
            'image_id': 3,
            'objects': [
                {
                    'bounding_box': {
                        'xmin': 23, 'xmax': 98, 'ymin': 1000, 'ymax': 1023
                    },
                    'label': "Plastic"
                },
                {
                    'bounding_box': {
                        'xmin': 564, 'xmax': 978, 'ymin': 342, 'ymax': 675
                    },
                    'label': "Metal"
                }
            ]
        }
    ]

    response = client.put(
        "/api/v1/campaigns/1/objects", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: campaigns.add_objects"


def test_add_objects_to_images_in_campaign_with_user_key(client, app, db,
                                                         mocker):
    headers = get_headers(db)  # TODO: Change this to campaign keys

    # TODO: add some campaigns and images to DB and set IDs below

    json_payload = [
        {
            'image_id': 1,
            'objects': [
                {
                    'bounding_box': {
                        'xmin': 123, 'xmax': 256, 'ymin': 187, 'ymax': 231
                    },
                    'label': "PET"
                },
                {
                    'bounding_box': {
                        'xmin': 234, 'xmax': 324, 'ymin': 564, 'ymax': 765
                    },
                    'label': "Organic"
                }
            ]
        }
    ]

    response = client.put(
        "/api/v1/campaigns/1/objects", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: campaigns.add_objects"


def test_add_objects_to_images_in_campaign_with_translations(client, app, db,
                                                             mocker):
    headers = get_headers(db)

    # TODO: add some campaigns and images to DB and set IDs below

    json_payload = [
        {
            'image_id': 1,
            'objects': [
                {
                    'bounding_box': {
                        'xmin': 123, 'xmax': 256, 'ymin': 187, 'ymax': 231
                    },
                    'label': "PET",
                    'label_translated': 'Plastic'
                },
                {
                    'bounding_box': {
                        'xmin': 234, 'xmax': 324, 'ymin': 564, 'ymax': 765
                    },
                    'label': "Treetrunk",
                    'label_translated': "Organic"
                }
            ]
        }
    ]

    response = client.put(
        "/api/v1/campaigns/1/objects", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: campaigns.add_objects"


def test_add_objects_to_images_in_campaign_with_confidence(client, app, db,
                                                           mocker):
    headers = get_headers(db)

    # TODO: add some campaigns and images to DB and set IDs below

    json_payload = [
        {
            'image_id': 1,
            'objects': [
                {
                    'bounding_box': {
                        'xmin': 123, 'xmax': 256, 'ymin': 187, 'ymax': 231
                    },
                    'label': "PET",
                    'confidence': 0.56
                },
                {
                    'bounding_box': {
                        'xmin': 234, 'xmax': 324, 'ymin': 564, 'ymax': 765
                    },
                    'label': "Treetrunk",
                    'confidence': 0.87
                }
            ]
        }
    ]

    response = client.put(
        "/api/v1/campaigns/1/objects", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: campaigns.add_objects"
