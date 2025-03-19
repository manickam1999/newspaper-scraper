import os
import requests
from PIL import Image
from utils.logger import logger

def fetch_images(zoom_url, total_pages, temp_dir, formatted_date, cookie=None):
    
    cookie_string="vn=7FYPt42dJ8Q%3D; extvn=bNhDAnhWzF8%3D; JSESSIONID=AC985C97CABBA9CA2C07A5A502E48172; _ga=GA1.1.704106634.1733365408; visid_incap_3130433=i5/HSResTpyrilZ++sg5YEUoVmcAAAAAQUIPAAAAAABlB47Riyaznltg47rQ9HOg; workstationCookie=1733699655492; vuidjson=FsQ10ex63%2FBh3DR2OYEuhGEt4ycDJC2YWCajSJDPU351CkuZRnltUrIcwBcd67l39t9w8vx%2B4CM%3D; _gcl_au=1.1.386170537.1741400656; nlbi_3130433=Yc31OMd3tVp4jCnTkANNcgAAAAAEc5kSm1VcRG6c3hiLuFKN; incap_ses_1139_3130433=B68YR7ucHAuWTzJRuIrOD4MX2mcAAAAAx5H1o8Fj1MeIZz0xd77dCA==; _ga_KESNC53HMR=GS1.1.1742346116.27.1.1742346123.53.0.1239023175"

    base_url = zoom_url.rsplit("Zoom-", 1)[0]

    for page in range(1, total_pages + 1):
        image_url = f"{base_url}Zoom-{page}.jpg"
        progress = (page / total_pages) * 100
        logger.info(
            f"Fetching image {page} of {total_pages} ({progress:.2f}% complete)"
        )
        headers = {
        "Referer": "https://digital.theedgemalaysia.com/theedgemediagroup/pageflip/swipe/tem/{formatted_date}tem#/{page}/",
        "Cookie": cookie_string
        }

        try:
            response = requests.get(image_url, headers=headers)
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
