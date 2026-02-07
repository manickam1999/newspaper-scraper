from datetime import datetime
import os
import time
import traceback
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
    
    # Use environment variable for Chrome binary, with fallback paths
    chrome_bin = os.environ.get('CHROME_BIN')
    if chrome_bin and os.path.exists(chrome_bin):
        chrome_options.binary_location = chrome_bin
    elif os.path.exists("/usr/bin/chromium"):
        chrome_options.binary_location = "/usr/bin/chromium"
    elif os.path.exists("/usr/bin/google-chrome-stable"):
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


def save_debug_snapshot(driver, prefix, step_name):
    """
    Save screenshot and HTML dump for debugging.

    Args:
        driver: Selenium WebDriver instance
        prefix: Prefix for filename (e.g., "login_failure")
        step_name: Description of the step (e.g., "after_login_button_click")

    Returns:
        tuple: (screenshot_path, html_path)
    """
    # Create debug directory if it doesn't exist
    debug_dir = "/home/rajesh/Desktop/newspaper-scraper/debug"
    os.makedirs(debug_dir, exist_ok=True)

    # Generate timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save screenshot
    screenshot_filename = f"{prefix}_{step_name}_{timestamp}.png"
    screenshot_path = os.path.join(debug_dir, screenshot_filename)
    try:
        driver.save_screenshot(screenshot_path)
        logger.info(f"Screenshot saved: {screenshot_path}")
    except Exception as e:
        logger.error(f"Failed to save screenshot: {e}")
        screenshot_path = None

    # Save HTML source
    html_filename = f"{prefix}_{step_name}_{timestamp}.html"
    html_path = os.path.join(debug_dir, html_filename)
    try:
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info(f"HTML dump saved: {html_path}")
    except Exception as e:
        logger.error(f"Failed to save HTML: {e}")
        html_path = None

    return screenshot_path, html_path


def log_page_elements(driver, description="Page elements"):
    """
    Log all input fields and buttons visible on the page for debugging.

    Args:
        driver: Selenium WebDriver instance
        description: Description of what's being logged
    """
    try:
        logger.info(f"=== {description} ===")

        # Log all input fields
        inputs = driver.find_elements(By.TAG_NAME, "input")
        logger.info(f"Found {len(inputs)} input fields:")
        for i, inp in enumerate(inputs[:10]):  # Limit to first 10
            input_id = inp.get_attribute("id") or "no-id"
            input_type = inp.get_attribute("type") or "no-type"
            input_name = inp.get_attribute("name") or "no-name"
            input_placeholder = inp.get_attribute("placeholder") or "no-placeholder"
            is_visible = inp.is_displayed()
            logger.info(f"  Input {i}: id='{input_id}', type='{input_type}', name='{input_name}', "
                       f"placeholder='{input_placeholder}', visible={is_visible}")

        # Log all buttons
        buttons = driver.find_elements(By.TAG_NAME, "button")
        logger.info(f"Found {len(buttons)} buttons:")
        for i, btn in enumerate(buttons[:10]):  # Limit to first 10
            btn_text = btn.text or "no-text"
            btn_id = btn.get_attribute("id") or "no-id"
            is_visible = btn.is_displayed()
            logger.info(f"  Button {i}: id='{btn_id}', text='{btn_text}', visible={is_visible}")

        logger.info(f"=== End {description} ===")

    except Exception as e:
        logger.error(f"Failed to log page elements: {e}")


def scrape_magazine(driver, config, checkpoint, temp_dir):
    edge_config = config["edge"]
    url, username, password = edge_config["url"], edge_config["username"], edge_config["password"]
    config_cookie = edge_config.get("cookie")  # Keep as fallback

    # Initialize cookie manager
    cookie_manager = CookieManager(session_dir="session")

    if "edge" not in checkpoint:
        checkpoint["edge"] = {"version": None}
    latest, date = is_latest(driver, url, checkpoint["edge"]["version"])
    if latest:
        logger.info("Exiting script as the latest version is already published")
        return None, None, None

    formatted_date = datetime.strptime(date, "%d/%m/%Y").strftime("%Y%m%d")

    # Login and extract cookies automatically
    authenticated, fresh_cookie = login_and_extract_cookies(
        driver, cookie_manager, url, username, password
    )
    if not authenticated:
        logger.error("Authentication failed")
        return None, None, None

    # Use fresh cookie if available, otherwise fallback to config cookie
    active_cookie = fresh_cookie if fresh_cookie else config_cookie

    total_pages = get_total_pages(driver)
    zoom_url = get_zoom_url(driver)

    logger.info(f"Using temporary directory: {temp_dir}")
    fetch_images(zoom_url, total_pages, temp_dir, formatted_date, active_cookie)
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


