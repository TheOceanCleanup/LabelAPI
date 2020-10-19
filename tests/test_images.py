import datetime
from common.azure import AzureWrapper
from tests.shared import get_headers, add_user, add_imagesets, add_images, \
    add_campaigns, add_image_to_campaign, add_object, create_basic_testset, \
        add_images_campaigns, add_labeler_user


def test_list_images(client, app, db, mocker):
    headers = get_headers(db)

    now = datetime.datetime.now()
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)

    expected = {
        "pagination": {
            "page": 1,
            "pages": 1,
            "total": 3,
            "per_page": 10,
            "next": None,
            "prev": None
        },
        "images": [
            {
                "image_id": 1,
                "blobstorage_path": "/some/path/file1.png",
                "imageset": None,
                "date_taken": None,
                "location_taken": None,
                "type": "drone",
                "metadata": {
                    "source": "video1.mp4",
                    "frame": 1337
                },
                "tss_id": None,
                "file": {
                    "filetype": None,
                    "filesize": None,
                    "dimensions": {
                        "width": None,
                        "height": None
                    }
                }
            },
            {
                "image_id": 2,
                "blobstorage_path": "/some/otherpath/file2.png",
                "imageset": {
                    "imageset_id": 1,
                    "title": "some image set"
                },
                "date_taken": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "location_taken": "Dominican Republic - Bridge A",
                "type": "bridge",
                "metadata": None,
                "tss_id": None,
                "file": {
                    "filetype": "JPEG",
                    "filesize": 123456,
                    "dimensions": {
                        "width": 1920,
                        "height": 1080
                    }
                }
            },
            {
                "image_id": 3,
                "blobstorage_path": "/some/otherpath/file3.png",
                "imageset": {
                    "imageset_id": 1,
                    "title": "some image set"
                },
                "date_taken": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "location_taken": "Dominican Republic - Bridge A",
                "type": "bridge",
                "metadata": None,
                "tss_id": None,
                "file": {
                    "filetype": "JPEG",
                    "filesize": 123321,
                    "dimensions": {
                        "width": 1920,
                        "height": 1080
                    }
                }
            }
        ]
    }

    response = client.get("/api/v1/images", headers=headers)

    assert response.status_code == 200
    assert response.json == expected


def test_list_images_pagination(client, app, db, mocker):
    headers = get_headers(db)

    now = datetime.datetime.now()
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)

    response = client.get("/api/v1/images", headers=headers)

    expected = {
        "pagination": {
            "page": 2,
            "pages": 2,
            "total": 3,
            "per_page": 2,
            "next": None,
            "prev": 1
        },
        "images": [
            {
                "image_id": 3,
                "blobstorage_path": "/some/otherpath/file3.png",
                "imageset": {
                    "imageset_id": 1,
                    "title": "some image set"
                },
                "date_taken": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "location_taken": "Dominican Republic - Bridge A",
                "type": "bridge",
                "metadata": None,
                "tss_id": None,
                "file": {
                    "filetype": "JPEG",
                    "filesize": 123321,
                    "dimensions": {
                        "width": 1920,
                        "height": 1080
                    }
                }
            }
        ]
    }

    response = client.get("/api/v1/images?page=2&per_page=2", headers=headers)

    assert response.status_code == 200
    assert response.json == expected


