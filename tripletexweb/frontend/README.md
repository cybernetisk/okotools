# okoreports frontend

This provides the frontend that generates accounting reports.

It is not required to have node or npm installed locally to
run or develop the application, all will be done inside Docker.

## Development

You need to run the backend API to be able to load data into the frontend application.

Install javascript dependencies:

```
docker-compose run frontend-builder npm install
```

Make sure to rerun this if `package.json` is modified.

Now you can start the development server:

```
docker-compose up frontend-builder
```

And go to http://localhost:3000/

## Building for deployment

```
# install dependencies
docker-compose run frontend-builder npm install

# build dist
docker-compose run frontend-builder npm run compile:prod

# build docker image
docker-compose build frontend

# push to Docker hub
docker login # if you are not already logged in
docker-compose push frontend
```

## Simulating production

```
docker-compose up frontend
```

Navigate to http://localhost:8050/
