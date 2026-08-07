Running the app in Docker

Build the image (from project root):

```bash
docker build -t dqc-qube:local .
```

The image uses `uv sync --locked` to install the exact dependencies recorded in
`uv.lock` into `/opt/venv`. It targets Linux AMD64 because the locked
`bqskitrs` dependency does not publish Linux ARM64 wheels. Docker Desktop runs
the image through emulation when the host uses Apple Silicon.

Run the container and map port 8000 to localhost:

```bash
docker run --rm -p 8000:8000 -v "$PWD":/app dqc-qube:local
```

Or with docker-compose (recommended for development):

```bash
docker compose up --build
```

Open http://localhost:8000 in your browser.
