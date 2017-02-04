from bisect import bisect_left
import datetime as dt
import itertools
import heapq
import numpy as np
from functools import reduce
import pickle

__all__ = ["take_closest", "add_to_dict", "flatten", "split", "my_division", "parse_isoformat_date"]

def take_closest(l, date):
    pos = bisect_left(l, date)

    if pos == 0:
        return 0
    elif pos == len(l):
        return -1

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

        indexPos = len(result) - 1
        if not result or val != result[-1]:
            result.append(val)
            indexPos += 1

        indexes[index].append(indexPos)

    return result, indexes

def intersect_lists(lists):
    return reduce(np.intersect1d, lists)

def pickleLoader(pklFile):
    result = []
    try:
        while True:
            result.append(pickle.load(pklFile))
    except EOFError:
        return result

def pickleExtend(l, pklFile):
    for item in l:
        pickle.dump(item, pklFile)