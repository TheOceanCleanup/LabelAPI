from tests.shared import get_headers, add_user, add_imagesets, add_images, \
    add_campaigns, add_image_to_campaign, add_object
import datetime


def create_basic_testset(db):
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)
    campaign1, campaign2, campaign3 = add_campaigns(db, user, now, yesterday)
    ci1 = add_image_to_campaign(db, img1, campaign3)
    ci2 = add_image_to_campaign(db, img1, campaign3)
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
                    "total": 0,
                    "done": 0
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
        'title': 'Some test set',
        'labeler_email': 'label@example.com',
        'metadata': {
            'field1': 'value1',
            'field2': {
                'subfield1': 'value2',
                'subfield2': 3
            }
        },
        'label_translations': {
            'original_label': 'translated_label'
        }
    }
    response = client.post(
        "/api/v1/campaigns", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: campaigns.add_campaign"


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

    # TODO: add some campaigns, images and objects to DB
    response = client.get("/api/v1/campaigns/1/objects", headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: campaigns.get_objects"


def test_get_images_in_campaign_with_campaign_key(client, app, db, mocker):
    headers = get_headers(db)  # TODO: Change this to campaign keys

    # TODO: add images, campaigns to DB

    response = client.get("/api/v1/campaigns/1/images", headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: campaigns.get_images"


def test_images_in_campaign_with_user_key(client, app, db, mocker):
    headers = get_headers(db)

    # TODO: add images, campaigns to DB

    response = client.get("/api/v1/campaigns/1/images", headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: campaigns.get_images"


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
