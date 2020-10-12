from flask import has_request_context
import logging
import flask_login


class RequestFormatter(logging.Formatter):
    def format(self, record):
        # TODO implement

        return super().format(record)


def create_logger(loglevel):
    """ Set logger to both file and stream logger"""
    logger = logging.getLogger('label-api')
    if not logger.handlers:
        logger.setLevel(loglevel)
        ch = logging.StreamHandler()
        # TODO: add desired params
        log_format = \
            RequestFormatter(
                "%(asctime)s [%(filename)s:%(lineno)s - %(funcName)s() ] "
                "%(message)s"
            )
        ch.setFormatter(log_format)
        logger.addHandler(ch)
    return logger
