import json

import requests
import telebot
from telebot import apihelper
from telebot.types import Message

from api import say, send_sticker, host, chat_list
from central.utils.args_manager import get_arg, get_proxy
from central.utils.commands import CommandManager
from central.utils.query_manager import create_user, check_admin, set_admin
from central.utils.talk_manager import add_text, add_sticker
from anime_bot.anime import AnimeCommands
from central.utils.logger import BotLogger

bot = telebot.TeleBot(get_arg('token')['value'])
apihelper.proxy = get_proxy()
anime_commands = AnimeCommands()
anime_commands.__int__(bot, apihelper.proxy)
command_manager = CommandManager()
command_manager.__int__(bot)
command_manager.set_commands()


@bot.message_handler(func=lambda message: create_user(message))
def new_account(message: Message):
    say(bot, message, 'es', 'new-account')
    bot.send_message(message.chat.id, command_manager.help_command())


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message: Message):
    bot.send_message(message.chat.id, command_manager.help_command())


@bot.message_handler(commands=['chapter_today'])
def chapters_command(message: Message):
    anime_commands.print_chapters(message)


@bot.message_handler(commands=['anime_today'])
def animes_command(message: Message):
    anime_commands.animes_today(message)


@bot.message_handler(commands=['anime_find', 'anime_search'])
def find_anime(message: Message):
    anime_commands.search_result(message)


# Admin commands
@bot.message_handler(commands=['add_text', 'add_message'], func=check_admin)
def new_text(message: Message):
    add_text(message, bot.get_me().id, 'es')
    send_sticker(bot, message, 'ok')


@bot.message_handler(commands=['add_sticker'], func=check_admin)
def new_sticker(message: Message):
    add_sticker(message, bot, 'es')


@bot.message_handler(commands=['new_token'], func=check_admin)
def set_token(message: Message):
    new_token = requests.get(host('tokens', 'generate'))
    new_token = new_token.json()['token']
    send_sticker(bot, message, 'roger')
    say(bot, message, 'es', 'new-token')
    bot.send_message(message.chat.id, new_token)


@bot.message_handler(commands=['set_admin'])
def new_admin(message: Message):
    if set_admin(message).status_code == 200:
        send_sticker(bot, message, 'dazzling')
        say(bot, message, 'es', 'new-admin')
    else: say(bot, message, 'es', 'invalid-token')


@bot.message_handler(content_types=['sticker'], func=check_admin)
def sticker_id(message: Message):
    sticker = message.sticker.file_id
    say(bot, message, 'es', 'sticker-received')
    bot.send_message(message.chat.id, sticker)


@bot.message_handler(commands=['send_message'], func=check_admin)
def share_notice(message: Message):
    photo = message.reply_to_message.photo
    if photo is not None: photo = photo[-1].file_id
    caption = message.reply_to_message.caption
    sticker = message.reply_to_message.sticker
    if sticker is not None: sticker = sticker.file_id
    send_type = {
        'text': bot.send_message,
        'photo': bot.send_photo,
        'sticker': bot.send_sticker
    }
    args = {
        'text': [caption],
        'photo': [photo, caption],
        'sticker': [sticker]
    }
    content_type = message.reply_to_message.content_type
    error_text = 'failed to send a message from chat '
    error_text = f'[{BotLogger().date}] {error_text}'
    for chat in chat_list(bot.get_me().id):
        kwargs = chat['id'], *args[content_type]
        try: send_type[content_type](*kwargs)
        except: print(error_text + str(chat['id']))


@bot.message_handler(func=lambda message: message.text[0] == '/')
def command_not_found(message: Message):
    send_sticker(bot, message, 'question')
    say(bot, message, 'es', 'command-not-found')


@bot.callback_query_handler(func=lambda message: True)
def query(message: telebot.types.CallbackQuery):
    BotLogger().action_log(message)
    chapter_list = anime_commands.chapter_list
    reply = json.loads(message.data)
    is_chapter = type(reply) == list
    if is_chapter and reply[0] in chapter_list:
        download = anime_commands.download_chapter
        chapter = chapter_list[reply[0]][reply[1]]
        download(message.message, chapter)
    elif reply in anime_commands.animes:
        args = bot, message.message, 'ok'
        sticker = send_sticker(*args)
        bot.clear_step_handler(sticker)
        anime = anime_commands.animes[reply]
        command = anime_commands.print_anime
        command(message.message, anime)


if __name__ == '__main__':
    bot.infinity_polling()
