import datetime
from tests.shared import get_headers, add_user, add_imagesets, add_images
from models.image import ImageSet, Image
from common.azure import AzureWrapper


def test_list_imagesets(client, app, db, mocker):
    headers = get_headers(db)

    now = datetime.datetime.now()
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)

    expected = {
        "pagination": {
            "page": 1,
            "pages": 1,
            "total": 3,
            "per_page": 10,
            "next": None,
            "prev": None
        },
        "image_sets": [
            {
                "imageset_id": 1,
                "title": "some image set",
                "status": "created",
                "metadata": None,
                "blobstorage_path": "/some/otherpath",
                "date_created": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "date_finished": None,
                "created_by": "someone@example.com"
            },
            {
                "imageset_id": 2,
                "title": "some other image set",
                "status": "created",
                "metadata": None,
                "blobstorage_path": "/some/path",
                "date_created": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "date_finished": None,
                "created_by": "someone@example.com"
            },
            {
                "imageset_id": 3,
                "title": "A third set",
                "status": "finished",
                "metadata": {
                    "note": "Special Drone footage"
                },
                "blobstorage_path": "/some/thirdpath",
                "date_created": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "date_finished": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "created_by": "someone@example.com"
            }
        ]
    }

    response = client.get("/api/v1/image_sets", headers=headers)
    assert response.status_code == 200
    assert response.json == expected


def test_list_imagesets_pagination(client, app, db, mocker):
    headers = get_headers(db)

    now = datetime.datetime.now()
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)

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
        "image_sets": [
            {
                "imageset_id": 3,
                "title": "A third set",
                "status": "finished",
                "metadata": {
                    "note": "Special Drone footage"
                },
                "blobstorage_path": "/some/thirdpath",
                "date_created": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "date_finished": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "created_by": "someone@example.com"
            }
        ]
    }

    response = client.get(
        "/api/v1/image_sets?page=2&per_page=2", headers=headers)
    assert response.status_code == 200
    assert response.json == expected


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

    mocker.patch(
        "models.image.AzureWrapper.create_container",
        return_value="container_name"
    )

    mocker.patch(
        "models.image.AzureWrapper.get_container_sas_url",
        return_value="some_sas_url"
    )

    expected = {
        "imageset_id": 1,
        "title": "Some test set",
        "status": "created",
        "metadata": {
            "field1": "value1",
            "field2": {
                "subfield1": "value2",
                "subfield2": 3
            },
        },
        "blobstorage_path": "container_name",
        "dropbox_url": "some_sas_url",
        "date_finished": None,
        "created_by": "test@example.com"
    }

    response = client.post(
        "/api/v1/image_sets", json=json_payload, headers=headers)
    assert response.status_code == 200

    # As date is filled by DB, testing for equality is not possible. Remove and
    # test after.
    resp_no_date = response.json
    del resp_no_date["date_created"]

    assert response.json == expected


def test_new_imageset_already_exists(client, app, db, mocker):
    headers = get_headers(db)

    user = add_user(db)
    add_imagesets(db, user, datetime.datetime.now())

    json_payload = {
        'title': 'some other image set'
    }

    response = client.post(
        "/api/v1/image_sets", json=json_payload, headers=headers)

    assert response.status_code == 409

def test_new_imageset_azure_failure(client, app, db, mocker):
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

    mocker.patch(
        "models.image.AzureWrapper.create_container",
        return_value=False
    )

    response = client.post(
        "/api/v1/image_sets", json=json_payload, headers=headers)
    assert response.status_code == 500

    # Verify the image set was not added to the database
    assert db.session.query(ImageSet).count() == 0


class DummyProperties:
    def __init__(self, content_length):
        self.content_length = content_length

class DummyFile:
    def __init__(self, name, properties):
        self.name = name
        self.properties = properties


