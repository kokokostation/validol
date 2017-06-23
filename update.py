import io
import os
import shutil
import zipfile
from distutils.dir_util import copy_tree

import requests


def update_sources():
    archive = requests.get("https://github.com/kokokostation/COTs/archive/master.zip").content
    file = io.BytesIO(archive)

    with zipfile.ZipFile(file, "r") as zip_file:
        zip_file.extractall()
        path = zip_file.namelist()[0]

    copy_tree(path, os.curdir)
    shutil.rmtree(path)

if __name__ == '__main__':
    update_sources()
