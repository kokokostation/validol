from datetime import date

import numpy as np
import pandas as pd
from pyparsing import alphas

from validol.model.resource_manager import evaluator
from validol.model.store.collectors.monetary_delta import MonetaryDelta
from validol.model.store.miners.monetary import Monetary
from validol.model.store.miners.prices import InvestingPrice
from validol.model.store.resource import Resource
from validol.model.store.structures import atom
from validol.model.store.miners.weekly_reports.flavors import WEEKLY_REPORT_FLAVORS


class ResourceManager:
    def __init__(self, model_launcher):
        self.model_launcher = model_launcher

    @staticmethod
    def add_letter(df, letter):
        return df.rename(str, {name: evaluator.Atom(name, letter).full_name
                               for name in df.columns if name != "Date"})

    @staticmethod
    def merge_dfs(dfs):
        complete_df = dfs[0]
        for df in dfs[1:]:
            complete_df = complete_df.merge(df, 'outer', 'Date', sort=True)

        return complete_df

    def prepare_actives(self, actives_info, prices_info=None):
        dfs = []

        for letter, (flavor, platform, active) in zip(alphas, actives_info):
            active_df = flavor.get_df(platform, active)

            if prices_info is not None:
                active_df = ResourceManager.add_letter(active_df, letter)

            dfs.append(active_df)

        if prices_info is not None:
            self.add_prices(prices_info, dfs)

        return dfs

    def add_prices(self, prices_info, dfs):
        for letter, df, prices_pair_id in zip(alphas, dfs, prices_info):
            begin, end = map(lambda row: date.fromtimestamp(df.Date.iloc[row]), (0, -1))

            prices = InvestingPrice(self.model_launcher, prices_pair_id)
            if prices_pair_id is None:
                prices_df = pd.DataFrame(columns=[name for name, _ in prices.schema],
                                         dtype=np.float64)
            else:
                prices_df = prices.read_dates(begin, end)
            dfs.append(ResourceManager.add_letter(prices_df, letter))

    def prepare_tables(self, table_pattern, actives_info, prices_info):
        dfs = self.prepare_actives(actives_info, prices_info)

        global_begin = date.fromtimestamp(min([df.Date[0] for df in dfs if not df.empty]))
        global_end = date.fromtimestamp(max([df.Date.iloc[-1] for df in dfs if not df.empty]))

        for resource in (Monetary(self.model_launcher),
                         MonetaryDelta(self.model_launcher)):
            dfs.append(resource.read_dates(global_begin, global_end))

        complete_df = ResourceManager.merge_dfs(dfs)

        evaluator_ = evaluator.Evaluator(complete_df, self.model_launcher.get_atoms())

        evaluator_.evaluate(table_pattern.all_formulas())

        return evaluator_.get_result()

    def get_primary_atoms(self):
        result = []

        for cls in (Monetary, MonetaryDelta, InvestingPrice):
            result.extend([atom.Atom(name, name, cls.INDEPENDENT)
                           for name in Resource.get_atoms(cls.SCHEMA)])

        flavor_atom_names = [name
                             for flavor in WEEKLY_REPORT_FLAVORS
                             for name in Resource.get_atoms(flavor.get("schema", []))]

        result.extend([atom.Atom(name, name, False) for name in sorted(set(flavor_atom_names))])

        return result