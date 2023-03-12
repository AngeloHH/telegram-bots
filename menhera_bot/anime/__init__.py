from _thread import start_new_thread
from time import sleep

import cloudscraper
import requests
import telebot
from telebot.types import Message

from menhera_bot.anime.crud import AnimeFLV
from menhera_bot.anime.models import list_chapters, chapter_details, anime_details, anime_selected
from menhera_bot.api import say, host, send_sticker, invalid_type
from menhera_bot.logger import BotLogger


class AnimeCommands:
    def __int__(self, bot: telebot.TeleBot, proxy=None):
        self.chapter_list, self.animes = {}, {}
        self.account_data, self.bot = {}, bot
        self.anime_api = AnimeFLV()
        self.create_scraper(proxy)
        start_new_thread(self.update_scraper, (proxy,))

    def create_scraper(self, proxy=None):
        while True:
            scraper = cloudscraper.create_scraper()
            self.anime_api.cloud_scraper = scraper
            self.anime_api.cloud_scraper.proxies = proxy
            response = self.anime_api.cloud_scraper.get
            response = response(self.anime_api.base_url)
            if response.status_code == 200: break

    def update_scraper(self, proxy=None):
        while True:
            sleep(10 * 60)
            try: self.create_scraper(proxy)
            except: pass

    def download_chapter(self, message: Message, url):
        key = 'downloading-chapter', 'download-error'
        say(self.bot, message, 'es', key[0])
        link = host('media', 'download', url['server'].lower())
        resp = requests.get(link, {'url': url['url']})
        if resp.status_code != 200:
            send_sticker(self.bot, message, 'congested')
            return say(self.bot, message, 'es', key[1])
        for url in resp.json():
            url = host(*url.split('/')[1:])
            data = requests.get(url).content
            args = message.chat.id, data
            kwargs = {'visible_file_name': url.split('/')[-1]}
            self.bot.send_document(*args, **kwargs)
            requests.get(url.replace('get', 'delete'))

    def print_chapter(self, message: Message, chapters):
        """
        Send selected chapter for download
        :param message: Message sending by user
        :param chapters: List of today chapters
        """
        if invalid_type(int, message, self.bot, 'es'): return
        chapter = chapters[int(message.text) - 1]
        getter = self.anime_api.cloud_scraper
        BotLogger().action_log(message)
        chapter = chapter_details(getter, chapter)
        key = next(k for k in chapter[1].keys())
        self.chapter_list[key] = chapter[1][key]
        args = [self.bot.send_photo, self.print_chapter]
        args[0] = args[0](message.chat.id, **chapter[0])
        self.bot.register_next_step_handler(*args, chapters)

    def print_chapters(self, message: Message):
        chapters = self.anime_api.main_page().chapter_list
        arguments = {'chat_id': message.chat.id, **list_chapters(chapters)}
        args = self.bot.send_message(**arguments), self.print_chapter
        self.bot.register_next_step_handler(*args, chapters)

    def print_anime(self, message: Message, anime: dict):
        chapters_count = len(anime['chapters'])
        args = message.chat.id, anime_selected(anime, 50)
        reply = self.bot.send_photo(args[0], **args[1])
        args = self.bot, message, 'too-much-chapters'
        if chapters_count > 50:
            send_sticker(*args)
            say(self.bot, message, 'es', args[2])
        chapters = anime['chapters']
        chapters = [{'url': url} for url in chapters]
        args = reply, self.print_chapter, chapters
        self.bot.register_next_step_handler(*args)

    def print_animes(self, message: Message, animes: list):
        for anime in animes:
            anime_page = self.anime_api.anime_page
            anime = anime_page(anime['url'])
            self.animes[anime['id']] = anime
            anime = anime_details(anime)
            self.bot.send_photo(message.chat.id, **anime)
        say(self.bot, message, 'es', 'task-ending')

    def animes_today(self, message: Message):
        animes = self.anime_api.main_page().anime_list
        self.print_animes(message, animes)

    def search_result(self, message: Message):
        command = message.text.split(' ')[0] + ' '
        anime = message.text.replace(command, '')
        anime_list = self.anime_api.find_anime(anime)
        anime_list = [{'url': url} for url in anime_list]
        self.print_animes(message, anime_list)
