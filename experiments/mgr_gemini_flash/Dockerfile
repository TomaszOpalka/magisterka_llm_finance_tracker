# Stage 1: Build
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Final
FROM python:3.12-slim

WORKDIR /app

# Copying from the builder stage
COPY --from=builder /install /usr/local
COPY . .

RUN mkdir -p /app/data && chown -R 1000:1000 /app/data

USER 1000

EXPOSE 8002

ENV DATABASE_URL="sqlite+aiosqlite:////app/data/finance.db"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]