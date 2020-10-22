FROM python:3.7-slim

# Install build dependencies
# RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev
# RUN apk add --virtual=build gcc libffi-dev musl-dev openssl-dev make cmake g++

# RUN apk add jpeg-dev zlib-dev
RUN apt-get update && apt-get -y install gcc libpq-dev
# ENV LIBRARY_PATH=/lib:/usr/lib

# Install dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

ARG GIT_BRANCH=unspecified
LABEL git_branch=$GIT_BRANCH
ENV GIT_BRANCH=$GIT_BRANCH

ARG GIT_COMMIT=unspecified
LABEL git_commit=$GIT_COMMIT
ENV GIT_COMMIT=$GIT_COMMIT

ARG VERSION=unspecified
LABEL version=$VERSION
ENV VERSION=$VERSION

EXPOSE 8080

ENV FLASK_APP=main.py:app
CMD exec gunicorn --statsd-host=localhost:9125 --statsd-prefix=label-storage --bind :8080 --workers 2 --threads 4 wsgi:app
