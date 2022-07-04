FROM python:3.10-alpine

RUN apk --no-cache add \
      ca-certificates

RUN mkdir -p /usr/src/app
RUN mkdir -p /usr/src/libs
RUN mkdir -p /var/okoreports/reports

# (cd tripletex && python setup.py bdist_wheel -d ..)
COPY cyb_tripletex-0.0.1-py3-none-any.whl /usr/src/libs/

COPY tripletexweb/backend/requirements.txt /usr/src/app/

WORKDIR /usr/src/app
RUN pip install --no-cache-dir -r requirements.txt --find-links /usr/src/libs

EXPOSE 8000
CMD ["/start.sh"]

COPY tripletexweb/backend/container/start.sh /start.sh
COPY tripletexweb/backend/container/gunicorn.py /gunicorn.py
COPY tripletexweb/backend/app /usr/src/app
