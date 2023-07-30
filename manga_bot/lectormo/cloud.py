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
    disable_warnings(exceptions.InsecureRequestWarning)
    content = LectorMO().scraper.get(url, verify=False)
    images, content = [], content.content
    image = Image.open(BytesIO(content))
    width, height = image.size
    value = height * (max_width * 100 / width) / 100
    new_height = math.ceil((height - value) + max_height)

    if max_height > height:
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        return [buffer.getvalue()]

    for y in range(math.ceil(value / new_height)):
        current, buffer = new_height * y, io.BytesIO()
        next_height = new_height * (y + 1)
        if height == current or (height - current) < 0:
            break
        if (height - next_height) <= min_height:
            next_height += height - next_height
        img = image.crop((0, current, width, next_height))
        img.save(buffer, format='JPEG')
        images.append(buffer.getvalue())
    return images


def upload_images(images: list[str]) -> list[str]:
    images_url, url = [], 'https://telegra.ph/upload'
    for img in images:
        for image in split_image(img, 732, 690, 80):
            data = requests.post(url, files={'file': image})
            data = data.json()[0]['src']
            images_url.append('https://telegra.ph' + data)
    return images_url


def upload_chapter(title: str, author: str, images: list[str], per_page: int):
    tags = [f'<img src="{url}">' for url in images]
    telegraph, urls = Telegraph(), []
    telegraph.create_account(short_name=author)
    for i in range(0, len(images), per_page)[::-1]:
        content = '\n'.join(tags[i:i+per_page])
        if len(urls) != 0:
            total_pages = math.ceil(len(images) / per_page)
            page_number = total_pages - len(urls) + 1
            text = f'Next Page {page_number} / {total_pages}'
            content += f'<a href="{urls[-1]}">{text}</a>'
        args = dict(title=title, html_content=content)
        urls.append(telegraph.create_page(**args)['url'])
        time.sleep(1)
    return urls
