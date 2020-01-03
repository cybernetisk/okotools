#!/bin/sh
set -e

exec gunicorn \
  -b 0.0.0.0:8000 \
  -w 2 \
  server:app
