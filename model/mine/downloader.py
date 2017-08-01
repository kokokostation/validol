import html
import io
from zipfile import ZipFile

import requests


def read_url(url):
    return requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})


def read_url_text(url):
    r = read_url(url)
    r.encoding = 'utf-8'
    temp = r.text
    content = html.unescape(temp)
    while temp != content:
        temp = content
        content = html.unescape(content)

    return content


def read_url_one_filed_zip(url):
    archive = read_url(url).content
    file_like_archive = io.BytesIO(archive)

    with ZipFile(file_like_archive, "r") as zip_file:
        path = zip_file.namelist()[0]
        return zip_file.read(path).decode('utf-8')