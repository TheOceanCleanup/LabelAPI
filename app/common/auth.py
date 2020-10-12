import flask_login

login_manager = flask_login.LoginManager()


@login_manager.request_loader
def request_loader(request):
    api_key = request.headers.get('Authentication-Key')
    api_secret = request.headers.get('Authentication-Secret')

    # Validate key against DB, return grants / user
    # TODO: Supposed to return user - how to deal with campaign based auth?

    return None  # Not a device or a consumer, return None == Unauthenticated


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
