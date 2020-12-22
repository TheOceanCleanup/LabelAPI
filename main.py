import connexion
from flask_migrate import Migrate
from flask import abort
from models.campaign import Campaign, CampaignImage
from models.image import Image, ImageSet
from models.object import Object
from models.user import User, Role
from common.db import db, status_check as db_status_check, \
    version_check as db_version_check
from common.azure import AzureWrapper
from common.auth import login_manager
from common.logger import create_logger
from common.sentry import Sentry
import os

# Set up logging
logger = create_logger(os.environ.get('LOGLEVEL', 'INFO'))


class App:

    instance = None

    def __init__(self):
        # Configure Sentry
        sentry = Sentry("https://16f5d3ca5e42426cbafca33ff6a0786f@o486030.ingest.sentry.io/5567167")
        sentry.add_sensitive_value(os.environ['DB_CONNECTION_STRING'])
        sentry.add_sensitive_value(os.environ['AZURE_STORAGE_CONNECTION_STRING'])
        sentry.add_sensitive_value(os.environ['AZURE_ML_SP_PASSWORD'])

        """ Initialize app """
        app = connexion.FlaskApp(
            __name__,
            specification_dir="."
        )
        app.app.config["SQLALCHEMY_DATABASE_URI"] = \
            os.environ.get("DB_CONNECTION_STRING")

        app.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 60,
            "pool_size": 10
        }
        db.init_app(app.app)

        migrate = Migrate()
        migrate.init_app(app.app, db)

        login_manager.init_app(app.app)

        app.add_api("api.yaml",
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


@app.before_request
def before_request_func():
    logger.info("")


@app.route("/info/version", methods=["GET"])
def handle_version():
    version = os.environ.get("VERSION", "?")
    branch = os.environ.get("GIT_BRANCH", "?")
    commit = os.environ.get("GIT_COMMIT", "?")
    return "Version: %s (branch: %s, commit: %s)" % (version, branch, commit)


@app.route("/info/status", methods=["GET"])
def handle_status():
    result = {
        "database": {
            "Can connect": False,
            "Is correct version": False
        },
        "blobstorage": {
            "Can connect": False,
            "Container exists": False,
            "Can create container": False,
            "Can create blob": False
        },
        "azureml": {
            "Can get workspace": False,
            "Datastore exists": False
        },
        "environment": {
            "FLASK_APP": False,
            "DB_CONNECTION_STRING": False,
            "AZURE_STORAGE_CONNECTION_STRING": False,
            "AZURE_STORAGE_IMAGESET_CONTAINER": False,
            "AZURE_STORAGE_IMAGESET_FOLDER": False,
            "AZURE_ML_DATASTORE": False,
            "AZURE_ML_SUBSCRIPTION_ID": False,
            "AZURE_ML_RESOURCE_GROUP": False,
            "AZURE_ML_WORKSPACE_NAME": False,
            "AZURE_ML_SP_TENANT_ID": False,
            "AZURE_ML_SP_APPLICATION_ID": False,
            "AZURE_ML_SP_PASSWORD": False
        },
        "messages": []
    }

    # Start by checking the environment variables
    for key in result["environment"].keys():
        if key in os.environ:
            result["environment"][key] = True
        else:
            result["messages"].append(
                f"Required environment variable {key} missing"
            )
    
    # If any environment variables are unset, don't even continue
    if not all(result["environment"].values()):
        result["messages"].append(
            "Aborted further checks due to missing environment variables")
        return result, 500

    # Check database:
    # - Connect to database
    # - Schema version up to date
    result["database"]["Can connect"], msg = db_status_check()
    if msg is not None:
        result["messages"].append(msg)

    # Version check only makes sense if database is okay
    if result["database"]["Can connect"]:
        result["database"]["Is correct version"], msg = db_version_check()
        if msg is not None:
            result["messages"].append(msg)

    # Check Azure Storage
    # - Check if connection can be made to blob storage
    # - Check if required container exists
    # - Can create container
    # - Can upload file to uploads directory
    result["blobstorage"]["Can connect"], msg = \
        AzureWrapper.check_storage_connect()
    if msg is not None:
        result["messages"].append(msg)

    # Other checks only make sense if connection works
    if result["blobstorage"]["Can connect"]:
        result["blobstorage"]["Container exists"], msg = \
            AzureWrapper.check_container_exists()
        if msg is not None:
            result["messages"].append(msg)

        result["blobstorage"]["Can create container"], msg = \
            AzureWrapper.check_create_container()
        if msg is not None:
            result["messages"].append(msg)

        # Only if the container exists can we try to create a blob
        if result["blobstorage"]["Container exists"]:
            result["blobstorage"]["Can create blob"], msg = \
                AzureWrapper.check_create_blob()
            if msg is not None:
                result["messages"].append(msg)

    # Check Azure ML
    # - Can load workspace
    # - Datastore exists
    result["azureml"]["Can get workspace"], msg = \
        AzureWrapper.check_get_workspace()
    if msg is not None:
        result["messages"].append(msg)

    # Checking if datastore exists only makes sense if we can get workspace
    if result["azureml"]["Can get workspace"]:
        result["azureml"]["Datastore exists"], msg = \
            AzureWrapper.datastore_exists()
        if msg is not None:
            result["messages"].append(msg)

    # Validate all results to determine if we need to return 200 OK or 500
    if not all([
                all(result.get(x, {}).values())
                for x in ["database", "blobstorage", "azureml"]
            ]):
        return result, 500
    return result
