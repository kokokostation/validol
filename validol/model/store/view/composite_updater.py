from validol.model.store.resource import Updater
from validol.model.store.miners.daily_reports.updater import DailyReports
from validol.model.store.miners.daily_reports.expirations import Expirations
from validol.model.store.miners.weekly_reports.flavors import Cftc, Ice
from validol.model.store.miners.monetary import Monetary
from validol.model.store.view.pip_checker import PipChecker


class CompositeUpdater(Updater):
    def __init__(self, model_launcher, name, clss):
        Updater.__init__(self, model_launcher)

        self.name = name
        self.clss = clss

    def get_sources(self):
        return [{'name': self.name}]

    def update_source(self, source):
        return sum([cls(self.model_launcher).update_entire() for cls in self.clss], [])


class DailyUpdater(CompositeUpdater):
    CLSS = [Expirations, DailyReports]

    def __init__(self, model_launcher):
        CompositeUpdater.__init__(self, model_launcher, 'Update daily', DailyUpdater.CLSS)


class EntireUpdater(CompositeUpdater):
    CLSS = [Monetary, Cftc, Ice] + DailyUpdater.CLSS

    def __init__(self, model_launcher):
        CompositeUpdater.__init__(self, model_launcher, 'Update all', EntireUpdater.CLSS)


ALL_UPDATERS = EntireUpdater.CLSS + [DailyUpdater, EntireUpdater, PipChecker]


class UpdateManager(Updater):
    def __init__(self, model_launcher, clss=ALL_UPDATERS):
        Updater.__init__(self, model_launcher)

        self.updaters = [cls(model_launcher) for cls in clss]
        self.source_map = {}
        for d in [{source['name']: updater for source in updater.get_sources()}
                  for updater in self.updaters]:
            self.source_map.update(d)

    def update_source(self, source):
        return self.source_map[source].update_source(source)

    def get_sources(self):
        return sum([updater.get_sources() for updater in self.updaters], [])

    def config(self, source):
        return self.source_map[source].config(source)
