FROM python:3.15.2-alpine@sha256:0f9552bb28711333da16915ec146f5e6bb44a7fdac9ced15dc17c2e0206346dd
COPY --from=ghcr.io/astral-sh/uv:0.13.9@sha256:d3b601f0c7b118bc1753febf7c41cc80981df678445e0254284eecf84db79a7d /uv /bin/uv

RUN apk --no-cache add \
      ca-certificates

RUN mkdir -p /var/okoreports/reports

WORKDIR /usr/src/app
ENV UV_COMPILE_BYTECODE=1 UV_NO_CACHE=1 UV_PYTHON_DOWNLOADS=never
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev
ENV PATH="/usr/src/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["/start.sh"]

COPY container/start.sh /start.sh
COPY container/gunicorn.py /gunicorn.py
COPY app /usr/src/app
