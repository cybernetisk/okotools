#!/bin/sh

gunicorn \
  --config=/gunicorn.conf \
  --access-logfile '-' \
  --error-logfile '-' \
  app:app
