from datetime import datetime
import os
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from utils.logger import logger

def scrape_the_sun(driver, config, checkpoint, temp_dir, cookie=None):
    try:
        logger.info("Starting to scrape The Sun")
        sun_config = config["the_sun"]
        base_url = sun_config["url"]
        date = datetime.today().strftime('%Y%m%d')
        if date == checkpoint["sun"]["version"]:
            logger.info("The Sun: No new version available")
            return None, None, None
            
        url = f"{base_url}{date}"
        logger.info(f"Constructed URL for scraping: {url}")
        driver.get(url)

        wait = WebDriverWait(driver, 30)
        
        logger.info("Waiting for download button to appear...")
        btn_download = wait.until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR, 
                'button[title="Download"]'
            ))
        )
        
        logger.info("Waiting for preloader to disappear...")
        wait.until(
            EC.invisibility_of_element_located((
                By.ID, 
                'preloader'
            ))
        )
        
        logger.info("Download button found, attempting to click")
        try:
            btn_download.click()
        except:
            logger.info("Regular click failed, attempting JavaScript click")
            driver.execute_script("arguments[0].click();", btn_download)
        
        logger.info("Waiting for PDF download link to appear...")
        pdf_link = wait.until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                'a[download][title="Download the publication as a PDF file"]'
            ))
        )
        
        logger.info("Clicking PDF download link...")
        pdf_link.click()
        
        pdf_link = wait.until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                'a[download][title="Download the publication as a PDF file"]'
            ))
        )
        
        logger.info("Getting PDF download URL...")
        pdf_link = wait.until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                'a[download][title="Download the publication as a PDF file"]'
            ))
        )
        pdf_url = pdf_link.get_attribute('href')
        logger.info(f"PDF URL extracted: {pdf_url}")

        # Download PDF file
        logger.info("Initiating PDF download...")
        response = requests.get(pdf_url, stream=True)
        if response.status_code != 200:
            raise Exception(f"Failed to download PDF. Status code: {response.status_code}")

        # Setup file path
        pdf_filename = f"The Sun - {date}.pdf"
        pdf_path = os.path.join(temp_dir, pdf_filename)

        # Save PDF file
        logger.info(f"Saving PDF to: {pdf_path}")
        with open(pdf_path, 'wb') as pdf_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    pdf_file.write(chunk)
        
        logger.info("PDF downloaded and saved successfully")
        output_files = pdf_path
        return output_files, date, pdf_filename
        
    except Exception as e:
        logger.error(f"Failed to scrape The Sun: {str(e)}", exc_info=True)
        return [], None, str(e)
