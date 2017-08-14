from itertools import groupby

from validol.model.resource_manager.evaluator import Evaluator, NumericStringParser
from validol.model.store.miners.monetary import Monetary
from validol.model.store.structures.structure import Base, JSONCodec
from sqlalchemy import Column, String
from validol.model.resource_manager.atom_base import AtomBase


class Atom(Base, AtomBase):
    __tablename__ = "atoms"
    name = Column(String, primary_key=True)
    formula = Column(String)
    params = Column(JSONCodec())

    LETTER = '@letter'

    def __init__(self, name, formula, params):
        AtomBase.__init__(self, name, params)

        self.formula = formula

    def evaluate(self, evaluator, params, name):
        raise NotImplementedError


class MonetaryAtom(Atom):
    def __init__(self):
        Atom.__init__(self, "MBase", None, [])

    def evaluate(self, evaluator, params, name):
        df = Monetary(evaluator.model_launcher).read_dates_ts(evaluator.df.Date.iloc[0],
                                                                evaluator.df.Date.iloc[-1])

        evaluator.df = Evaluator.merge_dfs(evaluator.df, df.rename({"MBase": name}))


class FormulaAtom(Atom):
    def evaluate(self, evaluator, params, name):
        params_map = dict(zip(self.params, params))

        evaluator.df[name] = evaluator.parser.evaluate(self.formula, params_map)


class MBDeltaAtom(Atom):
    def __init__(self):
        Atom.__init__(self, "MBDelta", None, [])

    def evaluate(self, evaluator, params, name):
        df = Monetary(evaluator.model_launcher).read_dates_ts()
        mbase = df.MBase

        grouped_mbase = [(mbase[0], 1)] + [(k, len(list(g))) for k, g in groupby(mbase)]
        deltas = []
        for i in range(1, len(grouped_mbase)):
            k, n = grouped_mbase[i]
            delta = k - grouped_mbase[i - 1][0]

            for j in range(n):
                deltas.append(delta / n)

        df.MBase = deltas

        evaluator.df = Evaluator.merge_dfs(evaluator.df, df.rename({"MBase": name}))