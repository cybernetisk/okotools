#!/bin/bash

# This is only used for foreningenbs.no and not for CYB

docker run \
  -d \
  --net fbs \
  --restart always \
  --name okoreports-front \
  -v "$(pwd)/nginx-okoreports.conf":/etc/nginx/conf.d/default.conf \
  -v okoreports-reports:/var/www/okoreports-reports \
  -v okoreports-frontend-dist:/var/www/okoreports-frontend-dist \
  -p 127.0.0.1:8050:80 \
  nginx
