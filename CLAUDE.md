# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Edge Weekly Scraper - an automated newspaper scraping system that downloads The Edge Weekly newspaper, converts it to PDF with OCR, uploads to Google Drive, and sends email notifications. The system includes cookie management for authentication and checkpointing to avoid duplicate downloads.

## Key Commands

### Running the Application
```bash
python main.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Docker Operations
```bash
# Build and run with Docker Compose
docker-compose up --build

# Run standalone Docker container
docker build -t newspaper-scraper .
docker run newspaper-scraper
```

### Utility Scripts
```bash
# Clean up storage and delete old PDFs
python empty_trash.py
```

## Architecture Overview

### Core Components

1. **main.py** - Entry point that orchestrates the entire scraping workflow
2. **src/scraper.py** - Web scraping logic with Selenium, cookie-based authentication
3. **src/pages.py** - Image downloading and PDF creation with OCR processing
4. **src/drive.py** - Google Drive API integration for file uploads
5. **src/email.py** - Email notification system
6. **utils/** - Shared utilities (logging, config, checkpointing, cookies)

### Key Data Flow

1. Load configuration and checkpoint state
2. Check for new newspaper version using date comparison
3. Authenticate via cookies (fallback to manual login)
4. Download newspaper pages as images
5. Convert images to PDF with OCR using ocrmypdf
6. Upload to Google Drive with proper permissions
7. Send email notifications with download links
8. Update checkpoint to prevent re-processing

### Authentication System

The scraper uses a sophisticated cookie management system:
- **CookieManager** (scripts/cookie_manager.py) - Handles cookie persistence and validation
- **Cookie-based auth** - Primary authentication method using stored session cookies
- **Fallback login** - Manual username/password login when cookies fail
- **Cookie refresh** - Automatic cookie updates when authentication succeeds

### Configuration Structure

Uses YAML configuration (config/config.yaml) with sections for:
- `edge`: Website credentials and cookies
- `google_drive`: Service account and folder mappings
- `email`: SMTP settings and recipient lists

### Checkpoint System

- **checkpoint/checkpoint.yaml** - Stores processing state to prevent duplicates
- Tracks newspaper version/date to skip already processed issues
- Maintains folder configurations and processing history

### Chrome Profile Management

The system includes a persistent Chrome profile (chrome-profile/) for:
- Maintaining browser state across sessions
- Preserving cookies and authentication tokens
- Consistent user agent and browser fingerprinting

## Important Notes

- Requires valid subscription to The Edge Weekly
- Uses Google Drive API with service account authentication
- Implements OCR processing for searchable PDFs
- Containerized for deployment flexibility
- Supports multiple newspaper sources (Edge, Star, Sun)