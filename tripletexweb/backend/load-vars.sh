#!/bin/bash

if ! [ -f settings.py ]; then
    echo "Missing settings.py"
    echo "It must be set up manually with this template:"
    echo "https://github.com/cybrairai/okotools/blob/master/tripletex/settings.py"
    exit 1
fi

docker_args=''
if [ "$(hostname -s)" == "scw-78960e" ]; then
    docker_args="--net cyb"
else
    echo "Running in development mode, see load-vars.sh"
    docker_args="-p 8000:8000"
fi
