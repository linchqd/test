#!/bin/sh
# docker run --net host --restart always -v /data/redis:/data --name gate_redis -d redis redis-server --appendonly yes
# docker run --net host -d --restart always gate:v4 

set -e

/usr/local/bin/python3 /usr/local/bin/supervisord -c /home/admin/supervisord.conf

