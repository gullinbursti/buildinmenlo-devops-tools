DELETE FROM `tblChallengeVotes` WHERE `user_id` = 152805;
DELETE FROM `tblChallenges` WHERE `creator_id` = 152805;
DELETE FROM `tblUserPhones` WHERE `user_id` = 152805;
DELETE FROM `club_member` WHERE `user_id` = 152805;
DELETE FROM `tblFlaggedUserApprovals` WHERE `user_id` = 152805;
DELETE from `club_member` WHERE `club_id` IN (SELECT `id` FROM `club` WHERE `owner_id` = 152805);
DELETE FROM `club` WHERE `owner_id` = 152805;
DELETE FROM `tblUsers` WHERE `id` = 152805;
