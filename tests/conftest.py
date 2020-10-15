import pytest
import os
from common.db import db as _db
from main import App
from flask import request

port = 5005


@pytest.fixture
def app():
    os.environ["DB_CONNECTION_STRING"] = \
        'postgresql://toc:toc_pswd@localhost:5433/toc_test'

    app = App().app
    with app.app_context():
        _db.close_all_sessions()
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
