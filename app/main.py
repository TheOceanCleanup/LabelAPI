import connexion
from flask_migrate import Migrate
# from models.campaign import Campaign, CampaignImage
# from models.image import Image, ImageSet
# from models.object import Object
from common.db import db
import os

from swagger_ui_bundle import swagger_ui_3_path



class App:

    instance = None

    def __init__(self):
        """ Initialize app """

        app = connexion.FlaskApp(
            __name__,
            specification_dir='../'
        )
        app.app.config['SQLALCHEMY_DATABASE_URI'] = \
            os.environ.get('DB_CONNECTION_STRING')

        app.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app.app)

        migrate = Migrate()
        migrate.init_app(app.app, db)

        app.add_api('api.yaml',
                    strict_validation=True)

        self.app = app.app  # Flask app object
        self.application = app  # Connexion app object
        self.db = db
        self.migrate = migrate

        App.instance = self


def get_app():
    """
    Return the app object. If it was not created, do so first.

    :return: App object.
    """

    if App.instance is None:
        App()
    return App.instance


# Create Flask app object
app = get_app().app


@app.route("/info/version", methods=["GET"])
def handle_version():
    version = os.environ.get("VERSION", "?")
    branch = os.environ.get("GIT_BRANCH", "?")
    commit = os.environ.get("GIT_COMMIT", "?")
    return "Version: %s (branch: %s, commit: %s)" % (version, branch, commit)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True, use_reloader=True)
