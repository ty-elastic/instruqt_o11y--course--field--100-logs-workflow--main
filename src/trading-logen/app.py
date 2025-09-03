from flask import Flask, request, abort
from datetime import datetime, timezone, timedelta
import random
import ipaddress
import time
import logging
from threading import Thread
import yaml
import sys
import os

import ua_generator
from ua_generator.options import Options
from ua_generator.data.version import VersionRange
from faker import Faker

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

BACKLOG_Q_SEND_DELAY = 0.01
BACKLOG_Q_TIME_S = 60 * 60
BACKLOG_Q_BATCH_S = 60 * 2
BACKLOG_Q_TIMEOUT_MS = 10

DEBUG = False

def make_logger(service_name, max_logs_per_second):

    if not DEBUG:
        logger_provider = LoggerProvider(
            resource=Resource.create(
                {
                    "service.name": service_name,
                    "data_stream.dataset": service_name
                }
            ),
        )
        if 'COLLECTOR_ADDRESS' in os.environ:
            address = os.environ['COLLECTOR_ADDRESS']
        else:
            address = "collector"
        otlp_exporter = OTLPLogExporter(endpoint=f"http://{address}:4317", insecure=True)
        processor = BatchLogRecordProcessor(
            otlp_exporter,
            schedule_delay_millis=BACKLOG_Q_TIMEOUT_MS,
            max_queue_size=BACKLOG_Q_TIME_S * max_logs_per_second,
            max_export_batch_size=BACKLOG_Q_BATCH_S * max_logs_per_second,
        )
        logger_provider.add_log_record_processor(processor)
        handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    else:
        processor = None
        handler = logging.StreamHandler()
    logger = logging.getLogger(service_name)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger, processor

request_error_per_customer = {}
stock_price = {}

ERROR_RETRIES = 3

NUM_CUSTOMERS_PER_REGION = 10

REGIONS = ['NA', 'LATAM', 'EU', 'EMEA', 'APAC']
SYMBOLS = ['ZVZZT', 'ZALM', 'ZYX', 'CBAZ', 'BAA', 'OELK']

URLS = ['/trade/request', '/trade/status']
SIZE = {
    '/trade/request': (205, 220),
    '/trade/status': (316, 340),
}

CLIENTIPS_PER_REGION = {
    'NA': '107.80.0.0/16',
    'LATAM': '186.189.224.0/20',
    'EU': '149.254.212.0/24',
    'EMEA': '102.65.16.0/20',
    'APAC': '103.107.52.0/24'
}

CUSTOMERS_PER_REGION = {}
def generate_customers_per_region():
    fake = Faker()
    for region in REGIONS:
        CUSTOMERS_PER_REGION[region] = []
        for i in range(NUM_CUSTOMERS_PER_REGION):
            name = fake.unique.first_name().lower() + "." + fake.unique.last_name().lower()
            CUSTOMERS_PER_REGION[region].append(name)
generate_customers_per_region()

CHROME_VERSIONS = (125, 135)
BROWSER_PREFERENCE = ('chrome')
BROWSER_PREFERENCE_PERCENTAGE = 30

def make_ua_generator_options():
    ua_generator_options = Options()
    ua_generator_options.weighted_versions = True
    ua_generator_options.version_ranges = {
        'chrome': VersionRange(CHROME_VERSIONS[0], CHROME_VERSIONS[1]),
    }
    return ua_generator_options
ua_generator_options = make_ua_generator_options()

USERAGENTS_PER_USER = {}
def generate_useragent_per_user():
    for region in CUSTOMERS_PER_REGION.keys():
        for customer in CUSTOMERS_PER_REGION[region]:
            if random.randint(0,100) < BROWSER_PREFERENCE_PERCENTAGE:
                USERAGENTS_PER_USER[customer] = ua_generator.generate(browser=BROWSER_PREFERENCE, options=ua_generator_options)
            else:
                USERAGENTS_PER_USER[customer] = ua_generator.generate(options=ua_generator_options) 
