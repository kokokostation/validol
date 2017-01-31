import re
import datetime as dt
import os
import requests
import utils

__all__ = ["platformsFile", "datesFile", "pricesFile", "patternsFile", "monetaryFile", "get_prices", "get_mbase", "init", "update"]

platformsFile = "platforms"
datesFile = "dates"
pricesFile = "prices/pair_ids"
patternsFile = "patterns"
monetaryFile = "monetary"

def read_url(url):
    return requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).text

def unique(list_):
    return [list_[2 * i] for i in range(0, len(list_) // 2)]

first_date = dt.date(2005, 1, 4)

def get_dates(last_net_date):
    return [dt.date.fromordinal(d) for d in range(first_date.toordinal(), last_net_date.toordinal(), 7)]

def get_net_dates():
    return sorted([dt.datetime.strptime(d, "%m%d%y").date() for d in unique(re.findall(r'cot(\d{6})', read_url("http://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalViewable/index.htm")))])

def get_platforms():
    current_info = read_url("http://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm")
    current_info = current_info[re.search(r'<p><b>Futures-and-Options-Combined</b></p>', current_info).end():
                                re.search(r'<p><b>Supplemental Commodity Index</b></p>', current_info).start()]

    return list(zip(unique(re.findall(r'dea([a-z]*)lf', current_info)), re.findall(r'<p><b>([^<>]*)</b></p>', current_info)))

def get_actives(date, platform_code):
    content = read_url("http://www.cftc.gov/files/dea/cotarchives/" + str(date.year) +
                 "/futures/dea" + platform_code + "lf" + date.strftime("%m%d%y") + ".htm")

    return content

def get_current_actives(platform_code):
    content = read_url("http://www.cftc.gov/dea/futures/dea" + platform_code + "lf.htm")

    return content

def get_last_date():
    content = read_url("http://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm")

    date_match = re.search(r'Reports Dated (.*) - Current Disaggregated Reports:', content)

    return dt.datetime.strptime(date_match.group(1), "%B %d, %Y").date()

def normalize_url(url):
    return re.sub(r'https://[^.]*\.', r'https://www.', url)

#different urls
def get_active_info(url):
    new = False
    file = open(pricesFile, "a+")
    file.seek(0)

    pair_ids = []
    for line in file.read().splitlines():
        url_, pair_id, name = line.split(" ", 2)
        if url_ == url:
            file.close()
            return pair_id, name, new
        pair_ids.append(pair_id)

    content = read_url(url)

    pair_id = re.search(r'data-pair-id="(\d*)"', content).group(1)
    name = re.search(r'<title>(.*) - .*</title>', content).group(1)

    if pair_id not in pair_ids:
        file.write(url + " " + pair_id + " " + name + "\n")
        new = True

    return pair_id, name, new

def get_net_prices(begin, end, pair_id):
    start_date = begin.strftime("%d/%m/%Y")
    end_date = end.strftime("%d/%m/%Y")

    session = requests.Session()

    response = session.post(
        url='https://ru.investing.com/instruments/HistoricalDataAjax',
        data={
            'action': 'historical_data',
            'curr_id': pair_id,
            'st_date': start_date,
            'end_date': end_date,
            'interval_sec': 'Daily'
        },
        headers={
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0'
        }
    )

    parsed_dates = [dt.datetime.strptime(date, "%d.%m.%Y").date() for date in re.findall(r'class="first left bold noWrap">(.*)</td>', response.text)]
    parsed_values = [n for n in re.findall(r'<td.*>(\d+\.\d*|\d+)</td>', response.text)]

    result = ""
    for i in range(len(parsed_dates) - 1, -1, -1):
        result += parsed_dates[i].isoformat() + " " + parsed_values[4 * i] + "\n"

    return result

def get_prices(dates, url):
    url = normalize_url(url)

    pair_id, name, new = get_active_info(url)
    filePath = "prices/" + pair_id
    content = ""
    if not new:
        file = open(filePath, "r")
        begin, end = list(map(utils.parse_isoformat_date, file.readline().strip().split(" ")))

        if begin > dates[0] or dates[-1] > end:
            body = file.read()
            file.close()
            file = open(filePath, "w")

            if begin > dates[0]:
                content += get_net_prices(dates[0], begin - dt.timedelta(1), pair_id)
                begin = dates[0]
            content += body
            if dates[-1] > end:
                content += get_net_prices(end + dt.timedelta(1), dates[-1], pair_id)
                end = dates[-1]

            file.write(begin.isoformat() + " " + end.isoformat() + "\n")
            file.write(content)
        else:
            content = file.read()

        file.close()
    else:
        file = open(filePath, "w")
        file.write(dates[0].isoformat() + " " + dates[-1].isoformat() + "\n")
        content = get_net_prices(dates[0], dates[-1], pair_id)
        file.write(content)
        file.close()

    date_price = {}
    for line in content.splitlines():
        date, price = line.split(" ")
        date = utils.parse_isoformat_date(date)
        if dates[0] <= date <= dates[-1]:
            date_price[date] = float(price)

    result = []
    for date in dates:
        if date in date_price:
            result.append(date_price[date])
        else:
            result.append(None)

    return result, name, url, new

def get_net_mbase(cosd, coed):
    if cosd:
        cosd = (utils.parse_isoformat_date(cosd) + dt.timedelta(1)).isoformat()

    session = requests.Session()

    response = session.get(
        url='https://fred.stlouisfed.org/graph/fredgraph.csv',
        params={
            'cosd': cosd,
            'coed': coed,
            'id': "BOGMBASEW",
        },
        headers={
            'Host': "fred.stlouisfed.org",
            'User-Agent': 'Mozilla/5.0'
        }
    )

    if not response.text:
        return ""
    else:
        return response.text[response.text.find("\n") + 1:]

def get_mbase(requestedDates):
    file = open(monetaryFile, "r")
    data = [line.split(",") for line in file.read().splitlines()]
    file.close()

    dates = [utils.parse_isoformat_date(date) for date, _ in data]
    values = [int(value) for _, value in data]

    result = []
    for date in requestedDates:
        closest = utils.take_closest(dates, date)
        if abs(dates[closest].toordinal() - date.toordinal()) <= 7:
            result.append(values[closest])
        else:
            result.append(None)

    return result

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

#даты при закачке смотреть отдельно для каждой платформы
def update():
    monetary_file = open(monetaryFile, "a+")
    monetary_file.seek(0)

    content = monetary_file.read()
    if content:
        last_date = content.splitlines()[-1].split(",")[0]
    else:
        last_date = ""
    monetary_file.write(get_net_mbase(last_date, dt.date.today().isoformat()))

    monetary_file.close()

    dates_file = open(datesFile, "a+")
    dates_file.seek(0)

    last_net_date = get_last_date()
    written_dates = dates_file.read().splitlines()

    if written_dates and utils.parse_isoformat_date(written_dates[-1]) == last_net_date:
        return

    platforms_file = open(platformsFile, "w")
    net_platforms = get_platforms()
    for code, name in net_platforms:
        if not os.path.exists(code):
            os.makedirs(code)
        platforms_file.write(code + " " + name + "\n")
    platforms_file.close()

    dates = get_dates(last_net_date)
    all_dates = get_net_dates()
    all_dates.append(last_net_date)
    all_dates.extend(dates)
    all_dates = sorted(list(set(all_dates)))

    for code, _ in net_platforms:
        for date in all_dates[len(written_dates):-1]:
            file = open(code + "/" + date.isoformat(), "w")
            file.write(get_actives(date, code))
            file.close()
        file = open(code + "/" + all_dates[-1].isoformat(), "w")
        file.write(get_current_actives(code))
        file.close()

    for date in all_dates[len(written_dates):]:
        dates_file.write(date.isoformat() + "\n")
    dates_file.close()