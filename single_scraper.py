from urllib.parse import quote_plus, urlparse, parse_qs, urlencode
from lxml import html
import re
from datetime import datetime, timedelta
import pandas as pd
import requests
import pytz
import json
import csv
import os
import threading
import queue
import logging
from time import sleep

logger = logging.getLogger(__name__)

# STOCKS_FILE_NAME = 'nasdaqstocks.csv'
STOCKS_FILE_NAME = 'stocks_for_scrapping.csv'
DATA_TIMEZONE = pytz.timezone("US/Eastern")
MAX_THREADS = 100
DATA_DIR = "data"


def get_stocks(file_name=None):
    file_name = file_name or STOCKS_FILE_NAME
    with open(file_name, 'r') as f:
        reader = csv.reader(f, delimiter=',', quotechar='"')
        for row in reader:
            for stock in row:
                yield stock.strip()


def get_trading_dates(date):
    """
    Returns the dates for the latest 10 trading days
    """
    url = "https://query1.finance.yahoo.com/v7/finance/chart/X?period1={:.0f}&period2={:.0f}" \
          "&interval=1d&includeTimestamps=true".format((date - timedelta(days=20)).timestamp(),
                                                       date.timestamp())
    page = requests.get(url)
    chart = page.json()['chart']

    result = chart['result'][0]
    start = datetime.fromtimestamp(result['timestamp'][-10], tz=DATA_TIMEZONE)
    end = datetime.fromtimestamp(result['timestamp'][-1], tz=DATA_TIMEZONE)
    return start, end


def execute_safe(method, *args, **kwargs):
    errors = 0
    while True:
        try:
            response = method(*args, **kwargs)
        except Exception as e:
            errors += 1
            logger.error(e)
            sleep_time = errors * 10
            logger.info("sleep {}s".format(sleep_time))
            sleep(sleep_time)
        else:
            return response


def get_minute_data(symbol, now, timeout=None):
    start = now.replace(hour=9, minute=30, second=0, microsecond=0)
    end = start.replace(hour=16, minute=0)
    url = "https://query1.finance.yahoo.com/v7/finance/chart/{}?period1={:.0f}&period2={:.0f}" \
          "&interval=1m&indicators=quote&includeTimestamps=true&" \
          "events=div%7Csplit%7Cearn".format(symbol, start.timestamp(), end.timestamp())

    page = execute_safe(requests.get, url, timeout=timeout)

    result = page.json()['chart']['result']
    if not result:
        print(page.json())
        return
    data = result[0]
    quote = data['indicators']['quote'][0]
    if 'timestamp' not in data:
        return
    times = data['timestamp']
    df = pd.DataFrame(quote, index=[datetime.fromtimestamp(t, tz=DATA_TIMEZONE).astimezone(now.tzinfo) for t in times])
    return df[df.close.notnull()]


def pull_trades(stock, time, pageno=None):
    base_url = "http://www.nasdaq.com/symbol/{symbol}/time-sales?time={time}&pageno={pageno}"

    trades = []
    url = base_url.format(symbol=stock, time=time, pageno=pageno or 1)
    page_res = requests.get(url)
    sleep(2)
    tree = html.fromstring(page_res.content)

    table = tree.find('.//table[@id="AfterHoursPagingContents_Table"]')

    if table is not None:
        for row in table:
            if row.tag == 'tr':
                trades.append(tuple(col.text_content() for col in row))

    if pageno is None:
        pager = tree.find('.//ul[@id="pager"]')
        if pager is not None:
            page_links = pager.findall('.//a')
            if page_links:
                href = page_links[-1].attrib['href']
                parsed_url = urlparse(href)
                query_params = parse_qs(parsed_url.query)
                max_page = int(query_params['pageno'][0])

                for pn in range(1, max_page + 1):
                    res = pull_trades(stock, time, pageno=pn)
                    trades.extend(res)
    return trades


def trades_to_df(trades, date):
    # save resp
    raw_data = dict(time=[], price=[], volume=[])

    for time, price, volume in trades:
        time_str = re.sub(r'[^\d:]+', '', time)
        hour, minute, *_ = time_str.split(':')
        time = date.replace(hour=int(hour), minute=int(minute))
        price = float(re.sub(r'[^\d\.]+', '', price))
        volume = int(re.sub(r'[^\d]+', '', volume))

        raw_data['time'].append(time)
        raw_data['price'].append(price)
        raw_data['volume'].append(volume)

    df = pd.DataFrame(raw_data)
    df = df[df.volume >= 1000]
    df['cost'] = df.price * df.volume * 100
    df['trades_count'] = 1
    df = df.groupby(['time'])['cost', 'volume', 'trades_count'].sum()
    return df


def main():
    today = datetime.now(tz=DATA_TIMEZONE).replace(second=0, microsecond=0)
    print(today)
    if today.hour < 16:
        logger.error("It's too early to run the scrapper")
        return

    _, last_trading_date = get_trading_dates(today)
    if last_trading_date.date() != today.date():
        logger.error("It's not a trading day")
        return

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    today_dir = os.path.join(DATA_DIR, str(today.date()))
    if not os.path.exists(today_dir):
        os.makedirs(today_dir)

    for stock in get_stocks():
        now = datetime.now()
        minute_data = get_minute_data(stock, today)
        if minute_data is not None:
            del minute_data['volume']

            trades = []
            for time in range(1, 14):
                trades.extend(
                    pull_trades(stock, time)
                )
            trade_data = trades_to_df(trades, today)

            result = pd.merge(minute_data, trade_data, how="left", left_index=True, right_index=True)
            with open(os.path.join(today_dir, "{}.csv".format(stock)), "w") as f:
                result.to_csv(f)

        print(datetime.now() - now)


if __name__ == "__main__":
    main()
