#!/bin/bash

echo "Not updated for Docker-setup"
exit 1

# deploy script - deploys to internt.cyb.no/okoreports and foreningenbs.no/okoreports

echo "Deploying to internt.cyb.no"
ssh django@internt.cyb.no /bin/bash <<EOF
  cd /home/django/okotools
  git pull
  cd tripletexweb/web
  npm install
  npm run build
  cd ../../tripletex
  . env/bin/activate
  pip install -r requirements.txt
EOF

echo
echo "Deploying to foreningenbs.no"
ssh henrste@foreningenbs.no /bin/bash <<EOF
  eval \$(ssh-agent)
  ssh-add ~/.ssh/cyb_okotools
  cd /var/www/aliases/okoreports/okotools
  git pull
  cd tripletexweb/web
  npm install
  npm run build
  cd ../../tripletex
  . env/bin/activate
  pip install -r requirements.txt
EOF
