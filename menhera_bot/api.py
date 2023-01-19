import json
from sys import argv

import requests
import telebot

from telebot.types import Message

from menhera_bot.help import get_commands
from menhera_bot.logger import BotLogger


def get_proxy():
    proxy = argv[argv.index('-p') + 1] if '-p' in argv else None
    if proxy is None and '--proxy=' in str(argv):
        args = iter(arg for arg in argv if '--proxy=' in arg)
        proxy = next(args, None)
        proxy = None if proxy is None else proxy.replace('--proxy=', '')
    proxy = None if proxy is None else {'http': proxy, 'https': proxy}
    return proxy


def host(*args):
    server = '/'.join(str(a) for a in args)
    return f'http://127.0.0.1:8000/{server}'


def say(bot: telebot.TeleBot, message: Message, language, key):
    bot_id, chat_id = bot.get_me().id, message.chat.id
    url = host('bot', bot_id, 'lang', language, 'get')
    response = requests.get(url, params={'key': key})
    messages = []
    for msg in response.json():
        args = chat_id, msg['text']
        reply = bot.send_message(*args)
        messages.append(reply)
    return messages


def say_help():
    text = 'Use /help para mostrar el uso de comandos:\n\n'
    for command in get_commands('main.py'):
        text += f'» /{command.command}\n '
        text += f'{command.description}\n\n'
    return text


def send_sticker(bot: telebot.TeleBot, message: Message, key, **kwargs):
    url = host('bot', bot.get_me().id, 'stickers', key)
    sticker = requests.get(url).json()['sticker_id']
    return bot.send_sticker(message.chat.id, sticker, **kwargs)


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


def add_text(message: Message, bot_id, lang: str):
    key = message.text.split(' ')[1]
    text = message.text.index(key) + len(key)
    text = json.loads(f'[{message.text[text:]}]')
    text = [{'name': key, 'text': chat} for chat in text]
    url = host('bot', bot_id, 'lang', lang, 'add')
    [requests.post(url, json=t) for t in text]
    

def add_sticker(message: Message, bot, lang: str):
    url = host('bot', bot.get_me().id, 'stickers')
    if 'reply_to_message' not in message.json:
        say(bot, message, lang, 'no-selected-sticker')
    elif len(message.text.split(' ')) != 2:
        say(bot, message, lang, 'sticker-key-error')
    else:
        data = message.json['reply_to_message']
        data = data['sticker']
        requests.post(url, json={
            'sticker_id': data['file_id'],
            'emoji': data['emoji'],
            'name': message.text.split(' ')[1],
            'bot_id': bot.get_me().id
        })
        send_sticker(bot, message, 'ok')


def set_admin(bot: telebot.TeleBot, message: Message):
    url = host("tokens", "consume")
    response = requests.post(url, params={
        'token': message.text.split(' ')[1],
        'user_id': message.from_user.id
    })
    if response.status_code != 200:
        return say(bot, message, 'es', 'invalid-token')
    send_sticker(bot, message, 'dazzling')
    say(bot, message, 'es', 'new-admin')
