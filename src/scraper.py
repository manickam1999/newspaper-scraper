import os
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from src.pages import create_pdf_from_images, fetch_images
from utils.logger import logger
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service


def setup_driver():
    return webdriver.Chrome(service=Service(), options=webdriver.ChromeOptions())


def scrape_magazine(driver, config, checkpoint, temp_dir):
    edge_config = config["edge"]
    url, username, password = edge_config["url"], edge_config["username"], edge_config["password"]

    latest, date = is_latest(driver, url, checkpoint["version"])
    if latest:
        logger.info("Exiting script as the latest version is already published")
        return None, None, None

    login(driver, username, password)
    enable_workstation(driver)
    total_pages = get_total_pages(driver)
    zoom_url = get_zoom_url(driver)

    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie["name"], cookie["value"])

    logger.info(f"Using temporary directory: {temp_dir}")
    fetch_images(session, zoom_url, total_pages, temp_dir)
    file_name = f"Edge Magazine - {date}.pdf"
    output_file = os.path.join(temp_dir, file_name)
    create_pdf_from_images(temp_dir, output_file, total_pages)
    
    logger.info(f"PDF file created at: {output_file}")
    return output_file, date, file_name


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
