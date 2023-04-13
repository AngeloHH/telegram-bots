import requests

from central.utils.query_manager import host
from central.utils.talk_manager import say, send_sticker


def chat_list(bot_id):
    url = host('bot', bot_id, 'chat', 'list')
    print(requests.get(url).content)
    return requests.get(url).json()


def invalid_type(data_type, message, bot, lang):
    is_invalid = True
    try:
        data_type(message.text)
        is_invalid = False
    except:
        say(bot, message, lang, 'invalid-query')
        send_sticker(bot, message, 'clumsy')
    return is_invalid
