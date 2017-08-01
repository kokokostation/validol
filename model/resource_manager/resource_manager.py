from datetime import date

import pandas as pd
from pyparsing import alphas

from model.store.collectors.monetary_delta import MonetaryDelta
from model.store.miners.flavor import Active
from model.store.miners.monetary import Monetary
from model.store.miners.prices import InvestingPrice
from model.store.resource import Resource
from model.utils import flatten
from model.store.miners.flavors import FLAVORS_MAP
from model.store.structures import atom
from model.resource_manager import evaluator

class ResourceManager:
    def __init__(self, model_launcher):
        self.model_launcher = model_launcher
        self.dbh = self.model_launcher.dbh

    @staticmethod
    def add_letter(df, letter):
        return df.rename(str, {name: evaluator.Atom(name, letter).full_name
                               for name in df.columns if name != "Date"})

    def prepare_tables(self, table_pattern, info):
        dfs = []
        global_begin, global_end = (date.today(),) * 2

        for i, (flavor, platform, active, prices_pair_id) in enumerate(info):
            letter = alphas[i]

            dfs.append(ResourceManager.add_letter(
                Active(self.dbh, FLAVORS_MAP[flavor], platform, active).read_dates(), letter))

            begin, end = map(lambda row: date.fromtimestamp(dfs[-1].Date.iloc[row]), (0, -1))
            global_begin = min(global_begin, begin)
            global_end = max(global_end, end)

            prices = InvestingPrice(self.dbh, prices_pair_id)
            if prices_pair_id is None:
                prices_df = pd.DataFrame(columns=[name for name, _ in prices.schema])
            else:
                prices_df = prices.read_dates(begin, end)
            dfs.append(ResourceManager.add_letter(prices_df, letter))

        for resource in (Monetary(self.dbh), MonetaryDelta(self.dbh)):
            dfs.append(resource.read_dates(global_begin, global_end))

        complete_df = dfs[0]
        for df in dfs[1:]:
            complete_df = complete_df.merge(df, 'outer', 'Date', sort=True)

        evaluator_ = evaluator.Evaluator(complete_df, self.model_launcher.get_atoms())

        evaluator_.evaluate(table_pattern.all_formulas())

        return evaluator_.get_result()

    def get_primary_atoms(self):
        result = []

        for cls in (Monetary, MonetaryDelta, InvestingPrice):
            result.extend([atom.Atom(name, name, cls.INDEPENDENT)
                           for name in Resource.get_atoms(cls.SCHEMA)])

        flavor_atom_names = [name
                             for flavor in self.model_launcher.get_flavors()
                             for name in Resource.get_atoms(flavor["schema"])]

        result.extend([atom.Atom(name, name, False) for name in sorted(set(flavor_atom_names))])

        return result