import logging
import os

from celery import Celery
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from luxorbit.strava.client import StravaClient


def make_celery(app):
    celery = Celery(app.import_name)
    celery.conf.update(app.config["CELERY_CONFIG"])

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


app = Flask(__name__)
app.config.from_object("luxorbit.config")

# sqlalchemy
db = SQLAlchemy(app)

# Stravaclient
client = StravaClient(app)

# celery
celery = make_celery(app)

# Setup logging with gunicorn
if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

# Blueprints
from luxorbit.routes.challenge import c_bp, challenge_bp
from luxorbit.routes.layer import layer_bp

app.register_blueprint(challenge_bp)
app.register_blueprint(c_bp)
app.register_blueprint(layer_bp)
