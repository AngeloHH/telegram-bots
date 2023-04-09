import requests
from telebot.types import Message

from central.utils.logger import BotLogger


def host(*args):
    server = '/'.join(str(a) for a in args)
    return f'http://127.0.0.1:8000/{server}'


def create_user(message: Message, is_admin=False):
    BotLogger().command_log(message)
    url = host('users', message.from_user.id)
    if requests.get(url).status_code == 404:
        account = message.json['from']
        account['is_admin'] = is_admin
        requests.post(host('users'), json=account)
        return True
    return False


def check_admin(message: Message):
    url = host('users', message.from_user.id)
    response = requests.get(url)
    if response.status_code != 200:
        return False
    return response.json()['is_admin']


def set_admin(message: Message):
    url, params = host("tokens", "consume"), {
        'token': message.text.split(' ')[1],
        'user_id': message.from_user.id
    }
    return requests.post(url, params=params)
