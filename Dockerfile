FROM python:3.11

WORKDIR /app

# Install system dependencies including OCRmyPDF
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    chromium \
    chromium-driver \
    ghostscript \
    libmagic1 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Create directories for mounted volumes
RUN mkdir -p /app/config /app/credentials /app/checkpoint

# Copy application code
COPY . .

# Set volume mount points
VOLUME ["/app/config", "/app/credentials", "/app/checkpoint"]
