FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build deps (keep minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/

RUN pip install --upgrade pip
# Install runtime dependencies listed in pyproject
RUN pip install --no-cache-dir pennylane plotly qiskit shiny shinywidgets

# Copy app source
COPY . /app

EXPOSE 8000

CMD ["python", "run_server.py"]
