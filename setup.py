from setuptools import setup, find_packages

setup(
    name='validol',
    version='0.0.0',
    license='MIT',
    packages=find_packages(),
    install_requires=['pyparsing', 'numpy', 'pandas', 'requests', 'PyQt5', 'sqlalchemy'],
    entry_points={
        'console_scripts': [
            'validol=market_graphs.main:main',
            'validol-conf=market_graphs.migration_scripts.user_structures:main'
        ],
    },
)