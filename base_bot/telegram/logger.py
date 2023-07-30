import datetime

from telebot.types import Message


class LoggerManager:
    def __init__(self):
        self.format = '%Y-%m-%d %I:%M %p'

    def _account(self, message: Message):
        username = message.from_user.username
        if username is None:
            return message.from_user.first_name
        return username

    def _date(self):
        date = datetime.datetime.now()
        return date.strftime(self.format)

    def _action(self, message: Message):
        return 'command' if message.text[0] == '/' else 'text'

    def print(self, message: Message):
        date, user = self._date(), self._account(message)
        action = 'issued the ' + self._action(message)
        print(f'[{date}] {user} {action} "{message.text}"')
