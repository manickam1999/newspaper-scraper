import logging
import os
import tempfile
import requests
import yaml
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from PIL import Image

def create_custom_logger():
    logger = logging.getLogger('edge-converter')
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    file_handler = logging.FileHandler('edge_converter.log')
    file_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

def login(driver, url, username, password, logger):
    driver.get(url)
    
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
        EC.presence_of_element_located((By.CSS_SELECTOR, 'i.ti-user.ti-user-logged'))
    )
    logger.info("Login confirmed by presence of logged-in user icon")
    
    latest_paper = driver.find_element(By.CSS_SELECTOR, 'a[title="The Edge Malaysia"]')
    latest_paper.click()
    logger.info("Latest paper link clicked")
    
def enable_workstation(driver, logger):
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
            logger.info(f"Element not found after {click_counter} click(s). Exiting loop.")
            break
        except NoSuchElementException:
            logger.info(f"Element no longer exists after {click_counter} click(s). Exiting loop.")
            break
        
def get_total_pages(driver, logger):
    total_pages = driver.find_element(By.CSS_SELECTOR, 'i.vc_icon.fa.totalPages').text
    logger.info(f"Total pages: {total_pages}")
    return int(total_pages)

def get_zoom_url(driver, logger):
    for request in driver.requests:
        if 'Zoom-1' in request.url:
            logger.info(f"Zoom URL: {request.url}")
            return request.url
        
def fetch_images(session, zoom_url, total_pages, temp_dir, logger):
    base_url = zoom_url.rsplit('Zoom-', 1)[0]
    
    for page in range(1, total_pages + 1):
        image_url = f"{base_url}Zoom-{page}.jpg"
        progress = (page / total_pages) * 100
        logger.info(f"Fetching image {page} of {total_pages} ({progress:.2f}% complete)")
        
        try:
            response = session.get(image_url)
            response.raise_for_status()
            
            image_path = os.path.join(temp_dir, f'page_{page}.jpg')
            with open(image_path, 'wb') as file:
                file.write(response.content)
            
            logger.info(f"Successfully downloaded image {page}")
        
        except requests.RequestException as e:
            logger.error(f"Failed to download image {page}: {str(e)}")
    
    logger.info(f"All images have been fetched and saved in {temp_dir}")

def create_pdf_from_images(temp_dir, output_file, total_pages, logger):
    images = []
    for page in range(1, total_pages + 1):
        image_path = os.path.join(temp_dir, f'page_{page}.jpg')
        if os.path.exists(image_path):
            images.append(image_path)
            logger.info(f"Added page {page} to images list")
        else:
            logger.warning(f"Image for page {page} not found")
    
    if len(images) > 0:
        try:
            with Image.open(images[0]) as first_image:
                first_image.save(
                    output_file,
                    "PDF",
                    resolution=100.0,
                    save_all=True,
                    append_images=(Image.open(img) for img in images[1:])
                )
            logger.info(f"PDF created successfully: {output_file}")
        except Exception as e:
            logger.error(f"Error creating PDF: {str(e)}")
    else:
        logger.error("No images found to create PDF")


def main():
    logger = create_custom_logger()
    config = load_config()
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    
    try:
        edge_config = config.get('edge')
        url = edge_config.get('url')
        username = edge_config.get('username')
        password = edge_config.get('password')
        
        output_dir = edge_config.get('output_dir', os.getcwd())
        
        login(driver, url, username, password, logger)
        enable_workstation(driver, logger)
        total_pages = get_total_pages(driver, logger)
        zoom_url = get_zoom_url(driver, logger)
        
        session = requests.Session()
        for cookie in driver.get_cookies():
            session.cookies.set(cookie['name'], cookie['value'])
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(script_dir, "edge_magazine.pdf")
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Created temporary directory: {temp_dir}")
            fetch_images(session, zoom_url, total_pages, temp_dir, logger)
            output_file = os.path.join(output_dir, "edge_magazine.pdf")
            create_pdf_from_images(temp_dir, output_file, total_pages, logger)
        
        logger.info(f"PDF has been saved in {output_file}")
        logger.info("Temporary directory has been automatically removed")
        
        input("Press Enter to close the browser...")
        
    finally:
        # driver.quit()
        pass

if __name__ == "__main__":
    main()