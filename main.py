import os.path
import sys

args = iter(arg for arg in sys.argv if 'bot=' in arg)
if __name__ == '__main__':
    bot_name = next(arg.replace('bot=', '') for arg in args)
    py_file = open(os.path.join(bot_name, 'main.py')).read()
    exec(py_file)
