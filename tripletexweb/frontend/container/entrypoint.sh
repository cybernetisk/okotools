#!/usr/bin/env sh

# make sure we are the same user as the one who owns the files
# this is relevant because the source code is mounted from the host system

if [ $(id -u) = 0 ] && [ -f README.md ]; then
  uid=$(stat -c %u README.md)
  gid=$(stat -c %u README.md)

  if [ $(id -u) != $uid ]; then
    userdel app 2>/dev/null || true
    groupdel app 2>/dev/null || true
    groupadd -g $gid app 2>/dev/null
    useradd -m -g $gid -u $uid app 2>/dev/null

    chown -R app:app /home/app

    gosu app "$@"
    exit
  fi
fi

exec "$@"
