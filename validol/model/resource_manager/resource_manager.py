from pyparsing import alphas
import datetime as dt

from validol.model.resource_manager import evaluator
from validol.model.store.miners.prices import InvestingPrice
from validol.model.store.resource import Resource
from validol.model.resource_manager.atom_flavors import MonetaryAtom, MBDeltaAtom, Atom, AtomBase
from validol.model.store.miners.weekly_reports.flavors import WEEKLY_REPORT_FLAVORS
import validol.model.store.miners.daily_reports.ice as ice


class ResourceManager:
    def __init__(self, model_launcher):
        self.model_launcher = model_launcher

    @staticmethod
    def add_letter(df, letter):
        return df.rename(str, {name: str(AtomBase(name, [letter]))
                               for name in df.columns if name != "Date"})

    @staticmethod
    def merge_dfs(dfs):
        complete_df = dfs[0]
        for df in dfs[1:]:
            complete_df = evaluator.Evaluator.merge_dfs(complete_df, df)

        return complete_df

    def prepare_actives(self, actives_info, prices_info=None):
        dfs = []

        for letter, (flavor, platform, active, active_flavor) in zip(alphas, actives_info):
            active_df = flavor.get_df(platform, active, active_flavor, self.model_launcher)

            if prices_info is not None:
                active_df = ResourceManager.add_letter(active_df, letter)

            dfs.append(active_df)

        if prices_info is not None:
            self.add_prices(prices_info, dfs)

        return dfs

    def add_prices(self, prices_info, dfs):
        for letter, df, prices_pair_id in zip(alphas, dfs, prices_info):
            prices = InvestingPrice(self.model_launcher, prices_pair_id)
            if prices_pair_id is None:
                prices_df = prices.empty()
            else:
                prices_df = prices.read_dates(
                    *[dt.date.fromtimestamp(df.Date.iloc[i]) for i in (0, -1)])
            dfs.append(ResourceManager.add_letter(prices_df, letter))

    def prepare_tables(self, table_pattern, actives_info, prices_info):
        letter_map = dict(zip(alphas, actives_info))

        dfs = self.prepare_actives(actives_info, prices_info)

        complete_df = ResourceManager.merge_dfs(dfs)

        evaluator_ = evaluator.Evaluator(self.model_launcher, complete_df, letter_map)

        evaluator_.evaluate(table_pattern.all_formulas())

        return evaluator_.get_result()

    @staticmethod
    def get_primary_atoms():
        result = [MonetaryAtom(), MBDeltaAtom()]

        flavor_atom_names = [name
                             for flavor in WEEKLY_REPORT_FLAVORS
                             for name in Resource.get_atoms(flavor.get("schema", []))]

        names = sorted(set(flavor_atom_names +
                           Resource.get_atoms(ice.Active.SCHEMA[1:]) +
                           Resource.get_atoms(InvestingPrice.SCHEMA)))

        result.extend([Atom(name, None, [Atom.LETTER]) for name in names])

        return result