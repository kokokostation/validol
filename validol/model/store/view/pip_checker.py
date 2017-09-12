import json


from validol.model.mine.downloader import read_url_text
from validol.model.store.resource import Updater


class PipChecker(Updater):
    def get_sources(self):
        return [{'name': 'Validol pip update checker'}]

    @staticmethod
    def map_version(s):
        return [int(n) for n in s.split('.')]

    def update_source_impl(self, source):
        config = self.model_launcher.controller_launcher.get_package_config()

        info = json.loads(
            read_url_text('https://pypi.python.org/pypi/{}/json'.format(config['name'])))

        versions = list(sorted(PipChecker.map_version(s) for s in info['releases'].keys()))

        if versions[-1] != PipChecker.map_version(config['version']):
            self.model_launcher.controller_launcher.mark_update_required()

    def verbose(self, source):
        return False

