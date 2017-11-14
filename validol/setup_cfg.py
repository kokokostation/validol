SETUP_CONFIG = {
    'name': 'validol',
    'version': '0.0.39',
    'license': 'MIT',
    'install_requires': [
        'pyparsing',
        'numpy',
        'pandas==0.20.3',
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
        'croniter'
    ],
    'entry_points': {
        'console_scripts': [
            'validol=validol.main:main'
        ],
    },
    'include_package_data': True
}