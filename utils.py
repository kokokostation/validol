from bisect import bisect_left
import itertools

def takeClosest(l, date):
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