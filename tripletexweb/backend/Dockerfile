FROM python:3-alpine
MAINTAINER Henrik Steen <henrist@henrist.net>

RUN apk --update add \
      ca-certificates

RUN mkdir -p /usr/src/app
RUN mkdir -p /usr/src/tripletex
RUN mkdir -p /var/okoreports/reports

COPY tripletex/requirements.txt /usr/src/tripletex/
COPY tripletexweb/backend/app/requirements.txt /usr/src/app/

WORKDIR /usr/src/tripletex
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /usr/src/app
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
CMD ["/start.sh"]

COPY tripletex /usr/src/tripletex
COPY tripletexweb/backend/container/start.sh /start.sh
COPY tripletexweb/backend/container/gunicorn.conf /gunicorn.conf
COPY tripletexweb/backend/app /usr/src/app
