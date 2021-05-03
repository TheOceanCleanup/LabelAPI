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

from models.user import User, Role
from main import app
from common.db import db

email = ""

with app.app_context():
    user = User.find_or_create(email)
    api_key, api_secret = user.generate_api_key()
    print(f"User credentials:\n\tAPI Key: {api_key}\n\tAPI secret: {api_secret}")
    role = Role(role="image-admin", user=user)
    db.session.commit()
