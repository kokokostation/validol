from validol.migration.scripts.expirations_pdf_helper_fix import main as zzn_main
from validol.migration.scripts.db_fix import main as zzts_main
from validol.migration.scripts.platforms_fix import main as zztn_main
from validol.migration.scripts.preliminary_filter import main as zzt_main
from validol.migration.scripts.expirations_source_fix import main as zztf_main
from validol.model.utils.utils import map_version


# В базе записан последний прокинутый апдейт
# В MIGRATION_MAP первой компонентой указывается версия, после которой нужно прокидывать апдейт


MIGRATION_MAP = [
    ('0.0.9', zzn_main),
    ('0.0.27', zzts_main),
    ('0.0.29', zztn_main),
    ('0.0.30', zzt_main),
    ('0.0.34', zztf_main)
]


def init_version(model_launcher):
    current_version = model_launcher.controller_launcher.current_pip_version()
    return [version for version, _ in MIGRATION_MAP if map_version(version) < map_version(current_version)][-1]


def migrate(model_launcher):
    db_version = model_launcher.get_db_version()
    current_version = model_launcher.controller_launcher.current_pip_version()

    for version, migration_functor in MIGRATION_MAP:
        if map_version(db_version) < map_version(version) < map_version(current_version):
            migration_functor(model_launcher)
            model_launcher.write_db_version(version)
