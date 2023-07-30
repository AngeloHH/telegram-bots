import os
from sys import argv

from telebot.types import Message

from base_bot.commands.manager import CommandManager
from manga_bot.telegram.commands import MangaBot
TOKEN = next((arg.replace('token=', '') for arg in argv if 'token=' in arg), None)
manga_bot = MangaBot(TOKEN)
def create_user(message: Message): manga_bot.external_api.add_user(message, False)


@manga_bot.bot.message_handler(func=create_user)
def new_account(message: Message):
    manga_bot.talk(message.chat.id, 'new-account', 'es')
    manga_bot.send_welcome(message)


if __name__ == '__main__':
    path = os.path.dirname(os.path.abspath(__file__))
    manga_bot.external_api.set_host('127.0.0.1', 8000)
    args = manga_bot.bot, os.path.join(path, 'commands.yml')
    manga_bot.command_manager = CommandManager(*args)
    manga_bot.command_manager.set_commands()
    manga_bot.run()
