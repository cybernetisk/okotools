FROM python:3.15.2-slim@sha256:63bb298d2b7b88f176f51b5189f54ce6535c997682ea70885d2132f5d473a8a5

WORKDIR /code
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

COPY src/server.py /code
COPY container/start.sh /start.sh

VOLUME ["/data"]
ENV STORAGE_DIR=/data

EXPOSE 8000
CMD ["/start.sh"]
