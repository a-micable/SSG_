FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml README.md LICENSE /app/
COPY ssg /app/ssg

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir /app

ENV SSG_LOG_LEVEL=INFO
ENV SSG_LOG_FORMAT=json

# Default: isolated CLI sandbox (not a deployed service)
CMD ["ssg", "health"]
