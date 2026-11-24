FROM python:3.15.2-alpine@sha256:0f9552bb28711333da16915ec146f5e6bb44a7fdac9ced15dc17c2e0206346dd

RUN apk --no-cache add \
      ca-certificates

RUN mkdir -p /usr/src/app
RUN mkdir -p /var/okoreports/reports

COPY requirements.txt /usr/src/app/

WORKDIR /usr/src/app
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
CMD ["/start.sh"]

COPY container/start.sh /start.sh
COPY container/gunicorn.py /gunicorn.py
COPY app /usr/src/app
