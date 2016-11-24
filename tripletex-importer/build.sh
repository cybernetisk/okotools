#!/bin/bash

# we need the tripletex-folder as well, so copy this in and remove later
cp -rp ../tripletex tripletex-lib

docker build -t cyb/tripletex-importer .

rm -rf tripletex-lib
