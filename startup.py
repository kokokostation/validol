import os
import downloader
import filenames
import utils
import data_parser
import datetime as dt
import requests

#создать все необходимые файлы и поубирать if'ы
def init():
    ifNeedsUpdate = False
    if not os.path.exists("data"):
        ifNeedsUpdate = True
        os.makedirs("data")

    os.chdir("data")

    if not os.path.exists("prices"):
        os.makedirs("prices")

    if ifNeedsUpdate:
        update()

def update():
    try:
        dates_file = open(filenames.datesFile, "a+")
        dates_file.seek(0)

        last_net_date = downloader.get_last_date()
        written_dates = dates_file.read().splitlines()

        if written_dates and utils.parse_isoformat_date(written_dates[-1]) == last_net_date:
            return

        monetary_file = open(filenames.monetaryFile, "a+")
        monetary_file.seek(0)

        content = monetary_file.read()
        if content:
            last_date = content.splitlines()[-1].split(",")[0]
        else:
            last_date = ""
        monetary_file.write(downloader.get_net_mbase(last_date, dt.date.today().isoformat()))

        monetary_file.close()

        net_platforms = downloader.get_platforms()
        platforms_file = open(filenames.platformsFile, "w")
        for code, name in net_platforms:
            if not os.path.exists(code):
                os.makedirs(code)
                os.makedirs("/".join([code, filenames.parsed]))
            platforms_file.write(code + " " + name + "\n")
        platforms_file.close()

        dates = downloader.get_dates(last_net_date)
        all_dates = downloader.get_net_dates()
        all_dates.append(last_net_date)
        all_dates.extend(dates)
        all_dates = sorted(list(set(all_dates)))

        for code, _ in net_platforms:
            index = data_parser.get_actives(code)
            for date in all_dates[len(written_dates):]:
                filename = os.path.join(code, date.isoformat())
                if os.path.isfile(filename):
                    continue

                if date == all_dates[-1]:
                    data = downloader.get_current_actives(code)
                else:
                    data = downloader.get_actives(date, code)

                if data_parser.parse_date(code, date, data, index):
                    file = open(filename, "w")
                    file.write(data)
                    file.close()

        for date in all_dates[len(written_dates):]:
            dates_file.write(date.isoformat() + "\n")
        dates_file.close()

        return True
    except requests.exceptions.ConnectionError:
        return False
