#!/bin/bash

set -e

commit=$(git rev-parse --short HEAD)
docker build -t cyb/okoreports-frontend:$commit -t cyb/okoreports-frontend:latest .
