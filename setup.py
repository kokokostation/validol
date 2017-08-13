from setuptools import setup, find_packages

setup(
    name='validol',
    version='0.0.6',
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
        'tabula-py'
    ],
    entry_points={
        'console_scripts': [
            'validol=validol.main:main'
        ],
    },
)