from pyparsing import alphas
import datetime as dt
import pandas as pd

from validol.model.resource_manager import evaluator
from validol.model.store.miners.prices import InvestingPrice
from validol.model.store.resource import Resource
from validol.model.resource_manager.atom_flavors import MonetaryAtom, MBDeltaAtom, \
    LazyAtom, FormulaAtom, AtomBase, Apply, Merge, Curr
from validol.model.store.miners.weekly_reports.flavors import WEEKLY_REPORT_FLAVORS
from validol.model.store.miners.daily_reports.daily import DailyResource
from validol.model.utils import merge_dfs


class ResourceManager:
    def __init__(self, model_launcher):
        self.model_launcher = model_launcher

    @staticmethod
    def add_letter(df, letter):
        return df.rename(columns={name: str(AtomBase(name, [letter])) for name in df.columns})

    def prepare_actives(self, actives_info, prices_info=None):
        df = pd.DataFrame()

        for letter, ai in zip(alphas, actives_info):
            active_df = ai.flavor.get_df(ai, self.model_launcher)

            if prices_info is not None:
                active_df = ResourceManager.add_letter(active_df, letter)

            df = merge_dfs(df, active_df)

        begin, end = [dt.date.fromtimestamp(df.index[i]) for i in (0, -1)]

        if prices_info is not None:
            for letter, prices_pair_id in zip(alphas, prices_info):
                prices = InvestingPrice(self.model_launcher, prices_pair_id)

                if prices_pair_id is None:
                    prices_df = prices.empty()
                else:
                    prices_df = prices.read_dates(begin, end)

                df = merge_dfs(df, ResourceManager.add_letter(prices_df, letter))

        return df, (begin, end)

    def prepare_tables(self, table_pattern, actives_info, prices_info):
        letter_map = dict(zip(alphas, actives_info))

        df, range = self.prepare_actives(actives_info, prices_info)

        evaluator_ = evaluator.Evaluator(self.model_launcher, df, letter_map, range)

        return evaluator_.evaluate(table_pattern.all_formulas())

    @staticmethod
    def get_primary_atoms():
        result = [MonetaryAtom(), MBDeltaAtom(), Apply(), Merge(), Curr()]

        flavor_atom_names = [name
                             for flavor in WEEKLY_REPORT_FLAVORS
                             for name in Resource.get_atoms(flavor.get("schema", []))]

        names = sorted(set(flavor_atom_names +
                           Resource.get_atoms(DailyResource.SCHEMA[1:]) +
                           Resource.get_atoms(InvestingPrice.SCHEMA)))

        result.extend([LazyAtom(name, [FormulaAtom.LETTER]) for name in names])

        return result