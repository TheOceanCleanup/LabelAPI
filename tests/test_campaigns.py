from tests.shared import get_headers, add_user, add_imagesets, add_images, \
    add_campaigns, add_image_to_campaign, add_object, add_labeler_user, \
    create_basic_testset, add_images_campaigns
from models.campaign import Campaign, CampaignImage
from models.user import User, Role
from common.azure import AzureWrapper
import datetime
import bcrypt


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
                "date_created": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "date_started": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "date_completed": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "date_finished": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
                "date_created": yesterday.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "date_started": yesterday.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "date_completed": yesterday.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "date_finished": yesterday.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "created_by": "someone@example.com"
            },
            {
                "campaign_id": 3,
                "title": "A third Campaign",
                "status": "created",
                "progress": {
                    "total": 2,
                    "done": 1
                },
                "metadata": None,
                "label_translations": None,
                "date_created": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "date_started": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
                "status": "created",
                "progress": {
                    "total": 2,
                    "done": 1
                },
                "metadata": None,
                "label_translations": None,
                "date_created": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "date_started": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
        "status": "created",
        "progress": {
            "total": 2,
            "done": 1
        },
        "metadata": None,
        "label_translations": None,
        "date_created": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "date_started": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "date_completed": None,
        "date_finished": None,
        "created_by": "someone@example.com"
    }

    response = client.get("/api/v1/campaigns/3", headers=headers)
    assert response.status_code == 200
    assert response.json == expected


