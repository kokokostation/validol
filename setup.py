from setuptools import setup, find_packages

from validol.setup_cfg import SETUP_CONFIG


if __name__ == '__main__':
    setup(packages=find_packages(), **SETUP_CONFIG)