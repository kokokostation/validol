from itertools import groupby
from sqlalchemy import Column, String
import pandas as pd
from copy import deepcopy
from dateutil.relativedelta import relativedelta

from validol.model.store.miners.monetary import Monetary
from validol.model.store.structures.structure import Base, JSONCodec
from validol.model.resource_manager.atom_base import AtomBase, rangable
from validol.model.utils import to_timestamp, merge_dfs_list
from validol.model.store.miners.daily_reports.expirations import Expirations
from validol.model.store.structures.pdf_helper import PdfHelpers


class LazyAtom(AtomBase):
    @rangable
    def evaluate(self, evaluator, params):
        name = str(AtomBase(self.name, params))
        df = evaluator.df

        if name in df:
            begin, end = [to_timestamp(a) for a in evaluator.range]

            return df[name][(begin <= df.index) & (df.index <= end)]
        else:
            return pd.Series()


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
        df = MonetaryAtom().evaluate(evaluator, params)
        mbase = df.MBase

        grouped_mbase = [(mbase[0], 1)] + [(k, len(list(g))) for k, g in groupby(mbase)]
        deltas = []
        for i in range(1, len(grouped_mbase)):
            k, n = grouped_mbase[i]
            delta = k - grouped_mbase[i - 1][0]

            for j in range(n):
                deltas.append(delta / n)

        df.MBase = deltas

        return df.MBase


class Apply(AtomBase):
    def __init__(self):
        AtomBase.__init__(self, 'APPLY', ['...'])

    def evaluate(self, evaluator, params):
        return evaluator.atoms_map[params[0]].evaluate(evaluator, params[1:])


class Merge(AtomBase):
    def __init__(self):
        AtomBase.__init__(self, 'MERGE', ['df'])

    def evaluate(self, evaluator, params):
        return merge_dfs_list([param.to_frame('i') for param in params])['i']


class Curr(AtomBase):
    def __init__(self):
        AtomBase.__init__(self, 'CURR', ['@atom', FormulaAtom.LETTER, '@delta'])

    def evaluate(self, evaluator, params):
        ai = evaluator.letter_map[params[1]]

        atom_info = ai.flavor.get_full_df(ai, evaluator.model_launcher)
        atom_info['CONTRACT'] = atom_info['CONTRACT'].apply(Expirations.from_contract)

        exp = evaluator.model_launcher.get_exp_info(ai)
        exp_info = Expirations(evaluator.model_launcher).read_df('''
            SELECT
                Date, Contract
            FROM
                {table}
            WHERE
                PlatformCode = ? AND ActiveName = ? AND ActiveCode = ? AND Event = 'LTD'
        ''', params=(exp['PlatformCode'], exp['ActiveName'], exp['ActiveCode']))
        exp_info['Contract'] = exp_info['Contract'].apply(Expirations.from_contract)

        result = pd.DataFrame()

        for i in range(1, len(exp_info)):
            begin, end = exp_info.index[i - 1], exp_info.index[i]

            curr_contract = exp_info['Contract'].iloc[i] + relativedelta(months=int(params[2]))

            df = atom_info[
                (begin <= atom_info.index) &
                (atom_info.index < end) &
                (atom_info.CONTRACT == curr_contract)
            ]

            result = result.append(df)

        if not result.empty:
            return result[params[0]]
        else:
            return pd.Series()
