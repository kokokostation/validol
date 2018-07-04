import datetime as dt
from io import StringIO
import pandas as pd

from validol.model.store.resource import Platforms, FlavorUpdater
from validol.model.utils.utils import group_by
from validol.model.store.miners.weekly_reports.active import WeeklyActives, Active
from validol.model.store.miners.weekly_reports.utils import active_iterator
from validol.model.store.utils import reduce_ranges


class Flavor(FlavorUpdater):
    @staticmethod
    def get_active_platform_name(market_and_exchange_names):
        return [name.strip() for name in market_and_exchange_names.rsplit("-", 1)]

    def flavor_latest_year(self, flavor):
        curr_year = dt.date.today().year
        fly = -1

        for active in active_iterator(flavor, self.model_launcher):
            fly = max(fly, active.range()[1].year)

            if fly == curr_year:
                return fly

        return fly

    def if_initial(self, flavor):
        return Platforms(self.model_launcher, flavor['name']).is_initial()

    def get_df(self, flavor):
        cols = flavor["keys"] + \
               list(flavor["values"].keys()) + \
               flavor.get("add_cols", [])

        df = pd.DataFrame()

        for csv, date_fmt in self.load_csvs(flavor):
            df = df.append(pd.read_csv(
                StringIO(csv),
                usecols=cols,
                parse_dates=[flavor["date"]],
                date_parser=lambda date: dt.datetime.strptime(date, date_fmt).date()))

        df = df.rename(str, flavor["values"])

        df[flavor["keys"]] = df[flavor["keys"]].applymap(lambda x: x.strip())

        return df

    def process_flavor(self, df, flavor):
        info = group_by(df, flavor["keys"])

        actives_table = WeeklyActives(self.model_launcher, flavor['name'])
        platforms_table = Platforms(self.model_launcher, flavor['name'])

        platforms = set()
        actives = set()

        for code, name in info.groups.keys():
            active_name, platform_name = Flavor.get_active_platform_name(name)
            platforms.add((code, platform_name))
            actives.add((code, active_name))

        for table, columns, values in (
                (platforms_table, ("PlatformCode", "PlatformName"), platforms),
                (actives_table, ("PlatformCode", "ActiveName"), actives)):
            table.write_df(pd.DataFrame(list(values), columns=columns))

        ranges = []

        for code, name in info.groups.keys():
            active_name, _ = Flavor.get_active_platform_name(name)
            ranges.append(Active(self.model_launcher, flavor, code, active_name,
                                 info.get_group((code, name))).update())

        return reduce_ranges(ranges)

    def load_csvs(self, flavor):
        raise NotImplementedError
