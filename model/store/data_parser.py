import os
import re
import shutil
from itertools import groupby


from model import utils
from model.mine import downloader
import model.store.filenames as filenames

main_primary_labels = 11
primary_labels = ["OI", "NCL", "NCS", "CL", "CS", "NRL",
                  "NRS", "4L%", "4S%", "8L%", "8S%", "Quot", "MBase", "MBDelta"]
primary_types = [float] * len(primary_labels)


def reparse():
    for code, _ in get_platforms():
        parsed = os.path.join(code, filenames.parsed)
        if os.path.isdir(parsed):
            shutil.rmtree(parsed)
        index = []
        dates = list(sorted(map(utils.parse_isoformat_date, os.listdir(code))))
        os.mkdir(parsed)

        for date in dates:
            with open(os.path.join(code, date.isoformat()), "r") as file:
                parse_date(code, date, file.read(), index)


def parse_active(entry):
    name = entry.split("\n", 1)[0].rsplit(" - ", 1)[0].strip()
    entry = entry.replace(",", "")
    lines = [list(map(float, re.findall(r'\d+\.\d+|\d+', s)))
             for s in re.findall(r'\nAll ([^\n]*)\n', entry)]
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
    start, end = re.search(
        r'<!--ih:includeHTML file=\".*\"-->[ \r\n]*', content), re.search(r'<!--/ih:includeHTML-->', content)
    if start and end:
        activesList = list(filter(
            lambda s: '-' in s, re.compile(r'(?:[ \r]*\n){2,3}').split(content[start.end():end.start()])))
    else:
        return []

    return list(map(parse_active, activesList))


def places_num(bars, mbars):
    places = [b[1] for b in bars] + [b[1] for b in mbars]
    if places:
        return max(places) + 1
    else:
        return None


def get_platforms():
    if not os.path.isfile(filenames.platformsFile):
        return []

    with open(filenames.platformsFile, "r") as platforms:
        result = [str.split(" ", 1) for str in platforms.read().splitlines()]

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
            with open(
                "/".join([platform, filenames.parsed, filenames.activeIndex]), "a+") as activeIndex:
                activeIndex.write(key + "\n")

        with open(
            "/".join([platform, filenames.parsed, str(index.index(key))]), "a+") as file:
            file.write(date.isoformat())
            for i in range(len(primary_labels[:main_primary_labels])):
                file.write("\t" + str(value[i]))
            file.write("\n")

    return True


def get_active(platform, active, index):
    with open(
        os.path.join(platform, filenames.parsed, str(index.index(active))), "r") as file:
        lines = list(map(lambda s: s.split("\t"), file.read().splitlines()))
        dates = [utils.parse_isoformat_date(line[0]) for line in lines]
        fields = [list(map(lambda f, x: f(x), primary_types, line[1:]))
                  for line in lines]

    return dates, fields


def get_actives(platform):
    index = []
    fileName = os.path.join(platform, filenames.parsed, filenames.activeIndex)

    if not os.path.isfile(fileName):
        return index

    with open(fileName, "r") as file:
        index = file.read().splitlines()

    return index

