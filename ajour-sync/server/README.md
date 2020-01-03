# ajour-sync server

This is set up on in.cyb.no host in `/root/okotools/ajour-sync/server`.
The Git repo is cloned there.

The service runs as https://ajour-sync.cyb.no/

Updating:

```bash
git pull
docker-compose -f docker-compose.prod.yml up -d --build
```
