from itertools import groupby
from sqlalchemy import Column, String, orm
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
import datetime as dt

from validol.model.store.miners.monetary import MonetaryType
from validol.model.store.structures.structure import Base, JSONCodec
from validol.model.resource_manager.atom_base import AtomBase, rangable, series_map
from validol.model.utils.utils import to_timestamp, merge_dfs_list, FillSeries


class Currable:
    def get_full(self, ai, model_launcher):
        raise NotImplementedError

    def extract_info(self, df):
        raise NotImplementedError


class LazyAtom(AtomBase, Currable):
    @rangable
    def evaluate(self, evaluator, params):
        name = self.cache_name(params)

        df = evaluator.df

        if name in df:
            begin, end = [to_timestamp(a) for a in evaluator.range]

            return df[name][(begin <= df.index) & (df.index <= end)]
        else:
            return pd.Series()

    def get_full(self, ai, model_launcher):
        return ai.flavor.get_full_df(ai, model_launcher)

    def extract_info(self, df):
        return df[self.name]


class MonetaryAtom(AtomBase):
    def __init__(self, config_key):
        self._config_key = config_key

        AtomBase.__init__(self, self._config_key, [])

    @rangable
    def evaluate(self, evaluator, params):
        df = MonetaryType(evaluator.model_launcher, self._config_key).read_dates_dt(*evaluator.range)

        return df[self._config_key]


class FormulaAtom(Base, AtomBase):
    __tablename__ = "atoms"
    name = Column(String, primary_key=True)
    formula = Column(String)
    params = Column(JSONCodec())

    LETTER = '@letter'

    def __init__(self, name, formula, params):
        AtomBase.__init__(self, name, params, formula)

        self.formula = formula

    @rangable
    def evaluate(self, evaluator, params):
        params_map = dict(zip(self.params, params))

        return evaluator.parser.evaluate(self.formula, params_map)

    @orm.reconstructor
    def init_on_load(self):
        AtomBase.__init__(self, self.name, self.params, self.formula)


class MBDeltaAtom(AtomBase):
    def __init__(self):
        AtomBase.__init__(self, "MBDelta", [])

    @rangable
    def evaluate(self, evaluator, params):
        mbase = MonetaryAtom('MBase').evaluate(evaluator, params)

        grouped_mbase = [(mbase.iloc[0], 1)] + [(k, len(list(g))) for k, g in groupby(mbase)]
        deltas = []
        for i in range(1, len(grouped_mbase)):
            k, n = grouped_mbase[i]
            delta = k - grouped_mbase[i - 1][0]

            for j in range(n):
                deltas.append(delta / n)

        return pd.Series(deltas, index=mbase.index)




class Apply(AtomBase):
    def __init__(self):
        AtomBase.__init__(self, 'APPLY', ['atom, args separated by comma'])

    def evaluate(self, evaluator, params):
        return evaluator.atoms_map[params[0]].evaluate(evaluator, params[1:])


class Merge(AtomBase):
    def __init__(self):
        AtomBase.__init__(self, 'MERGE', ['dfs separated by comma'])

    def evaluate(self, evaluator, params):
        return merge_dfs_list([param.to_frame('i') for param in params])['i']


class Curr(AtomBase):
    def __init__(self):
        AtomBase.__init__(self, 'CURR', ['@atom', FormulaAtom.LETTER, '@delta'])

    def evaluate(self, evaluator, params):
        ai = evaluator.letter_map[params[1]]
        atom = evaluator.atoms_map[params[0]]

        df = evaluator.model_launcher.current(ai, int(params[2]), atom.get_full(ai, evaluator.model_launcher))

        if not df.empty:
            return atom.extract_info(df)
        else:
            return pd.Series()


class MlCurve(AtomBase, Currable):
    def __init__(self):
        AtomBase.__init__(self, 'MLCURVE', [FormulaAtom.LETTER])

    def evaluate(self, evaluator, params):
        ai = evaluator.letter_map[params[0]]

        return evaluator.model_launcher.get_ml_curves(ai)

    def get_full(self, ai, model_launcher):
        return model_launcher.get_ml_curves(ai, False)

    def extract_info(self, df):
        return df.CURVE


