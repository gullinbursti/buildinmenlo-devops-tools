#! /usr/bin/env python

import MySQLdb
import sys

USER = 
PASSWORD = 
HOST = 
DATABASE = 'hotornot-dev'


def delete_user(user_id):
    connection = MySQLdb.connect(
        host=HOST,
        db=DATABASE,
        user=USER,
        passwd=PASSWORD)
    cursor = connection.cursor()

    cursor.execute(
        'DELETE FROM `tblChallengeVotes` WHERE `user_id` = %s',
        (user_id,))
    print("Deleted from tblChallengeVotes: {}".format(cursor.rowcount))

    cursor.execute(
        'DELETE FROM `tblChallenges` WHERE `creator_id` = %s',
        (user_id,))
    print("Deleted from tblChallenges: {}".format(cursor.rowcount))

    cursor.execute(
        'DELETE FROM `tblUserPhones` WHERE `user_id` = %s',
        (user_id,))
    print("Deleted from tblUserPhones: {}".format(cursor.rowcount))

    cursor.execute(
        'DELETE FROM `club_member` WHERE `user_id` = %s',
        (user_id,))
    print("Deleted from club_member: {}".format(cursor.rowcount))

    cursor.execute(
        'DELETE FROM `tblFlaggedUserApprovals` WHERE `user_id` = %s',
        (user_id,))
    print("Deleted from tblFlaggedUserApprovals: {}".format(cursor.rowcount))

    cursor.execute(
        'DELETE from `club_member` WHERE `club_id` IN (SELECT `id` FROM `club` WHERE `owner_id` = %s)',
        (user_id,))
    print("Deleted from club_member: {}".format(cursor.rowcount))

    cursor.execute(
        'DELETE FROM `club` WHERE `owner_id` = %s',
        (user_id,))
    print("Deleted from club: {}".format(cursor.rowcount))

    cursor.execute(
        'DELETE FROM `tblUsers` WHERE `id` = %s',
        (user_id,))
    print("Deleted from tblUsers: {}".format(cursor.rowcount))

    connection.commit()


def main(argv):
    for user_id in argv:
        delete_user(user_id)

if __name__ == "__main__":
    main(sys.argv[1:])
