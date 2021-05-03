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

from flask import has_request_context, request
import logging
import flask_login
import sys


class RequestFormatter(logging.Formatter):
    def format(self, record):
        try:
            if has_request_context():
                if flask_login.current_user is not None:
                    try:
                        record.user = flask_login.current_user.email
                    except:
                        record.user = "anonymous"
                else:
                    record.user = "anonymous"

                record.url = request.url
                record.method = request.method
                record.remote_addr = request.remote_addr
            else:
                record.user = ""
                record.url = ""
                record.remote_addr = ""
                record.method = ""
        except:
            record.user = ""
            record.url = ""
            record.remote_addr = ""
            record.method = ""

        return super().format(record)


def create_logger(loglevel):
    """ Set logger to both file and stream logger"""
    # Manual logger
    logger = logging.getLogger('label-api')
    if not logger.handlers:
        ch = logging.StreamHandler(stream=sys.stdout)
        log_format = \
            RequestFormatter(
                "%(levelname)s %(asctime)s [%(filename)s:%(lineno)s - "
                "%(funcName)s() - %(method)s %(url)s - %(remote_addr)s - "
                "%(user)s] %(message)s"
            )
        ch.setFormatter(log_format)
        logger.addHandler(ch)
        logger.setLevel(loglevel)
        logger.propagate = False

    return logger
