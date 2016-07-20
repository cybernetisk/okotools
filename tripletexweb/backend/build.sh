#!/bin/bash

# we need the tripletex-folder as well, so copy this in and remove later
cp -rp ../../tripletex tripletex-lib

commit=$(git rev-parse --short HEAD)
docker build -t cyb/okoreports-backend:$commit -t cyb/okoreports-backend:latest .

rm -rf tripletex-lib
