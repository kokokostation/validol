import json


from validol.model.mine.downloader import read_url_text
from validol.model.store.resource import Updater
from validol.model.utils.utils import map_version


class PipChecker(Updater):
    def get_sources(self):
        return [{'name': 'Validol pip update checker'}]

    def update_source_impl(self, source):
        config = self.model_launcher.controller_launcher.get_package_config()

        info = json.loads(
            read_url_text('https://pypi.python.org/pypi/{}/json'.format(config['name'])))

        versions = list(sorted(map_version(s) for s in info['releases'].keys()))

        if max(versions) > map_version(config['version']):
            self.model_launcher.controller_launcher.mark_update_required()

    def config(self, source):
        return {
            'verbose': False,
            'important': False
        }

