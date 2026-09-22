FROM python:3.13

WORKDIR /workspaces

ENV UV_PROJECT_ENVIRONMENT=/usr/local

RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip uv

COPY ./pyproject.toml ./uv.lock ./README.md ./
COPY ./svgreportbuilder ./svgreportbuilder

RUN uv sync --locked --no-dev
