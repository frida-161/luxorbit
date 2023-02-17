from sqlalchemy.exc import SQLAlchemyError

from luxorbit.models import User


def db_is_populated():
    """Check if our database is already populated."""
    try:
        User.query.all()
        return True
    except SQLAlchemyError:
        return False


def create_superuser():
    """Create a default superuser account."""
    su = User(name="admin", superuser=True)
    su.set_password("admin")
    return su
