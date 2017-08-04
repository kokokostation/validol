from setuptools import setup, find_packages

setup(
    name='market-graphs',
    version='0.0.7',
    license='MIT',
    packages=find_packages(),
    install_requires=['pyparsing', 'numpy', 'pandas', 'requests', 'PyQt5'],
    entry_points={
        'console_scripts': [
            'market-graphs=market_graphs.main:main',
            'market-graphs-migrate-conf=market_graphs.migration_scripts.user_structures:main'
        ],
    },
)