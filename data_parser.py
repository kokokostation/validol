import re
import datetime as dt
import os
import downloader
import utils
import filenames
import formulae
from itertools import groupby

__all__ = ["table1_labels", "table2_labels", "table1_key_types", "table2_key_types", "places_num", "get_platforms", "get_cached_prices", "Grabber"]

main_primary_labels = 11
primary_labels = ["OI", "NCL", "NCS", "CL", "CS", "NRL", "NRS", "4L%", "4S%", "8L%", "8S%", "Quot", "MBase", "MBDelta"]
primary_types = [float] * len(primary_labels)

def parse_active(entry):
    name = entry.split("\n", 1)[0].rsplit(" - ", 1)[0]
    entry = entry.replace(",", "")
    lines = [list(map(float, re.findall(r'\d+\.\d+|\d+', s))) for s in re.findall(r'\nAll ([^\n]*)\n', entry)]
    fields = [lines[0][0],
              lines[0][1],
              lines[0][2],
              lines[0][4],
              lines[0][5],
              lines[0][8],
              lines[0][9],
              lines[-1][4],
              lines[-1][5],
              lines[-1][6],
              lines[-1][7]]
    return name, fields

def get_actives_from_page(content):
    start, end = re.search(r'<!--ih:includeHTML file=\".*\"-->\b', content), re.search(r'<!--/ih:includeHTML-->', content)
    if start and end:
        activesList = list(filter(lambda s: '-' in s, re.compile(r'(?:[ \r]*\n){2,3}').split(content[start.end():end.start()])))
    else:
        return []

    return list(map(parse_active, activesList))

def places_num(bars, mbars):
    places = [b for _, b in bars] + [b for _, b in mbars]
    if places:
        return max(places) + 1
    else:
        return None

def parse_axis(axis):
    return [list(map(parse_item, part.split("&"))) if part else [] for part in axis.split("#")]

def parse_item(item):
    if '^' in item:
        name, place = item.split("^")
        return int(name), int(place)
    else:
        return int(item)

def parse_pattern(line):
    items = line.split("\t")

    table, title = items[0], items[1]
    pattern = []
    for i in range(2, len(items), 2):
        pattern.append([parse_axis(items[i]), parse_axis(items[i + 1])])

    return table, title, pattern

def pack_bar(bar):
    name, place = bar
    return str(name) + "^" + str(place)

def pack_axis(lines, bars, mbars):
    return "&".join(map(str, lines)) + "#" + "&".join(map(pack_bar, bars)) + "#" + "&".join(map(pack_bar, mbars))

def pack_pattern(table, title, pattern):
    result = table + "\t" + title

    for g in pattern:
        for lines, bars, mbars in g:
            result += "\t" + pack_axis(lines, bars, mbars)

    return result

def get_cached_prices():
    result = []

    if not os.path.isfile(filenames.pricesFile):
        return result

    file = open(filenames.pricesFile, "r")

    for line in file.read().splitlines():
        url, pair_id, name = line.split(" ", 2)
        result.append((url, name))

    file.close()

    return result

def get_patterns():
    result = {}

    if not os.path.isfile(filenames.patternsFile):
        return result

    file = open(filenames.patternsFile, "r")
    for table, title, pattern in map(parse_pattern, file.read().splitlines()):
        utils.add_to_dict(result, table, title, pattern)

    file.close()

    return result

def add_pattern(table, title, pattern):
    file = open(filenames.patternsFile, "a+")
    file.write(pack_pattern(table, title, pattern) + "\n")
    file.close()

def get_platforms():
    if not os.path.isfile(filenames.platformsFile):
        return []

    platforms = open(filenames.platformsFile, "r")

    result = [str.split(" ", 1) for str in platforms.read().splitlines()]

    platforms.close()

    return result

def title(platformName, activeName, priceName):
    result = platformName + "/" + activeName
    if priceName:
        result += "; Quot from: " + priceName

    return result

def parse_date(platform, date, content, index):
    data = get_actives_from_page(content)

    if not data:
        return False

    for key, value in data:
        if key not in index:
            index.append(key)
            activeIndex = open("/".join([platform, filenames.parsed, filenames.activeIndex]), "a+")
            activeIndex.write(key + "\n")
            activeIndex.close()

        file = open("/".join([platform, filenames.parsed, str(index.index(key))]), "a+")
        file.write(date.isoformat())
        for i in range(len(primary_labels[:main_primary_labels])):
            file.write("\t" + str(value[i]))
        file.write("\n")
        file.close()

    return True

def get_active(platform, active, index):
    file = open("/".join([platform, filenames.parsed, str(index.index(active))]), "r")

    lines = list(map(lambda s: s.split("\t"), file.read().splitlines()))
    dates = [utils.parse_isoformat_date(line[0]) for line in lines]
    fields = [list(map(lambda f, x: f(x), primary_types, line[1:])) for line in lines]

    file.close()

    return dates, fields

def get_actives(platform):
    index = []
    fileName = "/".join([platform, filenames.parsed, filenames.activeIndex])

    if not os.path.isfile(fileName):
        return index

    file = open(fileName, "r")
    index = file.read().splitlines()
    file.close()

    return index

def prepare_active(platform, active, prices_pair_id):
    dates, values = get_active(platform, active, get_actives(platform))
    mbase = downloader.get_mbase(dates)

    if not prices_pair_id:
        prices = [None] * len(dates)
    else:
        prices = downloader.get_prices(dates, prices_pair_id)

    groupedMbase = [(mbase[0], 1)] + [(k, len(list(g))) for k, g in groupby(mbase)]
    deltas = []
    for i in range(1, len(groupedMbase)):
        k, n = groupedMbase[i]
        delta = k - groupedMbase[i - 1][0]

        for j in range(n):
            deltas.append(delta / n)

    for i in range(len(dates)):
        values[i].extend([prices[i], mbase[i], deltas[i]])

    return dates, values

def prepare_tables(tablePattern, info):
    data = [prepare_active(platform, active, prices_pair_id) for platform, active, prices_pair_id in info]

    allAtoms = dict([(name, formulae.compile_formula(formula)) for name, formula, _ in formulae.get_atoms()])

    allDates, indexes = utils.merge_lists([dates for dates, _ in data])
    newValues = []
    for table in tablePattern:
        values = [[None for _ in range(len(table))] for _ in range(len(allDates))]
        for i in range(len(table)):
            atoms, formula = table[i]
            atoms = [(allAtoms[atom], active) for atom, active in atoms]
            func = formulae.compile_formula(formula)
            if False not in [index < len(data) for _, index in atoms]:
                intersection = utils.intersect_lists([indexes[index] for _, index in atoms])
                for j in range(len(intersection)):
                    args = [atom(data[active][1][j]) for atom, active in atoms]
                    values[intersection[j]][i] = func(args)
        newValues.append(values)

    return allDates, newValues