generate_useragent_per_user()

IP_ADDRESS_PER_USER = {}
def generate_ipaddress_per_user():
    for region in CUSTOMERS_PER_REGION.keys():
        for customer in CUSTOMERS_PER_REGION[region]:
            network = ipaddress.ip_network(CLIENTIPS_PER_REGION[region])
            ip_list = [str(ip) for ip in network]
            IP_ADDRESS_PER_USER[customer] = random.choice(ip_list)
generate_ipaddress_per_user()

def get_customers():
    customers = []
    for region in CUSTOMERS_PER_REGION:
        for customer in CUSTOMERS_PER_REGION[region]:
            customers.append(customer)
    return customers

def generate_nginx_line(*, ip, timestamp, method, url, protocol, status_code, size, ref_url, user_agent):
    line = f"{ip} - - [{timestamp}] \"{method} {url} {protocol}\" {status_code} {size} \"{ref_url}\" \"{user_agent}\"\n"
    return line

def generate_trader_line(*, symbol, price):
    line = f"current market share price for {symbol}: ${price}"
    return line

def log_backoff(logger_tuple):
    processor = logger_tuple[1]
    if processor is not None:
        while len(processor._batch_processor._queue) == processor._batch_processor._max_queue_size:
            time.sleep(BACKLOG_Q_SEND_DELAY)
            #print('blocked')

LOG_LEVEL_LOOKUP = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}
start_times = {}
def log(logger_tuple, name, timestamp, level, body):
    logger = logger_tuple[0]

    level_num = LOG_LEVEL_LOOKUP[level]

    ct = timestamp.timestamp()
    if name not in start_times:
        start_times[name] = ct
    record = logger.makeRecord(name, level_num, f'{name}.py', 0, body, None, None)
    record.created = ct
    record.msecs = ct * 1000
    record.relativeCreated = (record.created - start_times[name]) * 1000

    log_backoff(logger_tuple)
    logger.handle(record)

def generate(*, name, generator_type, logger, start_timestamp, end_timestamp, logs_per_second, throttled):
    timestamp = start_timestamp

    while timestamp < end_timestamp if end_timestamp is not None else True:
        lines = []
        if generator_type == 'nginx':
            
            region = random.choice(REGIONS)
            customer_id = random.choice(CUSTOMERS_PER_REGION[region])
            url=random.choice(URLS)
            size=random.randrange(SIZE[url][0],SIZE[url][1])

            retries = 1
            if customer_id in request_error_per_customer:
                error_request = True if random.randint(0, 100) > (100-request_error_per_customer[customer_id]['amount']) else False
                if error_request:
                    retries = request_error_per_customer[customer_id]['retries']
            else:
                error_request = False

            send_timestamp = timestamp
            for i in range(retries):
                timestamp_str = send_timestamp.strftime("%d/%b/%Y:%H:%M:%S %z")

                line = generate_nginx_line(ip=IP_ADDRESS_PER_USER[customer_id],
                                    timestamp=timestamp_str,
                                    method='POST',
                                    url=url,
                                    protocol='HTTP/1.1',
                                    status_code=200 if error_request is False else 500,
                                    size=size,
                                    ref_url='-',
                                    user_agent=USERAGENTS_PER_USER[customer_id].text)
                lines.append(line)
                send_timestamp = send_timestamp + timedelta(seconds=1/1000)
        elif generator_type == 'trader':
            symbol = random.choice(SYMBOLS)
            if symbol not in stock_price:
                stock_price[symbol] = random.randrange(10,200)
            stock_price[symbol] = stock_price[symbol] + random.randrange(-10,10)
            if stock_price[symbol] <= 10:
                stock_price[symbol] = 10

            line = generate_trader_line(symbol=symbol, price=stock_price[symbol])
            lines.append(line)

        for line in lines:
            log(logger, name, timestamp, 'INFO', line)

        if throttled:
            wallclock = datetime.now(tz=timezone.utc)
            #print(f"wall={wallclock.timestamp()},time={timestamp.timestamp()}")
            delta = wallclock.timestamp() - timestamp.timestamp()
            #print(abs(delta))
            # leading
            if delta < 0:
                time.sleep(abs(delta))
        timestamp = timestamp + timedelta(seconds=1/logs_per_second)
    return timestamp

