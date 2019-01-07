SETUP_CONFIG = {
    'name': 'validol',
    'version': '0.0.52',
    'license': 'MIT',
    'install_requires': [
        'pyparsing==2.2.0',
        'numpy==1.14.2',
        'pandas==0.20.3',
        'requests==2.18.4',
        'PyQt5==5.9.2',
        'sqlalchemy==1.2.6',
        'requests-cache==0.4.13',
        'lxml==4.2.1',
        'beautifulsoup4==4.6.0',
        'marshmallow==2.15.0',
        'tabula-py==1.0.0',
        'python-dateutil==2.7.2',
        'PyPDF2==1.26.0',
        'croniter==0.3.20',
        'PySocks==1.6.7'
    ],
    'entry_points': {
        'console_scripts': [
            'validol=validol.main:main'
        ],
    },
    'include_package_data': True
}