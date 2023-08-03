import io
import zipfile

import psutil
from requests import Response

from base_bot.telegram.commands import BaseBot


def split_file(file: bytes, file_name: str, max_size: int) -> list[io.BytesIO]:
    memory = psutil.virtual_memory().available
    zip_data, chunk_list = io.BytesIO(), []
    zip_file = zipfile.ZipFile(zip_data, 'w')
    zip_file.writestr(file_name, file)
    last_size = 0
    zip_file.close()
    zip_data.seek(0)
    if (len(file) / max_size) > 1000:
        raise Exception('Too many files.')
    while True:
        if last_size == max_size:
            last_size = 0
            chunk_list[-1].seek(0)
        if last_size == 0:
            chunk_list.append(io.BytesIO())

        chunk_size = min(memory, max_size - last_size)
        last_size += chunk_size
        chunk_data = zip_data.read(chunk_size)

        if chunk_size > 0 and len(chunk_data) == 0:
            break
        chunk_list[-1].write(chunk_data)
    return chunk_list[:-1]


class UploadBot(BaseBot):
    def __init__(self, token: str, language: str = None, talk=None):
        super().__init__(token, language, talk)
        self.percent_text = '{}%'

    def download_process(self, chat_id: int, response: Response):
        length = response.headers.get('content-length', 0)
        file, downloaded, length = bytes(), 0, int(length)
        percent = self.percent_text.format(0)
        message = self.bot.send_message(chat_id, percent)
        for block in response.iter_content(chunk_size=8192):
            downloaded += len(block)
            file += block
            percent = '%02d' % ((downloaded / length) * 100)
            percent = self.percent_text.format(percent)
            arguments = percent, chat_id, message.id
            if message.text == percent:
                continue
            message = self.bot.edit_message_text(*arguments)
        return dict(content=file, name=response.url.split('/')[-1])
