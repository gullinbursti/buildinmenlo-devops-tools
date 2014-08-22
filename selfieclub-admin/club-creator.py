#! /usr/bin/env python

import argparse
import csv
import MySQLdb
import sys
import logging
import re
import os
import random
import ConfigParser

USER = None
PASSWORD = None
HOST = None
DATABASE = None

NAME_PREFIX_FILE = './resources/name_prefix-us_common.txt'
NAME_PREFIX_LENGTH_LIMIT = 15
NAME_PREFIX_REGEX = '^\w+$'
NAME_SUFFIX_VALUES = '0123456789'
NAME_SUFFIX_LENGTH = 10
PHONE_REGEX = '^\+1\d{10}$'
PHONE_AREACODE_REGEX = '^\+1(\d{3})\d{7}$'
CLUB_NAME_REGEX = '^\w+$'
CONFIG_SECTION = 'selfieclub-admin'
CONFIG_FILE = os.path.join(
    os.environ['HOME'], '.builtinmenlo', 'devops-tools.cnf')
LOG_LEVEL = logging.DEBUG
LOG_FILE = 'club-creator.log'
DRYRUN_DEFAULT = True

USER_IMAGE = 'http://hotornot-avatars.s3.amazonaws.com/avatarPlaceholder'
CLUB_IMAGE = 'http://hotornot-challenges.s3.amazonaws.com/schoolClubCover'

NAME_PREFIXES = None
DATABASE_CONNECTION = None


def main():
    logging.basicConfig(level=LOG_LEVEL, filename=LOG_FILE)
    read_configuration()
    args = process_args()
    process_csv(args.csv_files, dryrun=False)


def read_configuration():
    logging.debug("Reading configuration: %s[%s]", CONFIG_FILE, CONFIG_SECTION)

    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILE)

    global USER, PASSWORD, HOST, DATABASE
    USER = config.get(CONFIG_SECTION, 'db_user')
    PASSWORD = config.get(CONFIG_SECTION, 'db_password')
    HOST = config.get(CONFIG_SECTION, 'db_host')
    DATABASE = config.get(CONFIG_SECTION, 'db_database')

    logging.info("Configuration: %s", {
        'db_user': USER,
        'db_password': 'XXXXXX',
        'db_host': HOST,
        'db_database': DATABASE})


def process_csv(files, dryrun=DRYRUN_DEFAULT):
    for file in files:
        with open(file, 'r') as input_file:
            csv_reader = csv.reader(input_file)
            for row in csv_reader:
                process_new_club(row[1], row[0], dryrun=dryrun)
            input_file.close()


def process_new_club(name, phone, dryrun=DRYRUN_DEFAULT):
    logging.debug("Processing: %s", {'name': name, 'phone': phone})
    regex = re.compile(PHONE_REGEX)
    if not regex.match(phone):
        logging.error(
            "Phone '{}' does not match regex '{}'".format(phone, PHONE_REGEX))
        return
    regex = re.compile(CLUB_NAME_REGEX)
    if not regex.match(name):
        logging.error(
            "Club name '{}' does not match regex '{}'".format(
                name, CLUB_NAME_REGEX))
        return
    new_owner = generate_dumby_user_info(phone)
    club_labels = generate_club_labels(phone)
    try:
        create_all(
            club_name=name,
            club_type='SCHOOL',
            club_description=name,
            club_img=CLUB_IMAGE,
            club_labels=club_labels,
            new_owner=new_owner,
            dryrun=dryrun)
    except CreateAllException as detail:
        logging.error("Failed to create - {}".format(detail))


def generate_club_labels(phone):
    """
    Note that the return value has labels in order of importance. most
    important first.  This is important when looking for duplicate
    clubs.
    """
    match = re.match(PHONE_AREACODE_REGEX, phone)
    areacode = match.group(1)
    club_labels = (
        'areacode-{}-highschool'.format(areacode),
        'areacode-{}'.format(areacode),
        'highschool')
    return club_labels


def create_all(club_name, club_type, club_description, club_img,
               club_labels, new_owner, dryrun=DRYRUN_DEFAULT):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        if club_exists(cursor, club_name, club_labels[0]):
            raise CreateAllException(
                "Club '{}' with label '{}' already exists.".format(
                    club_name, club_labels[0]))
        owner_id = create_owner(cursor, new_owner['username'],
                                new_owner['img_url'], new_owner['email'])
        club_id = create_club(cursor, club_name, club_type, owner_id,
                              club_description, club_img)
        label_club(cursor, club_id, club_labels)
        if not dryrun:
            connection.commit()
        else:
            connection.rollback()
            logging.debug(
                "In 'dryrun' mode, rolling back on creating club '%s'",
                club_name)
    except MySQLdb.IntegrityError, e:
        if connection:
            connection.rollback()
        raise CreateAllException(e)
    except MySQLdb.ProgrammingError, e:
        if connection:
            connection.rollback()
        raise CreateAllException(e)
    except MySQLdb.OperationalError, e:
        if connection:
            connection.rollback()
        raise CreateAllException(e)
    else:
        logging.info(
            "Created club:  %s",
            {'club_id': club_id,
             'club_name': club_name,
             'club_type': club_type,
             'owner_id': owner_id,
             'owner_name': new_owner['username']})
    finally:
        if cursor:
            cursor.close()


