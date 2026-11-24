FROM python:3.10-alpine

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
