#! /usr/bin/env python

import ConfigParser
import MySQLdb
import argparse
import logging
import os
import sys
from colorlog import ColoredFormatter

USER = None
PASSWORD = None
HOST = None
DATABASE = None
LOGGER = None

QUERY_INTERVAL = 45
LOG_LEVEL = logging.DEBUG
CONFIG_SECTION = 'selfieclub-readonly'
CONFIG_FILE = os.path.join(
    os.environ['HOME'], '.builtinmenlo', 'devops-tools.cnf')

PRE_REGISTRATION_NAMES = (
    'coolswagger',
    'hotbitchswaglove',
    'hotswaglover',
    'instachallenger',
    'lovepeaceswaghot',
    'picchampX',
    'snap4snap',
    'snapforsnapper',
    'snaphard',
    'snaphardyo',
    'swagluver',
    'tumblrSwag',
    'yoloswag',
    'yoosnapyoo',
    'yosnaper')


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
    installs = total_installs(cursor)
    status_updates = total_status_updates(cursor)
    with_name = total_registered_with_name(cursor)
    verified = total_users_with_validated_phone_numbers(cursor)
    pin_failed = total_pin_fails(cursor)
    no_pin_attempt = total_pin_no_try(cursor)
    clubs_created = total_clubs_create_by_new_users(cursor)
    clubs_joined = total_clubs_joined_by_new_users(cursor)
    club_invites = total_club_invites(cursor)
    emotions = total_emotions_new_users(cursor)
    # AVG. STATUS UPDATE PER USER AVG
    updates_per_user = float(status_updates) / float(installs)
    LOGGER.info('Status updates per new users [avg]: %s', updates_per_user)
    # AVG. EMOTIONS PER STATUS UPDATE AVG
    emotions_per_status = float(emotions) / float(status_updates)
    LOGGER.info('Emotions per status update [avg]: %s', emotions_per_status)
    # AVG. # OF CLUB INVITES PER USER AVG
    clubs_per_user = float(club_invites) / float(installs)
    LOGGER.info('Club invites per new user [avg]: %s', clubs_per_user)
    # AVG. # OF CLUB JOINS PER USER   AVG
    club_joins_per_user = float(clubs_joined) / float(installs)
    LOGGER.info('Club joins per new user [avg]: %s', club_joins_per_user)


# TODO
# # OF CLUBS CREATED MINUS USER CLUB  COUNT
def total_user_clubs_invites(cursor):
    result = quick_db_query(
        cursor,
        """
        TODO
        """,
        (QUERY_INTERVAL,))
    LOGGER.info('TODO [count]: %s', result)
    return result


# # OF CLUB INVITES (MEMBER OR NON MEMBER COUNT
def total_emotions_new_users(cursor):
    result = quick_db_query(
        cursor,
        """
        SELECT COUNT(1)
            FROM tblChallengeSubjectMap
            WHERE challenge_id IN
                (SELECT id FROM tblChallenges
                    WHERE added >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                    AND creator_id IN
                        (SELECT id FROM tblUsers WHERE added >= DATE_SUB(CURDATE(), INTERVAL %s DAY)))  # noqa
        """,
        (QUERY_INTERVAL, QUERY_INTERVAL))
    LOGGER.info('Total emotions from new users [count]: %s', result)
    return result


# # OF CLUB INVITES (MEMBER OR NON MEMBER COUNT
def total_club_invites(cursor):
    result = quick_db_query(
        cursor,
        """
        SELECT COUNT(1)
            FROM club_member JOIN club ON (club_id = club.id)
            WHERE invited >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                AND club.owner_id IN
                    (SELECT id FROM tblUsers WHERE added >= DATE_SUB(CURDATE(), INTERVAL %s DAY))  # noqa
        """,
        (QUERY_INTERVAL, QUERY_INTERVAL))
    LOGGER.info('Total clubs invites by new users [count]: %s', result)
    return result