def login_and_extract_cookies(driver, cookie_manager, url, username, password):
    """
    Perform fresh login and extract cookies for API calls.

    Flow:
    1. Perform fresh login
    2. Enable workstation (handle modal)
    3. Extract cookies from Selenium
    4. Convert to HTTP string format
    5. Update config.yaml
    6. Return HTTP cookie string for immediate use

    Args:
        driver: Selenium WebDriver instance
        cookie_manager: CookieManager instance
        url: Website URL
        username: Login username
        password: Login password

    Returns:
        tuple: (authenticated: bool, http_cookie_string: str or None)
    """
    try:
        # Step 1: Perform fresh login
        authenticated = login_with_credentials(driver, url, username, password)
        if not authenticated:
            logger.error("Login failed, cannot extract cookies")
            return False, None

        # Step 2: Enable workstation (handle modal if it appears)
        enable_workstation(driver)

        # Step 3: Extract cookies from Selenium driver
        http_cookie = cookie_manager.cookies_to_http_string(
            driver,
            domain_filter="theedgemalaysia.com"
        )

        if not http_cookie:
            logger.error("Failed to extract HTTP cookie string")
            return True, None  # Login succeeded but cookie extraction failed

        # Step 4: Save cookies in Selenium format (optional, for reference)
        cookie_manager.save_cookies(driver, "edge")

        # Step 5: Update config.yaml with HTTP cookie string
        cookie_manager.update_config_cookie(http_cookie, config_file="config/config.yaml")

        logger.info("Cookie extraction and config update completed successfully")
        return True, http_cookie

    except Exception as e:
        logger.error(f"Error in login_and_extract_cookies: {e}")
        return False, None