def test_change_imageset_status(client, app, db, mocker):
    headers = get_headers(db)

    now = datetime.datetime.now()
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)

    mocker.patch(
        "models.image.ImageSet.finish_set"
    )

    json_payload = {
        'new_status': 'finished'
    }

    response = client.put(
        "/api/v1/image_sets/1", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "ok"

    ImageSet.finish_set.assert_called_once()


def test_change_imageset_status_invalid(client, app, db, mocker):
    headers = get_headers(db)

    now = datetime.datetime.now()
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)

    json_payload = {
        'new_status': 'finished'
    }

    response = client.put(
        "/api/v1/image_sets/3", json=json_payload, headers=headers)
    assert response.status_code == 409
    assert response.json['detail'] == \
        'Not allowed to go from "finished" to "finished"'


def test_set_finish(client, app, db, mocker):
    headers = get_headers(db)

    now = datetime.datetime.now()
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)

    mocker.patch(
        "models.image.AzureWrapper.copy_contents",
        return_value=[
            DummyFile('file1', DummyProperties(123)),
            DummyFile('file2', DummyProperties(456)),
        ]
    )
    mocker.patch(
        "models.image.AzureWrapper.get_image_information",
        return_value=("PNG", 789, 900)
    )
    mocker.patch(
        "models.image.AzureWrapper.delete_container"
    )

    imgset1.finish_set(app, db)

    AzureWrapper.copy_contents.assert_called_once_with(
        "/some/otherpath",
        "",
        "upload-container",
        "uploads/some-image-set"
    )
    AzureWrapper.get_image_information.assert_has_calls([
        mocker.call("upload-container/uploads/some-image-set/file1"),
        mocker.call("upload-container/uploads/some-image-set/file2")
    ])
    AzureWrapper.delete_container.assert_called_once_with(
        "/some/otherpath"
    )

    img1 = db.session.query(Image)\
                     .filter(Image.blobstorage_path == \
                             "upload-container/uploads/some-image-set/file1")\
                     .first()
    img2 = db.session.query(Image)\
                     .filter(Image.blobstorage_path == \
                             "upload-container/uploads/some-image-set/file1")\
                     .first()
    imgset1 = db.session.query(ImageSet).get(1)

    assert img1 is not None
    assert img2 is not None
    assert img1.filetype == "PNG"
    assert img1.width == 789
    assert img1.height == 900
    assert imgset1.blobstorage_path == \
        'upload-container/uploads/some-image-set'


def test_set_finish_copy_failed(client, app, db, mocker):
    headers = get_headers(db)

    now = datetime.datetime.now()
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)

    mocker.patch(
        "models.image.AzureWrapper.copy_contents",
        return_value=False
    )
    mocker.patch(
        "models.image.AzureWrapper.get_image_information",
        return_value=("PNG", 789, 900)
    )
    mocker.patch(
        "models.image.AzureWrapper.delete_container"
    )

    imgset1.finish_set(app, db)

    AzureWrapper.copy_contents.assert_called_once_with(
        "/some/otherpath",
        "",
        "upload-container",
        "uploads/some-image-set"
    )
    AzureWrapper.get_image_information.assert_not_called()
    AzureWrapper.delete_container.assert_not_called()


    img1 = db.session.query(Image)\
                     .filter(Image.blobstorage_path == \
                             "upload-container/uploads/some-image-set/file1")\
                     .first()
    img2 = db.session.query(Image)\
                     .filter(Image.blobstorage_path == \
                             "upload-container/uploads/some-image-set/file1")\
                     .first()
    imgset1 = db.session.query(ImageSet).get(1)

    assert img1 is None
    assert img2 is None
    assert imgset1.blobstorage_path == '/some/otherpath'


