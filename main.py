import os
import sys
import signal
import tempfile
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import pytz

from src.drive import (
    handle_drive_upload,
    set_file_permissions,
)
from src.email import handle_email
from src.scraper import scrape_magazine, setup_driver
from utils.logger import logger
from utils.checkpoint import load_checkpoint, save_checkpoint
from utils.config import load_config
import ocrmypdf


def run_scraper():
    """
    Main scraping function - encapsulates the scraping workflow.
    Called by the scheduler every Saturday at 4am.
    """
    logger.info("=" * 60)
    logger.info(f"Starting scheduled scraper run at {datetime.now()}")
    logger.info("=" * 60)

    driver = None
    try:
        config = load_config("config/config.yaml")
        checkpoint = load_checkpoint()

        driver = setup_driver()

        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Created temporary directory: {temp_dir}")

            output_file, date, file_name = scrape_magazine(
                driver, config, checkpoint, temp_dir
            )

            if not output_file:
                logger.info("No new newspaper to process (already up to date)")
                return

            input_file = output_file
            output_file = input_file.replace(".pdf", "_ocr.pdf")

            ocrmypdf.ocr(
                input_file=input_file,
                output_file=output_file,
                language='eng',
            )

            if os.path.exists(output_file):
                drive_service, file_id, drive_link = handle_drive_upload(
                    config, output_file, file_name
                )
                set_file_permissions(
                    drive_service, file_id, config["email"]["receiver_emails"]
                )

                handle_email(config, drive_link, date)

                if "edge" not in checkpoint:
                    checkpoint["edge"] = {}
                checkpoint["edge"]["version"] = date
                save_checkpoint(checkpoint)

                logger.info(f"Successfully processed newspaper dated {date}")
            else:
                logger.error(f"Output file not found: {output_file}")

    except Exception as e:
        logger.error(f"Scraper run failed with error: {e}", exc_info=True)
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")

    logger.info("Scraper run completed")
    logger.info("=" * 60)


def job_listener(event):
    """Listener for scheduler job events."""
    if event.exception:
        logger.error(f"Job {event.job_id} failed with exception: {event.exception}")
    else:
        logger.info(f"Job {event.job_id} executed successfully")


def main():
    """
    Main entry point - sets up scheduler for weekly Saturday 4am runs.
    """
    timezone = pytz.timezone('Asia/Kuala_Lumpur')

    logger.info("=" * 60)
    logger.info("Newspaper Scraper Scheduler Starting")
    logger.info(f"Timezone: {timezone}")
    logger.info(f"Current time: {datetime.now(timezone)}")
    logger.info("Scheduled: Every Saturday at 4:00 AM")
    logger.info("=" * 60)

    scheduler = BlockingScheduler(timezone=timezone)

    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    scheduler.add_job(
        run_scraper,
        CronTrigger(
            day_of_week='sat',
            hour=4,
            minute=0,
            timezone=timezone
        ),
        id='weekly_newspaper_scrape',
        name='Weekly Newspaper Scraper',
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )

    job = scheduler.get_job('weekly_newspaper_scrape')
    if job:
        next_run = job.trigger.get_next_fire_time(None, datetime.now(timezone))
        logger.info(f"Next scheduled run: {next_run}")

    if os.environ.get('RUN_ON_STARTUP', '').lower() == 'true':
        logger.info("RUN_ON_STARTUP is set - running scraper immediately")
        run_scraper()

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down scheduler...")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        logger.info("Scheduler started. Waiting for scheduled runs...")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    main()
