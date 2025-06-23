# Project Brief: Edge Weekly Scraper

## Core Purpose
Automated newspaper scraper that downloads The Edge Weekly, converts it to PDF with OCR, uploads to Google Drive, and sends email notifications to improve accessibility for elderly users.

## Primary Goals
1. **Accessibility Enhancement**: Convert online newspaper to PDF format for easier reading by elderly users who struggle with complex web interfaces
2. **Automation**: Fully automated download, processing, and distribution pipeline
3. **Quality**: OCR-processed PDFs for better text accessibility
4. **Distribution**: Seamless sharing via Google Drive links and email notifications

## Core Requirements
- Valid subscription to The Edge Weekly required
- Web scraping with Selenium for login and content access
- PDF creation from downloaded magazine page images
- OCR processing for text accessibility
- Google Drive integration for cloud storage
- Email notifications with download links
- Checkpoint system to prevent duplicate downloads

## Target Users
- Elderly users who find the newspaper's online interface challenging
- Users who prefer PDF reading experience over web browsing
- Users who need accessible document formats

## Technical Constraints
- Requires active subscription to The Edge Weekly
- Chrome WebDriver dependency for web scraping
- Google Cloud project with Drive API access
- Gmail account for notifications
- Python 3.7+ environment

## Success Metrics
- Automatic detection and download of new issues
- Successful PDF conversion with OCR
- Reliable Google Drive upload and sharing
- Timely email notifications to recipients
- No duplicate downloads (checkpoint system working)

## Project Scope
**In Scope:**
- Web scraping of The Edge Weekly digital platform
- Image download and PDF compilation
- OCR processing for accessibility
- Google Drive storage and permissions
- Email notification system
- Checkpoint management for state tracking

**Out of Scope:**
- Other newspaper sources
- Manual intervention required processes
- Local storage as primary storage method
- Advanced PDF editing features beyond OCR
