# Stage 1: Build environment
FROM python:3.12-slim AS builder

# Set environment variables to optimize Python execution
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install system dependencies (if any are required by yfinance or others in the future)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy only requirements to cache them in Docker layer
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create a dedicated directory for the database to ensure volume persistence
# This prevents the database from being overwritten if the container is rebuilt
RUN mkdir -p /app/data

# Expose the application port
EXPOSE 8001

# Command to run the application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]