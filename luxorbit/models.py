from geoalchemy2 import Geometry
from s2pg import db
from sqlalchemy_utils import create_view
from sqlalchemy import func, select


class Token(db.Model):
    __tablename__ = 'token'
    id = db.Column(db.Integer, primary_key = True)
    access_token = db.Column(db.String)
    refresh_token = db.Column(db.String)
    expires_at = db.Column(db.Integer)

class DataPoint(db.Model):
    __tablename__ = 'data_points'
    id = db.Column(db.Integer, primary_key = True)
    activity = db.Column(db.String,
        db.ForeignKey('activities.id'), nullable = False)
    altitude = db.Column(db.Float)
    cadence = db.Column(db.Integer)
    distance = db.Column(db.Float)
    heartrate = db.Column(db.Integer)
    moving = db.Column(db.Boolean)
    watts = db.Column(db.Integer)
    grade_smooth = db.Column(db.Float)
    velocity_smooth = db.Column(db.Float)
    time = db.Column(db.Integer)
    temp = db.Column(db.Integer)
    geom = db.Column(Geometry('POINT'))

class Activity(db.Model):
    __tablename__ = 'activities'
    id = db.Column(db.String, primary_key = True)
    name = db.Column(db.String)
    type = db.Column(db.String)
    gear_id = db.Column(db.String)
    suffer_score = db.Column(db.Integer)
    calories = db.Column(db.Integer)
    device_name = db.Column(db.String)
    trainer = db.Column(db.Boolean)
    commute = db.Column(db.Boolean)
    manual = db.Column(db.Boolean)
    points = db.relationship(
        'DataPoint', backref = 'activities', lazy = True)

stmt = select([
    Activity.id,
    Activity.gear_id,
    func.ST_SetSRID(func.ST_MakeLine(DataPoint.geom), 4326).label('geom')
    ]).select_from(DataPoint.__table__.join(Activity,
    DataPoint.activity == Activity.id)).group_by(Activity.id)

view = create_view('linien', stmt, db.Model.metadata)

class Linien(db.Model):
    __table__ = view
