#!/bin/bash

# This script build a Docker image we can push to our Docker registry
# and pull from the servers where we want to run the frontend

docker-compose run frontend-builder npm install
docker-compose run frontend-builder npm run compile:prod
docker-compose build frontend
