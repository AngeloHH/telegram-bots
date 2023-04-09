import json

import requests
import telebot
from bs4 import BeautifulSoup


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
