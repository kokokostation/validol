import urllib.request as ul
import re
import datetime as dt
import os
import downloader
import numpy as np

#ice us bug

def parse_isoformat_date(date):
    return dt.datetime.strptime(date, "%Y-%m-%d").date()

def parse_active(entry):
    entry = entry.replace(",", "")
    name = entry[:re.search(r' - ', entry).start()]
    lines = [list(map(float, re.findall(r'\d+\.\d+|\d+', s))) for s in re.findall(r'All([^n]*)\\n', entry)]
    fields = {"OI": lines[0][0],
              "NCL": lines[0][1],
              "NCS": lines[0][2],
              "CL": lines[0][4],
              "CS": lines[0][5],
              "4L%": lines[-1][4],
              "4S%": lines[-1][5],
              "8L%": lines[-1][6],
              "8S%": lines[-1][7]}
    return name, fields

def get_actives_from_page(content):
    start, end = re.search(r'<!--ih:includeHTML file=\".*\"-->[ \t]*', content), re.search(r'<!--/ih:includeHTML-->', content)
    if start and end:
        content = re.compile(r'\\n[\', b\\tr]*\\n[\', b]*').split(content[start.end():end.start()])
    else:
        return []

    return dict(map(parse_active, content[:-1]))

def get_all_actives(platform_code):
    result = []
    for file_name in os.listdir(platform_code):
        file = open(platform_code + "/" + file_name, "r")
        actives = get_actives_from_page(file.read())
        file.close()
        if actives:
            result.append((parse_isoformat_date(file_name), actives))

    return result

# table2_labels = ["4L", "4S", "8L", "8S", "4L/4S", "L/S", "Price", "A/B", "C/A", "D/A"]

def round_dict(dict_, precision=3):
    for key in dict_.keys():
        if type(dict_[key]) == float:
            dict_[key] = round(dict_[key], precision)
    return dict_

# def table2_from_fields(fields):
#     data = [fields["4L"],
#             fields["4S"],
#             fields["8L"],
#             fields["8S"],
#             fields["4L"] / fields["4S"],
#             (fields["4L"] / fields["4S"] + fields["8L"] / fields["8S"]) / 2]
#
#     return round_list(data)

def table1_from_fields(fields):
    data = {"OI": fields["OI"],
            "NCL": fields["NCL"],
            "NCS": fields["NCS"],
            "NCCP": fields["NCL"] - fields["NCS"],
            "NCB": 100 * fields["OI"] / (fields["OI"] + fields["NCL"]),
            "CL": fields["CL"],
            "CS": fields["CS"],
            "CCP": fields["CL"] - fields["CS"],
            "CB": 100 * fields["CL"] / (fields["CL"] + fields["CS"]),
            "4L%": fields["4L%"],
            "4S%": fields["4S%"],
            "8L%": fields["8L%"],
            "8S%": fields["8S%"],
            "4L%/4S%": fields["4L%"] / fields["4S%"],
            "L%/S%": (fields["4L%"] / fields["4S%"] + fields["8L%"] / fields["8S%"]) / 2,
            "4L": (fields["NCL"] + fields["CL"]) * fields["4L%"] / 100,
            "4S": (fields["NCS"] + fields["CS"]) * fields["4S%"] / 100,
            "4L/4S": (fields["NCL"] + fields["CL"]) * fields["4L%"] / ((fields["NCS"] + fields["CS"]) * fields["4S%"]),
            "8L": (fields["NCL"] + fields["CL"]) * fields["8L%"] / 100,
            "8S": (fields["NCS"] + fields["CS"]) * fields["8S%"] / 100,
            "(4L/4S + 8L/8S)/2": ((fields["NCL"] + fields["CL"]) * fields["4L%"] / ((fields["NCS"] + fields["CS"]) * fields["4S%"]) +
             (fields["NCL"] + fields["CL"]) * fields["8L%"] / ((fields["NCS"] + fields["CS"]) * fields["8S%"])) / 2
            }

    return round_dict(data)

def table2_from_fields(fields):
    data = {"4L%": fields["4L%"],
            "4S%": fields["4S%"],
            "8L%": fields["8L%"],
            "8S%": fields["8S%"],
            "4L%/4S%": fields["4L%"] / fields["4S%"],
            "L%/S%": (fields["4L%"] / fields["4S%"] + fields["8L%"] / fields["8S%"]) / 2
            }

    return round_dict(data)

graph1_info = [(["OI"], [("NCCP", 1), ("CCP", 1)]), (["4L%/4S%", "L%/S%"], [("4L%", 1), ("4S%", -1), ("8L%", 1), ("8S%", -1)]), (["Price"], [])]
table1_labels = ["Date", "OI", "NCL", "NCS", "NCCP", "NCB", "CL", "CS", "CCP", "CB", "4L%", "8L%", "8S%", "4L%/4S%", "L%/S%", "4L", "4S", "4L/4S", "8L", "8S", "(4L/4S + 8L/8S)/2", "Price"]

graph2_info = []
table2_labels = ["Date", "4L%", "8L%", "8S%", "4L%/4S%", "L%/S%", "Price"]

class Grabber:
    def __init__(self):
        self.actives = {}

    def get_actives(self, platform_code):
        self.actives[platform_code] = get_all_actives(platform_code)
        return list(set([key for date, active in self.actives[platform_code] for key in active.keys()]))

    def get_platforms(self):
        platforms = open(downloader.platformsFile, "r")

        result = [tuple(str.split(" ", 1)) for str in platforms.read().splitlines()]

        platforms.close()

        return result

    def get_info(self, platform, active, from_fields, prices_url):
        result = sorted([(date, from_fields(actives[active])) for date, actives in self.actives[platform] if active in actives])
        prices, name, url, new = downloader.get_prices([date for date, _ in result], prices_url)
        for i in range(len(prices)):
            result[i][1]["Date"] = result[i][0]
            result[i][1]["Price"] = prices[i]

        return [i[1] for i in result], name, url, new

    def get_cached_prices(self):
        if not os.path.isfile(downloader.pricesFile):
            return []

        file = open(downloader.pricesFile, "r")

        result = []
        for line in file.read().splitlines():
            url, pair_id, name = line.split(" ", 2)
            result.append((url, name))

        file.close()

        return result

    def get_patterns(self, table_name):
        if not os.path.isfile(downloader.pricesFile):
            return []

        file = open(downloader.patternsFile, "r")


