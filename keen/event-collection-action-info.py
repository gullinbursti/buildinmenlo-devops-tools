#! /usr/bin/env python

from colorlog import ColoredFormatter
from keen.client import KeenClient
import ConfigParser
import csv
import json
import logging
import os
import requests
import sys


KEEN_PROJECT_ID = None
KEEN_WRITE_KEY = None
KEEN_READ_KEY = None
KEEN_MASTER_KEY = None
KEEN_BASE_URL = None
LOGGER = None

KEEN_TIME_FRAME = 'previous_45_days'
OUTPUT_CSV_FILE = 'keen-event-collection-action-info.csv'
LOG_LEVEL = logging.DEBUG
CONFIG_SECTION = 'keen'
CONFIG_FILE = os.path.join(
    os.environ['HOME'], '.builtinmenlo', 'devops-tools.cnf')


def main():
    global LOGGER
    LOGGER = get_logger()
    read_configuration()

    LOGGER.info('Writing CSV to: %s', os.path.abspath(OUTPUT_CSV_FILE))
    with open(OUTPUT_CSV_FILE, 'wb') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow([
            'Event collection name',
            'Action name',
            'Event action count',
            'Oldest event',
            'Newest event'])
        for event_action in next_action():
            action_array = action_to_array(event_action)
            LOGGER.info('Processed: %s', action_array)
            csvwriter.writerow(action_array)


def action_to_array(collection):
    return [
        collection['event_name'],
        collection['action'],
        collection['count'],
        collection['oldest'],
        collection['newest']]


def next_action():
    event_collections = get_event_collections()
    keen_client = get_keen_client()
    for collection in event_collections:
        name = collection['name']
        for action in keen_client.select_unique(event_collection=name,
                                                target_property='action'):
            yield get_event_action_data(keen_client, collection, action)


def get_event_action_data(keen_client, collection, action):
    name = collection['name']
    filters = [{
        'property_name': 'action',
        'operator': 'eq',
        'property_value': action}]
    count = keen_client.count(
        event_collection=name,
        timeframe=KEEN_TIME_FRAME,
        filters=filters)
    oldest = keen_client.minimum(
        event_collection=name,
        target_property='keen.timestamp',
        timeframe=KEEN_TIME_FRAME,
        filters=filters)
    newest = keen_client.maximum(
        event_collection=name,
        target_property='keen.timestamp',
        timeframe=KEEN_TIME_FRAME,
        filters=filters)
    return {
        'event_name': name,
        'action': action,
        'count': count,
        'oldest': oldest,
        'newest': newest}


def get_event_collections():
    url = '{}/projects/{}/events'.format(KEEN_BASE_URL, KEEN_PROJECT_ID)
    parameters = {'api_key': KEEN_MASTER_KEY}
    response = requests.get(url, params=parameters)
    return json.loads(response.text)


def get_keen_client():
    return KeenClient(
        project_id=KEEN_PROJECT_ID,
        write_key=KEEN_WRITE_KEY,
        read_key=KEEN_READ_KEY)


def to_json(data):
    return json.dumps(data, indent=4, sort_keys=True)


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
    global KEEN_PROJECT_ID, KEEN_WRITE_KEY, KEEN_READ_KEY, KEEN_MASTER_KEY, \
        KEEN_BASE_URL
    KEEN_PROJECT_ID = config.get(CONFIG_SECTION, 'project_id')
    KEEN_WRITE_KEY = config.get(CONFIG_SECTION, 'write_key')
    KEEN_READ_KEY = config.get(CONFIG_SECTION, 'read_key')
    KEEN_MASTER_KEY = config.get(CONFIG_SECTION, 'master_key')
    KEEN_BASE_URL = config.get(CONFIG_SECTION, 'base_url')


if __name__ == "__main__":
    main()
