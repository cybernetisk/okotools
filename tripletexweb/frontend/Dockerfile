# This Dockerfile wraps the built static files inside an
# nginx container, so we can easily run it self-contained
# instead of having to publish the static files somewhere

FROM nginx:1.31.10@sha256:a786635fd3c7b9a57ea089ab1c0713e510f3b548b65fe699ce3d59e4a926b37e

COPY dist /usr/share/nginx/html
