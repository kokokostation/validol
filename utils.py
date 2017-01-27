from bisect import bisect_left

def takeClosest(list, date):
    pos = bisect_left(list, date)

    if pos == 0:
        return 0
    elif pos == len(list):
        return -1

    before = list[pos - 1]
    after = list[pos]

    if after.toordinal() - date.toordinal() < date.toordinal() - before.toordinal():
        return pos
    else:
        return pos - 1