# # OF CLUB JOINS COUNT
def total_clubs_joined_by_new_users(cursor):
    result = quick_db_query(
        cursor,
        """
        SELECT COUNT(1)
            FROM club_member
            WHERE joined >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                AND user_id IN
                    (SELECT id FROM tblUsers
                        WHERE added >= DATE_SUB(CURDATE(), INTERVAL %s DAY))
        """,
        (QUERY_INTERVAL, QUERY_INTERVAL))
    LOGGER.info('Total clubs joined by new users [count]: %s', result)
    return result


# # OF TOTAL CLUBS    COUNT
def total_clubs_create_by_new_users(cursor):
    result = quick_db_query(
        cursor,
        """
        SELECT COUNT(1)
            FROM club
            WHERE added >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                AND owner_id IN
                    (SELECT id FROM tblUsers
                        WHERE added >= DATE_SUB(CURDATE(), INTERVAL %s DAY))
        """,
        (QUERY_INTERVAL, QUERY_INTERVAL))
    LOGGER.info('Total clubs created by new users [count]: %s', result)
    return result


# # OF TOTAL STATUS UPDATES   COUNT
def total_status_updates(cursor):
    result = quick_db_query(
        cursor,
        """
        SELECT COUNT(1)
            FROM tblChallenges
            WHERE added >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                AND creator_id IN
                    (SELECT id FROM tblUsers
                        WHERE added >= DATE_SUB(CURDATE(), INTERVAL %s DAY))
        """,
        (QUERY_INTERVAL, QUERY_INTERVAL))
    LOGGER.info('Total status updates [count]: %s', result)
    return result


# Got a pin, but never attempted to verify
def total_pin_no_try(cursor):
    result = quick_db_query(
        cursor,
        """
        SELECT COUNT(1)
            FROM tblUserPhones
            WHERE verified = 0
                AND verify_count_total = 0
                AND created >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        """,
        (QUERY_INTERVAL,))
    LOGGER.info('Total users that did not attempt PIN verification '
                '[count]: %s',
                result)
    return result


# # OF TOTAL USERS WITH FAILED PIN    COUNT
def total_pin_fails(cursor):
    result = quick_db_query(
        cursor,
        """
        SELECT COUNT(1) FROM tblUserPhones
            WHERE verified = 0
                AND verify_count_total > 0
                AND created >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        """,
        (QUERY_INTERVAL,))
    LOGGER.info('Total users that failed pin verification [count]: %s',
                result)
    return result


# # OF TOTAL INSTALLS COUNT
def total_installs(cursor):
    result = quick_db_query(
        cursor,
        """
        SELECT COUNT(1)
            FROM tblUsers
            WHERE added >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        """,
        (QUERY_INTERVAL,))
    LOGGER.info('Total number of installs [count]: %s', result)
    return result


# # OF TOTAL REG USERS WITH USERNAME  COUNT
def total_registered_with_name(cursor):
    excluded_usernames = ' AND '.join(
        'username NOT LIKE \'%%{}%%\''.format(name)
        for name in PRE_REGISTRATION_NAMES)
    result = quick_db_query(
        cursor,
        """
        SELECT COUNT(1)
            FROM tblUsers
            WHERE ({} AND username IS NOT NULL)
                AND added >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        """.format(excluded_usernames),
        (QUERY_INTERVAL,))
    LOGGER.info('Total number of registered users with names [count]: %s',
                result)
    return result


# # OF TOTAL USERS WITH SUCESSFUL PIN COUNT
def total_users_with_validated_phone_numbers(cursor):
    result = quick_db_query(
        cursor,
        """
        SELECT COUNT(1)
            FROM tblUserPhones
            WHERE verified != 0
                AND created >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        """,
        (QUERY_INTERVAL,))
    LOGGER.info('Total users with validated numbers [count]: %s', result)
    return result


def quick_db_query(cursor, query, parameters):
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
        description='Delete user directly from database (MySQL)')
    # TODO - Add 'dryrun' switch
    return parser.parse_args()


if __name__ == "__main__":
    main()
