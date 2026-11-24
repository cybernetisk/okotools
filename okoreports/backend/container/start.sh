#!/bin/sh

exec gunicorn \
  --config=/gunicorn.py \
  --access-logfile '-' \
  --error-logfile '-' \
  --timeout 120 \
  app:app
