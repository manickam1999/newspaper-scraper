import re
import os
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from utils.logger import logger
from src.pages import create_pdf_from_images

def get_sections(driver):
    sections = []
    news_rows = driver.find_elements(By.CLASS_NAME, "news-row")
    
    for row in news_rows:
        img_element = row.find_element(By.CSS_SELECTOR, "img[src^='https://starepaper']")
        section_element = row.find_element(By.TAG_NAME, "a")
        
        img_url = img_element.get_attribute("src")
        section_name = section_element.text
        
        img_url = img_url.replace("/thumbnails/", "/pages/large/")
        
        sections.append({
            "image": img_url,
            "section": section_name
        })
    
    return sections

def fetch_images(driver, url, temp_dir):
    page = 1
    total_pages = 0
    session = requests.Session()
    
    while True:
        current_url = url.replace("1.JPG", f"{page}.JPG")
        try:
            response = session.get(current_url)
            if response.status_code == 404:
                break
                
            response.raise_for_status()
            total_pages += 1
            
            # Save the image
            image_path = os.path.join(temp_dir, f"page_{page}.jpg")
            with open(image_path, "wb") as file:
                file.write(response.content)
                
            logger.info(f"Successfully downloaded image {page}")
            page += 1
            
        except requests.exceptions.RequestException as e:
            if response.status_code == 404:
                break
            logger.error(f"Failed to download image {page}: {str(e)}")
            break
    
    logger.info(f"All images have been fetched and saved in {temp_dir}")
    return total_pages

def scrape_the_star(driver, config, checkpoint, temp_dir, cookie=None):
    star_config = config["the_star"]
    url, username, password = (
        star_config["url"],
        star_config["username"],
        star_config["password"],
    )

    driver.get(url)

    wait = WebDriverWait(driver, 30)

    username_field = wait.until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
    password_field = wait.until(
        EC.presence_of_element_located((By.NAME, "password"))
    )

    username_field.clear()
    username_field.send_keys(username)
    password_field.clear()
    password_field.send_keys(password)

    login_button = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
    )
    login_button.click()

    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "modal-content")))

    wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "modal-content")))

    date = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "custom-date"))).text
    date = re.sub(r'^[A-Za-z]+, ', '', date).replace(" ", "").replace("/", "-")

    if date == checkpoint["the_star"]["version"]:
        return None, None, None

    sections = get_sections(driver)
    output_files = []
    
    for section in sections:
        section_dir = os.path.join(temp_dir, section["section"])
        os.makedirs(section_dir, exist_ok=True)
        
        logger.info(f"Processing section: {section['section']}")
        total_pages = fetch_images(driver, section["image"], section_dir)
        
        if total_pages > 0:
            file_name = f"Star {section['section']} - {date}.pdf"
            output_file = os.path.join(temp_dir, file_name)
            create_pdf_from_images(section_dir, output_file, total_pages)
            output_files.append(output_file)
            logger.info(f"Created PDF for section {section['section']}: {output_file}")
    
    return output_files, date, None
