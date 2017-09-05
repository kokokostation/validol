from validol.model.utils import date_range
from validol.model.store.resource import ActiveResource
from validol.model.utils import concat


class DailyResource(ActiveResource):
    def __init__(self, model_launcher, platform_code, active_name, actives_cls, flavor,
                 pdf_helper):
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
        raise NotImplementedError

    def download_date(self, date):
        raise NotImplementedError