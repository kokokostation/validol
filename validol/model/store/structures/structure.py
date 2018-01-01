from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import TypeDecorator
from sqlalchemy import String
from functools import wraps
import json
from sqlalchemy.exc import IntegrityError


class JSONCodec(TypeDecorator):
    impl = String

    def __init__(self, schema=None, post_load=None, pre_dump=None, *args, **kwargs):
        TypeDecorator.__init__(self, *args, **kwargs)
        self.schema = schema
        self.post_load = post_load
        self.pre_dump = pre_dump

    def process_bind_param(self, value, dialect):
        if self.pre_dump is not None:
            value = self.pre_dump(value)

        if self.schema is None:
            value = json.dumps(value)
        else:
            value = self.schema.dumps(value).data

        return value

    def process_result_value(self, value, dialect):
        if self.schema is None:
            value = json.loads(value)
        else:
            value = self.schema.loads(value).data

        if self.post_load is not None:
            value = self.post_load(value)

        return value


def with_session(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        session = self.session

        result = f(self, session, *args, **kwargs)

        session.commit()
        session.close()

        return result

    return wrapper


Base = declarative_base()


class PieceNameError(Exception):
    pass


class Structure:
    def __init__(self, klass, model_launcher, engine=None):
        self.klass = klass
        self.model_launcher = model_launcher
        if engine is None:
            engine = self.model_launcher.user_engine

        self.klass.__table__.create(bind=engine, checkfirst=True)
        self.Session = sessionmaker(bind=engine, expire_on_commit=False)

    @with_session
    def write(self, session, item):
        session.merge(item)

    @with_session
    def read(self, session, pred=None):
        result = session.query(self.klass)

        if pred is not None:
            result = result.filter(pred)

        return result.all()

    def read_all_by_name(self, name):
        return self.read(self.klass.name == name)

    def read_by_name(self, name):
        return self.read_all_by_name(name)[0]

    @with_session
    def remove_by_pred(self, session, pred=None):
        session \
            .query(self.klass) \
            .filter(pred) \
            .delete(synchronize_session=False)

    @with_session
    def remove(self, session, item):
        session.delete(item)

    def remove_by_name(self, name):
        self.remove_by_pred(self.klass.name == name)

    @property
    def session(self):
        return self.Session()

    @with_session
    def one_or_none(self, session):
        return session.query(self.klass).first()


class NamedStructure(Structure):
    def write(self, item):
        try:
            super().write(item)
        except IntegrityError:
            raise PieceNameError
