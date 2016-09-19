#!/bin/bash

# deploy script - deploys to okoreports.cyb.no and foreningenbs.no/okoreports

echo "Deploying to okoreports.cyb.no"
ssh root@okoreports.cyb.no /bin/bash <<EOF
  cd /root/drift/okoreports
  ./update.sh
EOF

echo
echo "Deploying to foreningenbs.no"
ssh henrste@foreningenbs.no /bin/bash <<EOF
  set -e
  eval \$(ssh-agent)
  ssh-add ~/.ssh/cyb_okotools
  cd /var/www/aliases/okoreports/okotools
  git pull
  cd tripletexweb/backend
  ./update.sh
  cd ../frontend
  ./update-dist.sh
EOF
