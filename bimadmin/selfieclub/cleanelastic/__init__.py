#! /usr/bin/env python
# pylint: disable=global-statement
# TODO - eliminate:
#    - global-statement

from colorlog import ColoredFormatter
from elasticsearch import Elasticsearch
import ConfigParser
import MySQLdb
import argparse
import logging
import os
import re
import sys

USER = None
PASSWORD = None
HOST = None
DATABASE = None
LOGGER = None
ELASTICSEARCH_HOST = None
ELASTICSEARCH_PORT = None

LOG_LEVEL = logging.DEBUG
CONFIG_SECTION = 'selfieclub-admin'

CONFIG_FILE_GLOBAL_BASE = os.path.join(
    '/etc', 'builtinmenlo', 'devops-tools')
CONFIG_FILE_USER_BASE = os.path.join(
    os.environ['HOME'], '.builtinmenlo', 'devops-tools')
CONFIG_FILE_EXTENTION = 'cnf'


def main():
    global LOGGER
    args = process_args()
    LOGGER = get_logger(args.log_file)
    LOGGER.info("Logging to file: %s", os.path.abspath(args.log_file))
    load_configuration(get_configuration_files(args.environment))
    process(args.is_dryrun)


def process(is_dryrun):
    connection = MySQLdb.connect(
        host=HOST,
        db=DATABASE,
        user=USER,
        passwd=PASSWORD)
    clean_elasticsearch(connection, is_dryrun)
    connection.close()


def clean_elasticsearch(connection, is_dryrun):
    # indexes = ['contact_lists', 'social']
    indexes = ['social']
    query = {
        'from': 0, 'size': 50,
        'query': {
            'match_all': {}
        }
    }
    elastic = Elasticsearch([
        {'host': ELASTICSEARCH_HOST,
         'port': ELASTICSEARCH_PORT}])
    cursor = connection.cursor()
    query_response = elastic.search(index=indexes, body=query)
    records = query_response['hits']['hits']
    for record in records:
        # If social/friends, id is source_target
        user_id = record['_source']['target']
        es_username = record['_source']['target_data']['username']
        statement = 'SELECT username FROM tblUsers WHERE id = %s'
        cursor.execute(statement, [user_id])
        rows = cursor.fetchall()
        db_username = None
        for row in rows:
            db_username = row[0]
        if not db_username or (es_username != db_username):
            delete_from_elasticsearch(user_id, es_username, is_dryrun)


def delete_from_elasticsearch(user_id, username, is_dryrun):
    indexes = ['contact_lists', 'social']
    query = {
        'from': 0, 'size': 50,
        'query': {
            'term': {'id': user_id}
        },
        'fields': ['_id', '_index', '_type']
    }
    elastic = Elasticsearch([
        {'host': ELASTICSEARCH_HOST,
         'port': ELASTICSEARCH_PORT}])
    query_response = elastic.search(index=indexes, body=query)
    records = query_response['hits']['hits']
    LOGGER.info(
        'Deleting the following records from Elasticsearch pertaining to '
        'user \'%s\' (%s):', username, user_id)
    for record in records:
        delete_response = {}
        if not is_dryrun:
            delete_response = elastic.delete(
                index=record['_index'],
                doc_type=record['_type'],
                id=record['_id'])
        else:
            delete_response['ok'] = '*dryrun*'
        LOGGER.info('    Deleted from Elasticsearch /%s/%s/%s: %s',
                    record['_index'], record['_type'], record['_id'],
                    delete_response['ok'])
    if is_dryrun:
        LOGGER.warn(
            'In *dryrun* mode.  Not deleting user from Elasticsearch: %s (%s)',
            username, user_id)


def get_logger(log_file):
    name = os.path.basename(__file__)
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    handler_stdout = logging.StreamHandler(sys.stdout)
    handler_stdout.setFormatter(ColoredFormatter(
        "%(log_color)s%(levelname)-8s %(message)s%(reset)s"))
    handler_stdout.setLevel(LOG_LEVEL)
    logger.addHandler(handler_stdout)

    handler_file = logging.FileHandler(log_file)
    handler_file.setFormatter(logging.Formatter(
        "%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s"))
    handler_file.setLevel(LOG_LEVEL)
    logger.addHandler(handler_file)

    return logger


def default_log():
    file_name = os.path.basename(__file__)
    return re.sub(r'\..*', '.log', file_name)


def load_configuration(configuration_files):
    LOGGER.debug(
        'Attempting to read configuration section [%s] from the following '
        'file(s), in order: %s',
        CONFIG_SECTION,
        configuration_files)
    config = ConfigParser.ConfigParser()
    read_files = config.read(configuration_files)
    if read_files:
        LOGGER.info(
            'Loaded the [%s] section from the following file(s): %s',
            CONFIG_SECTION,
            read_files)
    else:
        LOGGER.error(
            'Failed to find any of the following configuration '
            'files: %s',
            configuration_files)
        sys.exit(1)
    global USER, PASSWORD, HOST, DATABASE, ELASTICSEARCH_HOST, \
        ELASTICSEARCH_PORT
    USER = config.get(CONFIG_SECTION, 'db_user')
    PASSWORD = config.get(CONFIG_SECTION, 'db_password')
    HOST = config.get(CONFIG_SECTION, 'db_host')
    DATABASE = config.get(CONFIG_SECTION, 'db_database')
    ELASTICSEARCH_HOST = config.get(CONFIG_SECTION, 'elasticsearch_host')
    ELASTICSEARCH_PORT = config.get(CONFIG_SECTION, 'elasticsearch_port')

    LOGGER.info("Configuration: %s", {
        'db_user': USER,
        'db_password': 'XXXXXX',
        'db_host': HOST,
        'db_database': DATABASE,
        'elasticsearch_host': ELASTICSEARCH_HOST,
        'elasticsearch_port': ELASTICSEARCH_PORT})


def get_configuration_files(environment):
    return ['.'.join([file_base, CONFIG_FILE_EXTENTION]) for file_base in (
        '-'.join([CONFIG_FILE_GLOBAL_BASE, environment]),
        '-'.join([CONFIG_FILE_USER_BASE, environment]))]


def process_args():
    parser = argparse.ArgumentParser(
        description='Delete user directly from database (MySQL).')
    parser.add_argument(
        '--log',
        nargs='?',
        dest='log_file',
        default=default_log(),
        help='Use if you do not want changes committed to the database.')
    parser.add_argument(
        '--dryrun',
        action='store_const',
        dest='is_dryrun',
        default=False,
        const=True,
        help='Use if you do not want changes committed to the database.')
    environment_group = parser.add_mutually_exclusive_group(
        required=True)
    environment_group.add_argument(
        '--devint',
        action='store_const',
        dest='environment',
        const='devint',
        help='Perform on production environment.')
    environment_group.add_argument(
        '--prod',
        action='store_const',
        dest='environment',
        const='prod',
        help='Perform on dev integration environment.')
    environment_group.add_argument(
        '--local_dev',
        action='store_const',
        dest='environment',
        const='local_dev',
        help='Perform on a developer\'s local environment.')
    return parser.parse_args()
