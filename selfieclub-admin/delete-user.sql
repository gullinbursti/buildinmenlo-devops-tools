DELETE FROM `tblChallengeVotes` WHERE `user_id` = 192045;
DELETE FROM `tbl_status_update_emotion` WHERE `status_update_id` IN (SELECT `id` FROM `tblChallenges` WHERE `creator_id` =192045);
DELETE FROM `tblChallenges` WHERE `creator_id` = 192045;
DELETE FROM `tblUserPhones` WHERE `user_id` = 192045;
DELETE FROM `club_member` WHERE `user_id` = 192045;
DELETE FROM `tblFlaggedUserApprovals` WHERE `user_id` = 192045;
DELETE from `club_member` WHERE `club_id` IN (SELECT `id` FROM `club` WHERE `owner_id` = 192045);
DELETE FROM `club` WHERE `owner_id` = 192045;
DELETE FROM `moji_invite` WHERE `member_id` = 192045;
DELETE FROM `tblUsers` WHERE `id` = 192045;


