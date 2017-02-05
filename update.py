import requests
import zipfile
import io

def update_sources():
    archive = requests.get("https://github.com/kokokostation/COTs/archive/master.zip").content
    file = io.BytesIO(archive)

    zipFile = zipfile.ZipFile(file,"r")
    for name in zipFile.namelist()[1:]:
        open(name.split("/")[1], "wb").write(zipFile.read(name))