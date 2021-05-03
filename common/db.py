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

from flask_sqlalchemy import SQLAlchemy
from alembic import config
from alembic import script
from alembic.runtime import migration
import logging
import os

logger = logging.getLogger("label-api")


db = SQLAlchemy()


def status_check():
    """
    Check whether a connection to the database can be made.
    """
    try:
        with db.engine.connect() as conn:
            conn.execute("SELECT 1")
            return True, None
    except Exception as e:
        logger.error(f"Connect to database failed: {e}")
        return False, f"Failed to connect to database: {e}"


def version_check():
    """
    Check whether the installed database version is the latest version
    """
    alembic_cfg = config.Config('migrations/alembic.ini')
    script_ = script.ScriptDirectory.from_config(alembic_cfg)
    latest_version = script_.get_current_head()

    with db.engine.connect() as conn:
        conn.execute(f'SET search_path TO {os.environ["DB_SCHEMA"]}, public')
        installed_version = \
            migration.MigrationContext.configure(conn).get_current_revision()

    if installed_version is None:
        logger.error(f"No database version detected - run `flask db upgrade`")
        return False, "No database version detected - run `flask db upgrade`"

    if installed_version == latest_version:
        return True, None
    else:
        logger.error(
            f"Database is not up to date - Installed: {installed_version}, "\
            f"Latest {latest_version}. - run `flask db upgrade`"
        )
        return \
            False,\
            f"Database is not up to date - Installed: {installed_version}, "\
            f"Latest {latest_version}. - run `flask db upgrade`"
