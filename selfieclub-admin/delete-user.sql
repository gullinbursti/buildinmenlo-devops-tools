DELETE FROM `tblChallengeVotes` WHERE `user_id` = 195020;
DELETE FROM `tblChallenges` WHERE `creator_id` = 195020;
DELETE FROM `tblUserPhones` WHERE `user_id` = 195020;
DELETE FROM `club_member` WHERE `user_id` = 195020;
DELETE FROM `tblFlaggedUserApprovals` WHERE `user_id` = 195020;
DELETE from `club_member` WHERE `club_id` IN (SELECT `id` FROM `club` WHERE `owner_id` = 195020);
DELETE FROM `club` WHERE `owner_id` = 195020;
DELETE FROM `tblUsers` WHERE `id` = 195020;