class ArgMin(AtomBase):
    def __init__(self):
        AtomBase.__init__(self, 'ARGMIN', ['series of series'])

    def evaluate(self, evaluator, params):
        return params[0].apply(lambda curve: curve.argmin())


class Quantile(AtomBase):
    def __init__(self):
        AtomBase.__init__(self, 'QUANTILE', ['series of series', 'quantile', 'min or max'])

    @staticmethod
    def get_quantile(series, q, minmax):
        argmin = series.argmin()

        ml = series[argmin] * (1 + q)

        if minmax == 'min':
            series = series.loc[:argmin].iloc[::-1]
        else:
            series = series.loc[argmin:]

        if len(series) < 2:
            return np.NaN

        return np.interp(ml, series.values, series.index)

    def evaluate(self, evaluator, params):
        return params[0].apply(lambda curve: Quantile.get_quantile(curve, params[1], params[2]))


class Min(AtomBase):
    def __init__(self):
        AtomBase.__init__(self, 'MIN', ['series of series'])

    def evaluate(self, evaluator, params):
        return params[0].apply(lambda curve: curve.min())


class Expirations(AtomBase):
    def __init__(self):
        AtomBase.__init__(self, 'EXPS', ['@letter'])

    def evaluate(self, evaluator, params):
        return evaluator.model_launcher.get_expirations(evaluator.letter_map[params[0]])

    def note(self):
        return {'fill_method': 'bfill'}


class FillAtom(AtomBase):
    def __init__(self):
        AtomBase.__init__(self, 'FILL', ['series', 'fill_method'],
                          '''fill nans according to fill_method. 
Works for operands of arithmetic operations. For example: "OI(A) / FILL(MBase(), linear)"

fill_method possible values:
    "linear" -- linear interpolation
    "forward" -- use PREVIOUS valid observation to fill gap
    "backward" -- use NEXT valid obsrevation to fill gap''')

    def evaluate(self, evaluator, params):
        return FillSeries(params[0], params[1])


class CFYAAtom(AtomBase):
    def __init__(self):
        AtomBase.__init__(self, 'CFYA', ['series'],
                          'Change from year ago. This function takes time series. '
                          'For every point A of the series CFYA(date(A)) = value(A) - value(B), '
                          'where date(B) is the closest point to (date(A) - year)')

    @staticmethod
    def _absolute_delta(first_date, second_date):
        return abs((first_date - second_date).total_seconds())

    @series_map()
    def evaluate(self, evaluator, series):
        back_index = 0
        result = series[series.index >= (series.index[0] + relativedelta(years=1))].copy()

        for i, (date, value) in enumerate(result.iteritems()):
            year_ago = date - relativedelta(years=1)

            for next_date in series.index[back_index + 1:]:
                if self._absolute_delta(year_ago, next_date) < \
                   self._absolute_delta(year_ago, series.index[back_index]):
                    back_index += 1
                else:
                    break

            result.iloc[i] = value - series.iloc[back_index]

        return result


class QuarterMeanAtom(AtomBase):
    def __init__(self):
        AtomBase.__init__(self, 'QMEAN', ['series'], 'Calculates average for every series quarter, '
                                                     'even if a quarter contains only one value')

    @series_map()
    def evaluate(self, evaluator, series):
        index, data = [], []
        first_date = series.index[0]
        first_quarter_month = [b for b in range(1, 13, 3) if b <= first_date.month][-1]
        current_quarter = dt.date(first_date.year, first_quarter_month, 1)

        while current_quarter <= series.index[-1]:
            current_quarter_end = current_quarter + relativedelta(months=3)
            segment = series.loc[current_quarter:current_quarter_end]

            data.extend([segment.mean()] * 2)
            index.extend([current_quarter, current_quarter_end - relativedelta(days=1)])

            current_quarter = current_quarter_end

        return pd.Series(data, index=index)
