# Introduction

This project contains the Label Store API for The Ocean Cleanup. This is used
to manage the full lifecycle of manually-labeled images from many different
sources.

# Configuration

The following environment variables can/need to be provided

| Variable | Required | Description |
| --- | --- | --- |
| FLASK_APP | True | Should be set to `main.py:app`
| DB_CONNECTION_STRING | True | Database connection string |
| DB_SCHEMA | True | Database schema to use. Note that this must exist already |
| AZURE_STORAGE_CONNECTION_STRING | True | Connection string for the blob storage account |
| AZURE_STORAGE_IMAGESET_CONTAINER | True | Container where new imagesets will be uploaded |
| AZURE_STORAGE_IMAGESET_FOLDER | True | Base folder (or path of folders) where new imagesets will be uploaded |
| IMAGE_READ_TOKEN_VALID_DAYS | False | Number of days the token returned for an image gives access (defaults to 7 if not set) |
| IMAGESET_UPLOAD_TOKEN_VALID_DAYS | False | Number of days the token returned for uploading images is valid (defaults to 7 if not set) |
| AZURE_ML_DATASTORE | True | Name of the datastore that reflects the container of our images |
| AZURE_ML_SUBSCRIPTION_ID | True | Subscription ID where the Azure ML workspace is located |
| AZURE_ML_RESOURCE_GROUP | True | Resource Group where the Azure ML workspace is located |
| AZURE_ML_WORKSPACE_NAME | True | Name of the Azure ML workspace |
| AZURE_ML_SP_TENANT_ID | True | Parameters to service principal for Azure ML |
| AZURE_ML_SP_APPLICATION_ID | True | Parameters to service principal for Azure ML |
| AZURE_ML_SP_PASSWORD | True | Parameters to service principal for Azure ML |

# API documentation

When the server is running, go to `<server_url>/api/v1/ui` to see a 
rendered version of the API specification. This uses the built-in Swagger 
UI.

Unfortunately, because Connexion does not support two-part API keys as
security configuration natively and it's not possible to disable Connexion
built-in security, we've had to disable the security definition of the API
spec. As a result, the UI is not able to interactively interact with the
API through the "Try it out" functionality, as it will not include the
required security parameters. For more information, see
https://github.com/zalando/connexion/issues/586 and
https://github.com/zalando/connexion/issues/1120.

If this functionality is ever desired, we may be able to add this manually
as part of the Swagger UI configuration through the `requestInterceptor`,
see
https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/

# Connect to Azure ML

In order to connect to Azure ML, the container in which the images are
stored should be configured as a DataStore in Azure ML. This datastore
should be given a name, and then be provided as environment variable
`AZURE_ML_DATASTORE` to this application.

In addition, the `AZURE_ML_SUBSCRIPTION_ID`, `AZURE_ML_RESOURCE_GROUP` and
`AZURE_ML_WORKSPACE_NAME` environment variables should be provided (see 
above).

Finally, a service principal should be created, and the credentials entered
through the `AZURE_ML_SP_TENANT_ID`, `AZURE_ML_SP_APPLICATION_ID` and
`AZURE_ML_SP_PASSWORD` environment variables. For creating the correct
SP, see the example on https://render.githubusercontent.com/view/ipynb?commit=c1b125025ade0e48fa04c8e774ecedb8df5acdc0&enc_url=68747470733a2f2f7261772e67697468756275736572636f6e74656e742e636f6d2f417a7572652f4d616368696e654c6561726e696e674e6f7465626f6f6b732f633162313235303235616465306534386661303463386537373465636564623864663561636463302f686f772d746f2d7573652d617a7572656d6c2f6d616e6167652d617a7572656d6c2d736572766963652f61757468656e7469636174696f6e2d696e2d617a7572656d6c2f61757468656e7469636174696f6e2d696e2d617a7572656d6c2e6970796e62&nwo=Azure%2FMachineLearningNotebooks&path=how-to-use-azureml%2Fmanage-azureml-service%2Fauthentication-in-azureml%2Fauthentication-in-azureml.ipynb&repository_id=145148726&repository_type=Repository#Service-Principal-Authentication

# Database

## How-to: Create new database version

Alembic is set up (through flask-migrate), in order to easily track database
versions and changes. Follow the steps below to create a new database version.

### 1. Modify models

Make the desired changes to `app/models/*.py`

### 2. Create database version file

Open a terminal in the main folder of the app `app` with the environment all
set up (most importantly the environment variables such that a database
connection can be made) and run

```bash
flask db migrate -m "Short description of changes"
```

This will compare the models to what is currently in the database, and creates
a migration file to change the database to reflect the model. This file will be
stored in `app/migrations/versions`. After this file is created, check the
contents manually, and make sure to add it to GIT so the changes are tracked.

### 3. Apply the migration to the database

Set up the environment variables as required (if not already done) and perform

```bash
flask db upgrade
```

This command will check what version is currently in the database, and will run
all the migrations that have come after that.

# Testing

Tests are implemented for all endpoints, at the least the "Happy
Flow" but also a lot of basic 'bad' cases. The framework used is pytest.

In order to prepare a test environment, create a local PostgreSQL database
and set the connection string in `tests/conftest.py`. Then create a Python
environment that includes both the requirements from `requirements.txt` and
`test_requirements.txt`.

To run the tests, navigate to the main folder of the app and execute
`pytest` or alternatively if you want to have coverage statistics run
`coverage run -m pytest`. To see the coverage, do either `coverage report`
or `coverage html` to create an HTML based coverage report.
