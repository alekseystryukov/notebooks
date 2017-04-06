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

######


def get_proxies():
    with open("proxies_approved.csv", "r") as f:
        proxies = f.read().split()
    return proxies


class ProxyFailException(Exception):
    pass


# class TaskFailException(Exception):
#     pass
#
#
# class PullTradesTask:
#
#     def __init__(self, proxies):
#         self.proxies = proxies
#         self.proxy = self.get_proxy()
#
#     @staticmethod
#     def get_trades_page_tree(symbol, proxy, time, page_no):
#         base_url = "http://www.nasdaq.com/symbol/{symbol}/time-sales?time={time}&pageno={pageno}"
#         url = base_url.format(symbol=symbol, time=time, pageno=page_no)
#         try:
#             kwargs = dict(timeout=6)
#             if proxy:
#                 kwargs['proxies'] = {'http': "http://{}".format(proxy)}
#
#             page_res = requests.get(url, **kwargs)
#             tree = html.fromstring(page_res.content)
#         except Exception as e:
#             raise ProxyFailException(e)
#         else:
#             return tree
#
#     @staticmethod
#     def get_trades_content_from_tree(tree):
#         trades = []
#         table = tree.find('.//table[@id="AfterHoursPagingContents_Table"]')
#         if table is None:
#             raise ProxyFailException('The table is missing')
#         else:
#             for row in table:
#                 if row.tag == 'tr':
#                     trades.append(tuple(col.text_content() for col in row))
#         return trades
#
#     def get_proxy(self):
#         if self.proxies is None:
#             return
#
#         try:
#             proxy = self.proxies.get_nowait()
#         except queue.Empty:
#             raise TaskFailException("Proxy queue is empty")
#         else:
#             return proxy
#
#     def __call__(self, symbol, date):
#
#         trades = []
#         for time in range(1, 14):
#             while True:
#                 try:
#                     tree = self.get_trades_page_tree(symbol, self.proxy, time, 1)
#                     trades.extend(self.get_trades_content_from_tree(tree))
#                 except ProxyFailException as e:
#                     print(e)
#                     print(self.proxy)
#                     self.proxy = self.get_proxy()
#                 else:
#                     break
#
#             pager = tree.find('.//ul[@id="pager"]')
#             if pager is not None:
#                 page_links = pager.findall('.//a')
#                 if page_links:
#                     href = page_links[-1].attrib['href']
#                     parsed_url = urlparse(href)
#                     query_params = parse_qs(parsed_url.query)
#                     max_page = int(query_params['pageno'][0])
#                     for page_no in range(2, max_page + 1):
#
#                         while True:
#                             try:
#                                 tree = self.get_trades_page_tree(symbol, self.proxy, time, page_no)
#                                 trades.extend(self.get_trades_content_from_tree(tree))
#                             except ProxyFailException as e:
#                                 print(e)
#                                 self.proxy = self.get_proxy()
#                             else:
#                                 break
#
#         raw_data = dict(time=[], price=[], volume=[])
#         for time, price, volume in trades:
#             time_str = re.sub(r'[^\d:]+', '', time)
#             hour, minute, *_ = time_str.split(':')
#             time = date.replace(hour=int(hour), minute=int(minute))
#             price = float(re.sub(r'[^\d\.]+', '', price))
#             volume = int(re.sub(r'[^\d]+', '', volume))
#
#             raw_data['time'].append(time)
#             raw_data['price'].append(price)
#             raw_data['volume'].append(volume)
#
#         df = pd.DataFrame(raw_data)
#         df = df[df.volume >= 1000]
#         df['cost'] = df.price * df.volume * 100
#         df['trades_count'] = 1
#         df = df.groupby(['time'])['cost', 'volume', 'trades_count'].sum()
#         return df
#
#
# def task_exec(proxies, symbol, today, today_dir):
#     minute_data = get_minute_data(symbol, today)
#     if minute_data is not None:
#         del minute_data['volume']
#         # trade_data = get_volume_options(stock, len(minute_data), today)
#
#         trade_data = PullTradesTask(proxies)(symbol, today)
#         result = pd.merge(minute_data, trade_data, how="left", left_index=True, right_index=True)
#         with open(os.path.join(today_dir, "{}.csv".format(symbol)), "w") as f:
#             result.to_csv(f)
#
#
# def save_data(stocks, today, today_dir):
#     tasks = queue.Queue()
#     proxies = queue.Queue()
#     for p in get_proxies():
#         proxies.put(p)
#
#     threads_len = min(len(stocks), MAX_THREADS)
#
#     def worker():
#         nonlocal threads_len
#
#         while True:
#             symbol = tasks.get()
#             if symbol is None:
#                 break
#
#             try:
#                 task_exec(proxies, symbol, today, today_dir)
#             except TaskFailException:
#                 threads_len -= 1
#                 print('Kill task;threads left: {}'. format(threads_len))
#                 break
#             finally:
#                 tasks.task_done()
#
#     threads = []
#     for i in range(threads_len):
#         t = threading.Thread(target=worker)
#         t.start()
#         threads.append(t)
#
#     for stock in stocks:
#         tasks.put(stock)
#
#     # block until all tasks are done
#     tasks.join()
#
#     # stop workers
#     for i in range(len(threads)):
#         tasks.put(None)
#
#     for t in threads:
#         t.join()


