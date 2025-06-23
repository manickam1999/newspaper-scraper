# System Patterns: Edge Weekly Scraper

## Architecture Overview
The system follows a linear pipeline pattern with clear separation of concerns across five main components:

```
Web Scraping → Image Processing → PDF Creation → Cloud Storage → Notification
    ↓              ↓                ↓              ↓              ↓
  scraper.py    pages.py         main.py       drive.py      email.py
```

## Key Design Patterns

### 1. Pipeline Pattern
**Location**: `main.py`
- Sequential processing stages with clear handoffs
- Each stage produces output for the next stage
- Fail-fast approach - pipeline stops if any stage fails
- Temporary directory management for intermediate files

### 2. Configuration-Driven Pattern
**Location**: `utils/config.py`
- External YAML configuration for all settings
- Separation of code from environment-specific data
- Supports multiple environments without code changes

### 3. Checkpoint Pattern
**Location**: `utils/checkpoint.py`
- State persistence to prevent duplicate processing
- Version tracking using publication dates
- Graceful resumption after interruptions

### 4. Driver Pattern (Selenium)
**Location**: `scraper.py`
- Centralized WebDriver setup and configuration
- Reusable driver instance across scraping operations
- Proper resource cleanup with driver.quit()

## Component Relationships

### Core Processing Flow
```
main() 
├── load_config() → Configuration loading
├── load_checkpoint() → State management
├── setup_driver() → WebDriver initialization
├── scrape_magazine() → Web scraping pipeline
│   ├── is_latest() → Version checking
│   ├── login() → Authentication
│   ├── get_total_pages() → Content discovery
│   ├── get_zoom_url() → URL extraction
│   └── fetch_images() → Image downloading
├── ocrmypdf.ocr() → OCR processing
├── handle_drive_upload() → Cloud storage
├── set_file_permissions() → Access control
├── handle_email() → Notifications
└── save_checkpoint() → State persistence
```

### Data Flow Patterns
1. **Configuration Flow**: YAML → Config object → Component parameters
2. **State Flow**: Checkpoint file → Memory → Updated checkpoint
3. **Content Flow**: Web pages → Images → PDF → Drive → Email link
4. **Error Flow**: Exceptions → Logger → Graceful exit

## Critical Implementation Paths

### Authentication & Access Control
- **Login sequence**: CSS selectors → Form filling → Confirmation wait
- **Permission model**: Service account → Folder sharing → Email access
- **Security pattern**: Credential isolation in config files

### Content Processing Pipeline
- **Image extraction**: Selenium wire requests → URL patterns → Download
- **PDF creation**: Image ordering → PIL processing → File output
- **OCR enhancement**: Input PDF → OCR processing → Enhanced output

### State Management
- **Version detection**: DOM parsing → Date extraction → Comparison
- **Checkpoint updates**: Successful completion → State save → Next run preparation
- **Error recovery**: Checkpoint preservation → Manual retry capability

## Technology Integration Patterns

### Selenium Integration
- **Wire protocol**: Captures network requests for URL extraction
- **Wait strategies**: Explicit waits for dynamic content loading
- **Element selection**: CSS selectors with fallback strategies

### Google Services Integration
- **Service account pattern**: JSON key → Authentication → API access
- **Drive API usage**: Upload → Permission setting → Link generation
- **Gmail integration**: SMTP → HTML email → Link embedding

### File System Patterns
- **Temporary storage**: Context managers for automatic cleanup
- **Output organization**: Date-based naming → Predictable structure
- **Resource management**: File handles → Memory cleanup → Storage efficiency

## Error Handling Strategies

### Graceful Degradation
- **Network issues**: Retry logic with exponential backoff
- **Authentication failures**: Clear error messages with resolution steps
- **File operations**: Atomic operations with rollback capability

### Logging Pattern
- **Structured logging**: Component → Action → Result pattern
- **Debug information**: Request URLs, file paths, processing steps
- **Error context**: Full stack traces with business context

## Scalability Considerations

### Current Limitations
- **Single publication**: Designed specifically for Edge Weekly
- **Sequential processing**: No parallel image downloading
- **Local execution**: Single machine dependency

### Extension Points
- **Configuration-driven sources**: Easy addition of new publications
- **Modular components**: Independent component replacement/enhancement
- **Plugin architecture**: Additional processing steps can be inserted
