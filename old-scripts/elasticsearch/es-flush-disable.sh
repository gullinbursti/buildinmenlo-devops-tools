# true or false
DISABLE=$1
curl -XPUT 'localhost:9200/_settings' -d '{
   "index" : {
      "translog.disable_flush" : "'$DISABLE'"
   }
}' 
