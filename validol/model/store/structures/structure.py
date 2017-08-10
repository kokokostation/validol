from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from functools import wraps


def with_session(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        session = self.session

        result = f(self, session, *args, **kwargs)

        session.commit()

        return result

    return wrapper


Base = declarative_base()


class Structure:
    def __init__(self, klass, model_launcher):
        self.klass = klass
        self.model_launcher = model_launcher

        self.klass.__table__.create(bind=self.model_launcher.user_dbh, checkfirst=True)
        self.Session = sessionmaker(bind=self.model_launcher.user_dbh, expire_on_commit=False)

    @with_session
    def write(self, session, item):
        session.add(item)

    @with_session
    def read(self, session, pred=None):
        result = session.query(self.klass)

        if pred is not None:
            result = result.filter(pred)

        return result.all()

    def read_by_name(self, name):
        return self.read(self.klass.name == name)[0]

    @with_session
    def remove_by_pred(self, session, pred):
        session\
            .query(self.klass)\
            .filter(pred)\
            .delete(synchronize_session=False)

    def remove_by_name(self, name):
        self.remove_by_pred(self.klass.name == name)

    @property
    def session(self):
        return self.Session()