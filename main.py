import os
import tempfile
from src.drive import (
    handle_drive_upload,
    set_file_permissions,
)
from src.email import handle_email
from src.scraper import scrape_magazine, setup_driver
from utils.logger import logger
from utils.checkpoint import load_checkpoint, save_checkpoint
from utils.config import load_config


def main():
    config = load_config("config.yaml")
    checkpoint = load_checkpoint()

    driver = setup_driver()

    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Created temporary directory: {temp_dir}")

        output_file, date, file_name = scrape_magazine(
            driver, config, checkpoint, temp_dir
        )
        if not output_file:
            return

        if os.path.exists(output_file):
            drive_service, file_id, drive_link = handle_drive_upload(
                config, output_file, file_name
            )
            set_file_permissions(
                drive_service, file_id, config["email"]["receiver_emails"]
            )

            handle_email(config, drive_link, date)

            checkpoint["version"] = date
            save_checkpoint(checkpoint)
        else:
            logger.error(f"Output file not found: {output_file}")

    driver.quit()


if __name__ == "__main__":
    main()
