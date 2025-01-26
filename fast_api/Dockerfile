FROM python:3.11-slim

# Create app directory and scripts directory
RUN mkdir -p /app /scripts

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    xvfb \
    xauth \
    chromium \
    chromium-driver \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libspeechd2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    procps \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /var/log && \
    chmod 777 /var/log

# Install pip and upgrade it
RUN pip install --no-cache-dir --upgrade pip

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install playwright browsers
RUN playwright install chromium
RUN playwright install-deps

# Create startup script in /scripts instead of /app
RUN echo '#!/bin/bash' > /scripts/docker-entrypoint.sh && \
    echo 'set -e' >> /scripts/docker-entrypoint.sh && \
    echo 'cd /app' >> /scripts/docker-entrypoint.sh && \
    echo 'export PYTHONPATH=/app' >> /scripts/docker-entrypoint.sh && \
    echo 'touch ~/.Xauthority' >> /scripts/docker-entrypoint.sh && \
    echo 'Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &' >> /scripts/docker-entrypoint.sh && \
    echo 'export DISPLAY=:99' >> /scripts/docker-entrypoint.sh && \
    echo 'sleep 1' >> /scripts/docker-entrypoint.sh && \
    echo 'exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug' >> /scripts/docker-entrypoint.sh && \
    chmod +x /scripts/docker-entrypoint.sh

# Copy the rest of the application
COPY . .

EXPOSE 8000

CMD ["/scripts/docker-entrypoint.sh"]