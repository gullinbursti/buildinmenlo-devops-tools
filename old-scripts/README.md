Summary
=======

This directory contains old scripts that were once on `api.letsvolley.com`.


elasticsearch-backup.sh
-----------------------

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

