from mock import Mock, call, patch
import re


class TestDeleteFromDb(object):
    # pylint: disable=no-self-use

    @patch('bimadmin.selfieclub.deleteuser.LOGGER', Mock())
    def test_commits_on_nodryrun(self):
        """
        On dryrun == False, make sure that `delete_from_db` calls commit().
        """
        # *arrange*
        from bimadmin.selfieclub import deleteuser
        connection = Mock()
        # *act*
        deleteuser.delete_from_db(connection, 876876, 'ksdjfhsk', False)
        # *assert*
        connection.commit.assert_called_with()

    @patch('bimadmin.selfieclub.deleteuser.LOGGER', Mock())
    def test_rolls_back_on_dryrun(self):
        """
        On dryrun, make sure that `delete_from_db`:
            - calls rollback()
            - never calls commit()
        """
        # *arrange*
        from bimadmin.selfieclub import deleteuser
        connection = Mock()
        # *act*
        deleteuser.delete_from_db(connection, 876876, 'ksdjfhsk', True)
        # *assert*
        connection.rollback.assert_called_with()
        assert connection.commit.called == 0

    @patch('bimadmin.selfieclub.deleteuser.LOGGER', Mock())
    def test_makes_expected_delete_calls(self):
        """
        Make sure that `delete_from_db` actually makes the expected DB calls.

        Note that this test likely goes beyond what should typically be done in
        a unittest.  It is only here given the nature of deleting a user.
        """
        # *arrange*
        from bimadmin.selfieclub import deleteuser
        user_id = 92387429
        expected = [
            call(r'DELETE FROM club\b', (user_id,)),
            call(r'DELETE FROM club_member\b', (user_id,)),
            call(r'DELETE FROM moji_invite\b', (user_id,)),
            call(r'DELETE FROM tblChallengeParticipants\b', (user_id,)),
            call(r'DELETE FROM tblChallengeVotes\b', (user_id,)),
            call(r'DELETE FROM tblChallenges\b', (user_id,)),
            call(r'DELETE FROM tblFlaggedUserApprovals\b', (user_id,)),
            call(r'DELETE FROM tblUserPhones\b', (user_id,)),
            call(r'DELETE FROM tblUsers\b', (user_id,)),
            call(r'DELETE FROM tbl_club_label_club\b', (user_id,)),
            call(r'DELETE FROM tbl_status_update_emotion\b', (user_id,))]
        cursor = Mock()
        connection = Mock()
        connection.cursor.return_value = cursor
        # *act*
        deleteuser.delete_from_db(connection, user_id, 'ksdjfhsk', True)
        # *assert*
        TestDeleteFromDb.assert_expected_db_calls(cursor.execute.mock_calls,
                                                  expected)

    @staticmethod
    def assert_expected_db_calls(actual_calls, expected_calls):
        actual_data = [x[1] for x in actual_calls]
        expected_data = [x[1] for x in expected_calls]
        for expected_index, expected in enumerate(expected_data):
            regex = re.compile(expected[0])
            to_delete = []
            for index, actual in enumerate(actual_data):
                match = regex.search(actual[0])
                if match and actual[1] == expected[1]:
                    to_delete.append(index)
            assert \
                len(to_delete) >= 1, \
                'Not found - {}'.format(expected_data[expected_index])
            to_delete.sort(reverse=True)
            for index in to_delete:
                del actual_data[index]
        assert len(actual_data) == 0, 'Extra calls - {}'.format(actual_data)
