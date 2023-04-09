import json

import requests

access_token = 'c83962c9984f2595fc0c8c1cc422b72daefc0ffe6b8f7084366c3b9f18fd'
content = [
    {'tag': 'img', 'attrs': {'src': 'https://telegra.ph/file/ece64219aa562a752be99.jpg'}},
    {'tag': 'img', 'attrs': {'src': 'https://telegra.ph/file/fa968766042be51fbe18e.jpg'}},
    {'tag': 'img', 'attrs': {'src': 'https://telegra.ph/file/b9a7143b854d442e2adb1.jpg'}},
    {'tag': 'img', 'attrs': {'src': 'https://telegra.ph/file/f630f131c8cbe2dadffd2.jpg'}}
]


response = requests.get(
    'https://api.telegra.ph/createPage',
    params={
        'access_token': access_token,
        'title': 'Mi primer artículo',
        'author_name': 'Anonymous',
        'content': json.dumps(content),
        'return_content': True
    }
)

if __name__ == '__main__':
    print(response.json())
