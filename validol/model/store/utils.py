import datetime as dt


def reduce_ranges(ranges):
    if not ranges:
        return [None, None]

    return [f(l) if l else None for f, l in
            zip((min, max), map(lambda x: list(filter(None.__ne__, x)), zip(*ranges)))]


def range_from_timestamp(range):
    return [None if ts is None else dt.date.fromtimestamp(ts) for ts in range]