# Edge Weekly Scraper

This project is an automated scraper for The Edge Weekly Newspaper. It logs in to the Edge Weekly website, downloads the latest issue, converts it to a PDF, uploads it to Google Drive, and sends email notifications with the download link.

> **_IMPORTANT:_** This scraper requires a valid subscription to The Edge Weekly. You can purchase a subscription at [The Edge Malaysia Subscription Page](https://subscribe.theedgemalaysia.com/subcribe-tecd.html).

## Why was this made?

This project was created to improve the reading experience for elderly users who are not tech-savvy and may find the newspaper's online interface challenging. By converting the newspaper to a PDF, it becomes much easier to read, as the only tool needed is the zoom function.

## Features

- Web scraping using Selenium
- PDF creation from downloaded images
- Google Drive integration for file storage
- Email notifications
- Checkpointing to avoid duplicate downloads

## Project Structure

- `main.py`: The entry point of the application
- `src/`
  - `scraper.py`: Contains the web scraping logic
  - `pages.py`: Handles image downloading and PDF creation
  - `drive.py`: Manages Google Drive operations
  - `email.py`: Handles email notifications
- `utils/`: Contains utility functions (logger, config, checkpoint)

## Prerequisites

- Python 3.7+
- Chrome WebDriver
- Google Cloud project with Drive API enabled
- Gmail account for sending notifications
- Active subscription to The Edge Weekly

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/manickam1999/edge-magazine-scraper.git
   cd edge-magazine-scraper
   ```

2. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up Google Drive API:
   - Follow the guide at [How to Create a Google Service Account for API Access](https://www.labnol.org/google-api-service-account-220404) to:
     - Create a service account
     - Download the service account JSON key file
     - Create a folder in Google Drive
     - Share the folder with the service account email

   This step will provide you with the `service_account_file` path and the `folder_name` for your config.

4. Set up your `config.yaml` file with the following structure:

   ```yaml
   edge:
     url: "https://digital.theedgemalaysia.com/"
     username: "your_username"
     password: "your_password"

   google_drive:
     service_account_file: "path/to/your/service_account.json"
     folder_name: "edge-weekly"

   email:
     sender_email: "your_email@gmail.com"
     sender_password: "your_app_password"
     receiver_emails:
       - "recipient1@example.com"
       - "recipient2@example.com"
     subject: "Edge Weekly PDF"
     body: "Please find the link to the latest Edge Weekly PDF below:"
   ```

## Usage

Run the script with:

```bash
python main.py
```

The script will:

1. Check if there's a new issue available
2. If so, it will download the newspaper pages
3. Convert the pages to a PDF
4. Upload the PDF to Google Drive
5. Send email notifications with the download link
