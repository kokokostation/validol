from functools import lru_cache

from validol.model.utils.utils import date_range, concat
from validol.model.store.resource import ActiveResource
from validol.model.utils.fs_cache import FsCache


class NetCache:
    def get(self, handle, with_cache):
        raise NotImplementedError

    def delete(self, handle):
        raise NotImplementedError

    def file(self, handle):
        return handle

    def one(self):
        raise NotImplementedError

    def handle(self, file):
        return file

    def available_handles(self):
        raise NotImplementedError


class Cache:
    def __init__(self, net_cache, fs_cache):
        self.net_cache = net_cache
        self.fs_cache = fs_cache

        self.fs_handle_map = {self.net_cache.handle(file): file for file in self.fs_cache.get_filenames()}

    def get(self, handle):
        if self.fs_cache.available():
            filename = self.file(handle)

            if filename is not None:
                content = self.fs_cache.read_file(filename)
            else:
                content = None

            if content is None:
                filename, content = self.net_cache.get(handle, False)
                if filename is not None:
                    self.fs_cache.write_file(filename, content)

            return content
        else:
            filename, content = self.net_cache.get(handle, True)

            return content

    def delete(self, handle):
        if self.fs_cache.available():
            filename = self.file(handle)
            if filename is not None:
                self.fs_cache.delete(filename)
        else:
            self.net_cache.delete(handle)

    def one(self):
        content = None

        if self.fs_cache.available():
            content = self.fs_cache.one()

        if content is None:
            content = self.net_cache.one()

        return content

    def file(self, handle):
        filename = self.net_cache.file(handle)

        if filename is None:
            filename = self.fs_handle_map[handle]

        return filename

    def available_handles(self):
        return set(self.fs_handle_map.keys()) | set(self.net_cache.available_handles())


class DailyResource(ActiveResource):
    def __init__(self, model_launcher, platform_code, active_name, actives_cls, flavor,
                 pdf_helper, active_cache):
        ActiveResource.__init__(self,
                                flavor["schema"],
                                model_launcher,
                                platform_code,
                                active_name,
                                flavor["name"],
                                actives_cls=actives_cls,
                                modifier=flavor['constraint'])

        self.model_launcher = model_launcher
        self.pdf_helper = pdf_helper
        self.active_cache = active_cache

    def get_flavors(self):
        df = self.read_df('SELECT DISTINCT CONTRACT AS active_flavor FROM "{table}"', index_on=False)

        return df

    def get_flavor(self, contract):
        return self.read_df('SELECT * FROM "{table}" WHERE CONTRACT = ?', params=(contract,))

    def download_dates(self, dates):
        return concat([self.download_date(date) for date in dates])

    def initial_fill(self):
        df = self.pdf_helper.initial(self.model_launcher)

        if not df.empty:
            net_df = self.download_dates(set(self.available_dates()) - set(df.Date))
        else:
            net_df = self.download_dates(self.available_dates())

        return df.append(net_df)

    def fill(self, first, last):
        return self.download_dates(set(self.available_dates()) & set(date_range(first, last)))

    def available_dates(self):
        fs_cache = FsCache(self.pdf_helper.active_folder)
        self.cache = Cache(self.active_cache, fs_cache)

        return self.cache.available_handles()

    def download_date(self, date):
        raise NotImplementedError