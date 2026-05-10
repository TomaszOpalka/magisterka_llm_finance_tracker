# Base image
FROM python:3.12-slim

# Environment configuration
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Application directory
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create persistent data directory
RUN mkdir -p /app/data

# Copy application source code
COPY . .

# Expose application port
EXPOSE 8003

# Default database location for persistence
ENV DATABASE_URL=sqlite+aiosqlite:////app/data/finance.db

# Run FastAPI application
CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]