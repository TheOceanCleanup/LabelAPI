import pytest
from flask import g, session
import os
import datetime
from tests.shared import get_headers, add_user, add_imagesets, add_images


def test_list_images(client, app, db, mocker):
    headers = get_headers(db)

    now = datetime.datetime.now()
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)

    response = client.get("/api/v1/images", headers=headers)

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


def test_list_objects_in_image_simple(client, app, db, mocker):
    headers = get_headers(db)

    # TODO: add images, campaigns, objects to DB

    response = client.get("/api/v1/images/1/objects", headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: images.get_objects"


def test_list_objects_in_image_prioritize_default(client, app, db, mocker):
    headers = get_headers(db)

    # TODO: add images, campaigns, objects to DB. Use multiple campaigns with
    #       prioritization

    response = client.get("/api/v1/images/1/objects", headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: images.get_objects"


def test_list_objects_in_image_prioritize_provided(client, app, db, mocker):
    headers = get_headers(db)

    # TODO: add images, campaigns, objects to DB. Use multiple campaigns with
    #       prioritization

    response = client.get("/api/v1/images/1/objects?campaigns=2,3,1", headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: images.get_objects"


def test_images_get_link_with_campaign_key(client, app, db, mocker):
    headers = get_headers(db)  # TODO: Change this to campaign keys

    # TODO: add images, campaigns to DB

    response = client.get("/api/v1/images/1", headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: images.get_image_url"


def test_images_get_link_with_user_key(client, app, db, mocker):
    headers = get_headers(db)

    # TODO: add images, campaigns to DB

    response = client.get("/api/v1/images/1", headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: images.get_image_url"
