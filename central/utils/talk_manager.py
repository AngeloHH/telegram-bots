import json

import requests
import telebot
from telebot.types import Message

from central.utils.query_manager import host
from menhera_bot.help import get_commands


def say(bot: telebot.TeleBot, message: Message, language, key, **kwargs):
    bot_id, chat_id = bot.get_me().id, message.chat.id
    url = host('bot', bot_id, 'lang', language, 'get')
    response, messages = requests.get(url, params={'key': key}), []
    for message in response.json():
        messages.append(bot.send_message(chat_id, message['text'], **kwargs))
    return messages


def say_help(text='Use /help para mostrar el uso de comandos:\n\n', path='main.py'):
    for command in get_commands(path):
        text += f'» /{command.command}\n {command.description}\n\n'
    return text


def send_sticker(bot: telebot.TeleBot, message: Message, key: str, **kwargs):
    url = host('bot', bot.get_me().id, 'stickers', key)
    sticker = requests.get(url).json()['sticker_id']
    return bot.send_sticker(message.chat.id, sticker, **kwargs)


def add_text(message: Message, bot_id: int, lang: str):
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


def invalid_type(data_type, message, bot, lang):
    is_invalid = True
    try:
        data_type(message.text)
        is_invalid = False
    except:
        say(bot, message, lang, 'invalid-query')
        send_sticker(bot, message, 'clumsy')
    return is_invalid
