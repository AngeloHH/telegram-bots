import ast
import re

import telebot


def read_commands(file_name, admin_key) -> list:
    file = open(file_name, 'r').read().split('@bot')
    commands = []
    for data in ['@bot' + text for text in file[1:]]:
        command = re.search(r'@bot.[^*.\n]+', data)
        details = re.search(r'"""[^*]+"""', data)
        name = re.search(r'commands=[^*.)]+', command[0])
        if name is not None and details is not None:
            name = name[0].replace('commands=', '')
            details = details[0].replace('"""', '')
            commands.append({
                'command': ast.literal_eval(name)[0],
                'details': details.strip(),
                'only_staff': admin_key in command[0]
            })
    return commands


def get_commands(file_name):
    args = file_name, 'is_admin(m)'
    bot_command, result = telebot.types.BotCommand, read_commands(*args)
    command_list = [bot_command(command['command'], command['details'])
                    for command in result if not command['only_staff']]
    return command_list
