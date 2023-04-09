import json
import re

import telebot
from telebot import apihelper
from telebot.types import Message

from central.utils.args_manager import get_proxy, get_arg
from central.utils.logger import BotLogger
from central.utils.query_manager import set_admin, create_user, check_admin
from central.utils.talk_manager import say, send_sticker, say_help, add_sticker, add_text
from manga_bot.manga import MangaCommands

bot = telebot.TeleBot(get_arg('token')['value'])
apihelper.proxy, chats = get_proxy(), []
manga_command = MangaCommands()
manga_command.__int__(bot)
def query_handler(handler): return type(json.loads(handler.data)) != list


@bot.message_handler(func=create_user)
def new_account(message: Message):
    say(bot, message, 'es', 'new-account')
    bot.send_message(message.chat.id, say_help())


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message: Message):
    bot.send_message(message.chat.id, say_help())


@bot.message_handler(commands=['trending'])
def get_trending(message: Message):
    manga_command.get_trending(message)


@bot.message_handler(commands=['populars'])
def get_trending(message: Message):
    manga_command.get_populars(message)


@bot.message_handler(commands=['search'])
def search_manga(message: Message):
    command = re.findall(r"/(\w+)", message.text)
    command = f'/{command[0]} '
    chat_id = message.chat.id
    search = message.text.replace(command, '')
    if search == '': return None
    comics = manga_command.manga_api.search(search)
    manga_command.list_comics(comics, chat_id)


@bot.message_handler(commands=['set_admin'])
def new_admin(message: Message):
    if set_admin(message).status_code != 200:
        return say(bot, message, 'es', 'invalid-token')
    send_sticker(bot, message, 'dazzling')
    say(bot, message, 'es', 'new-admin')


@bot.message_handler(commands=['add_text', 'add_message'], func=check_admin)
def new_text(message: Message):
    add_text(message, bot.get_me().id, 'es')
    send_sticker(bot, message, 'ok')


@bot.message_handler(commands=['add_sticker'], func=check_admin)
def new_sticker(message: Message): add_sticker(message, bot, 'es')


@bot.message_handler(func=lambda message: message.text[0] == '/')
def command_not_found(message: Message):
    send_sticker(bot, message, 'question')
    say(bot, message, 'es', 'command-not-found')


@bot.callback_query_handler(func=lambda data: query_handler)
def query(message: telebot.types.CallbackQuery):
    BotLogger().action_log(message)
    return manga_command.chapter_keyboard(message)


if __name__ == '__main__':
    bot.infinity_polling()
