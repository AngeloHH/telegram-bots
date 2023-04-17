import telebot
import yaml


def get_args(command):
    if 'arguments' not in command: return ''
    args = command['arguments']
    args = [args] if type(args) == str else args
    return ' '.join([f'<{arg}>' for arg in args])


class CommandManager:
    def __int__(self, bot: telebot.TeleBot, path: str = 'commands.yaml'):
        data = yaml.safe_load(open(path, 'rb').read())
        self.data = [comm['command'] for comm in data]
        self.data = self.split_data()
        self.bot, self.set = bot, telebot.types.BotCommand
        self.help_text = 'Use /help para mostrar el uso de comandos:\n\n'

    def split_data(self):
        commands = []
        for command in self.data:
            is_list = type(command['name']) == list
            if not is_list: command['name'] = [command['name']]
            for name in command['name']:
                commands.append({**command, 'name': name})
        return commands

    def set_commands(self):
        commands = [self.set(command['name'], command['details'])
                    for command in self.data]
        return self.bot.set_my_commands(commands)

    def help_command(self, text: str = None):
        text = self.help_text if text is None else text
        for command in self.data:
            text += f'» /{command["name"]}'
            text += f' {get_args(command)}'
            text += f'\n {command["details"]}\n\n'
        return text
