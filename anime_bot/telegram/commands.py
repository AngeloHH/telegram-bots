import json
import re
import time

import telebot

from anime_bot.anime.scraper import AnimeFLV
from anime_bot.telegram import models
from upload_bot.telegram.commands import UploadBot, split_file
from upload_bot.yourupload.scraper import YourUpload
from base_bot.telegram.commands import BaseBot


def new_keyboard(chapters: list, related: bool = True):
    buttons = []
    kwargs = dict(resize_keyboard=True, one_time_keyboard=True)
    keyboard = telebot.types.ReplyKeyboardMarkup(**kwargs)
    for index, chapter in enumerate(chapters):
        if related is True and chapter == str:
            index = int(chapter.split('-')[-1])
        chapter = '%02d' % (index + 1)
        buttons.append(telebot.types.KeyboardButton(chapter))
    return keyboard.add(*buttons)


def new_anime(anime: dict):
    data = json.dumps(['select_anime', anime['id']])
    keyboard = telebot.types.InlineKeyboardMarkup()
    button = dict(text='Seleccionar', callback_data=data)
    button = telebot.types.InlineKeyboardButton(**button)
    keyboard.add(button)
    text = models.anime_details(anime)
    data = dict(reply_markup=keyboard)
    return dict(photo=anime['images'][0], caption=text, **data)


class AnimeBot(BaseBot):
    def __init__(self, token: str, language: str = None, talk=None):
        super().__init__(token, language, talk)
        self.upload_bot = UploadBot(token, language, talk)
        self.anime, self.anime_list, self.chapter_list = AnimeFLV(), {}, {}
        self.commands.extend([
            dict(commands=['anime_search'], callback=self.search_anime),
            dict(commands=['anime_today'], callback=self.animes_today),
            dict(commands=['chapter_today'], callback=self.chapters_today)
        ])
        self.upload_bot.bot, self.chunk_size = self.bot, 49 * 1024 ** 2
        self.bot.callback_query_handler(func=lambda _: True)(self.select_query)

    def download_chapter(self, message: telebot.types.CallbackQuery):
        chapter = self.chapter_list[json.loads(message.data)[1]]
        url = next(s['url'] for s in chapter['urls'] if s['name'] == 'yu')
        response = YourUpload().get_file(url, stream=True)
        chat_id, episode = message.message.chat.id, url.split('-')[-1]
        file = self.upload_bot.download_process(chat_id, response)
        files = split_file(file['content'], file['name'], self.chunk_size)
        for index, chunk in enumerate(files):
            name = f'{chapter["id"]}_{episode}.zip.{"%03d" % (index + 1)}'
            data = chunk.getvalue()
            self.bot.send_document(chat_id, data, visible_file_name=name)

    def select_anime(self, message: telebot.types.CallbackQuery):
        anime = self.anime_list[json.loads(message.data)[1]]
        anime = self.anime.anime_details(anime['url'])
        kwargs, chat_id = new_anime(anime), message.message.chat.id
        kwargs['reply_markup'] = new_keyboard(anime['chapters'])
        message = self.bot.send_photo(chat_id, **kwargs)
        arguments = message, self.select_chapter, anime['chapters']
        self.bot.register_next_step_handler(*arguments)

    def select_chapter(self, message: telebot.types.Message, chapters: list):
        if not message.text.isdigit(): return self._next_handler(message)
        chapter = self.anime.chapter_details(chapters[int(message.text) - 1])
        text, chat_id = models.chapter_details(chapter), message.chat.id
        keyboard = telebot.types.InlineKeyboardMarkup()
        callback = json.dumps(['download_chapter', chapter['id']])
        self.chapter_list[chapter['id']] = chapter
        button = dict(text='Descargar', callback_data=callback)
        keyboard.add(telebot.types.InlineKeyboardButton(**button))
        arguments = chat_id, chapter['image'], text
        message = self.bot.send_photo(*arguments, reply_markup=keyboard)
        callback = self.select_chapter
        self.bot.register_next_step_handler(message, callback, chapters)

    def chapters_today(self, message: telebot.types.Message):
        chapter_list = self.anime.main_page()[0]
        text = models.chapter_list(chapter_list)

        chapter_list = [chapter['url'] for chapter in chapter_list]
        keyboard = new_keyboard(chapter_list, related=False)
        callback, chat_id = self.select_chapter, message.chat.id
        self.talk(message.chat.id, 'chapters-today', self.lang)

        message = self.bot.send_message(chat_id, text, reply_markup=keyboard)
        self.bot.register_next_step_handler(message, callback, chapter_list)

    def print_animes(self, anime_list: list[dict], chat_id: int):
        for anime in anime_list:
            self.anime_list[anime['id']] = anime
            time.sleep(0.25)
            self.bot.send_photo(chat_id, **new_anime(anime))

    def animes_today(self, message: telebot.types.Message):
        self.talk(message.chat.id, 'animes-today', self.lang)
        anime_list = self.anime.main_page()[1]
        self.print_animes(anime_list, message.chat.id)

    def search_anime(self, message: telebot.types.Message):
        self.talk(message.chat.id, 'find-anime', self.lang)
        command = re.findall(r"/(\w+)", message.text)[0]
        command = message.text.replace(f'/{command}', '')
        anime_list = self.anime.find_anime(command)
        self.print_animes(anime_list, message.chat.id)

    def select_query(self, message: telebot.types.CallbackQuery):
        getattr(self, json.loads(message.data)[0])(message)
