# This Dockerfile wraps the built static files inside an
# nginx container, so we can easily run it self-contained
# instead of having to publish the static files somewhere

FROM nginx

COPY dist /usr/share/nginx/html
