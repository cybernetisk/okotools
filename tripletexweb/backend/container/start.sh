#!/bin/sh

gunicorn \
  --config=/gunicorn.conf \
  app:app
