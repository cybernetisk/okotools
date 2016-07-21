#!/bin/bash

set -e

./build.sh

docker rm -f cyb-okoreports-backend 2>/dev/null || true

./run.sh
