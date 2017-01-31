import re
import datetime as dt
import os
import downloader
import utils

__all__ = ["table1_labels", "table2_labels", "table1_key_types", "table2_key_types", "places_num", "get_platforms", "get_cached_prices", "Grabber"]

def parse_active(entry):
    entry = entry.replace(",", "")
    name = entry[:re.search(r' - ', entry).start()]
    lines = [list(map(float, re.findall(r'\d+\.\d+|\d+', s))) for s in re.findall(r'All([^n]*)\\n', entry)]
    fields = {"OI": lines[0][0],
              "NCL": lines[0][1],
              "NCS": lines[0][2],
              "CL": lines[0][4],
              "CS": lines[0][5],
              "NRL": lines[0][8],
              "NRS": lines[0][9],
              "4L%": lines[-1][4],
              "4S%": lines[-1][5],
              "8L%": lines[-1][6],
              "8S%": lines[-1][7]}
    return name, fields

def get_actives_from_page(content):
    start, end = re.search(r'<!--ih:includeHTML file=\".*\"-->[\t\\rnb\' ,]*', content), re.search(r'<!--/ih:includeHTML-->', content)
    if start and end:
        activesList = list(filter(lambda s: '-' in s, re.compile(r'([\', b\\r]*\\n){2,3}[\', b]*').split(content[start.end():end.start()])))
    else:
        return []

    return dict(map(parse_active, activesList))

def get_all_actives(platform_code):
    result = []
    for file_name in os.listdir(platform_code):
        file = open(platform_code + "/" + file_name, "r")
        actives = get_actives_from_page(file.read())
        file.close()
        if actives:
            result.append((utils.parse_isoformat_date(file_name), actives))

    return result

def round_dict(dict_, precision=3):
    for key in dict_.keys():
        if type(dict_[key]) == float:
            dict_[key] = round(dict_[key], precision)
    return dict_

def from_fields(fields):
    data = {"OI": fields["OI"],
            "NCL": fields["NCL"],
            "NCS": fields["NCS"],
            "NCCP": fields["NCL"] - fields["NCS"],
            "NCB": utils.my_division(100 * fields["OI"], (fields["OI"] + fields["NCL"])),
            "CL": fields["CL"],
            "CS": fields["CS"],
            "CCP": fields["CL"] - fields["CS"],
            "CB": utils.my_division(100 * fields["CL"], (fields["CL"] + fields["CS"])),
            "NRL": fields["NRL"],
            "NRS": fields["NRS"],
            "NRCP": fields["NRL"] - fields["NRS"],
            "NRB": utils.my_division(100 * fields["NRL"], (fields["NRL"] + fields["NRS"])),
            "4L%": fields["4L%"],
            "4S%": fields["4S%"],
            "8L%": fields["8L%"],
            "8S%": fields["8S%"],
            "4L%/4S%": utils.my_division(fields["4L%"], fields["4S%"]),
            "L%/S%": (utils.my_division(fields["4L%"], fields["4S%"]) + utils.my_division(fields["8L%"], fields["8S%"])) / 2,
            "4L": (fields["NCL"] + fields["CL"] + fields["NRL"]) * fields["4L%"] / 100,
            "4S": (fields["NCS"] + fields["CS"] + fields["NRS"]) * fields["4S%"] / 100,
            "8L": (fields["NCL"] + fields["CL"] + fields["NRL"]) * fields["8L%"] / 100,
            "8S": (fields["NCS"] + fields["CS"] + fields["NRS"]) * fields["8S%"] / 100,
            }

    extra = {"4L/4S": utils.my_division(data["4L"], data["4S"]),
             "(4L/4S + 8L/8S)/2": (utils.my_division(data["4L"], data["4S"]) + utils.my_division(data["8L"], data["8S"])) / 2
            }

    data.update(extra)

    return round_dict(data)

