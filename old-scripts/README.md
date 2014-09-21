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

