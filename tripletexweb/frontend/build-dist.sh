#!/bin/bash

docker_args=''

if [ "$(hostname -s)" == "athene" ]; then
  docker_args='-e BACKEND_URL=/okoreports/'
fi

docker run \
  --rm \
  -v okoreports-frontend-dist:/usr/src/app-dist \
  -e NODE_ENV=production \
  $docker_args \
  cyb/okoreports-frontend \
  /build.sh
