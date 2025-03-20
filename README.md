# Edge Weekly & Star Scraper

This project is an automated scraper for The Edge Weekly Newspaper and The Star newspaper. It logs in to the respective websites, downloads the latest issues, converts them to PDF, uploads them to Google Drive, and sends email notifications with the download links.

> **_IMPORTANT:_**
>
> - This scraper requires a valid subscription to The Edge Weekly. You can purchase a subscription at [The Edge Malaysia Subscription Page](https://subscribe.theedgemalaysia.com/subcribe-tecd.html).
> - For The Star content, you need a valid subscription from [The Star E-Paper](https://newsstand.thestar.com.my/).

## Why was this made?

This project was created to improve the reading experience for elderly users who are not tech-savvy and may find the newspapers' online interfaces challenging. By converting the newspapers to PDFs, it becomes much easier to read, as the only tool needed is the zoom function.

## Features

- Web scraping using Selenium 4.x
- PDF creation from downloaded images using Pillow
- Google Drive integration for file storage
- Email notifications
- Checkpointing to avoid duplicate downloads
- Docker support for easy deployment
- Environment variable configuration support
- Support for both Edge Weekly and The Star newspapers
- Cookie-based authentication support

## Project Structure

```
.
├── main.py                 # Application entry point
├── run.sh                  # Convenience script for running the application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker container definition
├── docker-compose.yml     # Docker compose configuration
├── .dockerignore         # Docker build exclusions
├── src/
│   ├── scraper.py       # Main web scraping logic
│   ├── pages.py         # Image downloading and PDF creation
│   ├── drive.py         # Google Drive operations
│   ├── email.py         # Email notification handling
│   └── star/
│       └── scraper.py   # Star-specific scraping logic
└── utils/
    ├── checkpoint.py    # Download state management
    ├── config.py        # Configuration handling
    └── logger.py        # Logging utilities
```

## Prerequisites

- Python 3.8+ (recommended)
- Chrome/Chromium browser
- Active subscriptions to The Edge Weekly and/or The Star
- Google Cloud project with Drive API enabled
- Gmail account for sending notifications

## Installation

### Method 1: Traditional Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/edge-converter.git
   cd edge-converter
   ```

2. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up Google Drive API:
   - Create a service account following [Google's official guide](https://cloud.google.com/iam/docs/creating-managing-service-accounts)
   - Download the service account JSON key file
   - Create a folder in Google Drive
   - Share the folder with the service account email

### Method 2: Docker Installation

1. Clone the repository as shown above
2. Ensure Docker and Docker Compose are installed on your system
3. Build and run using Docker Compose:

   ```bash
   docker-compose up --build
   ```

## Configuration

You can configure the application using either a `config.yaml` file or environment variables.

### Using config.yaml

```yaml
mode: "edge"  # Options: "edge", "star",

edge:
  url: "https://digital.theedgemalaysia.com/"
  username: "your_username"
  password: "your_password"
  cookie: "your_auth_cookie"  # Optional: Use cookie-based authentication instead of username/password

star:
  url: "https://newsstand.thestar.com.my/"
  username: "your_username"
  password: "your_password"
  cookie: "your_auth_cookie"  # Optional: Use cookie-based authentication instead of username/password

google_drive:
  service_account_file: "path/to/your/service_account.json"
  folder_name: "newspapers"  # All PDFs will be stored here

email:
  sender_email: "your_email@gmail.com"
  sender_password: "your_app_password"
  receiver_emails:
    - "recipient1@example.com"
    - "recipient2@example.com"
  subject: "Weekly Newspaper PDF"
  body: "Please find the link to the latest newspaper PDF below:"
```

### Using Environment Variables

You can also use environment variables by creating a `.env` file:

```env
MODE=both  # Options: edge, star, both

# Edge Weekly Configuration
EDGE_URL=https://digital.theedgemalaysia.com/
EDGE_USERNAME=your_username
EDGE_PASSWORD=your_password
EDGE_COOKIE=your_auth_cookie

# The Star Configuration
STAR_URL=https://newsstand.thestar.com.my/
STAR_USERNAME=your_username
STAR_PASSWORD=your_password
STAR_COOKIE=your_auth_cookie

# Google Drive Configuration
GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE=path/to/your/service_account.json
GOOGLE_DRIVE_FOLDER_NAME=newspapers

# Email Configuration
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com
EMAIL_SUBJECT=Weekly Newspaper PDF
```

## Usage

### Running with Python

```bash
# Using the convenience script
./run.sh

# Or directly with Python
python main.py --mode edge  # For Edge Weekly only
python main.py --mode star  # For The Star only
python main.py --mode both  # For both newspapers
```

### Running with Docker

```bash
# Start the container
docker-compose up

# Or run in detached mode
docker-compose up -d
```

The script will:

1. Check if there's a new issue available for the configured newspaper(s)
2. Download the newspaper pages if a new issue is found
3. Convert the pages to a PDF
4. Upload the PDF to Google Drive
5. Send email notifications with the download link

## Dependencies

Key dependencies include:

- selenium (4.24.0) for web automation
- Pillow (10.4.0) for image processing
- google-api-python-client for Drive API integration
- python-dotenv (1.0.1) for environment variable management
- PyYAML (6.0.2) for configuration file parsing

For a complete list of dependencies, see `requirements.txt`.
