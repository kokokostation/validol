from itertools import groupby

from validol.model.store.miners.monetary import Monetary
from validol.model.store.resource import Resource
from validol.model.utils import date_from_timestamp


class MonetaryDelta(Resource):
    SCHEMA = [("MBDelta", "REAL")]
    INDEPENDENT = True

    def __init__(self, model_launcher):
        Resource.__init__(self, model_launcher.main_dbh, "MonetaryDelta", MonetaryDelta.SCHEMA)

        self.source = Monetary(model_launcher)

    def deltas(self, mbase):
        grouped_mbase = [(mbase[0], 1)] + [(k, len(list(g))) for k, g in groupby(mbase)]
        deltas = []
        for i in range(1, len(grouped_mbase)):
            k, n = grouped_mbase[i]
            delta = k - grouped_mbase[i - 1][0]

            for j in range(n):
                deltas.append(delta / n)

        return deltas

    def fill(self, first, last):
        return self.initial_fill()

    def initial_fill(self):
        df = date_from_timestamp(self.source.read_dates().rename(str, {"MBase": "MBDelta"}))
        df.MBDelta = self.deltas(df.MBDelta)
        return df

    # not optimal, but who cares, todo: remove this atom and come up with common scheme to add runtime atom