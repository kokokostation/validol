from datetime import timedelta

from model.store.collectors.monetary_delta import MonetaryDelta
from model.store.miners.cots import Active
from model.store.miners.monetary import Monetary
from model.store.miners.prices import InvestingPrice
from model.store.resource import Resource
from model.store.structures.evaluator import NumericStringParser
from model.utils import intersect_lists, merge_lists
from model.utils import take_closest


class ResourceManager:
    RESOURCES = (Monetary, MonetaryDelta, InvestingPrice)

    def __init__(self, model_launcher):
        self.model_launcher = model_launcher
        self.dbh = self.model_launcher.dbh

    @staticmethod
    def get_nearest_dates(resource, requested_dates, precision=7):
        df = resource.read_dates(
            requested_dates[0] - timedelta(days=precision),
            requested_dates[-1] + timedelta(days=precision))

        dates, values = ResourceManager.get_dates_values(df)

        result = []
        for date in requested_dates:
            closest = take_closest(dates, date)
            if abs(df.Date[closest].toordinal() - date.toordinal()) <= precision:
                result.append(values[closest])
            else:
                result.append([None] * len(resource.schema))

        return result

    @staticmethod
    def get_dates_values(df):
        return df.Date.tolist(), df.drop('Date', 1).values.tolist()

    def obtain_values(self, requested_dates, cls, *args):
        if cls == Monetary:
            return ResourceManager.get_nearest_dates(Monetary(self.dbh), requested_dates)
        elif cls == MonetaryDelta:
            return ResourceManager.get_nearest_dates(MonetaryDelta(self.dbh), requested_dates)
        elif cls == InvestingPrice:
            pair_id = args[0]
            if not pair_id:
                return [[None]] * len(requested_dates)
            else:
                dates = InvestingPrice(self.dbh, pair_id) \
                    .read_dates(requested_dates[0], requested_dates[-1]) \
                    .set_index("Date").to_dict()['Quot']

                return [[dates.get(date, None)] for date in requested_dates]

    def get_active(self, platform, active):
        df = Active(self.dbh, platform, active).read_dates()

        return ResourceManager.get_dates_values(df)

    def prepare_active(self, platform, active, args):
        dates, values = self.get_active(platform, active)

        cls_values = [self.obtain_values(dates, cls, *args) for cls, args in zip(ResourceManager.RESOURCES, args)]

        for i, value in enumerate(values):
            value.extend(sum([values[i] for values in cls_values], []))

        return dates, values

    def prepare_tables(self, table_pattern, info):
        data = [self.prepare_active(platform, active, ([], [], [prices_pair_id]))
                for platform, active, prices_pair_id in info]

        compiler = NumericStringParser()

        all_atoms = dict((atom.name, compiler.compile(atom.formula_to_compile)) for atom in self.model_launcher.get_atoms())

        all_dates, indexes = merge_lists([dates for dates, _ in data])
        new_values = []
        for table in table_pattern.formulae:
            values = [[None] * len(table) for _ in range(len(all_dates))]

            for i, (atoms, formula) in enumerate(table):
                atoms = [(all_atoms[atom], active) for atom, active in atoms]
                func = compiler.compile(formula)

                if False not in [index < len(data) for _, index in atoms]:
                    intersection = intersect_lists([indexes[index] for _, index in atoms])
                    for j, index in enumerate(intersection):
                        args = [atom(data[active][1][j]) for atom, active in atoms]
                        values[index][i] = func(args)

            new_values.append(values)

        return all_dates, new_values

    def get_primary_atoms(self):
        return sum([Resource.get_atoms(cls) for cls in (Active,) + ResourceManager.RESOURCES], [])