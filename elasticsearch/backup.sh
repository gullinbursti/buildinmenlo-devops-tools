#! /bin/bash

set -o errexit
set -o nounset
set -o errtrace

# SCRIPTS=/home/volley/admin/bin/elasticsearch
TO_FOLDER=.
FROM=/var/lib/elasticsearch

DATE=`date +%Y-%m-%d_%H`
TO=$TO_FOLDER/$DATE
echo "rsync from $FROM to $TO"
# the first times rsync can take a bit long - do not disable flusing
rsync -a $FROM $TO

# now disable flushing and do one manual flushing
#----
# $SCRIPTS/es-flush-disable.sh true
curl -XPUT 'localhost:9200/_settings' -d '{
   "index" : {
      "translog.disable_flush" : "'true'"
   }
}'
#----



#----
# $SCRIPTS/es-flush.sh
curl -XPOST 'localhost:9200/_flush'
#----


# ... and sync again
rsync -a $FROM $TO

#----
# $SCRIPTS/es-flush-disable.sh false
curl -XPUT 'localhost:9200/_settings' -d '{
   "index" : {
      "translog.disable_flush" : "'false'"
   }
}'
#----

# now zip up final product
echo "\nzipping $TO $TO.tar.gz "
cd $TO_FOLDER
tar zcf $DATE.tar.gz $DATE
rm -rf $DATE
