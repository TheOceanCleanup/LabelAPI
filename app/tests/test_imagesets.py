import pytest
from flask import g, session
import os
from tests.shared import get_headers


def test_list_imagesets(client, app, db, mocker):
    headers = get_headers(db)

    # TODO: add some image sets to DB

    response = client.get("/api/v1/image_sets", headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: image_sets.list_imagesets"


def test_list_imagesets_pagination(client, app, db, mocker):
    headers = get_headers(db)

    # TODO: add some image sets to DB

    response = client.get("/api/v1/image_sets?page=2&per_page=2", headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: image_sets.list_imagesets"


def test_new_imageset(client, app, db, mocker):
    headers = get_headers(db)
    json_payload = {
        'title': 'Some test set',
        'metadata': {
            'field1': 'value1',
            'field2': {
                'subfield1': 'value2',
                'subfield2': 3
            }
        }
    }
    response = client.post("/api/v1/image_sets", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: image_sets.add_imageset"


def test_change_imageset_status(client, app, db, mocker):
    headers = get_headers(db)

    # TODO: add some image set to DB and set ID in url below

    json_payload = {
        'new_status': 'finished'
    }

    response = client.put("/api/v1/image_sets/1", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: image_sets.change_status"


def test_list_images_in_set(client, app, db, mocker):
    headers = get_headers(db)

    # TODO: add some image set and images to DB and set ID in url below

    response = client.get("/api/v1/image_sets/1/images", headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: image_sets.get_images"


def test_list_images_in_set_pagination(client, app, db, mocker):
    headers = get_headers(db)

    # TODO: add some image set and images to DB and set ID in url below

    response = client.get("/api/v1/image_sets/1/images?page=2&per_page=2", headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: image_sets.get_images"


def test_add_images_to_set_by_id(client, app, db, mocker):
    headers = get_headers(db)

    # TODO: add some image sets and images to DB and set IDs below

    json_payload = [
        {'id': 1},
        {'id': 2},
        {'id': 5}
    ]

    response = client.post("/api/v1/image_sets/1/images", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: image_sets.add_images"


def test_add_images_to_set_by_blobstorage_path(client, app, db, mocker):
    headers = get_headers(db)

    # TODO: add some image sets and images to DB and set IDs below

    json_payload = [
        {'filepath': '/'},
        {'filepath': '/'},
        {'filepath': '/'}
    ]

    response = client.post("/api/v1/image_sets/1/images", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: image_sets.add_images"


def test_add_images_to_set_mixed(client, app, db, mocker):
    headers = get_headers(db)

    # TODO: add some image sets and images to DB and set IDs below

    json_payload = [
        {'filepath': '/'},
        {'id': 3},
        {'filepath': '/'}
    ]

    response = client.post("/api/v1/image_sets/1/images", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "Not Implemented: image_sets.add_images"
