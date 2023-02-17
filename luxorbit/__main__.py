import sys

from luxorbit import app, db
from luxorbit.models import Base, User

if __name__ == "__main__":
    if "init_db" in sys.argv:
        with app.app_context():
            Base.metadata.create_all(db.engine)
            users = db.session.query(User).all()
            if len(users) == 0:
                su = User(name="admin", superuser=True)
                su.set_password("admin")
                db.session.add(su)
                db.session.commit()
