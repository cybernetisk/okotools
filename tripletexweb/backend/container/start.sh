#!/bin/sh

gunicorn \
  --config=/gunicorn.conf \
  --access-logfile '-' \
  --error-logfile '-' \
  --timeout 120 \
  app:app
