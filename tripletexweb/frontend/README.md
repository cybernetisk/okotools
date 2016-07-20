# okoreports frontend

This provides the frontend that generates accounting reports.

It is not required to have node or npm installed locally to
run or develop the application, all will be done inside Docker.

## Development

Run `./run-dev.sh` and it will start a Docker-instance,
mount the data in `app` directory in the container, and
run webpack development server which recompiles on changes.

Running the development server will add a `node_modules` folder
in the `app`-directory.

## Generate distribution files

By running `./update-dist.sh` it will generate distribution files
which are stored in `okoreports-frontend-dist` Docker volume that
can be mounted by nginx.