def login_with_credentials(driver, url, username, password):
    """
    Enhanced login using username and password with robust error handling and debugging.

    Args:
        driver: Selenium WebDriver instance
        url: Website URL
        username: Login username
        password: Login password

    Returns:
        bool: True if login successful, False otherwise
    """
    try:
        # Navigate to the site
        driver.get(url)
        logger.info("Navigated to Edge website")

        # Save debug snapshot after page load
        save_debug_snapshot(driver, "login_flow", "01_page_loaded")

        # Wait for page to fully load
        time.sleep(2)  # Allow any dynamic content to load

        # Check if already logged in (cookie still valid)
        try:
            already_logged_in = driver.find_elements(By.CSS_SELECTOR, "i.ti-user.ti-user-logged")
            if already_logged_in and any(elem.is_displayed() for elem in already_logged_in):
                logger.info("Already logged in via cookie - skipping manual login")
                save_debug_snapshot(driver, "login_flow", "02_already_logged_in")

                # Navigate directly to the paper section
                logger.info("Finding latest paper link")
                try:
                    latest_paper = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[title="The Edge Malaysia"]'))
                    )
                    latest_paper.click()
                    logger.info("Latest paper link clicked")
                    save_debug_snapshot(driver, "login_flow", "03_paper_opened_via_cookie")
                    logger.info("Login flow completed successfully (via cookie)")
                    return True
                except TimeoutException:
                    logger.warning("Latest paper link not found, will try manual login")
        except Exception as e:
            logger.debug(f"Could not check logged-in status: {e}")

        # Check for cookie consent or popups that might block interaction
        try:
            # Common cookie consent selectors
            cookie_buttons = driver.find_elements(By.XPATH,
                "//*[contains(text(), 'Accept') or contains(text(), 'OK') or contains(text(), 'Agree')]")
            for btn in cookie_buttons:
                if btn.is_displayed():
                    logger.info(f"Found potential cookie consent button: {btn.text}")
                    btn.click()
                    logger.info("Clicked cookie consent button")
                    time.sleep(1)
                    break
        except Exception as e:
            logger.debug(f"No cookie consent popup found or error clicking it: {e}")

        # Login Button - with explicit wait
        # Find actual login button (not "My profile" which also has vc_open_login class)
        logger.info("Finding login button")
        try:
            # Look for login button that does NOT have the logged-in icon
            login_buttons = driver.find_elements(By.CSS_SELECTOR, "a.vc_open_login.vc_nav_link")
            login_button = None

            for btn in login_buttons:
                # Skip if this is the "My profile" link (has ti-user-logged icon)
                if btn.find_elements(By.CSS_SELECTOR, "i.ti-user.ti-user-logged"):
                    logger.debug("Skipping 'My profile' link")
                    continue
                # This should be the actual login button
                if btn.is_displayed():
                    login_button = btn
                    logger.info("Found actual login button")
                    break

            if not login_button:
                logger.error("Login button not found (only found My Profile link)")
                save_debug_snapshot(driver, "login_failure", "02_login_button_not_found")
                log_page_elements(driver, "Page state when login button not found")
                return False

            # Scroll into view to ensure visibility
            driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
            time.sleep(0.5)

            # Click using JavaScript
            driver.execute_script("arguments[0].click();", login_button)
            logger.info("Login button clicked")
        except TimeoutException:
            logger.error("Login button not found within 15 seconds")
            save_debug_snapshot(driver, "login_failure", "02_login_button_not_found")
            log_page_elements(driver, "Page state when login button not found")
            return False

        # Wait for modal to appear and stabilize
        time.sleep(2)  # Give modal time to animate/render
        save_debug_snapshot(driver, "login_flow", "03_after_login_button_click")

        # Log all input fields on the page to help identify the correct selector
        log_page_elements(driver, "After login button click")

        # Login Form - Try multiple strategies to find username field
        logger.info("Finding username field")
        username_field = None

        # Strategy 1: Wait for ID "input_username"
        try:
            username_field = WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.ID, "input_username"))
            )
            logger.info("Found username field by ID: input_username")
        except TimeoutException:
            logger.warning("Username field not found by ID 'input_username', trying alternative selectors")

        # Strategy 2: Try common username field selectors
        if not username_field:
            alternative_selectors = [
                (By.NAME, "username"),
                (By.NAME, "user"),
                (By.NAME, "email"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='username' i]"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='email' i]"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.XPATH, "//input[@type='text' or @type='email'][1]"),  # First text/email input
            ]

            for by_type, selector in alternative_selectors:
                try:
                    username_field = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((by_type, selector))
                    )
                    logger.info(f"Found username field using {by_type}: {selector}")
                    break
                except TimeoutException:
                    continue

        # If still not found, fail with debug info
        if not username_field:
            logger.error("Username field not found with any selector strategy")
            save_debug_snapshot(driver, "login_failure", "04_username_field_not_found")
            log_page_elements(driver, "Page state when username field not found")
            return False

        # Fill username
        username_field.clear()
        username_field.send_keys(username)
        logger.info("Username entered")

        # Password Field - with robust selector strategy
        logger.info("Finding password field")
        password_field = None

        try:
            password_field = driver.find_element(By.ID, "input_password")
            logger.info("Found password field by ID: input_password")
        except NoSuchElementException:
            # Try alternative selectors
            alternative_password_selectors = [
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
            ]
            for by_type, selector in alternative_password_selectors:
                try:
                    password_field = driver.find_element(by_type, selector)
                    logger.info(f"Found password field using {by_type}: {selector}")
                    break
                except NoSuchElementException:
                    continue

        if not password_field:
            logger.error("Password field not found")
            save_debug_snapshot(driver, "login_failure", "05_password_field_not_found")
            return False

        password_field.clear()
        password_field.send_keys(password)
        logger.info("Password entered")

        # Save state before clicking submit
        save_debug_snapshot(driver, "login_flow", "06_before_submit")

        # Submit Button - with robust selector strategy
        logger.info("Finding submit button")
        submit_button = None

        try:
            submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
            logger.info("Found submit button by text 'Login'")
        except NoSuchElementException:
            # Try alternative selectors
            alternative_submit_selectors = [
                (By.XPATH, "//button[@type='submit']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//input[@type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Sign in')]"),
                (By.XPATH, "//button[contains(text(), 'Log in')]"),
            ]
            for by_type, selector in alternative_submit_selectors:
                try:
                    submit_button = driver.find_element(by_type, selector)
                    logger.info(f"Found submit button using {by_type}: {selector}")
                    break
                except NoSuchElementException:
                    continue

        if not submit_button:
            logger.error("Submit button not found")
            save_debug_snapshot(driver, "login_failure", "07_submit_button_not_found")
            return False

        submit_button.click()
        logger.info("Submit button clicked")

        # Wait for page transition
        time.sleep(2)
        save_debug_snapshot(driver, "login_flow", "08_after_submit")

        # Check for login confirmation - with increased timeout
        logger.info("Waiting for login confirmation")
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "i.ti-user.ti-user-logged"))
            )
            logger.info("Login confirmed by presence of logged-in user icon")
        except TimeoutException:
            logger.error("Login confirmation icon not found - login may have failed")
            save_debug_snapshot(driver, "login_failure", "09_no_login_confirmation")
            log_page_elements(driver, "Page state after login attempt")

            # Check for error messages
            try:
                error_elements = driver.find_elements(By.XPATH,
                    "//*[contains(@class, 'error') or contains(@class, 'alert')]")
                if error_elements:
                    for elem in error_elements:
                        if elem.is_displayed():
                            logger.error(f"Error message on page: {elem.text}")
            except Exception as e:
                logger.debug(f"Could not check for error messages: {e}")

            return False

        save_debug_snapshot(driver, "login_flow", "10_login_confirmed")

        # Navigate to the paper section
        logger.info("Finding latest paper link")
        try:
            latest_paper = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[title="The Edge Malaysia"]'))
            )
            latest_paper.click()
            logger.info("Latest paper link clicked")
        except TimeoutException:
            logger.error("Latest paper link not found")
            save_debug_snapshot(driver, "login_failure", "11_paper_link_not_found")
            return False

        save_debug_snapshot(driver, "login_flow", "12_final_success")
        logger.info("Login flow completed successfully")
        return True

    except Exception as e:
        logger.error(f"Login failed with exception: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Save debug snapshot on any exception
        try:
            save_debug_snapshot(driver, "login_exception", "error_state")
            log_page_elements(driver, "Page state during exception")
        except Exception as debug_error:
            logger.error(f"Failed to save debug snapshot during exception handling: {debug_error}")

        return False


def enable_workstation(driver):
    """
    Handle the workstation enabling modal that appears after login.
    The modal has an 'Enable' button that must be clicked.
    """
    try:
        # Wait for the modal and Enable button to appear
        logger.info("Checking for workstation enable modal...")
        enable_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[title="Enable"]'))
        )

        # Click the enable button (use JavaScript click to ensure onclick handler fires)
        driver.execute_script("arguments[0].click();", enable_button)
        logger.info("Workstation enable button clicked")

        # Wait for modal to disappear (wait for the button to become stale/removed)
        WebDriverWait(driver, 10).until(EC.staleness_of(enable_button))
        logger.info("Workstation enabled successfully")

    except TimeoutException:
        # Modal didn't appear - workstation already enabled or not required
        logger.info("No workstation enable modal found - continuing")
    except Exception as e:
        logger.warning(f"Error enabling workstation: {e}")


def get_total_pages(driver):
    total_pages = driver.find_element(By.CSS_SELECTOR, "i.vc_icon.fa.totalPages").text
    logger.info(f"Total pages: {total_pages}")
    return int(total_pages)


def get_zoom_url(driver):
    for request in driver.requests:
        if "Zoom-1" in request.url:
            logger.info(f"Zoom URL: {request.url}")
            return request.url
