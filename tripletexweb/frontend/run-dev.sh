#!/bin/bash

if [[ "$(docker images -q cyb/okoreports-frontend-dev 2> /dev/null)" == "" ]]; then
    ./build-dev.sh
fi

command=/dev.sh
if [ -n "$1" ]; then
    command="$@"
fi

docker run \
  -it \
  --rm \
  -e BACKEND_URL=http://localhost:8000/ \
  -v okoreports-frontend-dist:/usr/src/app-dist \
  -v okoreports-reports:/usr/src/app/reports \
  -v "$(pwd)/app":/usr/src/app \
  -p 3000:3000 \
  cyb/okoreports-frontend-dev \
  $command
