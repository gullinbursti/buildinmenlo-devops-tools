#! /usr/bin/env python

from colorlog import ColoredFormatter
from datetime import datetime, timedelta
from dateutil import rrule
import ConfigParser
import MySQLdb
import argparse
import calendar
import csv
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
    process_daily_last_365_days(cursor, now)
    process_weekly_last_12_months(cursor, now)
    process_monthly_last_12_months(cursor, now)


def process_daily_last_365_days(cursor, now):
    start = now - timedelta(days=365)
    file_name = '{}+{}+daily.csv'.format(OUTPUT_CSV_FILE_PREFIX,
                                         now.isoformat())
    LOGGER.info('Processing daily active users for the last 365 months.  '
                'Writing to CSV file: %s', os.path.abspath(file_name))
    with open(file_name, 'wb') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Day', 'Day\'s active users'])
        for current_date in rrule.rrule(rrule.DAILY, dtstart=start, until=now):
            start_string = current_date.strftime('%Y-%m-%d 00:00:00')
            end_string = current_date.strftime('%Y-%m-%d 23:59:59')
            count = get_count(cursor, start_string, end_string)
            csvwriter.writerow([current_date.strftime('%Y-%m-%d'), count])


def process_monthly_last_12_months(cursor, now):
    start = now - timedelta(days=365)
    file_name = '{}+{}+monthly.csv'.format(OUTPUT_CSV_FILE_PREFIX,
                                           now.isoformat())
    LOGGER.info('Processing monthly active users for the last 12 months.  '
                'Writing to CSV file: %s', os.path.abspath(file_name))
    with open(file_name, 'wb') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Month\'s start', 'Month\'s active users'])
        for current_date in rrule.rrule(rrule.MONTHLY, dtstart=start,
                                        until=now):
            start_string = current_date.strftime('%Y-%m-01 00:00:00')
            last_day = calendar.monthrange(current_date.year,
                                           current_date.month)[1]
            end_string = datetime(current_date.year, current_date.month,
                                  last_day).strftime('%Y-%m-%d 23:59:59')
            count = get_count(cursor, start_string, end_string)
            csvwriter.writerow([current_date.strftime('%Y-%m-01'), count])


def process_weekly_last_12_months(cursor, now):
    start = now - timedelta(days=365)
    file_name = '{}+{}+weekly.csv'.format(OUTPUT_CSV_FILE_PREFIX,
                                          now.isoformat())
    LOGGER.info('Processing weekly active users for the last 12 months.  '
                'Writing to CSV file: %s', os.path.abspath(file_name))
    with open(file_name, 'wb') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Week\'s start', 'Week\'s active users'])
        for current_date in rrule.rrule(rrule.WEEKLY, byweekday=rrule.SU,
                                        dtstart=start, until=now):
            start_string = current_date.strftime('%Y-%m-%d 00:00:00')
            end = current_date + timedelta(days=6)
            end_string = end.strftime('%Y-%m-%d 23:59:59')
            count = get_count(cursor, start_string, end_string)
            csvwriter.writerow([current_date.strftime('%Y-%m-%d'), count])


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