def bump_version_up_per_browser(*, browser, region, error=True):
    global request_error_per_customer

    for browser_version_range in ua_generator_options.version_ranges.keys():
        if browser_version_range == browser:
            last_max = ua_generator_options.version_ranges[browser].max_version.major
            ua_generator_options.version_ranges = {
                browser: VersionRange(last_max+1, last_max+1)
            }

    if region is not None:
        customers = CUSTOMERS_PER_REGION[region]
    else:
        customers = get_customers()
    for customer in customers:
        if USERAGENTS_PER_USER[customer].browser == browser:
            print(f'new ua for {browser}')
            USERAGENTS_PER_USER[customer] = ua_generator.generate(browser=browser, options=ua_generator_options)
            if error:
                print(f"start request error for customer {customer}")
                request_error_per_customer[customer] = {'amount': 100, 'retries': ERROR_RETRIES}

realtime = {}
@app.get('/status/realtime')
def get_realtime():
    global realtime
    retval = True
    for thread_name in realtime.keys():
        if realtime[thread_name] is False:
            retval = False

    if retval:
        return {"realtime": True}
    else:
        abort(404, description="not realtime")

@app.post('/err/browser/<browser>')
def err_request_ua(browser):
    global request_error_per_customer
    region = request.args.get('region', default=None, type=str)

    bump_version_up_per_browser(browser=browser, region=region)
    return request_error_per_customer

def run_schedule(thread_name, schedule):
    global realtime
    realtime[thread_name] = False

    last_ts = None
    loggers = {}

    max_lps = 0
    for item in schedule:
        print(f'{item}')
        if 'logs_per_second' in item:
            max_lps = max(max_lps, item['logs_per_second'])
        if 'name' in item and item['name'] not in loggers:
            loggers[item['name']] = make_logger(item['name'], max_lps)

    schedule_start = datetime.now(tz=timezone.utc)
    print(f'start @ {schedule_start}')
    for item in schedule:
        if item['type'] == 'nginx' or item['type'] == 'trader':
            if 'backfill_start_minutes' not in item:
                start = last_ts
            else:
                start = schedule_start - timedelta(minutes=item['backfill_start_minutes'])
            if 'backfill_stop_minutes' in item:
                stop = schedule_start - timedelta(minutes=item['backfill_stop_minutes'])
                send_delay = 0
                throttled = False
            # real time
            else:
                realtime[thread_name] = True
                stop = None
                throttled = True
            print(f'type={item['type']}, start={start}, stop={stop}, interval_s={1/item['logs_per_second']}, send_delay={send_delay}')
            last_ts = generate(name=item['name'], generator_type=item['type'], logger=loggers[item['name']], start_timestamp=start, 
                               end_timestamp=stop, logs_per_second=item['logs_per_second'], throttled=throttled)

        elif item['type'] == 'request_errors':
            bump_version_up_per_browser(browser=item['browser'], region=item['region'])

def load_config():
    try:
        with open('config.yaml', 'r') as file:
            data = yaml.safe_load(file)
            return data
    except FileNotFoundError:
        print("Error: 'config.yaml' not found.")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
config = load_config()

def run_threads():
    threads = []
    for thread in config['threads']:
        t = Thread(target=run_schedule, args=[thread['name'], thread['schedule']], daemon=False)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

t = Thread(target=run_threads, daemon=False)
t.start()
if __name__ == "__main__":
    t.join()
