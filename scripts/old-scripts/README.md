Summary
=======

This directory contains old scripts that were once on `api.letsvolley.com`.


elasticsearch-backup.sh
-----------------------


The following scripts were used in conjunction with `elasticsearch/backup.sh`:

- `elasticsearch/backup.sh` - actual backup script.
- `elasticsearch/es-flush-disable.sh` - `backup.sh` support script.
- `elasticsearch/es-flush.sh` - `backup.sh` support script.
- `elasticsearch/print-settings.sh` - `backup.sh` support script.

Old cron job on `api.letsvolley.com` was:

```
15 */4 * * * /bin/sh /home/volley/admin/bin/elasticsearch/backup.sh > backup.log 2>&1 &
```


queue_jobs.php
--------------

Old cron job on `api.letsvolley.com` was:

```
* * * * * /usr/bin/php /home/volley/admin/bin/gearman/admin/queue_jobs.php  > /tmp/cron.log 2>&1
```

Root Crontab from api.letsvolley.com
====================================

For safe keeping, the crontab from `api.letsvolley.com`:

```
#----
# UNKNOWN
#* * * * * /usr/bin/php -r 'require_once "vendor/autoload.php";BIM_App_Challenges::checkVolleyImagesFromLastXSeconds();' > /tmp/volley_check.log 2>&1
#* * * * * /usr/bin/php /home/volley/admin/bin/gearman/admin/queue_jobs.php  > /tmp/cron.log 2>&1
#*/14 * * * * /usr/bin/mysql -u root -e "update tblUsers set total_challenges=-1" hotornot-dev; (echo flush_all ; /bin/sleep 0.1) | /bin/nc 127.0.0.1 11211 > /tmp/selfie_clear_count.log 2>&1

#----
# Move to elastic00.prod
#15 */4 * * * /bin/sh /home/volley/admin/bin/elasticsearch/backup.sh > backup.log 2>&1 &

#----
# No longer needed
#0 7 * * * /bin/sh /home/shane/mysqlbackup_queue.sh
#0 8 * * * /bin/sh /home/shane/mysqlbackup_growth.sh
#0 */4 * * * /bin/sh /home/shane/mysqlbackup.sh

#----
# Already turned off - OLD
##*/2 * * * * /usr/bin/php -r 'require_once "vendor/autoload.php"; BIM_Growth_Webstagram_Routines::queueFollowAdLikers("AblesMi307");' > /tmp/queueFollowAdLikers.log 2>&1
```