def test_change_campaign_status(client, app, db, mocker):
    headers = get_headers(db)

    now, yesterday, user, img1, img2, img3, campaign1, campaign2, campaign3 = \
        add_images_campaigns(db)
    campaign1.status = "completed"
    db.session.commit()

    json_payload = {
        "new_status": "finished"
    }

    mocker.patch(
        "models.campaign.Campaign.finish_campaign"
    )

    response = client.put(
        "/api/v1/campaigns/1", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "ok"
    assert campaign1.status == "finished"

    Campaign.finish_campaign.assert_called_once()


def test_change_campaign_status_invalid(client, app, db, mocker):
    headers = get_headers(db)

    now, yesterday, user, img1, img2, img3, campaign1, campaign2, campaign3 = \
        add_images_campaigns(db)
    campaign1.status = "active"
    db.session.commit()

    json_payload = {
        "new_status": "finished"
    }

    mocker.patch(
        "models.campaign.Campaign.finish_campaign"
    )

    response = client.put(
        "/api/v1/campaigns/1", json=json_payload, headers=headers)
    assert response.status_code == 409
    assert campaign1.status == "active"

    Campaign.finish_campaign.assert_not_called()


def test_campaign_finish(client, app, db, mocker):
    headers = get_headers(db)

    now, yesterday = create_basic_testset(db)
    campaign3 = db.session.query(Campaign).get(3)
    campaign3.status = "active"
    db.session.commit()

    mocker.patch(
        "models.campaign.AzureWrapper.export_images_to_ML"
    )
    mocker.patch(
        "models.campaign.AzureWrapper.export_labels_to_ML"
    )

    campaign3.finish_campaign(app, db, 3, campaign3.title)

    AzureWrapper.export_images_to_ML.assert_called_once_with(
        "a-third-campaign_images",
        "Exported dataset as result of the finishing of labeling campaign "
        "a-third-campaign",
        ["path/file1.png", "otherpath/file2.png"]
    )
    AzureWrapper.export_labels_to_ML.assert_called_once_with(
        "a-third-campaign_labels",
        "Exported labels as result of the finishing of labeling campaign "
        "a-third-campaign",
        [
            {
                "image_url": "path/file1.png",
                "label": [
                    {
                        "label": "label1",
                        "bottomX": 1,
                        "topX": 2,
                        "bottomY": 3,
                        "topY": 4
                    },
                    {
                        "label": "label2",
                        "bottomX": 2,
                        "topX": 3,
                        "bottomY": 4,
                        "topY": 5
                    }
                ],
                "label_confidence": [None, None]
            },
            {
                "image_url": "otherpath/file2.png",
                "label": [
                    {
                        "label": "translated_label3",
                        "bottomX": 6,
                        "topX": 7,
                        "bottomY": 8,
                        "topY": 9
                    }
                ],
                "label_confidence": [0.87]
            }
        ]
    )


def test_add_images_to_campaign_by_id(client, app, db, mocker):
    headers = get_headers(db)

    now, yesterday, user, img1, img2, img3, campaign1, campaign2, campaign3 = \
        add_images_campaigns(db)

    json_payload = [
        {"id": 1},
        {"id": 3}
    ]

    response = client.post(
        "/api/v1/campaigns/3/images", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "ok"

    images = [x.image for x in campaign3.campaign_images]
    assert img1 in images
    assert img3 in images
    assert img2 not in images


def test_add_images_to_campaign_by_blobstorage_path(client, app, db, mocker):
    headers = get_headers(db)

    now, yesterday, user, img1, img2, img3, campaign1, campaign2, campaign3 = \
        add_images_campaigns(db)

    json_payload = [
        {"filepath": "/some/path/file1.png"},
        {"filepath": "/some/otherpath/file3.png"}
    ]

    response = client.post(
        "/api/v1/campaigns/3/images", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "ok"

    images = [x.image for x in campaign3.campaign_images]
    assert img1 in images
    assert img3 in images
    assert img2 not in images


def test_add_images_to_campaign_mixed(client, app, db, mocker):
    headers = get_headers(db)

    now, yesterday, user, img1, img2, img3, campaign1, campaign2, campaign3 = \
        add_images_campaigns(db)

    json_payload = [
        {"filepath": "/some/path/file1.png"},
        {"id": 3}
    ]

    response = client.post(
        "/api/v1/campaigns/3/images", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "ok"

    images = [x.image for x in campaign3.campaign_images]
    assert img1 in images
    assert img3 in images
    assert img2 not in images


def test_add_images_to_campaign_doesnt_exist(client, app, db, mocker):
    headers = get_headers(db)

    now, yesterday, user, img1, img2, img3, campaign1, campaign2, campaign3 = \
        add_images_campaigns(db)

    json_payload = [
        {"id": 3},
        {"id": 10}
    ]

    response = client.post(
        "/api/v1/campaigns/3/images", json=json_payload, headers=headers)
    assert response.status_code == 404
    assert response.json["detail"] == "Unknown image provided"

    # Verify that no images where added at all
    assert len(campaign3.campaign_images) == 0


def test_add_images_to_campaign_invalid_state(client, app, db, mocker):
    headers = get_headers(db)

    now, yesterday, user, img1, img2, img3, campaign1, campaign2, campaign3 = \
        add_images_campaigns(db)

    json_payload = [
        {"id": 1},
        {"id": 3}
    ]

    # Note campaign 2 - this has status finished
    response = client.post(
        "/api/v1/campaigns/2/images", json=json_payload, headers=headers)
    assert response.status_code == 409
    assert response.json["detail"] == \
        'Not allowed to add images while status is "finished"'

    # Verify that no images where added at all
    assert len(campaign2.campaign_images) == 0


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
                        "date_added": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
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
                        "date_added": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
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
                        "date_added": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
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
    headers = add_labeler_user(db, "campaign", 3)

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
    headers = add_labeler_user(db, "campaign", 3)

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
    headers = add_labeler_user(db, "campaign", 3)

    # Note the campaign id 2 in the requested link, this user has no role for
    # that
    response = client.get("/api/v1/campaigns/2/images", headers=headers)
    assert response.status_code == 401


def test_images_in_campaign_with_user_key(client, app, db, mocker):
    headers = get_headers(db)
    now, yesterday = create_basic_testset(db)

    # Add labeling user on campaign 3. Dont use the headers though
    add_labeler_user(db, "campaign", 3)

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
    now, yesterday = create_basic_testset(db, obj=False)

    # Add labeling user on campaign 3
    headers = add_labeler_user(db, "campaign", 3)

    # Set campaign 3 to active
    campaign = Campaign.query.get(3)
    campaign.status = "active"
    db.session.commit()

    json_payload = [
        {
            "image_id": 1,
            "objects": [
                {
                    "bounding_box": {
                        "xmin": 123, "xmax": 256, "ymin": 187, "ymax": 231
                    },
                    "label": "PET"
                },
                {
                    "bounding_box": {
                        "xmin": 234, "xmax": 324, "ymin": 564, "ymax": 765
                    },
                    "label": "Organic"
                }
            ]
        },
        {
            "image_id": 2,
            "objects": [
                {
                    "bounding_box": {
                        "xmin": 23, "xmax": 98, "ymin": 1000, "ymax": 1023
                    },
                    "label": "Plastic"
                },
                {
                    "bounding_box": {
                        "xmin": 564, "xmax": 978, "ymin": 342, "ymax": 675
                    },
                    "label": "Metal"
                }
            ]
        }
    ]

    response = client.put(
        "/api/v1/campaigns/3/objects", json=json_payload, headers=headers)
    assert response.status_code == 200

    # Some checks to assert the right objects ended up in the right place
    img1 = CampaignImage.query.filter(CampaignImage.image_id == 1).first()
    img2 = CampaignImage.query.filter(CampaignImage.image_id == 2).first()

    assert len(img1.objects) == 2
    assert len(img2.objects) == 2

    assert img1.objects[0].label_translated == "PET" \
        and img1.objects[0].label_original == "PET"
    assert img1.objects[1].label_translated == "Organic" \
        and img1.objects[1].label_original == "Organic"
    assert img2.objects[0].label_translated == "Plastic" \
        and img2.objects[0].label_original == "Plastic"
    assert img2.objects[1].label_translated == "Metal" \
        and img2.objects[1].label_original == "Metal"


def test_add_objects_to_images_in_campaign_with_user_key(client, app, db,
                                                         mocker):
    headers = get_headers(db)

    now, yesterday = create_basic_testset(db, obj=False)

    # Set campaign 3 to active
    campaign = Campaign.query.get(3)
    campaign.status = "active"
    db.session.commit()

    json_payload = [
        {
            "image_id": 1,
            "objects": [
                {
                    "bounding_box": {
                        "xmin": 123, "xmax": 256, "ymin": 187, "ymax": 231
                    },
                    "label": "PET"
                },
                {
                    "bounding_box": {
                        "xmin": 234, "xmax": 324, "ymin": 564, "ymax": 765
                    },
                    "label": "Organic"
                }
            ]
        },
        {
            "image_id": 2,
            "objects": [
                {
                    "bounding_box": {
                        "xmin": 23, "xmax": 98, "ymin": 1000, "ymax": 1023
                    },
                    "label": "Plastic"
                },
                {
                    "bounding_box": {
                        "xmin": 564, "xmax": 978, "ymin": 342, "ymax": 675
                    },
                    "label": "Metal"
                }
            ]
        }
    ]

    response = client.put(
        "/api/v1/campaigns/3/objects", json=json_payload, headers=headers)
    assert response.status_code == 200

    # Some checks to assert the right objects ended up in the right place
    img1 = CampaignImage.query.filter(CampaignImage.image_id == 1).first()
    img2 = CampaignImage.query.filter(CampaignImage.image_id == 2).first()

    assert len(img1.objects) == 2
    assert len(img2.objects) == 2

    assert img1.objects[0].label_translated == "PET" \
        and img1.objects[0].label_original == "PET"
    assert img1.objects[1].label_translated == "Organic" \
        and img1.objects[1].label_original == "Organic"
    assert img2.objects[0].label_translated == "Plastic" \
        and img2.objects[0].label_original == "Plastic"
    assert img2.objects[1].label_translated == "Metal" \
        and img2.objects[1].label_original == "Metal"

    assert img1.labeled == True
    assert img2.labeled == True
    assert campaign.status == 'completed'


def test_add_objects_to_images_in_campaign_wrong_status(client, app, db,
                                                        mocker):
    headers = get_headers(db)

    # Inserting the default objects in this test case
    now, yesterday = create_basic_testset(db)

    # Note that we don't change the campaign status to active - it's still in
    # created

    json_payload = [
        {
            "image_id": 1,
            "objects": [
                {
                    "bounding_box": {
                        "xmin": 123, "xmax": 256, "ymin": 187, "ymax": 231
                    },
                    "label": "Plastic"
                },
                {
                    "bounding_box": {
                        "xmin": 234, "xmax": 324, "ymin": 564, "ymax": 765
                    },
                    "label": "Organic"
                }
            ]
        }
    ]

    response = client.put(
        "/api/v1/campaigns/3/objects", json=json_payload, headers=headers)
    assert response.status_code == 409


def test_add_objects_to_images_in_campaign_with_translations(client, app, db,
                                                             mocker):
    headers = get_headers(db)
    now, yesterday = create_basic_testset(db, obj=False)

    # Set campaign 3 to active
    campaign = Campaign.query.get(3)
    campaign.status = "active"
    db.session.commit()

    json_payload = [
        {
            "image_id": 1,
            "objects": [
                {
                    "bounding_box": {
                        "xmin": 123, "xmax": 256, "ymin": 187, "ymax": 231
                    },
                    "label": "PET",
                    "label_translated": "Plastic"
                },
                {
                    "bounding_box": {
                        "xmin": 234, "xmax": 324, "ymin": 564, "ymax": 765
                    },
                    "label": "Tree",
                    "label_translated": "Organic"
                }
            ]
        }
    ]

    response = client.put(
        "/api/v1/campaigns/3/objects", json=json_payload, headers=headers)
    assert response.status_code == 200

    img1 = CampaignImage.query.filter(CampaignImage.image_id == 1).first()

    assert len(img1.objects) == 2

    assert img1.objects[0].label_translated == "Plastic" \
        and img1.objects[0].label_original == "PET"
    assert img1.objects[1].label_translated == "Organic" \
        and img1.objects[1].label_original == "Tree"

    # Good spot to check if the labeling progress is done correctly
    assert img1.labeled == True

    img2 = CampaignImage.query.filter(CampaignImage.image_id == 2).first()
    assert img2.labeled == False
    assert campaign.status == 'active'


def test_add_objects_to_images_in_campaign_with_confidence(client, app, db,
                                                           mocker):
    headers = get_headers(db)
    now, yesterday = create_basic_testset(db, obj=False)

    # Set campaign 3 to active
    campaign = Campaign.query.get(3)
    campaign.status = "active"
    db.session.commit()

    json_payload = [
        {
            "image_id": 1,
            "objects": [
                {
                    "bounding_box": {
                        "xmin": 123, "xmax": 256, "ymin": 187, "ymax": 231
                    },
                    "label": "Plastic",
                    "confidence": 0.87
                },
                {
                    "bounding_box": {
                        "xmin": 234, "xmax": 324, "ymin": 564, "ymax": 765
                    },
                    "label": "Organic",
                    "confidence": 0.56
                }
            ]
        }
    ]

    response = client.put(
        "/api/v1/campaigns/3/objects", json=json_payload, headers=headers)
    assert response.status_code == 200

    img1 = CampaignImage.query.filter(CampaignImage.image_id == 1).first()

    assert len(img1.objects) == 2

    assert img1.objects[0].label_translated == "Plastic"
    assert img1.objects[1].label_translated == "Organic"

def test_add_objects_to_images_in_campaign_overwrite_existing(client, app, db,
                                                              mocker):
    headers = get_headers(db)

    # Inserting the default objects in this test case
    now, yesterday = create_basic_testset(db)

    # Set campaign 3 to active
    campaign = Campaign.query.get(3)
    campaign.status = "active"
    db.session.commit()

    json_payload = [
        {
            "image_id": 1,
            "objects": [
                {
                    "bounding_box": {
                        "xmin": 123, "xmax": 256, "ymin": 187, "ymax": 231
                    },
                    "label": "Plastic"
                },
                {
                    "bounding_box": {
                        "xmin": 234, "xmax": 324, "ymin": 564, "ymax": 765
                    },
                    "label": "Organic"
                }
            ]
        }
    ]

    response = client.put(
        "/api/v1/campaigns/3/objects", json=json_payload, headers=headers)
    assert response.status_code == 200

    # Verify that only the new objects remain, not the old ones
    img1 = CampaignImage.query.filter(CampaignImage.image_id == 1).first()

    assert len(img1.objects) == 2

    # These would be "label1" and "label2" if the old labels are somehow
    # retained over the new ones
    assert img1.objects[0].label_translated == "Plastic"
    assert img1.objects[1].label_translated == "Organic"

def test_add_objects_to_images_in_campaign_image_doesnt_exist(client, app, db,
                                                              mocker):
    """
    In this test we verify that if one of the provided image_ids is not part of
    the campaign, no changes are made.
    """
    headers = get_headers(db)

    # Inserting the default objects in this test case
    now, yesterday = create_basic_testset(db)

    # Set campaign 3 to active
    campaign = Campaign.query.get(3)
    campaign.status = "active"
    db.session.commit()

    # First one is an existing image in this campaign, second one is an image
    # that is not part of this campaign.
    json_payload = [
        {
            "image_id": 1,
            "objects": [
                {
                    "bounding_box": {
                        "xmin": 123, "xmax": 256, "ymin": 187, "ymax": 231
                    },
                    "label": "Plastic"
                },
                {
                    "bounding_box": {
                        "xmin": 234, "xmax": 324, "ymin": 564, "ymax": 765
                    },
                    "label": "Organic"
                }
            ]
        },
        {
            "image_id": 3,
            "objects": [
                {
                    "bounding_box": {
                        "xmin": 123, "xmax": 256, "ymin": 187, "ymax": 231
                    },
                    "label": "Plastic"
                },
                {
                    "bounding_box": {
                        "xmin": 234, "xmax": 324, "ymin": 564, "ymax": 765
                    },
                    "label": "Organic"
                }
            ]
        }
    ]

    response = client.put(
        "/api/v1/campaigns/3/objects", json=json_payload, headers=headers)
    assert response.status_code == 404

    # Verify that the old objects remain on image 1
    img1 = CampaignImage.query.filter(CampaignImage.image_id == 1).first()

    assert len(img1.objects) == 2

    assert img1.objects[0].label_translated == "label1"
    assert img1.objects[1].label_translated == "label2"
