#!/bin/bash

docker run \
  -it \
  --rm \
  -v okoreports-frontend-dist:/usr/src/app-dist \
  -v okoreports-reports:/usr/src/app/reports \
  -p 3000:3000 \
  cyb/okoreports-frontend \
  bash