def test_list_objects_in_image_prioritize_default_match_in_first(
        client, app, db, mocker):
    """
    In this test case, we add objects to an image in both campaign 1 and
    campaign 2. We expect to get the return only from campaign 1, as the
    date_finished is newer than campaign 2.
    """
    headers = get_headers(db)

    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)
    campaign1, campaign2, campaign3 = add_campaigns(db, user, now, yesterday)
    ci1 = add_image_to_campaign(db, img1, campaign1)
    ci2 = add_image_to_campaign(db, img1, campaign2)
    obj1 = add_object(db, now, ci1, 'label1', None, None, [1, 2, 3, 4])
    obj2 = add_object(db, now, ci1, 'label2', None, None, [2, 3, 4, 5])
    obj3 = add_object(db, now, ci2, 'label3', None, None, [2, 3, 4, 5])
    obj4 = add_object(db, now, ci2, 'label4', None, None, [1, 4, 8, 16])

    expected = [
        {
            "object_id": obj1.id,
            "image_id": 1,
            "campaign_id": 1,
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
            "object_id": obj2.id,
            "image_id": 1,
            "campaign_id": 1,
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

    response = client.get("/api/v1/images/1/objects", headers=headers)
    assert response.status_code == 200
    assert response.json == expected


def test_list_objects_in_image_prioritize_default_match_not_in_first(
        client, app, db, mocker):
    """
    In this test case, we add objects to an image only in campaign 2. The
    image is not part of campaign 1. We expect to get the return from
    campaign 2.
    """
    headers = get_headers(db)

    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)
    campaign1, campaign2, campaign3 = add_campaigns(db, user, now, yesterday)
    ci2 = add_image_to_campaign(db, img1, campaign2)
    obj3 = add_object(db, now, ci2, 'label3', None, None, [2, 3, 4, 5])
    obj4 = add_object(db, now, ci2, 'label4', None, None, [1, 4, 8, 16])

    expected = [
        {
            "object_id": obj3.id,
            "image_id": 1,
            "campaign_id": 2,
            "label": "label3",
            "bounding_box": {
                "xmin": 2,
                "xmax": 3,
                "ymin": 4,
                "ymax": 5
            },
            "confidence": None,
            "date_added": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        },
        {
            "object_id": obj4.id,
            "image_id": 1,
            "campaign_id": 2,
            "label": "label4",
            "bounding_box": {
                "xmin": 1,
                "xmax": 4,
                "ymin": 8,
                "ymax": 16
            },
            "confidence": None,
            "date_added": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        }
    ]

    response = client.get("/api/v1/images/1/objects", headers=headers)
    assert response.status_code == 200
    assert response.json == expected


def test_list_objects_in_image_prioritize_provided_match_in_first(
        client, app, db, mocker):
    """
    In this test case, we add objects to an image in both campaign 1 and
    campaign 2. We then ask to get the return for campaign 2, and only if there
    is none from campaign 1. We expect to get the objects added in campaign 2,
    not campaign 1.
    """
    headers = get_headers(db)

    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)
    campaign1, campaign2, campaign3 = add_campaigns(db, user, now, yesterday)
    ci1 = add_image_to_campaign(db, img1, campaign1)
    ci2 = add_image_to_campaign(db, img1, campaign2)
    obj1 = add_object(db, now, ci1, 'label1', None, None, [1, 2, 3, 4])
    obj2 = add_object(db, now, ci1, 'label2', None, None, [2, 3, 4, 5])
    obj3 = add_object(db, now, ci2, 'label3', None, None, [2, 3, 4, 5])
    obj4 = add_object(db, now, ci2, 'label4', None, None, [1, 4, 8, 16])

    expected = [
        {
            "object_id": obj3.id,
            "image_id": 1,
            "campaign_id": 2,
            "label": "label3",
            "bounding_box": {
                "xmin": 2,
                "xmax": 3,
                "ymin": 4,
                "ymax": 5
            },
            "confidence": None,
            "date_added": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        },
        {
            "object_id": obj4.id,
            "image_id": 1,
            "campaign_id": 2,
            "label": "label4",
            "bounding_box": {
                "xmin": 1,
                "xmax": 4,
                "ymin": 8,
                "ymax": 16
            },
            "confidence": None,
            "date_added": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        }
    ]

    response = client.get("/api/v1/images/1/objects?campaigns=2,1",
                          headers=headers)
    assert response.status_code == 200
    assert response.json == expected


