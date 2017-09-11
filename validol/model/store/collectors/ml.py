import pandas as pd

from validol.model.utils import to_timestamp
from validol.model.store.resource import ActiveResource, FlavorUpdater, check_empty, Updater
from validol.model.store.miners.daily_reports.flavors import DAILY_REPORT_FLAVORS
from validol.model.utils import group_by


@check_empty
def pre_dump(df):
    df.CURVE = df.CURVE.apply(lambda series: series.to_json(orient='split'))

    return df

@check_empty
def post_load(df):
    df.CURVE = df.CURVE.map(lambda json: pd.read_json(json, typ='series', orient='split'))

    return df


class MlCurves(FlavorUpdater):
    def __init__(self, model_launcher):
        FlavorUpdater.__init__(self, model_launcher,
                               [flavor for flavor in DAILY_REPORT_FLAVORS if flavor['options']])

    def update_flavor(self, flavor):
        ranges = [
            MlCurve(self.model_launcher, ai).update()
            for ai in flavor['view'](flavor).all_actives(self.model_launcher, with_flavors=False)
        ]

        return Updater.reduce_ranges(ranges)


class MlCurve(ActiveResource):
    SCHEMA = [
        ('CONTRACT', 'TEXT'),
        ('CURVE', 'TEXT')
    ]

    def __init__(self, model_launcher, ai):
        ActiveResource.__init__(self,
                                MlCurve.SCHEMA,
                                model_launcher,
                                ai.platform,
                                ai.active,
                                'mlcurve_{view}'.format(view=ai.flavor.name()),
                                actives_cls=ai.flavor.actives_cls,
                                modifier='UNIQUE (Date, CONTRACT) ON CONFLICT IGNORE',
                                pre_dump=pre_dump,
                                post_load=post_load,
                                actives_flavor=ai.flavor.name())

        self.model_launcher = model_launcher
        self.ai = ai

    @staticmethod
    def ml(df):
        df = df.set_index('STRIKE', drop=False).sort_index()

        result = pd.Series()
        for letter, direction in (('C', 1), ('P', -1)):
            line = df.iloc[::direction]
            line = (abs(line.STRIKE.diff().fillna(0)) *
                    (line.OI * (line.PC == letter)).cumsum().shift(1).fillna(0)).cumsum()

            result = result.add(line, fill_value=0)

        return result.drop_duplicates()

    def process_dates(self, mapping):
        info = group_by(mapping(self.ai.flavor.get_full_df(self.ai, self.model_launcher)), ['Date', 'CONTRACT'])

        result = pd.DataFrame()

        for date, contract in info.groups.keys():
            result = result.append(pd.DataFrame(
                [[date, contract, MlCurve.ml(info.get_group((date, contract)))]],
                columns=['Date', 'CONTRACT', 'CURVE']))

        return result

    def fill(self, first, last):
        return self.process_dates(lambda df: df[(to_timestamp(first) <= df.index) &
                                                (df.index <= to_timestamp(last))])

    def initial_fill(self):
        return self.process_dates(lambda df: df)

    def read_curves(self, with_flavor):
        if with_flavor:
            return self.read_df('SELECT Date, CURVE FROM "{table}" WHERE CONTRACT = ?', params=(self.ai.active_flavor,)).CURVE
        else:
            return self.read_df()