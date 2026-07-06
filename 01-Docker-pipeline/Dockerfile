# Base image: slim Python 3.13 to keep the image small
FROM python:3.13.11-slim

# Copy the uv binary from its official image — uv is a fast Python package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# All files and commands run from /app inside the container
WORKDIR /app

# Make the virtualenv's binaries available without activating it
ENV PATH="/app/.venv/bin:$PATH"

# Copy dependency files first so Docker can cache this layer
# uv sync installs exactly what's in uv.lock (reproducible builds)
COPY pyproject.toml .python-version uv.lock ./
RUN uv sync --locked

# Copy the ingestion script
COPY ingest_data.py .

# Default command — any extra args passed to `docker run` are appended here
# e.g. docker run taxi_ingest:v001 --pg-host=pgdatabase
ENTRYPOINT ["uv", "run", "python", "ingest_data.py"]