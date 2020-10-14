import pytest
from flask import g, session
import os
from tests.shared import get_headers


def test_list_images(client, app, db, mocker):
    headers = get_headers()

    # TODO: add some images to DB

    response = client.get("/api/v1/images", headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: images.list_images"


def test_list_images_pagination(client, app, db, mocker):
    headers = get_headers()

    # TODO: add some images to DB

    response = client.get("/api/v1/images?page=2&per_page=2", headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: images.list_images"


def test_list_objects_in_image_simple(client, app, db, mocker):
    headers = get_headers()

    # TODO: add images, campaigns, objects to DB

    response = client.get("/api/v1/images/1/objects", headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: images.get_objects"


def test_list_objects_in_image_prioritize_default(client, app, db, mocker):
    headers = get_headers()

    # TODO: add images, campaigns, objects to DB. Use multiple campaigns with
    #       prioritization

    response = client.get("/api/v1/images/1/objects", headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: images.get_objects"


def test_list_objects_in_image_prioritize_provided(client, app, db, mocker):
    headers = get_headers()

    # TODO: add images, campaigns, objects to DB. Use multiple campaigns with
    #       prioritization

    response = client.get("/api/v1/images/1/objects?campaigns=2,3,1", headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: images.get_objects"


def test_images_get_link_with_campaign_key(client, app, db, mocker):
    headers = get_headers()  # TODO: Change this to campaign keys

    # TODO: add images, campaigns to DB

    response = client.get("/api/v1/images/1", headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: images.get_image_url"


def test_images_get_link_with_user_key(client, app, db, mocker):
    headers = get_headers()

    # TODO: add images, campaigns to DB

    response = client.get("/api/v1/images/1", headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: images.get_image_url"
