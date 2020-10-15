from tests.shared import get_headers
from models.user import User


def test_invalid_key(client, app, db, mocker):
    headers = get_headers(db)

    headers["Authentication-Key"] = "124"
    response = client.get("/api/v1/images", headers=headers)
    assert response.status_code == 401


def test_invalid_secret(client, app, db, mocker):
    headers = get_headers(db)

    headers["Authentication-Secret"] = "Foobaz"
    response = client.get("/api/v1/images", headers=headers)
    assert response.status_code == 401


def test_missing_api_key(client, app, db, mocker):
    headers = get_headers(db)

    del headers["Authentication-Key"]
    response = client.get("/api/v1/images", headers=headers)
    assert response.status_code == 401


def test_missing_api_secret(client, app, db, mocker):
    headers = get_headers(db)

    del headers["Authentication-Secret"]
    response = client.get("/api/v1/images", headers=headers)
    assert response.status_code == 401


def test_inactive_user(client, app, db, mocker):
    headers = get_headers(db)

    user = db.session.query(User)\
                     .filter(User.email == "test@example.com")\
                     .first()
    user.enabled = False
    db.session.commit()

    response = client.get("/api/v1/images", headers=headers)
    assert response.status_code == 401
