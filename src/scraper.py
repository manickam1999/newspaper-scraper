from datetime import datetime
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from src.pages import create_pdf_from_images, fetch_images
from utils.logger import logger
from utils.cookies import CookieManager
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options

def setup_driver():
    chrome_options = Options()
    
    # Essential Chrome options for headless/server environments
    chrome_options.add_argument("--headless")  # Enable headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--user-data-dir=/tmp/chrome-profile")
    
    # Explicitly set Chrome binary path
    chrome_options.binary_location = "/usr/bin/google-chrome-stable"
    
    try:
        # First try with webdriver-manager for compatible ChromeDriver
        logger.info("Initializing Chrome driver with webdriver-manager")
        from webdriver_manager.chrome import ChromeDriverManager
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Chrome driver initialized successfully with webdriver-manager")
        return driver
    except ImportError:
        logger.info("webdriver-manager not available, trying system ChromeDriver")
        try:
            service = ChromeService()
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Chrome driver initialized successfully with system ChromeDriver")
            return driver
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver with system ChromeDriver: {e}")
            raise e
    except Exception as e:
        logger.error(f"Failed to initialize Chrome driver with webdriver-manager: {e}")
        logger.info("Trying system ChromeDriver as fallback")
        try:
            service = ChromeService()
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Chrome driver initialized successfully with system ChromeDriver")
            return driver
        except Exception as e2:
            logger.error(f"Failed to initialize Chrome driver with system ChromeDriver: {e2}")
            raise e2


def scrape_magazine(driver, config, checkpoint, temp_dir):
    edge_config = config["edge"]
    url, username, password = edge_config["url"], edge_config["username"], edge_config["password"]
    
    # Initialize cookie manager
    cookie_manager = CookieManager()
    
    if "edge" not in checkpoint:
        checkpoint["edge"] = {"version": None}
    latest, date = is_latest(driver, url, checkpoint["edge"]["version"])
    if latest:
        logger.info("Exiting script as the latest version is already published")
        return None, None, None
    
    formatted_date = datetime.strptime(date, "%d/%m/%Y").strftime("%Y%m%d")
    
    # Try to authenticate using cookies first, fallback to manual login
    authenticated = authenticate_with_cookies(driver, cookie_manager, url, username, password)
    if not authenticated:
        logger.error("Authentication failed")
        return None, None, None
    
    total_pages = get_total_pages(driver)
    zoom_url = get_zoom_url(driver)

    logger.info(f"Using temporary directory: {temp_dir}")
    fetch_images(zoom_url, total_pages, temp_dir, formatted_date)
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


def authenticate_with_cookies(driver, cookie_manager, url, username, password):
    """Try to authenticate using saved cookies, fallback to manual login"""
    logger.info("Attempting authentication with cookie management")
    
    # First, navigate to the site
    driver.get(url)
    
    # Try to load existing cookies
    cookies_loaded = cookie_manager.load_cookies(driver, "edge")
    
    if cookies_loaded:
        # Check if cookies are still valid
        if cookie_manager.are_cookies_valid(driver):
            logger.info("Authentication successful using saved cookies")
            # Navigate to the paper section
            try:
                latest_paper = driver.find_element(By.CSS_SELECTOR, 'a[title="The Edge Malaysia"]')
                latest_paper.click()
                logger.info("Latest paper link clicked")
                return True
            except Exception as e:
                logger.warning(f"Failed to navigate to paper section with cookies: {e}")
                # Continue to manual login
    
    # Cookies didn't work, try manual login
    logger.info("Cookies invalid or not found, performing manual login")
    return login_and_save_cookies(driver, cookie_manager, username, password)

def login_and_save_cookies(driver, cookie_manager, username, password):
    """Perform manual login and save cookies for future use"""
    try:
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

        # Save cookies after successful login
        cookie_manager.save_cookies(driver, "edge")
        logger.info("Cookies saved after successful login")

        # Navigate to the paper section
        latest_paper = driver.find_element(By.CSS_SELECTOR, 'a[title="The Edge Malaysia"]')
        latest_paper.click()
        logger.info("Latest paper link clicked")
        
        return True
        
    except Exception as e:
        logger.error(f"Manual login failed: {e}")
        return False

def login(driver, username, password):
    """Legacy login function for backward compatibility"""
    cookie_manager = CookieManager()
    return login_and_save_cookies(driver, cookie_manager, username, password)


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
