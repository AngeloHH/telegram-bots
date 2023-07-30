import re
from time import sleep

import telebot

from base_bot.telegram.commands import BaseBot
from manga_bot.lectormo.cloud import upload_chapter, upload_images
from manga_bot.lectormo.scraper import LectorMO
from manga_bot.telegram.models import comic_model, comic_detail


def new_keyboard(chapters: list, current: int, max_len: int):
    kwargs = dict(resize_keyboard=True, one_time_keyboard=True)
    buttons = []
    for chapter in chapters[current:max_len]:
        buttons.append(telebot.types.KeyboardButton(chapter['number']))
    if len(chapters) > max_len:
        buttons.append(telebot.types.KeyboardButton('[ ... ]'))
    return telebot.types.ReplyKeyboardMarkup(**kwargs).add(*buttons)


class MangaBot(BaseBot):
    def __init__(self, token: str, language: str = None, talk=None):
        super().__init__(token, language, talk)
        self.comics, self.lector = {}, LectorMO()
        self.commands.extend([
            dict(commands=['trending', 'populars'], callback=self.trending_comic),
            dict(commands=['search'], callback=self.search_comic)
        ])
        self.bot.callback_query_handler(func=lambda _: True)(self.select_comic)
        self.chapters_len = 100
        self.lang = language or 'en'

    def _upload_chapter(self, chat_id: int, comic_name: str, chapter: dict):
        author, images = self.bot.get_me().first_name, []
        self.talk(chat_id, 'downloading-images', self.lang)
        while len(images) == 0:
            images = self.lector.get_images(chapter['scans'][0]['url'])
            sleep(1)
        urls = upload_chapter(comic_name, author, upload_images(images), 32)
        return self.bot.send_message(chat_id, urls[-1])

    def _print_comic(self, chat_id: int, comic: dict):
        url, image = comic['url'], comic['image']
        caption, self.comics[comic['id']] = comic_model(comic), url
        button = dict(text='Seleccionar', callback_data=comic['id'])
        keyboard = telebot.types.InlineKeyboardMarkup()
        button = telebot.types.InlineKeyboardButton(**button)
        keyboard.add(button)
        self.bot.send_photo(chat_id, image, caption, reply_markup=keyboard)

    def select_chapter(self, message: telebot.types.Message, comic: dict, last_chapter: int):
        chapter = next((c for c in comic['chapters'] if c['number'] == message.text), None)
        if message.text == '[ ... ]':
            next_stop = last_chapter + self.chapters_len
            keyboard = new_keyboard(comic['chapters'], last_chapter, next_stop)
            arguments = message.chat.id, comic['image'], comic_detail(comic, 400)
            next_step = self.bot.register_next_step_handler
            message = self.bot.send_photo(*arguments, reply_markup=keyboard)
            next_step(message, self.select_chapter, comic, next_stop)
        elif chapter is not None:
            self.talk(message.chat.id, 'chapter-selected', self.lang)
            message = self._upload_chapter(message.chat.id, comic['id'], chapter)
            kwargs = dict(comic=comic, last_chapter=last_chapter)
            self.bot.register_next_step_handler(message, self.select_chapter, **kwargs)
        else:
            self._next_handler(message)

    def select_comic(self, message: telebot.types.CallbackQuery):
        chat_id, comic_id = message.message.chat.id, message.data
        detail = self.lector.manga_details(self.comics[comic_id])
        self.talk(message.id, 'comic-selected', self.lang)
        keyboard = new_keyboard(detail['chapters'], 0, self.chapters_len)
        caption, image = comic_detail(detail, 400), detail['image']
        args = (chat_id, image, caption)
        kwargs = dict(comic=detail, last_chapter=self.chapters_len)
        message = self.bot.send_photo(*args, reply_markup=keyboard)
        self.bot.register_next_step_handler(message, self.select_chapter, **kwargs)

    def search_comic(self, message: telebot.types.Message):
        command = re.findall(r"/(\w+)", message.text)[0]
        command = message.text.replace(f'/{command}', '')
        self.talk(message.id, 'listing-comics', self.lang)
        for comic in self.lector.search(command.strip()):
            sleep(0.25)
            self._print_comic(message.chat.id, comic)
        self.talk(message.id, 'end-task', self.lang)

    def trending_comic(self, message: telebot.types.Message):
        command = re.findall(r"/(\w+)", message.text)[0]
        content = self.lector.scraper.get(self.lector.base_url)
        content = content.content
        self.talk(message.id, 'listing-comics', self.lang)
        for comic in self.lector.get_pill(command, content):
            sleep(0.25)
            self._print_comic(message.chat.id, comic)
        self.talk(message.id, 'end-task', self.lang)
