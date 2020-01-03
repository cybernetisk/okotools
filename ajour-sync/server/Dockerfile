FROM python:3.8-slim

RUN pip install poetry

WORKDIR /code
COPY poetry.lock pyproject.toml /code/

RUN set -eux; \
    poetry config virtualenvs.create false; \
    poetry install --no-interaction --no-ansi

COPY src/server.py /code
COPY container/start.sh /start.sh

VOLUME ["/data"]
ENV STORAGE_DIR=/data

EXPOSE 8000
CMD ["/start.sh"]
