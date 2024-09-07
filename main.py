import os
import tempfile
import requests
import yaml
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from PIL import Image

from src.drive import (
    find_or_create_folder,
    get_google_drive_service,
    set_file_permissions,
    upload_to_drive,
)
from src.email import send_email
from utils import logger


def load_config(file):
    with open(file, "r") as file:
        return yaml.safe_load(file)


def is_latest(driver, url, version):
    driver.get(url)
    logger.info("Finding the latest date")
    date = driver.find_element(By.ID, "vc_edition_calendar_1").get_attribute("value")
    if date == version:
        logger.info("The latest version is already downloaded")
        return True, date
    logger.info("The latest version is not downloaded")
    return False, date


def login(driver, username, password):
    # Login Button
    logger.info("Finding for login button")
    login_button = driver.find_element(By.CSS_SELECTOR, "a.vc_open_login.vc_nav_link")
    driver.execute_script("arguments[0].click();", login_button)
    logger.info("Login button clicked")

    # Login Form
    logger.info("Finding for username field")
    username_field = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "input_username"))
    )
    username_field.send_keys(username)

    logger.info("Finding for password field")
    password_field = driver.find_element(By.ID, "input_password")
    password_field.send_keys(password)

    # Submit Button for login form
    logger.info("Finding for submit button")
    submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
    submit_button.click()
    logger.info("Submit button clicked")

    # Check for login confirmation
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "i.ti-user.ti-user-logged"))
    )
    logger.info("Login confirmed by presence of logged-in user icon")

    latest_paper = driver.find_element(By.CSS_SELECTOR, 'a[title="The Edge Malaysia"]')
    latest_paper.click()
    logger.info("Latest paper link clicked")


def enable_workstation(driver):
    click_counter = 0
    while True:
        try:
            enable_workstation = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[title="Enable"]'))
            )
            enable_workstation.click()
            click_counter += 1
            logger.info(f"Enable workstation clicked {click_counter} time(s)")
        except TimeoutException:
            logger.info(
                f"Element not found after {click_counter} click(s). Exiting loop."
            )
            break
        except NoSuchElementException:
            logger.info(
                f"Element no longer exists after {click_counter} click(s). Exiting loop."
            )
            break


def get_total_pages(driver):
    total_pages = driver.find_element(By.CSS_SELECTOR, "i.vc_icon.fa.totalPages").text
    logger.info(f"Total pages: {total_pages}")
    return int(total_pages)


def get_zoom_url(driver):
    for request in driver.requests:
        if "Zoom-1" in request.url:
            logger.info(f"Zoom URL: {request.url}")
            return request.url


def fetch_images(session, zoom_url, total_pages, temp_dir):
    base_url = zoom_url.rsplit("Zoom-", 1)[0]

    for page in range(1, total_pages + 1):
        image_url = f"{base_url}Zoom-{page}.jpg"
        progress = (page / total_pages) * 100
        logger.info(
            f"Fetching image {page} of {total_pages} ({progress:.2f}% complete)"
        )

        try:
            response = session.get(image_url)
            response.raise_for_status()

            image_path = os.path.join(temp_dir, f"page_{page}.jpg")
            with open(image_path, "wb") as file:
                file.write(response.content)

            logger.info(f"Successfully downloaded image {page}")

        except requests.RequestException as e:
            logger.error(f"Failed to download image {page}: {str(e)}")

    logger.info(f"All images have been fetched and saved in {temp_dir}")


def create_pdf_from_images(temp_dir, output_file, total_pages):
    images = []
    for page in range(1, total_pages + 1):
        image_path = os.path.join(temp_dir, f"page_{page}.jpg")
        if os.path.exists(image_path):
            images.append(image_path)
            logger.info(f"Added page {page} to images list")
        else:
            logger.warning(f"Image for page {page} not found")
    if len(images) > 0:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        try:
            with Image.open(images[0]) as first_image:
                first_image.save(
                    output_file,
                    "PDF",
                    resolution=100.0,
                    save_all=True,
                    append_images=(Image.open(img) for img in images[1:]),
                )
            logger.info(f"PDF created successfully: {output_file}")
        except Exception as e:
            logger.error(f"Error creating PDF: {str(e)}")
    else:
        logger.error("No images found to create PDF")


def main():
    config = load_config("config.yaml")
    checkpoint_file = "checkpoint.yaml"
    if os.path.exists(checkpoint_file):
        checkpoint = load_config(checkpoint_file)
        logger.info(
            f"Checkpoint file {checkpoint_file} found with version {checkpoint.get('version')}"
        )
    else:
        logger.info(f"Checkpoint file {checkpoint_file} not found. Creating a new one.")
        checkpoint = {"version": None}

    driver = webdriver.Chrome(service=Service(), options=webdriver.ChromeOptions())

    try:
        # edge config
        edge_config = config.get("edge")
        url = edge_config.get("url")
        username = edge_config.get("username")
        password = edge_config.get("password")

        # email
        email_config = config.get("email", {})
        sender_email = email_config.get("sender_email")
        sender_password = email_config.get("sender_password")
        receiver_emails = email_config.get("receiver_emails", [])
        service_account_file = config.get("google_drive", {}).get(
            "service_account_file"
        )
        folder_name = config.get("google_drive", {}).get("folder_name")

        version = checkpoint.get("version")

        latest, date = is_latest(driver, url, version)

        if latest:
            logger.info("Exiting script as the latest version is already published")
            return

        login(driver, username, password)
        enable_workstation(driver)
        total_pages = get_total_pages(driver)
        zoom_url = get_zoom_url(driver)

        session = requests.Session()
        for cookie in driver.get_cookies():
            session.cookies.set(cookie["name"], cookie["value"])

        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Created temporary directory: {temp_dir}")
            fetch_images(session, zoom_url, total_pages, temp_dir)
            file_name = f"Edge Magazine - {date}.pdf"
            output_file = os.path.join(temp_dir, file_name)
            create_pdf_from_images(temp_dir, output_file, total_pages)

            try:
                drive_service = get_google_drive_service(service_account_file)
                folder_id = find_or_create_folder(drive_service, folder_name)
                file_id, drive_link = upload_to_drive(
                    drive_service, output_file, file_name, folder_id
                )
            except Exception as e:
                logger.error(
                    f"Failed to upload to Google Drive or set permissions: {str(e)}"
                )
                raise e

        set_file_permissions(drive_service, file_id, receiver_emails)
        subject = email_config.get("subject", f"Edge Magazine PDF - {date}")
        body = (
            email_config.get(
                "body", "Please find the link to the latest Edge Magazine PDF below:"
            )
            + f"\n\n{drive_link}"
        )

        if sender_email and sender_password and receiver_emails:
            if send_email(
                sender_email, sender_password, receiver_emails, subject, body
            ):
                print("Email sent successfully with Google Drive link")
            else:
                print("Failed to send email")
        else:
            print("Email configuration is incomplete. Skipping email sending.")

        checkpoint["version"] = date
        with open("checkpoint.yaml", "w") as file:
            yaml.dump(checkpoint, file)
        logger.info("Checkpoint has been updated with f{date}")

        input("Press Enter to close the browser...")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
