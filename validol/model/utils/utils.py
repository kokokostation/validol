import datetime as dt
import heapq
import itertools
from bisect import bisect_left
from functools import reduce
from time import mktime
import numpy as np
from tabula import read_pdf
import pandas as pd
import os
from PyPDF2 import PdfFileReader
from itertools import groupby
from operator import itemgetter
import re
from contextlib import contextmanager


def to_timestamp(date):
    return int(mktime(date.timetuple()))


def take_closest(l, date):
    pos = bisect_left(l, date)

    if pos == 0:
        return 0
    elif pos == len(l):
        return len(l) - 1

    before = l[pos - 1]
    after = l[pos]

    if after.toordinal() - date.toordinal() < date.toordinal() - before.toordinal():
        return pos
    else:
        return pos - 1


def flatten(l):
    while type(l[0]) == list:
        l = list(itertools.chain.from_iterable(l))

    return l


def split(l, value):
    return [list(group) for key, group in itertools.groupby(l, lambda x: x == value) if not key]


def my_division(a, b):
    if b != 0:
        return a / b
    else:
        return None


def none_filter(f):
    def func(*args):
        if None in args:
            return None
        else:
            return f(*args)

    return func


def parse_isoformat_date(date):
    return dt.datetime.strptime(date, "%Y-%m-%d").date()


def zip_map(funcList, values):
    return list(map(lambda f, x: f(x), funcList, values))


def merge_lists(lists):
    heads = [(lists[i][0], i) for i in range(len(lists))]
    indexes = [[] for _ in range(len(lists))]
    poses = [1 for _ in range(len(lists))]
    result = []
    heapq.heapify(heads)
    while len(heads):
        val, index = heapq.heappop(heads)
        pos = poses[index]
        if pos != len(lists[index]):
            heapq.heappush(heads, (lists[index][pos], index))
            poses[index] += 1

        index_pos = len(result) - 1
        if not result or val != result[-1]:
            result.append(val)
            index_pos += 1

        indexes[index].append(index_pos)

    return result, indexes


def intersect_lists(lists):
    return reduce(np.intersect1d, lists)


def group_by(df, columns):
    return df.groupby(columns, sort=False)[[col for col in df.columns if col not in columns]]


def map_attr(df, attr, func):
    result = df.copy()
    setattr(result, attr, getattr(result, attr).map(func))

    return result


def date_from_timestamp(df):
    return map_attr(df, 'index', dt.date.fromtimestamp)


def date_field_to_timestamp(df):
    return map_attr(df, 'Date', to_timestamp)


def date_to_timestamp(df):
    return map_attr(df, 'index', to_timestamp)


def remove_duplications(arr):
    s = set()
    result = []
    for item in arr:
        if item not in s:
            s.add(item)
            result.append(item)

    return result


def pdf(fname, config):
    df = pd.DataFrame()

    for page, area in config['pages']:
        if isinstance(page, int) or page == 'all':
            pgs = [page]
        else:
            begin, end = [int({'start': 1, 'end': PdfFileReader(fname).getNumPages()}.get(x, x))
                          for x in page.split('-')]
            pgs = range(begin, end + 1)

        for i in pgs:
            success = False

            for processor in config['processors']:
                try:
                    df = df.append(processor.get('postprocessor', lambda x: x)(
                        read_pdf(fname,
                                 pages=i,
                                 area=area,
                                 encoding='cp1251' if os.name == 'nt' else 'utf-8',
                                 **processor['kwargs'])))

                    success = True
                    break
                except:
                    pass

            if not success:
                raise ValueError

    return df


def date_range(first, last):
    return [first + dt.timedelta(i) for i in range(0, (last - first).days + 1)]


def merge_dfs(dfa, dfb):
    suffix = "_y"

    merged = dfa.merge(dfb, 'outer', left_index=True, right_index=True,
                       sort=True, suffixes=("", suffix))

    intersection = set(dfa.columns) & set(dfb.columns)

    for col in intersection:
        merged[col].fillna(merged[col + suffix], inplace=True)
        del merged[col + suffix]

    return merged


def merge_dfs_list(dfs):
    result = dfs[0]
    for df in dfs[1:]:
        result = merge_dfs(result, df)

    return result


def isfile(ftp, file):
    try:
        ftp.size(file)
        return True
    except:
        return False


def concat(dfs):
    if dfs:
        return pd.concat(dfs)
    else:
        return pd.DataFrame()


class TempFile:
    def __init__(self):
        self.name = 'tempfile{}'.format(np.random.randint(1e8))

    def __enter__(self):
        self.file = open(self.name, 'wb')

        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()

        os.remove(self.name)


def get_pages_run(fobj, phrase):
    result = []

    pfr = PdfFileReader(fobj)
    for page in range(pfr.getNumPages()):
        if phrase in pfr.getPage(page).extractText():
            result.append(page + 1)
        elif result:
            return result

    return result


def first_run(items):
    for k, g in groupby(enumerate(items), lambda ix: ix[0] - ix[1]):
        return map(itemgetter(1), g)


def get_filename(response):
    disposition = response.headers['Content-Disposition']
    return re.search('filename="(.+)"', disposition).group(1)


def map_version(s):
    return [int(n) for n in s.split('.')]


@contextmanager
def dummy_ctx_mgr():
    yield


class FillSeries(pd.Series):
    METHODS = {
        'linear': lambda s: s.interpolate('index'),
        'forward': lambda s: s.fillna(method='ffill'),
        'backward': lambda s: s.fillna(method='bfill')
    }

    def __init__(self, series, fill_method):
        if fill_method not in FillSeries.METHODS:
            raise Exception("There is no fill method '{}' for FillSeries".format(fill_method))

        pd.Series.__init__(self, series.copy())

        self.fill_method = FillSeries.METHODS[fill_method]

    def adjust(self, series):
        result = self.align(series)[0]
        notna = result.dropna()
        result = result.loc[notna.index[0]:notna.index[-1]]

        return self.fill_method(result)
