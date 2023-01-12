from stravalib import Client
import os


class StravaClient(Client):
    """A stravalib Client with a few extras."""

    def __init__(self):
        """Init function of the StravaClient class."""
        super().__init__()
        self.client_id = os.environ['STRAVA_CLIENT_ID']
        self.client_secret = os.environ['STRAVA_CLIENT_SECRET']

    def refresh_access_token(self, refresh_token):
        """Get a new access token."""
        return super().refresh_access_token(
            client_id=self.client_id,
            client_secret=self.client_secret,
            refresh_token=refresh_token
        )

    def authorization_url(self, redirect_uri):
        """Get an authorization url."""
        return super().authorization_url(
            client_id=self.client_id,
            redirect_uri=redirect_uri
        )

    def exchange_code_for_token(self, code):
        """Exchange a code for a Token and safe it to the DB."""
        return super().exchange_code_for_token(
            client_id=self.client_id,
            client_secret=self.client_secret,
            code=code
        )
