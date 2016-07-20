#!/bin/bash

docker run \
  --rm \
  -v okoreports-frontend-dist:/usr/src/app-dist \
  -e NODE_ENV=production \
  cyb/okoreports-frontend \
  /build.sh
