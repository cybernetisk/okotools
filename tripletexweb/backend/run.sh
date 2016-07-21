#!/bin/bash

set -e

. load-vars.sh

running=$(docker inspect --format="{{ .State.Running }}" cyb-okoreports-backend 2>/dev/null || true)
if [ "$running" != "" ]; then
    printf "The container already exists. Do you want to remove it? (y/n) "
    read remove

    if [ "$remove" != "y" ]; then
        echo "Aborting"
        exit 1
    fi

    docker rm -f cyb-okoreports-backend 2>/dev/null || true
fi

docker run \
  $docker_args \
  --name cyb-okoreports-backend \
  -d --restart=always \
  -v okoreports-reports:/var/okoreports/reports \
  -v "$(pwd)/settings.py":/usr/src/tripletex/settings_local.py \
  cyb/okoreports-backend
