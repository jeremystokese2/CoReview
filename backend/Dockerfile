FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml ./
# uv.lock is generated on first `uv sync`; copy if present.
COPY uv.loc[k] ./

RUN uv sync --no-dev

COPY app ./app
COPY scripts ./scripts

RUN useradd -m appuser \
    && mkdir -p /app/data/snapshots \
    && chown -R appuser /app

USER appuser

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
