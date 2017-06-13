import datetime as dt
import html
import os
import re

import requests

from model import utils
from model.store import filenames


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

def unique(list_):
    return [list_[2 * i] for i in range(0, len(list_) // 2)]

first_date = dt.date(2005, 1, 4)


def get_dates(last_net_date):
    return [dt.date.fromordinal(d) for d in range(first_date.toordinal(), last_net_date.toordinal(), 7)]


def get_net_dates():
    return sorted([dt.datetime.strptime(d, "%m%d%y").date() for d in unique(re.findall(r'cot(\d{6})', read_url_text("http://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalViewable/index.htm")))])


def get_platforms():
    current_info = read_url_text(
        "http://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm")
    current_info = current_info[re.search(r'<p><b>Futures-and-Options-Combined</b></p>', current_info).end():
                                re.search(r'<p><b>Supplemental Commodity Index</b></p>', current_info).start()]

    return list(zip(unique(re.findall(r'dea([a-z]*)lf', current_info)), re.findall(r'<p><b>([^<>]*)</b></p>', current_info)))


def get_actives(date, platform_code):
    content = read_url_text("http://www.cftc.gov/files/dea/cotarchives/" + str(date.year) +
                       "/futures/dea" + platform_code + "lf" + date.strftime("%m%d%y") + ".htm")

    return content


def get_current_actives(platform_code):
    content = read_url_text(
        "http://www.cftc.gov/dea/futures/dea" + platform_code + "lf.htm")

    return content


def get_last_date():
    content = read_url_text(
        "http://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm")

    date_match = re.search(
        r'Reports Dated (.*) - Current Disaggregated Reports:', content)

    return dt.datetime.strptime(date_match.group(1), "%B %d, %Y").date()
