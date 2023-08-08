import os
from sys import argv

from telebot.types import Message

from anime_bot.telegram.commands import AnimeBot
from base_bot.commands.manager import CommandManager
from base_bot.talker.manager import TalkerManager

TOKEN = next((arg.replace('token=', '') for arg in argv if 'token=' in arg), None)
anime_bot = AnimeBot(TOKEN)
def create_user(message: Message): anime_bot.external_api.add_user(message, False)


@anime_bot.bot.message_handler(func=create_user)
def new_account(message: Message):
    anime_bot.talk(message.chat.id, 'new-account', 'es')
    anime_bot.send_welcome(message)


if __name__ == '__main__':
    path = os.path.dirname(os.path.abspath(__file__))
    anime_bot.external_api.set_host('127.0.0.1', 8089)
    commands = 'anime_bot/commands.yaml'
    args = anime_bot.bot, os.path.join(path, commands)
    anime_bot.command_manager = CommandManager(*args)
    anime_bot.command_manager.set_commands()
    anime_bot.talk = TalkerManager(anime_bot.bot).talk
    anime_bot.run()
