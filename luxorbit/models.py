import enum

from flask_login import UserMixin
from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship
from werkzeug.security import check_password_hash, generate_password_hash

Base = declarative_base()


class GeometryType(enum.Enum):
    """Available geodata types."""

    POINT = "point"
    LINE = "line"
    POLYGON = "polygon"


class Layer(Base):
    """universal Geodata Layer Model"""

    __tablename__ = "layer"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(Enum(GeometryType))
    file_blob = Column(LargeBinary, nullable=False)
    name_col = Column(String)
    about_col = Column(String)
    link_col = Column(String)
    image_col = Column(String)
    weight_col = Column(String)
    order_col = Column(String)
    challenge_id = Column(Integer, ForeignKey("challenge.id"))


class User(UserMixin, Base):
    """Model for our users."""

    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False, unique=True)
    password_hash = Column(String(120))
    superuser = Column(Boolean, default=False)
    challenges = relationship("Challenge", backref="user", lazy=True)

    def set_password(self, password):
        """Set the password for the user."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check the users password."""
        return check_password_hash(self.password_hash, password)


class Challenge(Base):
    """Model for our challenges"""

    __tablename__ = "challenge"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"))
    roundtrip = Column(Boolean, default=False)
    layers = relationship("Layer", backref="challenge", lazy=True)
    roundtrip = Column(Boolean, default=False)
    required_distance = Column(Integer, default=0)
    required_elevation = Column(Integer, default=0)
