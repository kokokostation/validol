SETUP_CONFIG = {
    'name': 'validol',
    'version': '0.0.18',
    'license': 'MIT',
    'install_requires': [
        'pyparsing',
        'numpy',
        'pandas',
        'requests',
        'PyQt5',
        'sqlalchemy',
        'requests-cache',
        'lxml',
        'beautifulsoup4',
        'marshmallow',
        'tabula-py',
        'python-dateutil',
        'PyPDF2',
        'croniter',
        'tendo'
    ],
    'entry_points': {
        'console_scripts': [
            'validol=validol.main:main'
        ],
    },
    'include_package_data': True
}