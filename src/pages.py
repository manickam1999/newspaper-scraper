import os
import requests
from PIL import Image
from utils.logger import logger

def fetch_images(zoom_url, total_pages, temp_dir, formatted_date, config_cookie=None):
    
    # Use config cookie if provided, otherwise use fallback cookie
    if config_cookie:
        cookie_string = config_cookie
        logger.info("Using cookie from config for API calls")
    else:
        # Fallback cookie if config cookie is not available
        cookie_string="JSESSIONID=B92E88392B6886B8440F88EBE9B88F27; vn=7FYPt42dJ8Q%3D; extvn=bNhDAnhWzF8%3D; JSESSIONID=FCD25F2D71B6C212FE9AD32307FC5D78; visid_incap_3130433=eLKboCzLQB2kzNBhLoVFnrKcWGgAAAAAQUIPAAAAAACAGwlmPS5JlJkZwVu4gWcF; nlbi_3130433=r1XaWJwpvXbEk7I7kANNcgAAAAA3SQKI3B1fKW0nTJq/hp4t; incap_ses_1673_3130433=ZGfea0MHH0gI4npc9LA3F7KcWGgAAAAAFSId5bRLnjYqsyXbFAA7Dg==; _ga=GA1.1.1539179138.1750637748; _gcl_au=1.1.1033607849.1750637748; vuidjson=FsQ10ex63%2FBh3DR2OYEuhGEt4ycDJC2YWCajSJDPU351CkuZRnltUrIcwBcd67l39t9w8vx%2B4CM%3D; workstationCookie=1750637772794; _ga_KESNC53HMR=GS2.1.s1750637747$o1$g1$t1750637781$j26$l0$h799963808"
        logger.info("Using fallback cookie for API calls")


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
