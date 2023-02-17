import os

SECRET_KEY = os.getenv("SECRET_KEY", "verytopsecret")

# SQLALCHEMY
SQLALCHEMY_DATABASE_URI = os.getenv(
    "SQLALCHEMY_DATABASE_URI", "postgresql://luxorbit:luxorbit@luxorbit-db/luxorbit"
)

CELERY_CONFIG = {
    "broker_url": "redis://redis:6379",
    "result_backend": "redis://redis:6379",
}

# strava
STRAVA_CLIENT_ID = os.environ["STRAVA_CLIENT_ID"]
STRAVA_CLIENT_SECRET = os.environ["STRAVA_CLIENT_SECRET"]


BASE_URL = os.environ["BASE_URL"]
