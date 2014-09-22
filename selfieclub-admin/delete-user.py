#! /usr/bin/env python

import ConfigParser
import MySQLdb
import argparse
import logging
import os
import sys
from colorlog import ColoredFormatter
import re

USER = None
PASSWORD = None
HOST = None
DATABASE = None
LOGGER = None

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
    process(args.is_userids, args.user_keys, args.is_dryrun)


def process(is_userids, keys, is_dryrun):
    connection = MySQLdb.connect(
        host=HOST,
        db=DATABASE,
        user=USER,
        passwd=PASSWORD)
    if is_userids:
        users = get_user_by_id(connection, keys)
    else:
        users = get_user_by_name(connection, keys)
    LOGGER.info("Attempting to delete: %s", users)
    delete_all(connection, users, is_dryrun)
    connection.close()


def delete_all(connection, users, is_dryrun):
    for user in users:
        delete_user(connection, user['id'], user['name'], is_dryrun)


def delete_user(connection, user_id, username, is_dryrun):
    cursor = connection.cursor()
    LOGGER.info("Preparing to delete '%s' (%s):", username, user_id)
    delete(
        cursor,
        'DELETE FROM tblChallengeParticipants WHERE user_id = %s',
        (user_id,),
        'tblChallengeParticipants')
    delete(
        cursor,
        'DELETE FROM tblChallengeVotes WHERE user_id = %s',
        (user_id,), 'tblChallengeVotes')
    delete(
        cursor,
        """
        DELETE FROM tbl_status_update_emotion
            WHERE status_update_id IN (
                SELECT id FROM tblChallenges WHERE creator_id = %s)
        """,
        (user_id,),
        'tbl_status_update_emotion')
    delete(
        cursor,
        'DELETE FROM tblFlaggedUserApprovals WHERE user_id = %s',
        (user_id,),
        'tblFlaggedUserApprovals.user_id')
    delete(
        cursor,
        """
        DELETE FROM tblFlaggedUserApprovals
            WHERE challenge_id IN (
                SELECT tblChallenges.id
                    FROM tblChallenges WHERE tblChallenges.creator_id = %s)
        """,
        (user_id,),
        'tblFlaggedUserApprovals JOIN tblChallenges')
    delete(
        cursor,
        'DELETE FROM tblChallenges WHERE creator_id = %s',
        (user_id,),
        'tblChallenges')
    delete(
        cursor,
        'DELETE FROM tblUserPhones WHERE user_id = %s',
        (user_id,),
        'tblUserPhones')
    delete(
        cursor,
        'DELETE FROM club_member WHERE user_id = %s',
        (user_id,),
        'club_member')
    delete(
        cursor,
        """
        DELETE from club_member
            WHERE club_id IN (
                SELECT club.id FROM club WHERE club.owner_id = %s)
        """,
        (user_id,),
        'club_member')
    delete(
        cursor,
        """
        DELETE FROM tbl_club_label_club
            WHERE club_id IN (
                SELECT club.id FROM club WHERE club.owner_id = %s)
        """,
        (user_id,),
        'tbl_club_label_club')
    delete(
        cursor,
        'DELETE FROM club WHERE owner_id = %s',
        (user_id,),
        'club')
    delete(
        cursor,
        'DELETE FROM moji_invite WHERE member_id = %s',
        (user_id,),
        'moji_invite')
    delete(
        cursor,
        'DELETE FROM tblUsers WHERE id = %s',
        (user_id,),
        'tblUsers')
    if not is_dryrun:
        connection.commit()
    else:
        connection.rollback()
        LOGGER.warn("In *dryrun* mode.  Not deleting user: '%s' (%s)",
                    username, user_id)


def delete(cursor, statement, parameters, main_table):
    cursor.execute(statement, parameters)
    LOGGER.info("    Deleting from '%s': %s", main_table, cursor.rowcount)


def get_user_by_id(connection, user_ids):
    cursor = connection.cursor()
    data = []
    for id in user_ids:
        id = long(id)
        cursor.execute("SELECT username FROM tblUsers WHERE id = %s", (id,))
        result = cursor.fetchone()
        if not result:
            LOGGER.error("User with id '%s' does not exist.", id)
            continue
        data.append({'id': id, 'name': result[0]})
    cursor.close()
    return data


def get_user_by_name(connection, user_names):
    cursor = connection.cursor()
    data = []
    for name in user_names:
        cursor.execute("SELECT id FROM tblUsers WHERE username = %s",
                       (name,))
        result = cursor.fetchone()
        if not result:
            LOGGER.error("User with name '%s' does not exist.", name)
            continue
        data.append({'id': result[0], 'name': name})
    cursor.close()
    return data


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
    return re.sub('\..*', '.log', file_name)


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


def get_configuration_files(environment):
    return ['.'.join([file, CONFIG_FILE_EXTENTION]) for file in (
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
    parser.add_argument(
        '--usernames',
        action='store_const',
        dest='is_userids',
        default=True,
        const=False,
        help='Set if KEY(s) are usernames, otherwise user_ids are expected.')
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
    parser.add_argument(
        'user_keys',
        metavar='KEY',
        nargs='+',
        help='Either the user names, or ID, but never both.')
    # TODO - Add 'dryrun' switch
    return parser.parse_args()


if __name__ == "__main__":
    main()
