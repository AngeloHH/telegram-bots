import re
import time

import telebot

from base_bot.commands.manager import CommandManager
from base_bot.external.manager import CentralApi
from base_bot.telegram.logger import LoggerManager


class BaseBot:
    def __init__(self, token: str, language: str = None, talk=None):
        self.bot = telebot.TeleBot(token)
        self.talk = (lambda chat_id, key, lang, **kwargs: print(key))
        self.talk = talk or self.talk
        self.lang = language or 'en'
        self.command_manager = CommandManager(self.bot)
        self.external_api = CentralApi()
        self.logger = LoggerManager()
        self.commands = [
            dict(commands=['start', 'help'], callback=self.send_welcome),
            dict(commands=['add_text'], func=self._check_admin, callback=self.add_text),
            dict(commands=['add_sticker'], func=self._check_admin, callback=self.add_sticker),
            dict(commands=['new_token'], func=self._check_admin, callback=self.new_token),
            dict(commands=['set_admin'], callback=self.new_admin),
            dict(commands=['stop'], func=self._check_admin, callback=self.stop),
        ]

    def _next_handler(self, message: telebot.types.Message):
        command = re.findall(r"/(\w+)", message.text)[0]
        for handler in self.bot.message_handlers:
            commands = handler['filters'].get('commands', '')
            if command in commands:
                handler['function'](message)
        self.logger.print(message)

    def _check_admin(self, message: telebot.types.Message):
        return self.external_api.get_admin(message.chat.id)
    
    def _set_handlers(self):
        def custom_handler(function):
            def wrapper(message):
                self.logger.print(message)
                function(message)
            return wrapper

        for command in self.commands:
            handler = custom_handler(command['callback'])
            del command['callback']
            self.bot.message_handler(**command)(handler)

    def run(self, *args, **kwargs):
        self._set_handlers()
        while True:
            try:
                self.bot.infinity_polling()
                break
            except ConnectionError as error:
                print(error)
                time.sleep(60)

    def stop(self, *args, **kwargs):
        self.bot.stop_polling()

    def send_welcome(self, message: telebot.types.Message):
        commands = self.command_manager.help_command()
        self.bot.send_message(message.chat.id, commands)

    def add_text(self, message: telebot.types.Message):
        bot_id = self.bot.get_me().id
        self.external_api.add_text(bot_id, self.lang, message)

    def add_sticker(self, message: telebot.types.Message):
        bot_id = self.bot.get_me().id
        self.external_api.add_sticker(bot_id, message)

    def new_token(self, message: telebot.types.Message):
        arguments = self.bot.get_me().id, 'token-text', self.lang
        text = self.external_api.get_text(*arguments)
        token = self.external_api.get_token()
        if len(text) > 0 and '{}' in text[0]:
            token = text[0].format(token)
        self.bot.send_message(message.chat.id, token)

    def new_admin(self, message: telebot.types.Message):
        response = self.external_api.set_admin(message)
        if response.status_code != 200:
            chat_id = message.chat.id
            self.talk(chat_id, 'token-error', self.lang)
