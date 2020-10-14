import flask_login
from common.db import db
from models.user import User

login_manager = flask_login.LoginManager()


@login_manager.request_loader
def request_loader(request):
    api_key = request.headers.get('Authentication-Key')
    api_secret = request.headers.get('Authentication-Secret')

    # Validate key against DB, return user
    user = db.session.query(User).filter_by(API_KEY=api_key).first()
    if user is not None and api_secret and user.check_password(api_secret):
        return user

    return None  # Not a User or invalid key, return None == Unauthenticated


@login_manager.unauthorized_handler
def unauthorized():
    return (
        {
            'error': 'Unauthorized request please make sure you set the '
                     'Application-Key and Application-Secret in the header'
        },
        401,
        {'ContentType': 'application/json'}
    )
