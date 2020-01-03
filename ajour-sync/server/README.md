# ajour-sync server

This is set up on in.cyb.no host in `/root/okotools/ajour-sync/server`.
The Git repo is cloned there.

The services runs as https://ajour-sync.cyb.no/

Updating (or initial setup):

```bash
git pull
docker-compose -f docker-compose.prod.yml up -d --build
```
