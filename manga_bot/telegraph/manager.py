import io
import math
import time
from io import BytesIO
from typing import Generator

import requests
from PIL import Image
from telegraph import Telegraph
from urllib3 import disable_warnings, exceptions

from manga_bot.lectormo.scraper import LectorMO


def get_coordinates(image_size: tuple[int, int], default_size: tuple[int, int], min_height: int):
    width, height = image_size
    coordinates = []
    # Calculate the scaled size based on the image's aspect ratio.
    scaled_size = math.ceil((height / width) * default_size[0])
    max_size = math.ceil(height / (scaled_size / default_size[1]))
    # Loop through the image coordinates vertically in chunks.
    for current_y in range(0, height, max_size):
        next_y = current_y + max_size
        # Ensure that the next chunk doesn't exceed the image height.
        next_y = next_y if height - next_y >= 0 else height
        # Check if the next image chunk is too small to split.
        if height - next_y != 0 and height - next_y <= min_height:
            j = math.ceil((height - current_y) / 2)
            coordinates.append((current_y, j + current_y))
            coordinates.append((j + current_y, height))
            break
        # Append the current chunk's coordinates to the list.
        coordinates.append((current_y, next_y))
    return coordinates


def split_image(url: str, max_width: int, max_height: int, min_height: int) -> list[bytes]:
    """ Download the image and split it into small parts. """
    # Disable SSL warnings (the certificated is expired).
    disable_warnings(exceptions.InsecureRequestWarning)
    # Get the image and their dimensions.
    content = LectorMO().scraper.get(url, verify=False)
    images, content = [], content.content
    image = Image.open(BytesIO(content))
    width, height = image.size

    coordinates = get_coordinates(image.size, (max_width, max_height), min_height)
    # If the max height is less that the current height set the image without cuts
    coordinates = [(0, image.size[1])] if max_height >= height else coordinates
    for current, next_height in coordinates:
        buffer = io.BytesIO()
        # Cut the image and save it in an array buffer.
        img = image.crop((0, current, width, next_height))
        img.save(buffer, format='JPEG')
        images.append(buffer.getvalue())
    return images


def upload_images(images: list[str], callback=None, **kwargs) -> list[str]:
    images_url, url = [], 'https://telegra.ph/upload'
    for index, img in enumerate(images):
        # Split the image and upload to Telegraph cloud.
        for image in split_image(img, 732, 690, 80):
            data = requests.post(url, files={'file': image})
            data = data.json()[0]['src']
            images_url.append('https://telegra.ph' + data)
        if callback is not None:
            callback(percent=(index + 1) / len(images) * 100, **kwargs)
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
