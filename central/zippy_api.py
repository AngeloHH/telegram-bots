import os

import js2py
import requests
from bs4 import BeautifulSoup


class Zippy:
    def __init__(self, url):
        self.base_url = url
        self.request = requests.Session()
        self.container = BeautifulSoup()

    def start(self):
        response = self.request.get(self.base_url).content
        soup = BeautifulSoup(response, 'html.parser')
        self.container = soup.find('div', {'id': 'lrbox'})

    def get_details(self) -> dict:
        data_raw = self.container.find_all('font')
        return {'status': 404} if len(data_raw) == 5 else {
            'name': data_raw[2].text,
            'size': data_raw[4].text,
            'creation-date': data_raw[6].text,
            'status': 200,
            'file-url': self.get_url()
        }

    def get_url(self):
        script = self.container.find_all('script')[2].text
        script = script.replace("document.getElementById('dlbutton').", '')
        script = script.replace("document.getElementById('fimage').", '')
        script = script.replace("document.getElementById('fimage')", 'false')
        context = js2py.EvalJs()
        context.execute(script)
        base_url = self.base_url[:self.base_url.index('/v/')]
        return base_url + context.href

    def download(self, file_path, callback=None, **args):
        details = self.get_details()
        file_url = details['file-url']
        length = self.request.head(file_url).headers['Content-Length']
        response = self.request.get(file_url, stream=True)
        os.makedirs(file_path) if not os.path.isdir(file_path) else None
        file = open(os.path.join(file_path, details['name']), 'wb')
        for data in response.iter_content(chunk_size=1024):
            file.write(data)
            percentage = ((len(data) * 100) / int(length))
            callback(percentage=percentage, **args) if callback else None
        return open(os.path.join(file_path, details['name']), 'rb')
