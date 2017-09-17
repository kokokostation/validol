from validol.migration.scripts.expirations_pdf_helper_fix import main as zzn_main
from validol.model.utils.utils import map_version


# В базе записан последний прокинутый апдейт
# В MIGRATION_MAP первой компонентой указывается версия, после которой нужно прокидывать апдейт


MIGRATION_MAP = [
    ('0.0.9', zzn_main)
]


def init_version(model_launcher):
    current_version = model_launcher.controller_launcher.current_pip_version()
    return [version for version, _ in MIGRATION_MAP if map_version(version) < map_version(current_version)][-1]


def migrate(model_launcher):
    db_version = model_launcher.get_db_version()
    current_version = model_launcher.controller_launcher.current_pip_version()

    for version, migration_functor in MIGRATION_MAP:
        if map_version(db_version) < map_version(version) < map_version(current_version):
            migration_functor()
            model_launcher.write_db_version(version)
