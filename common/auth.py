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

import flask_login
from common.db import db
from models.user import User
import logging

logger = logging.getLogger("label-api")

login_manager = flask_login.LoginManager()


@login_manager.request_loader
def request_loader(request):
    api_key = request.headers.get("Authentication-Key")
    api_secret = request.headers.get("Authentication-Secret")

    # Validate key against DB, return user
    user = db.session.query(User).filter_by(API_KEY=api_key).first()
    if user is not None and api_secret and user.is_active() \
            and user.check_password(api_secret):
        return user

    return None  # Not a User or invalid key, return None == Unauthenticated


@login_manager.unauthorized_handler
def unauthorized():
    logger.warning("Invalid or missing credentials")
    return (
        {
            "error": "Unauthorized request please make sure you set the "
                     "Authentication-Key and Authentication-Secret in the "
                     "header"
        },
        401,
        {"ContentType": "application/json"}
    )