def test_list_objects_in_image_prioritize_provided_match_not_in_first(
        client, app, db, mocker):
    """
    In this test case, we add objects to an image in only campaign 1. Campaign
    3 is set to unlabeled. We then ask to get the return for campaign 3, and
    only if there is none from campaign 1. We expect to get the objects added
    in campaign 1, as there are none from campaign 3.
    """
    headers = get_headers(db)

    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)
    campaign1, campaign2, campaign3 = add_campaigns(db, user, now, yesterday)
    ci1 = add_image_to_campaign(db, img1, campaign1)
    ci2 = add_image_to_campaign(db, img1, campaign3)
    obj1 = add_object(db, now, ci1, 'label1', None, None, [1, 2, 3, 4])
    obj2 = add_object(db, now, ci1, 'label2', None, None, [2, 3, 4, 5])

    ci2.labeled = False
    db.session.commit()

    expected = [
        {
            "object_id": obj1.id,
            "image_id": 1,
            "campaign_id": 1,
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
            "object_id": obj2.id,
            "image_id": 1,
            "campaign_id": 1,
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

    response = client.get("/api/v1/images/1/objects?campaigns=3,1",
                          headers=headers)
    assert response.status_code == 200
    assert response.json == expected


def test_list_objects_in_image_prioritize_provided_no_match(
        client, app, db, mocker):
    """
    In this test case, we add objects to an image in campaign 2. We then ask to
    get the images specifying only campaign 1. We expect to get no objects.
    """
    headers = get_headers(db)

    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)
    campaign1, campaign2, campaign3 = add_campaigns(db, user, now, yesterday)
    ci1 = add_image_to_campaign(db, img1, campaign1)
    ci2 = add_image_to_campaign(db, img1, campaign2)
    obj3 = add_object(db, now, ci2, 'label3', None, None, [2, 3, 4, 5])
    obj4 = add_object(db, now, ci2, 'label4', None, None, [1, 4, 8, 16])

    expected = []

    response = client.get("/api/v1/images/1/objects?campaigns=1",
                          headers=headers)
    assert response.status_code == 200
    assert response.json == expected


def test_list_objects_in_image_prioritize_default_match_in_first_not_finished(
        client, app, db, mocker):
    """
    In this test case, we add objects to an image in campaign 2 and campaign 3.
    We then ask to get the return without specifying the campaigns. We expect
    to get the objects added in campaign 2, as campaign 3 is not in finished
    state.
    """
    headers = get_headers(db)

    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)
    campaign1, campaign2, campaign3 = add_campaigns(db, user, now, yesterday)
    ci1 = add_image_to_campaign(db, img1, campaign3)
    ci2 = add_image_to_campaign(db, img1, campaign2)
    obj1 = add_object(db, now, ci1, 'label1', None, None, [1, 2, 3, 4])
    obj2 = add_object(db, now, ci1, 'label2', None, None, [2, 3, 4, 5])
    obj3 = add_object(db, now, ci2, 'label3', None, None, [2, 3, 4, 5])
    obj4 = add_object(db, now, ci2, 'label4', None, None, [1, 4, 8, 16])

    expected = [
        {
            "object_id": obj3.id,
            "image_id": 1,
            "campaign_id": 2,
            "label": "label3",
            "bounding_box": {
                "xmin": 2,
                "xmax": 3,
                "ymin": 4,
                "ymax": 5
            },
            "confidence": None,
            "date_added": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        },
        {
            "object_id": obj4.id,
            "image_id": 1,
            "campaign_id": 2,
            "label": "label4",
            "bounding_box": {
                "xmin": 1,
                "xmax": 4,
                "ymin": 8,
                "ymax": 16
            },
            "confidence": None,
            "date_added": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        }
    ]

    response = client.get("/api/v1/images/1/objects", headers=headers)
    assert response.status_code == 200
    assert response.json == expected


class mydatetime:
    @classmethod
    def utcnow(cls):
        return datetime.datetime(2020, 10, 19, 12, 34, 56)


def test_images_get_link_with_campaign_key(client, app, db, mocker):
    # Add labeling user on campaign 3
    headers = add_labeler_user(db, "campaign", 3)

    now, yesterday = create_basic_testset(db)

    mocker.patch(
        "models.image.AzureWrapper.get_sas_url",
        return_value="url"
    )
    # Patch datetime to get a predictable 'expires'  call
    mocker.patch(
        "models.image.datetime",
        mydatetime
    )

    response = client.get("/api/v1/images/1", headers=headers)

    assert response.status_code == 303

    AzureWrapper.get_sas_url.assert_called_once_with(
        '/some/path/file1.png',
        expires=datetime.datetime(2020, 10, 26, 12, 34, 56),
        permissions=["read"]
    )


def test_images_get_link_with_no_campaign_key(client, app, db, mocker):
    # Add labeling user on campaign 3 (image is in campaign 3)
    headers = add_labeler_user(db, "campaign", 2)

    now, yesterday = create_basic_testset(db)

    response = client.get("/api/v1/images/1", headers=headers)

    assert response.status_code == 401


def test_images_get_link_with_user_key(client, app, db, mocker):
    headers = get_headers(db)

    now, yesterday = create_basic_testset(db)


    mocker.patch(
        "models.image.AzureWrapper.get_sas_url",
        return_value="url"
    )
    # Patch datetime to get a predictable 'expires'  call
    mocker.patch(
        "models.image.datetime",
        mydatetime
    )

    response = client.get("/api/v1/images/1", headers=headers)

    assert response.status_code == 303

    AzureWrapper.get_sas_url.assert_called_once_with(
        '/some/path/file1.png',
        expires=datetime.datetime(2020, 10, 26, 12, 34, 56),
        permissions=["read"]
    )
