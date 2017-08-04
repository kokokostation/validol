import datetime as dt
import heapq
import itertools
from bisect import bisect_left
from functools import reduce
from time import mktime

import numpy as np


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

def date_to_timestamp(df):
    df.Date = df.apply(lambda row: to_timestamp(row['Date']), axis=1)
    return df

def date_from_timestamp(df):
    df.Date = df.apply(lambda row: dt.date.fromtimestamp(row['Date']), axis=1)
    return df

def remove_duplications(arr):
    s = set()
    result = []
    for item in arr:
        if item not in s:
            s.add(item)
            result.append(item)

    return result