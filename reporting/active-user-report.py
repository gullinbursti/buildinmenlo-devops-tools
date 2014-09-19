#! /usr/bin/env python

from colorlog import ColoredFormatter
from datetime import datetime, timedelta
from dateutil import rrule
from dateutil.relativedelta import relativedelta
import ConfigParser
import MySQLdb
import argparse
import calendar
import logging
import os
import sys

USER = None
PASSWORD = None
HOST = None
DATABASE = None
LOGGER = None

LOG_LEVEL = logging.DEBUG
OUTPUT_CSV_FILE_SUMMARY_PREFIX = 'active-user-report-summary'
OUTPUT_CSV_FILE_PREFIX = 'active-user-report'
CONFIG_SECTION = 'selfieclub-readonly'
CONFIG_FILE = os.path.join(
    os.environ['HOME'], '.builtinmenlo', 'devops-tools.cnf')


def main():
    global LOGGER
    LOGGER = get_logger()
    read_configuration()
    process()


def process():
    connection = MySQLdb.connect(
        host=HOST,
        db=DATABASE,
        user=USER,
        passwd=PASSWORD)
    cursor = connection.cursor()
    now = datetime.utcnow()
    process_yesterday(cursor, now)
    process_24_hours(cursor, now)
    process_last_week(cursor, now)
    process_7_days(cursor, now)
    process_last_month(cursor, now)
    process_last_30_days(cursor, now)


def process_yesterday(cursor, now):
    yesterday = now - timedelta(days=1)
    start_string = yesterday.strftime('%Y-%m-%d 00:00:00')
    end_string = yesterday.strftime('%Y-%m-%d 23:59:59')
    count = get_count(cursor, start_string, end_string)
    LOGGER.info('Yesterday\'s active users (%s through %s): %s',
                start_string, end_string, count)
    return count


def process_24_hours(cursor, now):
    start = now - timedelta(hours=24)
    start_string = start.strftime('%Y-%m-%d %H:%M:%S')
    end_string = now.strftime('%Y-%m-%d %H:%M:%S')
    count = get_count(cursor, start_string, end_string)
    LOGGER.info('Active users in the last 24 hours (%s through %s): %s',
                start_string, end_string, count)
    return count


def process_last_week(cursor, now):
    current_date = now + relativedelta(weekday=rrule.SU(-2))
    start_string = current_date.strftime('%Y-%m-%d 00:00:00')
    end = current_date + timedelta(days=6)
    end_string = end.strftime('%Y-%m-%d 23:59:59')
    count = get_count(cursor, start_string, end_string)
    LOGGER.info('Active users last week (%s through %s): %s',
                start_string, end_string, count)
    return count


def process_7_days(cursor, now):
    current_date = now - timedelta(days=7)
    start_string = current_date.strftime('%Y-%m-%d %H:%M:%S')
    end_string = now.strftime('%Y-%m-%d %H:%M:%S')
    count = get_count(cursor, start_string, end_string)
    LOGGER.info('Active users last 7 days (%s through %s): %s',
                start_string, end_string, count)
    return count


def process_last_month(cursor, now):
    current_date = now + relativedelta(months=-1)
    start_string = current_date.strftime('%Y-%m-01 00:00:00')
    last_day = calendar.monthrange(current_date.year, current_date.month)[1]
    end_string = datetime(current_date.year, current_date.month, last_day) \
        .strftime('%Y-%m-%d 23:59:59')
    count = get_count(cursor, start_string, end_string)
    LOGGER.info('Active users last month (%s through %s): %s',
                start_string, end_string, count)
    return count


def process_last_30_days(cursor, now):
    current_date = now - timedelta(days=30)
    start_string = current_date.strftime('%Y-%m-%d %H:%M:%S')
    end_string = now.strftime('%Y-%m-%d %H:%M:%S')
    count = get_count(cursor, start_string, end_string)
    LOGGER.info('Active users last 30 days (%s through %s): %s',
                start_string, end_string, count)
    return count


def get_count(cursor, start, end):
    return quick_db_query(
        cursor,
        "SELECT COUNT(1) FROM tblUsers WHERE last_login BETWEEN %s AND %s",
        (start, end))


def quick_db_query(cursor, query, parameters=None):
    cursor.execute(query, parameters)
    result = cursor.fetchone()
    if not result:
        LOGGER.error("Query failed: %s", query)
        sys.exit(1)
    return result[0]


def get_logger():
    name = os.path.basename(__file__)
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    handler_stdout = logging.StreamHandler(sys.stdout)
    handler_stdout.setFormatter(ColoredFormatter(
        "%(log_color)s%(levelname)-8s %(message)s%(reset)s"))
    handler_stdout.setLevel(LOG_LEVEL)
    logger.addHandler(handler_stdout)

    return logger


def read_configuration():
    LOGGER.debug("Reading configuration: %s[%s]", CONFIG_FILE, CONFIG_SECTION)
    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILE)
    global USER, PASSWORD, HOST, DATABASE
    USER = config.get(CONFIG_SECTION, 'db_user')
    PASSWORD = config.get(CONFIG_SECTION, 'db_password')
    HOST = config.get(CONFIG_SECTION, 'db_host')
    DATABASE = config.get(CONFIG_SECTION, 'db_database')
    LOGGER.info("Configuration: %s", {
        'db_user': USER,
        'db_password': 'XXXXXX',
        'db_host': HOST,
        'db_database': DATABASE})


def process_args():
    parser = argparse.ArgumentParser(
        description='Generate active users reports on daily, weekly, and '
                    'monthly intervals')
    return parser.parse_args()


if __name__ == "__main__":
    main()
