import requests
import zipfile
import io
import os
import shutil

def update_sources():
    archive = requests.get("https://github.com/kokokostation/COTs/archive/master.zip").content
    file = io.BytesIO(archive)

    zipFile = zipfile.ZipFile(file,"r")
    zipFile.extractall()
    path = zipFile.namelist()[0]
    zipFile.close()

    for target in os.listdir(path):
        try:
            shutil.rmtree(target)
        except NotADirectoryError:
            try:
                os.unlink(target)
            except FileNotFoundError:
                pass
        shutil.move(os.path.join(path, target), target)

    shutil.rmtree(path)

if __name__ == '__main__':
    update_sources()