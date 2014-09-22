SCRIPTS=/home/volley/admin/bin/elasticsearch
TO_FOLDER=/home/shane/esbackups
FROM=/elasticsearch/data
 
DATE=`date +%Y-%m-%d_%H`
TO=$TO_FOLDER/$DATE
echo "rsync from $FROM to $TO"
# the first times rsync can take a bit long - do not disable flusing
rsync -a $FROM $TO
 
# now disable flushing and do one manual flushing
$SCRIPTS/es-flush-disable.sh true
$SCRIPTS/es-flush.sh
# ... and sync again
rsync -a $FROM $TO
 
$SCRIPTS/es-flush-disable.sh false

# now zip up final product
echo "\nzipping $TO $TO.tar.gz "
cd $TO_FOLDER
/bin/tar zcf $DATE.tar.gz $DATE
/bin/rm -rf $DATE
