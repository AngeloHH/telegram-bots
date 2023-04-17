import datetime
import io
import json

import requests
import telebot
from PIL import Image
from bs4 import BeautifulSoup


def split_image(image: bytes, max_height: int = 2160) -> list:
    data = Image.open(io.BytesIO(image))
    width, height = data.size
    if height <= max_height: return [image]
    height, images = height // max_height, []
    for i in range(height):
        y = (i * max_height), ((i + 1) * max_height)
        image_crop = data.crop((0, y[0], width, y[1]))
        new_image = io.BytesIO()
        image_crop.save(new_image, format='JPEG')
        images.append(new_image.getvalue())
    return images


class TelegraphApi:
    def __int__(self, bot: telebot.TeleBot):
        params = bot.get_me().username, bot.get_me().first_name
        params = dict(short_name=params[0], author_name=params[1])
        self.base_url = 'https://api.telegra.ph/'
        account = self.base_url + 'createAccount'
        data = requests.get(account, params=params)
        self.access_token = data.json()['result']['access_token']
        self.author_name = params['author_name']

    def get_error(self, raw_text: bytes):
        raw_text = BeautifulSoup(raw_text, 'html.parser')
        code = raw_text.find('title')
        return dict(ok=False, result={'code': code.text})

    def send_post(self, title: str, content: list[dict]):
        create_url = self.base_url + 'createPage'
        data = requests.get(create_url, params=dict(
            access_token=self.access_token, title=title,
            author_name=self.author_name,
            content=json.dumps(content), return_content=True
        ))
        has_errors = data.status_code == 200
        def get_error(): return self.get_error(data.content)
        return data.json() if has_errors else get_error()

    def upload_images(self, images: list[bytes], callback=None, message=telebot.types.Message):
        image_list = []
        def add(array: list, *items): [array.append(item) for item in items]
        def call(image): callback(image, message, len(image_list))
        [add(image_list, *split_image(image)) for image in images]
        return [self.upload_image(image, call) for image in image_list]

    def upload_image(self, image: bytes, callback=None, *args, **kwargs):
        def get_url(img): return 'https://telegra.ph' + img['src']
        uploads = 'https://telegra.ph/upload'
        response = requests.post(uploads, files=dict(file=image))
        images = [get_url(image) for image in response.json()][0]
        if callback is not None: callback(images, *args, **kwargs)
        return {"tag": "img", "attrs": {"src": images}}


def create_text(tag: str, children: list[dict:str], **kwargs):
    return dict(tag=tag, children=children, **kwargs)


def create_link(text: str, url: str):
    return create_text('a', [text], attrs={'href': url})
