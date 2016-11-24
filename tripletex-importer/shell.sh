#!/bin/bash

# This script will set up a temporary container and optionally run
# the provided command, or else start a shell. The container will
# be removed after use.

if ! [ -f reports.json ]; then
  echo "Missing reports.json"
  exit 1
elif ! [ -f settings.py ]; then
  echo "Missing settings.py"
  exit 1
fi

docker run \
  -it \
  --rm \
  -v "$(pwd)/settings.py":/usr/src/tripletex/settings_local.py \
  -v "$(pwd)/reports.json":/usr/src/app/reports.json \
  cyb/tripletex-importer \
  $@
