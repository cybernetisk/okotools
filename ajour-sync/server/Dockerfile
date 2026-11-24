FROM python:3.15.2-slim@sha256:63bb298d2b7b88f176f51b5189f54ce6535c997682ea70885d2132f5d473a8a5
COPY --from=ghcr.io/astral-sh/uv:0.13.9@sha256:d3b601f0c7b118bc1753febf7c41cc80981df678445e0254284eecf84db79a7d /uv /bin/uv

WORKDIR /code
ENV UV_COMPILE_BYTECODE=1 UV_NO_CACHE=1 UV_PYTHON_DOWNLOADS=never
COPY pyproject.toml uv.lock /code/
RUN uv sync --locked
ENV PATH="/code/.venv/bin:$PATH"

COPY src/server.py /code
COPY container/start.sh /start.sh

VOLUME ["/data"]
ENV STORAGE_DIR=/data

EXPOSE 8000
CMD ["/start.sh"]
