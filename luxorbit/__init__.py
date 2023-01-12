from flask_sqlalchemy import SQLAlchemy
from celery import Celery
from flask import Flask
import os

from luxorbit.client import StravaClient


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
app.config.update(
    CELERY_CONFIG={
        'broker_url': 'redis://redis:6379',
        'result_backend': 'redis://redis:6379'
    }
)
celery = make_celery(app)

SECRET_KEY = os.getenv('SECRET_KEY', 'notverysecret')
app.config['SECRET_KEY'] = SECRET_KEY

client = StravaClient()


#db = SQLAlchemy(app)
#db.create_all()

import luxorbit.auth, luxorbit.strava
