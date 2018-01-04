import html
import io
from zipfile import ZipFile, BadZipFile
import requests
from requests_cache import enabled
from functools import wraps


def read_url_(url):
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})

    return response if response.ok else None


def read_url(url, cache_enabled=False):
    if cache_enabled:
        with enabled():
            return read_url_(url)
    else:
        return read_url_(url)


def url_reader(f):
    @wraps(f)
    def wrapped(url, cache_enabled=False):
        response = read_url(url, cache_enabled)

        if response is None:
            return None

        return f(response)

    return wrapped


@url_reader
def read_url_text(response):
    response.encoding = 'utf-8'
    temp = response.text
    content = html.unescape(temp)
    while temp != content:
        temp = content
        content = html.unescape(content)

    return content


@url_reader
def read_url_one_filed_zip(response):
    archive = response.content
    file_like_archive = io.BytesIO(archive)

    try:
        with ZipFile(file_like_archive, "r") as zip_file:
            path = zip_file.namelist()[0]
            return zip_file.read(path).decode('utf-8')
    except BadZipFile:
        return None