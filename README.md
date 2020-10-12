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