# -- old method


def pull_trades(proxy, q, r, stock, time, pageno=None):
    base_url = "http://www.nasdaq.com/symbol/{symbol}/time-sales?time={time}&pageno={pageno}"
    url = base_url.format(symbol=stock, time=time, pageno=pageno or 1)
    try:
        page_res = requests.get(url, timeout=12, proxies={'http': "http://{}".format(proxy)})
        tree = html.fromstring(page_res.content)
    except Exception as e:
        raise ProxyFailException(e)
    else:
        table = tree.find('.//table[@id="AfterHoursPagingContents_Table"]')
        if table is None:
            raise ProxyFailException('The table is missing; {}'.format(proxy))
        else:
            sleep(5)
            for row in table:
                if row.tag == 'tr':
                    r.put(tuple(col.text_content() for col in row))

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
                        q.put((stock, time, pn))
            else:
                print('The pager is missing; {}; {}'.format(url, proxy))


def load_in_parallel(stock, date):
    tasks = queue.Queue()  # queue with arguments for the 'get_transactions' function
    responses = queue.Queue()  # queue with raw responses
    proxies = queue.Queue()
    for p in get_proxies():
        proxies.put(p)

    def get_proxy():
        try:
            proxy = proxies.get_nowait()
        except queue.Empty:
            pass
            print("Error: you have used all the proxies - this worker will stop")
        else:
            return proxy

    def worker():
        proxy = get_proxy()
        while proxy is not None:
            args = tasks.get()
            if args is None:
                break
            while True:
                try:
                    pull_trades(proxy, tasks, responses, *args)
                except ProxyFailException as e:
                    print(e)
                    proxy = get_proxy()
                    if proxy is None:
                        tasks.put(args)  # put the task back and die
                        break
                else:
                    break
            tasks.task_done()

    threads = []
    for i in range(100):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    for i in range(1, 14):
        tasks.put((stock, i))

    # block until all tasks are done
    tasks.join()

    # stop workers
    for i in range(len(threads)):
        tasks.put(None)

    for t in threads:
        t.join()

    # save resp
    raw_data = dict(time=[], price=[], volume=[])

    while True:
        try:
            time, price, volume = responses.get(block=False)
        except queue.Empty:
            break
        else:
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
        print(stock, now)
        minute_data = get_minute_data(stock, today)
        if minute_data is not None:
            del minute_data['volume']
            trade_data = load_in_parallel(stock, today)
            result = pd.merge(minute_data, trade_data, how="left", left_index=True, right_index=True)
            with open(os.path.join(today_dir, "{}.csv".format(stock)), "w") as f:
                result.to_csv(f)

        print(datetime.now() - now)


if __name__ == "__main__":
    main()
