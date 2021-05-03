# LabelAPI - Server program that provides API to manage training sets for machine learning image recognition models
# Copyright (C) 2020-2021 The Ocean Cleanup™
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
