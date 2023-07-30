import os.path

import telebot
import yaml


def get_args(command):
    args = command.get('arguments', '')
    if type(args) == str and args != '':
        args = [args]
    args = [f'<{arg}>' for arg in args]
    return ' '.join(args)


class CommandManager:
    def __init__(self, bot: telebot.TeleBot, path: str = 'commands.yaml'):
        self.bot, self.data = bot, self.get_commands(path)
        self.help_text = 'Use /help para mostrar el uso de comandos:\n\n'

    def get_commands(self, path):
        if not os.path.isfile(path):
            return []
        data = yaml.safe_load(open(path, 'rb').read())
        return [comm['command'] for comm in data]

    def split_data(self):
        commands = []
        for command in self.data:
            is_list = type(command['name']) == list
            if not is_list: command['name'] = [command['name']]
            for name in command['name']:
                commands.append({**command, 'name': name})
        return commands

    def set_commands(self):
        commands = []
        for data in self.data:
            command = telebot.types.BotCommand
            values = list(data.values())[:2]
            commands.append(command(*values))
        return self.bot.set_my_commands(commands)

    def help_command(self, text: str = None):
        text = self.help_text if text is None else text
        for command in self.data:
            text += f'» /{command["name"]}'
            text += f' {get_args(command)}'
            text += f'\n {command["details"]}\n\n'
        return text
