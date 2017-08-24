from setuptools import setup, find_packages

setup(
    name='validol',
    version='0.0.9',
    license='MIT',
    packages=find_packages(),
    install_requires=[
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
        'python-dateutil'
    ],
    entry_points={
        'console_scripts': [
            'validol=validol.main:main',
            'validol-conf=validol.migration_scripts.atoms_migration:main'
        ],
    },
)