ARG RUNTIME_PLATFORM=linux/amd64

FROM --platform=${RUNTIME_PLATFORM} ghcr.io/astral-sh/uv:0.11.19 AS uv

FROM --platform=${RUNTIME_PLATFORM} python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Retain a compiler for dependencies that do not publish Python 3.14 wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /bin/

# Install the locked dependencies before copying source so this layer is cached
# until the project metadata changes. The repository is an application rather
# than an installable Python package, so the project itself is not installed.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

COPY . .

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "python", "run_server.py"]
