#!/bin/bash

# deploy script - deploys to okoreports.cyb.no and foreningenbs.no/okoreports

echo "Deploying to okoreports.cyb.no"
ssh root@okoreports.cyb.no /bin/bash <<EOF
  set -e
  cd /root/drift/okoreports
  docker-compose pull
  docker-compose up -d
EOF

# deploy of foreningenbs.no is now controlled from
# https://github.com/blindern/drift/blob/master/ansible/site.yml

# echo
# echo "Deploying to foreningenbs.no"
# ssh henrste@foreningenbs.no /bin/bash <<EOF
#   set -e
#   cd /fbs/drift/services/okoreports
#   docker-compose pull
#   docker-compose up -d
# EOF
