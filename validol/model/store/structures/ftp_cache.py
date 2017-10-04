from sqlalchemy import Column, String, LargeBinary
from io import BytesIO
from ftplib import FTP

from validol.model.store.structures.structure import NamedStructure, Base


class FtpCacheEntry(Base):
    __tablename__ = 'ftp'
    name = Column(String, primary_key=True)
    value = Column(LargeBinary)

    @staticmethod
    def load(ftp_server, file):
        with FTP(ftp_server) as ftp:
            ftp.login()
            data = BytesIO()
            ftp.retrbinary('RETR {}'.format(file), data.write)

        return FtpCacheEntry(name=file, value=data.getvalue())


class FtpCache(NamedStructure):
    def __init__(self, model_launcher):
        NamedStructure.__init__(self, FtpCacheEntry, model_launcher, model_launcher.cache_engine)

    def get(self, ftp_server, file, with_cache=True):
        if with_cache:
            try:
                return self.read_by_name(file).value
            except:
                obj = FtpCacheEntry.load(ftp_server, file)

                self.write(obj)
        else:
            obj = FtpCacheEntry.load(ftp_server, file)

        return obj.value

