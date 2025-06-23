# Technical Context: Edge Weekly Scraper

## Technology Stack

### Core Technologies
- **Python 3.7+**: Primary runtime environment
- **Selenium 4.24.0**: Web automation and scraping
- **Chrome WebDriver**: Browser automation engine
- **OCRmyPDF**: OCR processing for text accessibility
- **Pillow 10.4.0**: Image processing for PDF creation

### Cloud Services
- **Google Drive API**: Cloud storage and file sharing
- **Google Service Account**: Authentication and API access
- **Gmail SMTP**: Email notification delivery

### Dependencies Overview
```yaml
Web Scraping:
  - selenium: 4.24.0
  - selenium-wire: 5.1.0 (network request capture)
  
Image/PDF Processing:
  - pillow: 10.4.0
  - ocrmypdf: (OCR processing)
  
Google Integration:
  - google-api-python-client: 2.144.0
  - google-auth: 2.34.0
  - google-auth-oauthlib: 1.2.1
  
Configuration:
  - PyYAML: 6.0.2
  - python-dotenv: 1.0.1
  
HTTP/Requests:
  - requests: 2.32.3
  - urllib3: 2.2.2
```

## Development Environment

### System Requirements
- **Operating System**: Linux/Windows/macOS with Python support
- **Python Version**: 3.7 or higher
- **Chrome Browser**: Required for WebDriver
- **Internet Connection**: Required for web scraping and API calls
- **Storage**: Temporary space for image processing

### Configuration Dependencies
- **Google Cloud Project**: Drive API enabled
- **Service Account**: JSON key file with Drive permissions
- **Gmail Account**: App password for SMTP access
- **Edge Weekly Subscription**: Valid user credentials

### File Structure
```
edge-converter/
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
├── config/
│   └── config.yaml        # Configuration file
├── src/
│   ├── scraper.py         # Web scraping logic
│   ├── pages.py           # Image/PDF processing
│   ├── drive.py           # Google Drive operations
│   └── email.py           # Email notifications
├── utils/
│   ├── config.py          # Configuration loading
│   ├── logger.py          # Logging utilities
│   └── checkpoint.py      # State management
├── credentials/           # Service account files
├── checkpoint/           # State persistence
└── memory-bank/          # Documentation
```

## Technical Constraints

### Performance Limitations
- **Sequential Processing**: Images downloaded one by one
- **Memory Usage**: Temporary storage for full magazine images
- **Network Dependency**: Requires stable internet for scraping and uploads
- **Chrome Resource Usage**: Browser automation overhead

### Security Considerations
- **Credential Storage**: Service account keys in local files
- **Network Traffic**: Selenium wire captures all requests
- **Login Credentials**: Stored in configuration files
- **Drive Permissions**: Service account requires folder access

### Platform Dependencies
- **Chrome WebDriver**: Must match installed Chrome version
- **File System**: Temporary directory creation and cleanup
- **Network Protocols**: HTTPS for web scraping, SMTP for email

## Development Setup Process

### 1. Python Environment
```bash
# Clone repository
git clone <repository-url>
cd edge-converter

# Install dependencies
pip install -r requirements.txt
```

### 2. Google Cloud Setup
```bash
# Required steps:
# 1. Create Google Cloud project
# 2. Enable Drive API
# 3. Create service account
# 4. Download JSON key file
# 5. Create Drive folder
# 6. Share folder with service account email
```

### 3. Configuration Setup
```yaml
# config/config.yaml structure:
edge:
  url: "https://digital.theedgemalaysia.com/"
  username: "subscription_username"
  password: "subscription_password"

google_drive:
  service_account_file: "path/to/service_account.json"
  folder_name: "edge-weekly"

email:
  sender_email: "sender@gmail.com"
  sender_password: "gmail_app_password"
  receiver_emails:
    - "recipient@example.com"
  subject: "Edge Weekly PDF"
  body: "Latest Edge Weekly PDF download link:"
```

## Tool Usage Patterns

### Selenium Configuration
```python
# Chrome options for automation
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--start-maximized")
```

### OCR Processing
```python
# OCR enhancement pattern
ocrmypdf.ocr(
    input_file=original_pdf,
    output_file=enhanced_pdf,
    language='eng'
)
```

### Google API Authentication
```python
# Service account authentication
credentials = service_account.Credentials.from_service_account_file(
    service_account_file,
    scopes=['https://www.googleapis.com/auth/drive']
)
service = build('drive', 'v3', credentials=credentials)
```

## Deployment Considerations

### Docker Support
- **Dockerfile**: Available for containerized deployment
- **docker-compose.yml**: Orchestration configuration
- **Chrome in container**: Headless browser support

### Automation Options
- **Cron scheduling**: Regular execution on Linux/macOS
- **Task Scheduler**: Windows automation
- **Cloud functions**: Serverless deployment option

### Monitoring & Logging
- **File-based logging**: `edge_converter.log`
- **Structured logging**: Component-based message format
- **Error tracking**: Exception logging with context
- **Checkpoint monitoring**: State file for progress tracking

## Integration Points

### External Services
- **The Edge Weekly**: Target website for content scraping
- **Google Drive**: Cloud storage and sharing platform
- **Gmail SMTP**: Email delivery service

### Data Exchange Formats
- **YAML**: Configuration files
- **JSON**: Google API responses and service account keys
- **PDF**: Final output format
- **Images**: Intermediate processing format (JPEG/PNG)

### API Rate Limits
- **Google Drive API**: Per-project quotas and rate limits
- **Gmail SMTP**: Daily sending limits
- **Web scraping**: Respectful request timing to avoid blocking
