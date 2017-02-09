import requests
import zipfile
import io
from distutils.dir_util import copy_tree
import os
import shutil

def update_sources():
    archive = requests.get("https://github.com/kokokostation/COTs/archive/master.zip").content
    file = io.BytesIO(archive)

    zipFile = zipfile.ZipFile(file,"r")
    zipFile.extractall()
    path = zipFile.namelist()[0]
    zipFile.close()

    copy_tree(path, os.curdir)
    shutil.rmtree(path)

if __name__ == '__main__':
    update_sources()