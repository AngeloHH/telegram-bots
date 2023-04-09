import datetime
import sys

from telebot.types import Message, CallbackQuery


def get_name(message: Message):
    if message.from_user.username is None:
        return message.from_user.first_name
    return message.from_user.username


class BotLogger:
    def __init__(self):
        date_now = datetime.datetime.now().strftime
        self.date = date_now('%Y-%m-%d %I:%M%p')
        self.callback = print

    def message(self, text): print(f"[{self.date}] {text}")

    def command_log(self, message: Message):
        action = 'command' if message.text[0] == '/' else 'text'
        text = f'[{self.date}] {get_name(message)}'
        text += f' issued the {action} "{message.text}"'
        self.callback(text)

    def action_log(self, message: Message or CallbackQuery):
        is_message = type(message) == Message
        option = message.text if is_message else message.data
        text = f'[{self.date}] {get_name(message)}'
        text += f' choose the option {option}'
        self.callback(text)

    def error_log(self):
        exc_type, exc_object, exc_traceback = sys.exc_info()
        number = exc_traceback.tb_lineno
        filename = exc_traceback.tb_frame.f_code.co_filename
        text = f'[{self.date}] Exception type "{exc_type}" on'
        text += f' line #{number} in {filename}: {exc_object}'
        self.callback(text)