def club_exists(cursor, name, club_label):
    cursor.execute(
        """
        SELECT COUNT(1) FROM club JOIN tbl_club_label_club ON club.id = club_id
            WHERE
                name = %s
                AND clublabel_id = (
                    SELECT id FROM tbl_club_label WHERE name = %s);
        """,
        (name, club_label,))
    result = cursor.fetchone()
    return result[0] != 0


def label_club(cursor, club_id, labels):
    for club_label in labels:
        cursor.execute(
            "SELECT id FROM tbl_club_label WHERE name = %s", (club_label,))
        result = cursor.fetchone()
        if not result:
            clublabel_id = create_club_label(cursor, club_label, club_label)
        else:
            clublabel_id = result[0]
        create_club_label_map(cursor, clublabel_id, club_id)


def create_club_label_map(cursor, clublabel_id, club_id):
    cursor.execute(
        """
        INSERT INTO tbl_club_label_club
            (clublabel_id, club_id)
            VALUE (%s, %s);
        """,
        (clublabel_id, club_id))


def create_club_label(cursor, name, description):
    cursor.execute(
        """
        INSERT INTO tbl_club_label
            (name, description, updated, created)
            VALUE (%s, %s, NOW(), NOW());
        """,
        (name, description))
    return cursor.lastrowid


def create_club(cursor, name, club_type, owner_id, description, img):
    cursor.execute(
        """
        INSERT INTO `club`
            (`name`, `club_type_id`, `owner_id`, `description`, `img`,
                `added`)
            VALUE (%s, (SELECT id FROM tblClubTypeEnum WHERE club_type = %s),
                   %s, %s, %s, NOW());
        """,
        (name, club_type, owner_id, description, img))
    return cursor.lastrowid


def create_owner(cursor, username, img_url, email):
    cursor.execute(
        """
        INSERT INTO `tblUsers`
            (`username`, `img_url`, `email`, `sms_verified`, `fb_id`,
                `bio`, `website`, `points`, `added`)
            VALUE (%s, %s, %s, %s, %s, %s, %s, %s, NOW());
        """,
        (username, img_url, email, 1, '', '', '', 0))
    return cursor.lastrowid


def generate_dumby_user_info(phone):
    name = generate_unused_username()
    return {
        'username': name,
        'img_url': USER_IMAGE,
        'email': phone}


def generate_unused_username():
    cursor = get_db_connection().cursor()
    while True:
        new_name = generate_username()
        result = cursor.execute(
            "SELECT COUNT(1) FROM `tblUsers` WHERE username=%s",
            (new_name,))
        result = cursor.fetchone()

        if result[0] == 0:
            break
        else:
            logging.warn(
                "User name '{}' already exists, retrying".format(new_name))
    cursor.close()
    return new_name


def generate_username():
    if NAME_PREFIXES is None:
        load_name_prefixes()

    name = random.choice(NAME_PREFIXES)
    suffix = ''.join(
        random.choice(NAME_SUFFIX_VALUES)
        for i in range(NAME_SUFFIX_LENGTH))
    return name + suffix


def load_name_prefixes():
    global NAME_PREFIXES
    NAME_PREFIXES = []
    regex = re.compile(NAME_PREFIX_REGEX)
    with open(NAME_PREFIX_FILE, 'r') as name_prefixes:
        for name_prefix in name_prefixes:
            name_prefix = name_prefix.lower().strip()

            if len(name_prefix) > NAME_PREFIX_LENGTH_LIMIT:
                logging.critical(
                    "Name prefix '{}' is too long, greater than {}".format(
                        name_prefix, NAME_PREFIX_LENGTH_LIMIT))
                sys.exit(1)

            if not regex.match(name_prefix):
                logging.critical(
                    "Name prefix '{}' does not match regex '{}'".format(
                        name_prefix, NAME_PREFIX_REGEX))
                sys.exit(1)

            NAME_PREFIXES.append(name_prefix)


def get_db_connection():
    global DATABASE_CONNECTION
    if DATABASE_CONNECTION is None:
        logging.info("Connecting to database: {}".format(HOST))
        DATABASE_CONNECTION = MySQLdb.connect(
            host=HOST,
            db=DATABASE,
            user=USER,
            passwd=PASSWORD)
    return DATABASE_CONNECTION


class CreateAllException(Exception):
    pass


def process_args():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument(
        'csv_files',
        metavar='CSV_FILES',
        nargs='+',
        help='CSV files to process')
    # TODO - Add 'dryrun' switch
    return parser.parse_args()


if __name__ == "__main__":
    main()
