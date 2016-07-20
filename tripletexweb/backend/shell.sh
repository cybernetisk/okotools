#!/bin/bash

# This script will set up a temporary container and optionally run
# the provided command, or else start a shell. The container will
# be removed after use.

command=sh
if [ -n "$1" ]; then
    command="$@"
fi

. load-vars.sh

docker run \
  $docker_args \
  -it \
  --rm \
  -v okoreports-reports:/var/okoreports/reports \
  -v "$(pwd)/settings.py":/usr/src/tripletex/settings_local.py \
  cyb/okoreports \
  $command
