import argparse
import os
import tempfile
from src.drive import (
    handle_drive_upload,
    set_file_permissions,
)
from src.email import handle_email
from src.scraper import scrape_magazine, setup_driver
from src.star.scraper import scrape_the_star
from utils.logger import logger
from utils.checkpoint import load_checkpoint, save_checkpoint
from utils.config import load_config
import ocrmypdf


def main():
    parser = argparse.ArgumentParser(description='Edge Magazine Converter')
    parser.add_argument('--cookie', help='Cookie string for authentication')
    parser.add_argument('--mode', help='edge or star newspaper', default='edge')
    args = parser.parse_args()
    
    config = load_config("config/config.yaml")
    checkpoint = load_checkpoint()

    cookie = args.cookie if args.cookie else config.get("edge", {}).get("cookie")
    mode = args.mode

    driver = setup_driver()

    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Created temporary directory: {temp_dir}")
        if mode == 'star':
            output_files, date, file_name = scrape_the_star(driver, config, checkpoint, temp_dir)
            drive_links = []
            drive_service = None
            folder_id = None
            
            for file in output_files:
                input_file = file
                ocr_output = input_file.replace(".pdf", "_ocr.pdf")
                current_file_name = os.path.basename(input_file)
                
                ocrmypdf.ocr(
                    input_file=input_file,
                    output_file=ocr_output,
                    language='eng',
                )
                
                if not ocr_output:
                    return

                if os.path.exists(ocr_output):
                    drive_service, file_id, drive_link, new_folder_id = handle_drive_upload(
                        config, ocr_output, current_file_name, is_star=True, date=date
                    )
                    folder_id = new_folder_id
                    if file_id and drive_link:
                        logger.info(f"Upload successful! Drive Link: {drive_link}")
                        drive_links.append(f"{current_file_name}: {drive_link}")
                else:
                    logger.error(f"Output file not found: {ocr_output}")
            
            if drive_links:
                set_file_permissions(
                    drive_service, folder_id, config["email"]["receiver_emails"]
                )
                
                all_links = "\n".join(drive_links)
                
                handle_email(config, all_links, date, is_star=True)
                checkpoint["the_star"]["version"] = date
                save_checkpoint(checkpoint)
        
        elif mode == 'edge':
            output_file, date, file_name = scrape_magazine(
                driver, config, checkpoint, temp_dir, cookie
            )
            
            input_file = output_file
            output_file = input_file.replace(".pdf", "_ocr.pdf")
            
            ocrmypdf.ocr(
                input_file=input_file,
                output_file=output_file,
                language='eng',
            )
            
            if not output_file:
                return

            if os.path.exists(output_file):
                drive_service, file_id, drive_link = handle_drive_upload(
                    config, output_file, file_name, is_star=False
                )
                set_file_permissions(
                    drive_service, file_id, config["email"]["receiver_emails"]
                )

                handle_email(config, drive_link, date, is_star=False)

                checkpoint["edge"]["version"] = date
                save_checkpoint(checkpoint)
            else:
                logger.error(f"Output file not found: {output_file}")

if __name__ == "__main__":
    main()
