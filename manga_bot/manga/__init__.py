import math
import queue
import re
from _thread import start_new_thread
from time import sleep

import numpy as numpy
import requests
import telebot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup

from central.utils.talk_manager import say, send_sticker
from manga_bot.manga.models import MangaStarter
from manga_bot.telegraph_api import TelegraphApi, create_link, create_text


class MangaCommands:
    def __int__(self, bot: telebot.TeleBot):
        self.models, self.bot = MangaStarter(), bot
        self.models.__int__()
        self.manga_api = self.models.lector_api
        self.comic_list, self.percent = {}, {}
        self.telegraph_api = TelegraphApi()
        self.telegraph_api.__int__(self.bot)
        self.scraper = self.manga_api.scraper

    def get_memes(self, chat_id):
        latest_meme = None
        meme_queue = queue.Queue()

        def send_meme():
            while True:
                meme = meme_queue.get()['img']
                self.bot.send_photo(chat_id, meme)

        start_new_thread(send_meme, ())
        while True:
            get_memes = self.manga_api.get_memes
            sleep(10 * 60)
            memes = get_memes(self.models.main_page)
            if memes.index(latest_meme) != -1:
                memes = memes[:memes.index(latest_meme)]
            for index, meme in enumerate(memes):
                meme_queue.put(meme)
            latest_meme = memes[0]

    def comic_text(self, comic: dict):
        comic_details = self.manga_api.manga_details
        comic_details = comic_details(comic['url'])
        synopsis = comic_details['synopsis'][:300]
        genre = ", ".join(comic_details['genres'])
        text = "📚 Título: {}\n🔖 Géneros: {}\n📝"
        text += " Sinopsis: {}\n⭐️ Puntuación: {}"
        self.comic_list[comic['id']] = comic_details['chapters']
        return dict(caption=text.format(
            comic_details['subtitle'],
            genre, synopsis, comic['score']
        ), photo=comic['image'])

    def list_comics(self, comics: list, chat_id: int):
        for comic in comics:
            # sleep(1)
            arguments = self.comic_text(comic)
            arguments['chat_id'] = chat_id
            button = dict(text='Seleccionar', callback_data=comic['id'])
            button = InlineKeyboardButton(**button)
            keyboard = InlineKeyboardMarkup()
            keyboard = keyboard.add(*[button])
            arguments['reply_markup'] = keyboard
            self.bot.send_photo(**arguments)
        return None

    def get_genre(self, message: Message):
        genres, text = None, message.text
        if len(message.text.split(' ')) > 1:
            genres = text.split(' ')[1]
            genres = genres.replace('-', '')
            genres = genres.replace('—', '')
        return genres

    def get_trending(self, message: Message):
        genres = self.get_genre(message)
        comics = self.models.trending_comics(genres)
        self.list_comics(comics, message.chat.id)

    def get_populars(self, message: Message):
        genres = self.get_genre(message)
        comics = self.models.popular_comics(genres)
        self.list_comics(comics, message.chat.id)

    def image_percent(self, image, message: Message, images: int):
        message = self.percent[message.chat.id]
        search = re.search(r'\[(.*?)\]', message.text)
        if search is None: return None
        search = search.group()[1:-2]
        number = ((float(search) * images) / 100) + 1
        percent = round((number * 100) / images, 2)
        percent = percent if percent <= 100 else 100
        text = message.text.replace(search, str(percent))
        edit_message = self.bot.edit_message_text
        arguments = text, message.chat.id, message.id
        self.percent[message.chat.id] = edit_message(*arguments)

    def divide_post(self, images, comic_id):
        send_post = self.telegraph_api.send_post
        max_length = math.ceil(len(images) / 20)
        image_list = numpy.array_split(images, max_length)
        image_list = [*reversed(image_list)]
        for index, image in enumerate(image_list):
            image, text = list(image), 'Continue chapter'
            if index != 0:
                args = text, image_list[index - 1]
                args = 'h3', [create_link(*args)]
                image.append(create_text(*args))
            data = send_post(comic_id, image)
            image_list[index] = data['result']['url']
        return image_list[-1]

    def print_chapter(self, message: Message, images, comic_id):
        if len(images) == 0:
            send_sticker(self.bot, message, 'nervous')
            key = 'too-many-request'
            return say(self.bot, message, 'es', key)[0]
        send_post = self.telegraph_api.send_post
        post_data = send_post(comic_id, images)
        chat_id = message.chat.id
        send_message = self.bot.send_message
        if post_data['ok'] is False:
            post_data = self.divide_post(images, comic_id)
        else:
            post_data = post_data['result']['url']
        return send_message(chat_id, post_data)

    def select_chapter(self, message: Message, chapters: list, comic_id: str):
        def filter_chapter(comic): return comic['number'] == message.text
        chapter = next(c for c in chapters if filter_chapter(c))['scans'][0]
        images = self.manga_api.get_images(chapter['url'])
        kwargs = dict(chapters=chapters, comic_id=comic_id)
        images = [self.scraper.get(image).content for image in images]
        create_image = self.telegraph_api.upload_image
        next_step = self.bot.register_next_step_handler
        status = say(self.bot, message, 'es', 'download-status')[0]
        self.percent[message.chat.id] = status
        content = [create_image(i, self.image_percent, status, len(images)) for i in images]
        trigger = self.print_chapter(message, content, comic_id)
        next_step(trigger, self.select_chapter, **kwargs)

    def chapter_keyboard(self, message: telebot.types.CallbackQuery):
        photo_id = message.message.photo[-1].file_id
        chat_id = message.message.chat.id
        photo_url = self.bot.get_file_url(photo_id)
        photo = requests.get(photo_url).content
        self.bot.send_photo(chat_id, photo, message.message.caption)
        kwargs = dict(resize_keyboard=True, one_time_keyboard=True)
        next_step = self.bot.register_next_step_handler
        if len(self.comic_list[message.data]) <= 200:
            chapters = self.comic_list[message.data]
            trigger = self.bot, message.message, 'ok'
            cs_number = [KeyboardButton(c['number']) for c in chapters]
            keyboard = ReplyKeyboardMarkup(**kwargs).add(*cs_number)
            trigger = send_sticker(*trigger, reply_markup=keyboard)
            kwargs = dict(chapters=chapters, comic_id=message.data)
            next_step(trigger, self.select_chapter, **kwargs)
        else: say(self.bot, message.message, 'es', 'many-chapters')
