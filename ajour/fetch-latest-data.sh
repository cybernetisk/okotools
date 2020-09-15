#!/bin/bash
set -eu -o pipefail

last_file=$(
  ssh root@in.cyb.no bash <<EOF
    cd ajour-data
    ls -1 *.tgz | sort -n | tail -1
EOF
)

echo "Latest: $last_file"

outdir=data/${last_file%.tgz}
if [ -e "$outdir" ]; then
  echo "Already exist locally - aborting"
  exit
fi

echo "Downloading $last_file"
scp "root@in.cyb.no:ajour-data/$last_file" /tmp/data.tgz

mkdir "$outdir"
tar -C "$outdir" -zxf /tmp/data.tgz
