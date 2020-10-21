from flask import has_request_context, request
import logging
import flask_login
import sys


class RequestFormatter(logging.Formatter):
    def format(self, record):
        try:
            if has_request_context():
                if flask_login.current_user is not None:
                    record.user = flask_login.current_user.email
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

    return logger
