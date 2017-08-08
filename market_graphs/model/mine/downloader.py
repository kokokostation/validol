import html
import io
from zipfile import ZipFile

import requests
from requests_cache import enabled


def read_url_(url):
    return requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})


def read_url(url, cache_enabled=False):
    if cache_enabled:
        with enabled():
            return read_url_(url)
    else:
        return read_url_(url)


def read_url_text(url, cache_enabled=False):
    r = read_url(url, cache_enabled)
    r.encoding = 'utf-8'
    temp = r.text
    content = html.unescape(temp)
    while temp != content:
        temp = content
        content = html.unescape(content)

    return content


def read_url_one_filed_zip(url, cache_enabled=False):
    archive = read_url(url, cache_enabled).content
    file_like_archive = io.BytesIO(archive)

    with ZipFile(file_like_archive, "r") as zip_file:
        path = zip_file.namelist()[0]
        return zip_file.read(path).decode('utf-8')