import io
import math
import time
from io import BytesIO

import requests
from PIL import Image
from telegraph import Telegraph
from urllib3 import disable_warnings, exceptions

from manga_bot.lectormo.scraper import LectorMO


def split_image(url: str, max_width: int, max_height: int, min_height: int) -> list[bytes]:
    """ Download the image and split it into small parts. """
    # Disable SSL warnings (the certificated is expired).
    disable_warnings(exceptions.InsecureRequestWarning)
    # Get the image and their dimensions.
    content = LectorMO().scraper.get(url, verify=False)
    images, content = [], content.content
    image = Image.open(BytesIO(content))
    width, height = image.size
    # Get the relative size and the number of times to
    # cut the image.
    value = height * (max_width * 100 / width) / 100
    new_height = math.ceil((height - value) + max_height)

    # If the max height is less that the current height
    # return the image without cuts.
    if max_height > height:
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        return [buffer.getvalue()]

    # The big problem, split the image and round the number
    # of pixels per new image.
    for y in range(math.ceil(value / new_height)):
        current, buffer = new_height * y, io.BytesIO()
        next_height = new_height * (y + 1)
        # If the current height and the image height are
        # equals break the iteration.
        if height == current or (height - current) < 0:
            break
        # If the next image is too small merge it with this.
        if (height - next_height) <= min_height:
            next_height += height - next_height
        # Cut the image and save it in an array buffer.
        img = image.crop((0, current, width, next_height))
        img.save(buffer, format='JPEG')
        images.append(buffer.getvalue())
    return images


def upload_images(images: list[str]) -> list[str]:
    images_url, url = [], 'https://telegra.ph/upload'
    for img in images:
        # Split the image and upload to Telegraph cloud.
        for image in split_image(img, 732, 690, 80):
            data = requests.post(url, files={'file': image})
            data = data.json()[0]['src']
            images_url.append('https://telegra.ph' + data)
    return images_url


def upload_chapter(title: str, author: str, images: list[str], per_page: int):
    # Save the images in html format and create a
    # Telegraph profile.
    tags = [f'<img src="{url}">' for url in images]
    telegraph, urls = Telegraph(), []
    telegraph.create_account(short_name=author)

    # Iterate the images in groups.
    for i in range(0, len(images), per_page)[::-1]:
        content = '\n'.join(tags[i:i+per_page])
        # If not the first page add a new tag for redirect
        # to the next page.
        if len(urls) != 0:
            total_pages = math.ceil(len(images) / per_page)
            page_number = total_pages - len(urls) + 1
            text = f'Next Page {page_number} / {total_pages}'
            content += f'<a href="{urls[-1]}">{text}</a>'
        # Create the page and save.
        args = dict(title=title, html_content=content)
        urls.append(telegraph.create_page(**args)['url'])
        # Wait a few minutes to avoid overloading the cloud.
        time.sleep(1)
    return urls
