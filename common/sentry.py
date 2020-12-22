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
            environment=os.environ['NAMESPACE'],
            release=os.environ['GIT_COMMIT'],
            server_name=os.environ['NODE_NAME'],
            traces_sample_rate=1.0,
            before_send=strip_sensitive_data,
            send_default_pii=True
        )

        # Set tags for version, branch, and host_name
        sentry_sdk.set_tag("version", os.environ['VERSION'])
        sentry_sdk.set_tag("branch", os.environ['GIT_BRANCH'])
        sentry_sdk.set_tag("host_name", os.environ['HOSTNAME'])

    def add_sensitive_value(self, value):
        self.sensitive_data.append(value)

    @staticmethod
    def clear_breadcrumbs():
        with sentry_sdk.configure_scope() as scope:
            scope.clear_breadcrumbs()

