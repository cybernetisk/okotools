#!/bin/bash
set -eux

rm -rf dist/*

cp okolinks/index.html dist/

cd skjemaer
./create-dist.sh

cp -r dist ../dist/skjemaer/
