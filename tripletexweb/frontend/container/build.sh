#!/bin/sh

set -e

npm run build

rm -Rf /usr/src/app-dist/latest
mv /usr/src/app/dist /usr/src/app-dist/latest
