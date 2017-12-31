from itertools import groupby
from sqlalchemy import Column, String
import pandas as pd
import numpy as np

from validol.model.store.miners.monetary import Monetary
from validol.model.store.structures.structure import Base, JSONCodec
from validol.model.resource_manager.atom_base import AtomBase, rangable
from validol.model.utils.utils import to_timestamp, merge_dfs_list


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
    def __init__(self):
        AtomBase.__init__(self, "MBase", [])

    @rangable
    def evaluate(self, evaluator, params):
        df = Monetary(evaluator.model_launcher).read_dates_dt(*evaluator.range)

        return df.MBase


class FormulaAtom(Base, AtomBase):
    __tablename__ = "atoms"
    name = Column(String, primary_key=True)
    formula = Column(String)
    params = Column(JSONCodec())

    LETTER = '@letter'

    def __init__(self, name, formula, params):
        AtomBase.__init__(self, name, params)

        self.formula = formula

    @rangable
    def evaluate(self, evaluator, params):
        params_map = dict(zip(self.params, params))

        return evaluator.parser.evaluate(self.formula, params_map)


class MBDeltaAtom(AtomBase):
    def __init__(self):
        AtomBase.__init__(self, "MBDelta", [])

    @rangable
    def evaluate(self, evaluator, params):
        mbase = MonetaryAtom().evaluate(evaluator, params)

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