def test_list_images_in_set(client, app, db, mocker):
    headers = get_headers(db)

    now = datetime.datetime.now()
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)

    expected = {
        "pagination": {
            "page": 1,
            "pages": 1,
            "total": 2,
            "per_page": 10,
            "next": None,
            "prev": None
        },
        "images": [
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

    response = client.get("/api/v1/image_sets/1/images", headers=headers)
    assert response.status_code == 200
    assert response.json == expected


def test_list_images_in_set_pagination(client, app, db, mocker):
    headers = get_headers(db)

    now = datetime.datetime.now()
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)

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

    response = client.get(
        "/api/v1/image_sets/1/images?page=2&per_page=1", headers=headers)
    assert response.status_code == 200
    assert response.json == expected


def test_add_images_to_set_by_id(client, app, db, mocker):
    headers = get_headers(db)

    now = datetime.datetime.now()
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)

    # Remove the set from img3 to test multiple adds
    img3.imageset = None
    img3.imageset_id = None
    db.session.add(img3)
    db.session.commit()

    json_payload = [
        {'id': 1},
        {'id': 3}
    ]

    response = client.post(
        "/api/v1/image_sets/2/images", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "ok"

    assert img1 in imgset2.images
    assert img3 in imgset2.images
    assert img2 not in imgset2.images


def test_add_images_to_set_by_blobstorage_path(client, app, db, mocker):
    headers = get_headers(db)

    now = datetime.datetime.now()
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)

    # Remove the set from img3 to test multiple adds
    img3.imageset = None
    img3.imageset_id = None
    db.session.add(img3)
    db.session.commit()

    json_payload = [
        {'filepath': '/some/path/file1.png'},
        {'filepath': '/some/otherpath/file3.png'}
    ]

    response = client.post(
        "/api/v1/image_sets/2/images", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "ok"

    assert img1 in imgset2.images
    assert img3 in imgset2.images
    assert img2 not in imgset2.images


def test_add_images_to_set_mixed(client, app, db, mocker):
    headers = get_headers(db)

    now = datetime.datetime.now()
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)

    # Remove the set from img3 to test multiple adds
    img3.imageset = None
    img3.imageset_id = None
    db.session.add(img3)
    db.session.commit()

    json_payload = [
        {'filepath': '/some/path/file1.png'},
        {'id': 3}
    ]

    response = client.post(
        "/api/v1/image_sets/2/images", json=json_payload, headers=headers)
    assert response.status_code == 200
    assert response.json == "ok"

    assert img1 in imgset2.images
    assert img3 in imgset2.images
    assert img2 not in imgset2.images


def test_add_images_to_set_doesnt_exist(client, app, db, mocker):
    headers = get_headers(db)

    now = datetime.datetime.now()
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)

    # Remove the set from img3 to test
    img3.imageset = None
    img3.imageset_id = None
    db.session.add(img3)
    db.session.commit()

    json_payload = [
        {'id': 3},
        {'id': 10}
    ]

    response = client.post(
        "/api/v1/image_sets/2/images", json=json_payload, headers=headers)
    assert response.status_code == 404
    assert response.json['detail'] == "Unknown image provided"

    # Verify that no images where added at all
    assert len(imgset2.images) == 0


def test_add_images_to_set_invalid_state(client, app, db, mocker):
    headers = get_headers(db)

    now = datetime.datetime.now()
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)

    # Remove the set from img3 to test
    img3.imageset = None
    img3.imageset_id = None
    db.session.add(img3)
    db.session.commit()

    json_payload = [
        {'id': 1},
        {'id': 3}
    ]

    # Note image_set 3 - this has status finished
    response = client.post(
        "/api/v1/image_sets/3/images", json=json_payload, headers=headers)
    assert response.status_code == 409
    assert response.json['detail'] == \
        'Not allowed to add images while status is "finished"'

    # Verify that no images where added at all
    assert len(imgset3.images) == 0


def test_add_images_to_set_already_attached(client, app, db, mocker):
    headers = get_headers(db)

    now = datetime.datetime.now()
    user = add_user(db)
    imgset1, imgset2, imgset3 = add_imagesets(db, user, now)
    img1, img2, img3 = add_images(db, imgset1, now)

    json_payload = [
        {'id': 1},
        {'id': 3}
    ]

    response = client.post(
        "/api/v1/image_sets/2/images", json=json_payload, headers=headers)
    assert response.status_code == 409
    assert response.json['detail'] == \
        "Image 3 (/some/otherpath/file3.png) is already assigned to an " \
        "image set"

    # Verify that no images where added at all
    assert len(imgset3.images) == 0
