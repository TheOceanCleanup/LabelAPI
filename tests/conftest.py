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

import pytest
import os

os.environ["DB_SCHEMA"] = "labelapi"

os.environ['NAMESPACE'] = "testing"
os.environ['GIT_COMMIT'] = "new"
os.environ['NODE_NAME'] = "localhost"
os.environ['VERSION'] = 'test'
os.environ['GIT_BRANCH'] = 'master'
os.environ['HOSTNAME'] = 'this-pc'

os.environ["DB_CONNECTION_STRING"] = \
    'postgresql://toc:toc_pswd@localhost:5433/toc_test'
os.environ["AZURE_STORAGE_CONNECTION_STRING"] = "connstring"
os.environ['AZURE_ML_SP_PASSWORD'] = 'password'

from common.db import db as _db
from main import App
from flask import request
import sqlalchemy

port = 5005


@pytest.fixture
def app():
    os.environ["IMAGE_TOKEN_VALID_DAYS"] = "7"
    os.environ["AZURE_STORAGE_IMAGESET_CONTAINER"] = "upload-container"
    os.environ["AZURE_STORAGE_IMAGESET_FOLDER"] = "uploads"

    app = App().app
    with app.app_context():
        _db.close_all_sessions()

        if not _db.engine.dialect.has_schema(_db.engine, 'labelapi'):
            _db.engine.execute(sqlalchemy.schema.CreateSchema('labelapi'))

        _db.drop_all()
        _db.create_all()

        yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db():
    return _db


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@pytest.fixture
def real_server(app):
    global port
    port += 1

    @app.route('/shutdown', methods=('POST',))
    def shutdown():
        print("Shutting down")
        shutdown_server()
        return 'Shutting down server ...'

    import threading
    t = threading.Thread(
        target=app.run,
        kwargs={"host": '0.0.0.0', "port": port})
    t.start()
    yield port

    import requests
    requests.post('http://localhost:%s/shutdown' % str(port))
