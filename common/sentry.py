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

from sentry_sdk.integrations.flask import FlaskIntegration
import sentry_sdk
import json
import os


class Sentry:

    def __init__(self, dsn):
        self.sensitive_data = []

        def strip_sensitive_data(event, hint):
            # Strip sensitive data from event
            event_str = json.dumps(event)

            for value in self.sensitive_data:
                event_str = event_str.replace(value, 'SENSITIVE_DATA')

            return json.loads(event_str)

        # Initialize Sentry
        sentry_sdk.init(
            dsn=dsn,
            integrations=[FlaskIntegration()],
            environment=os.environ.get('NAMESPACE', ''),
            release=os.environ.get('GIT_COMMIT', ''),
            server_name=os.environ.get('NODE_NAME', ''),
            traces_sample_rate=float(os.environ.get('TRANSACTION_SAMPLING_RATE', 0)),
            before_send=strip_sensitive_data,
            send_default_pii=True
        )

        # Set tags for version, branch, and host_name
        sentry_sdk.set_tag("version", os.environ.get('VERSION', ''))
        sentry_sdk.set_tag("branch", os.environ.get('GIT_BRANCH', ''))
        sentry_sdk.set_tag("host_name", os.environ.get('HOSTNAME', ''))

    def add_sensitive_value(self, value):
        self.sensitive_data.append(value)

    @staticmethod
    def clear_breadcrumbs():
        with sentry_sdk.configure_scope() as scope:
            scope.clear_breadcrumbs()

