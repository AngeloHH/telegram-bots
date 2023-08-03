import json

import requests
import telebot
from telebot.types import Message

from central.utils.query_manager import host


def say(bot: telebot.TeleBot, message: Message, language, key, **kwargs):
    bot_id, chat_id = bot.get_me().id, message.chat.id
    url = host('bot', bot_id, 'lang', language, 'get')
    response, messages = requests.get(url, params={'key': key}), []
    for message in response.json():
        messages.append(bot.send_message(chat_id, message['text'], **kwargs))
    return messages


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


def resend_message(message: Message, bot: telebot.TeleBot):
    chat_id = message.text.split(' ')
    chat_id = chat_id[-1] if len(chat_id) == 2 else message.chat.id
    if message.reply_to_message is None: return None
    if message.reply_to_message.photo is not None:
        photo = message.reply_to_message.photo[-1]
        photo = photo.file_id
        caption = message.reply_to_message.caption
        return bot.send_photo(chat_id, photo, caption)

    if message.reply_to_message.document is not None:
        doc = message.reply_to_message.document.file_id
        caption = message.reply_to_message.caption
        return bot.send_document(chat_id, doc, caption)

    if message.reply_to_message.sticker is not None:
        sticker = message.reply_to_message.sticker
        sticker = sticker.file_id
        return bot.send_sticker(chat_id, sticker)


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
