from bisect import bisect_left
import datetime as dt
import itertools

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

def add_to_dict(dict, key1, key2, value):
    if key1 not in dict:
        dict[key1] = {}
    dict[key1][key2] = value

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