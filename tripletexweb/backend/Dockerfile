FROM python:3-alpine
MAINTAINER Henrik Steen <henrist@henrist.net>

RUN apk --update add \
      ca-certificates

RUN mkdir -p /usr/src/app
RUN mkdir -p /usr/src/tripletex
RUN mkdir -p /var/okoreports/reports

COPY tripletex-lib/requirements.txt /usr/src/tripletex/
COPY app/requirements.txt /usr/src/app/

WORKDIR /usr/src/tripletex
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /usr/src/app
RUN pip install --no-cache-dir -r requirements.txt

COPY tripletex-lib /usr/src/tripletex
COPY app /usr/src/app
COPY container/start.sh /start.sh
COPY container/gunicorn.conf /gunicorn.conf

EXPOSE 8000
CMD ["/start.sh"]
