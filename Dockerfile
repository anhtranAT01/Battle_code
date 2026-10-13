# Battlecode 9x9 RPS Platform - Production Dockerfile
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy platform source code
COPY config/ ./config/
COPY engine/ ./engine/
COPY server/ ./server/
COPY starter_kit/ ./starter_kit/
COPY web/ ./web/
COPY main.py .

# Create persistent storage directories for bots and replays
RUN mkdir -p /app/bots /app/replays

# Expose server port
EXPOSE 8000

# Healthcheck endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Launch production server
CMD ["python", "main.py", "--host", "0.0.0.0", "--port", "8000"]
