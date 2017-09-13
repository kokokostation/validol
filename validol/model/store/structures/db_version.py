from sqlalchemy import Column, String

from validol.model.store.structures.structure import Structure, Base, with_session


class DbVersion(Base):
    __tablename__ = 'db_version'

    version = Column(String, primary_key=True)

    def __init__(self, version):
        self.version = version


class DbVersionManager(Structure):
    def __init__(self, model_launcher):
        Structure.__init__(self, DbVersion, model_launcher)

        if self.one_or_none() is None:
            self.write(DbVersion('0.0.0'))

    def get_version(self):
        return self.one_or_none().version

    @with_session
    def write_version(self, session, version):
        version_obj = session.query(DbVersion).first()
        version_obj.version = version
