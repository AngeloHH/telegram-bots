from sys import argv


def long_value(arg):
    if len(arg.split('=')) == 1: return True
    else: return arg.split('=')[1]


def get_value(arg):
    index = argv.index(arg) + 1
    if len(argv) <= index or argv[index][0] == '-': return None
    else: return argv[index]


def list_args():
    args: list[dict] = [{
        'name': a.split('=')[0][2:],
        'key': a[2], 'value': long_value(a)
    } for a in argv if a[0:2] == '--']
    short_args: list[dict] = [{
        'name': None, 'key': a[1], 'value': get_value(a)
    } for a in argv if a[0:2] != '--' and a[0] == '-']
    return args + short_args


def get_arg(name):
    for arg in list_args():
        conditions = arg['name'] == name, arg['key'] == name[0]
        if conditions[0] or conditions[1]: return arg
    return {'name': name, 'key': name[0], 'value': None}


def get_proxy():
    proxy = get_arg('proxy')['value']
    data = {'http': proxy, 'https': proxy}
    return None if proxy is None else data
