import requests
from telebot.types import Message, CallbackQuery


class CentralApi:
    base_url = 'http://127.0.0.1:8089'

    def get_text(self, bot_id: int, key: str, lang: str) -> list[str]:
        url = f'{self.base_url}/bot/{bot_id}/lang/{lang}/get'
        response = requests.get(url, params=dict(key=key))
        return [message['text'] for message in response.json()]

    def get_sticker(self, bot_id: int, key: str) -> int:
        url = f'{self.base_url}/bot/{bot_id}/stickers/'
        return requests.get(url + key).json()['sticker_id']

    def get_user(self, user_id: int) -> dict or None:
        response = requests.get(f'{self.base_url}/users/{user_id}')
        return response.json() if response.status_code == 200 else None

    def get_admin(self, user_id: int) -> bool:
        account = self.get_user(user_id)
        return account['is_admin'] if account is not None else False

    def get_token(self,) -> str:
        url = f'{self.base_url}/tokens/generate'
        return requests.get(url).json()['token']

    def add_user(self, message: Message or CallbackQuery, is_admin: bool):
        account = message.json['from']
        account['is_admin'] = is_admin
        response = requests.post(f'{self.base_url}/users/', json=account)
        return response.status_code == 200

    def add_text(self, bot_id: int, lang: str, message: Message):
        key = message.text.split(' ')[1]
        index = message.text.index(key)
        text = message.text[index:]
        url = f'{self.base_url}/bot/{bot_id}/lang/{lang}/add'
        return requests.post(url, json=dict(name=key, text=text))

    def add_sticker(self, bot_id: int, message: Message):
        url = f'{self.base_url}/bot/{bot_id}/stickers'
        sticker = message.json.get('reply_to_message', None)
        if sticker is None:
            return None
        requests.post(url, json=dict(
            sticker_id=sticker['sticker']['file_id'],
            emoji=sticker['sticker']['emoji'],
            name=message.text.split(' ')[1], bot_id=bot_id
        ))

    def set_admin(self, message: Message):
        url = f'{self.base_url}/tokens/consume'
        user_id = message.from_user.id
        token = message.text.split(' ')[1]
        params = dict(token=token, user_id=user_id)
        return requests.post(url, json=params)

    def set_host(self, hostname, port, protocol='http'):
        self.base_url = f'{protocol}://{hostname}:{port}'
