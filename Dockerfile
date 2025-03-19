FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    chromium \
    chromium-driver \
    ghostscript \
    libmagic1 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Chrome
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV SELENIUM_HEADLESS=1
ENV PYTHONUNBUFFERED=1

# Create and set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir ocrmypdf

# Copy application code
COPY . .

# Create directories for mounted volumes
RUN mkdir -p /app/config /app/credentials /app/checkpoint

# Set volume mount points
VOLUME ["/app/config", "/app/credentials", "/app/checkpoint"]

# Run the application
CMD ["python", "main.py"]
