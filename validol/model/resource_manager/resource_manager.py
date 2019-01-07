from pyparsing import alphas
import datetime as dt
import pandas as pd

from validol.model.resource_manager import evaluator
from validol.model.store.miners.monetary import Monetary
from validol.model.store.miners.prices import InvestingPrice
from validol.model.store.resource import Resource
from validol.model.resource_manager.atom_flavors import MonetaryAtom, MBDeltaAtom, \
    LazyAtom, FormulaAtom, AtomBase, Apply, Merge, Curr, \
    MlCurve, ArgMin, Quantile, Min, Expirations, FillAtom, CFYAAtom, QuarterMeanAtom
from validol.model.store.miners.report_flavors import REPORT_FLAVORS
from validol.model.utils.utils import merge_dfs


class ResourceManager:
    def __init__(self, model_launcher):
        self.model_launcher = model_launcher

    @staticmethod
    def add_letter(df, letter):
        return df.rename(columns={name: str(AtomBase(name, [letter])) for name in df.columns})

    def prepare_actives(self, actives_info, pure_actives=False):
        df = pd.DataFrame()

        for letter, ai in zip(alphas, actives_info):
            active_df = ai.flavor.get_df(ai, self.model_launcher)

            if not pure_actives:
                active_df = ResourceManager.add_letter(active_df, letter)

            df = merge_dfs(df, active_df)

        begin, end = dt.date(2000, 1, 1), dt.date.today()

        if not df.empty:
            l, r = [dt.date.fromtimestamp(df.index[i]) for i in (0, -1)]
            begin, end = min(begin, l), max(end, r)

        if not pure_actives:
            for letter, ai in zip(alphas, actives_info):
                pair_id = self.model_launcher.get_prices_info(ai.price_url).get('pair_id', None)

                if pair_id is not None:
                    prices = InvestingPrice(self.model_launcher, pair_id)

                    prices_df = prices.read_dates(begin, end)

                    df = merge_dfs(df, ResourceManager.add_letter(prices_df, letter))

        return df, (begin, end)

    def prepare_tables(self, table_pattern, actives_info):
        letter_map = dict(zip(alphas, actives_info))

        df, range = self.prepare_actives(actives_info)

        evaluator_ = evaluator.Evaluator(self.model_launcher, df, letter_map, range)

        return evaluator_.evaluate(table_pattern.all_formulas())

    @staticmethod
    def get_primary_atoms():
        monetary_atoms = [MonetaryAtom(key) for key in Monetary.CONFIG]

        unique_atoms = [MBDeltaAtom(), Apply(), Merge(), Curr(), MlCurve(), ArgMin(), Quantile(),
                        Min(), Expirations(), FillAtom(), QuarterMeanAtom(), CFYAAtom()]

        flavor_atom_names = [name
                             for flavor in REPORT_FLAVORS
                             for name in Resource.get_flavor_atoms(flavor)]

        names = sorted(set(flavor_atom_names +
                           Resource.get_atoms(InvestingPrice.SCHEMA)))

        lazy_atoms = [LazyAtom(name, [FormulaAtom.LETTER]) for name in names]

        return monetary_atoms + unique_atoms + lazy_atoms