table1_labels = ["Date", "OI", "NCL", "NCS", "NCCP", "NCB", "CL", "CS",
                 "CCP", "CB", "NRL", "NRS", "NRCP", "NRB", "4L%", "4S%", "8L%",
                 "8S%", "4L%/4S%", "L%/S%", "Quot", "4L", "4S", "4L/4S",
                 "8L", "8S", "(4L/4S + 8L/8S)/2", "AL", "AS", "Asum", "MBase"]
table1_key_types = [dt.date] + ([float] * (len(table1_labels) - 1))

table2_labels = ["Date", "4L", "4S", "Quot", "AL", "AS", "4L/4S", "MBase"]
table2_key_types = [dt.date] + ([float] * (len(table2_labels) - 1))

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
        return name, int(place)
    else:
        return item

def parse_pattern(line):
    items = line.split("\t")

    table, title = items[0], items[1]
    pattern = []
    for i in range(2, len(items), 2):
        pattern.append([parse_axis(items[i]), parse_axis(items[i + 1])])

    return table, title, pattern

def pack_bar(bar):
    name, place = bar
    return name + "^" + str(place)

def pack_axis(lines, bars, mbars):
    return "&".join(lines) + "#" + "&".join(map(pack_bar, bars)) + "#" + "&".join(map(pack_bar, mbars))

def pack_pattern(table, title, pattern):
    result = table + "\t" + title

    for g in pattern:
        for lines, bars, mbars in g:
            result += "\t" + pack_axis(lines, bars, mbars)

    return result

def get_cached_prices():
    result = []

    if not os.path.isfile(downloader.pricesFile):
        return result

    file = open(downloader.pricesFile, "r")

    for line in file.read().splitlines():
        url, pair_id, name = line.split(" ", 2)
        result.append((url, name))

    file.close()

    return result

def get_patterns():
    result = {}

    if not os.path.isfile(downloader.patternsFile):
        return result

    file = open(downloader.patternsFile, "r")
    for table, title, pattern in map(parse_pattern, file.read().splitlines()):
        utils.add_to_dict(result, table, title, pattern)

    file.close()

    return result

def add_pattern(table, title, pattern):
    file = open(downloader.patternsFile, "a+")
    file.write(pack_pattern(table, title, pattern) + "\n")
    file.close()

def get_platforms():
    platforms = open(downloader.platformsFile, "r")

    result = [tuple(str.split(" ", 1)) for str in platforms.read().splitlines()]

    platforms.close()

    return result

def title(platformName, activeName, priceName):
    return platformName + "/" + activeName + "; Quot from: " + priceName

class Grabber:
    def __init__(self):
        self.actives = {}
        self.patterns = get_patterns()

    def get_actives(self, platform_code):
        if platform_code not in self.actives:
            self.actives[platform_code] = get_all_actives(platform_code)
        return list(set([key for date, active in self.actives[platform_code] for key in active.keys()]))

    def consolidate(self, platform, active, prices_url):
        result = sorted([(date, from_fields(actives[active])) for date, actives in self.actives[platform] if active in actives])
        dates = [date for date, _ in result]
        mbase = downloader.get_mbase(dates)

        for i in range(len(mbase)):
            currentInfo = result[i][1]
            currentInfo["Date"] = result[i][0]
            if mbase[i]:
                currentInfo["MBase"] = mbase[i]

        dicts = [i[1] for i in result]

        if not prices_url:
            return dicts, "", "", False

        prices, name, url, new = downloader.get_prices(dates, prices_url)
        for i in range(len(prices)):
            if prices[i]:
                currentInfo = result[i][1]
                currentMBase = mbase[i]
                currentInfo["Quot"] = prices[i]
                currentInfo["AL"] = currentInfo["Quot"] * currentInfo["4L"]
                currentInfo["ALN"] = currentInfo["AL"] / currentMBase
                currentInfo["AS"] = currentInfo["Quot"] * currentInfo["4S"]
                currentInfo["ASN"] = currentInfo["AS"] / currentMBase
                currentInfo["Asum"] = currentInfo["AL"] + currentInfo["AS"]

        return dicts, name, url, new






