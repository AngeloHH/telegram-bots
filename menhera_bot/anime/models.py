import json

import emoji
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup

from menhera_bot.anime import AnimeFLV


def get_stars(points=0.0): return ''.join(emoji.emojize(':star:') for a in range(round(points)))


def list_chapters(chapters: list) -> dict:
    text = 'Generando lista de capitulos diarios.\n'
    reply_markup, button = [], KeyboardButton
    for index, chapter in enumerate(chapters):
        text += f"[{'%02d' % (index + 1)}] » "
        text += f"{chapter['title']} {chapter['chapter']}\n"
        reply_markup.append(button('%02d' % (index + 1)))
    kwargs = {'resize_keyboard': True, 'one_time_keyboard': True}
    reply_markup = ReplyKeyboardMarkup(**kwargs).add(*reply_markup)
    return {'text': text, 'reply_markup': reply_markup}


def anime_details(anime: dict):
    args = {'photo': anime['image'], 'caption': anime['name']}
    text = '{}\nEstado: :warning:{}\nProximo Episodio: :calendar:{}\n'
    text += 'Categorias: {}\nVotos: {}\nCapitulos: {}\nSinopsis: {}'
    category, chapters = ', '.join(anime['category-list']), anime['chapters']
    synopsis = '' if anime['synopsis'] is None else anime['synopsis']
    votes, synopsis = get_stars(anime['votes']), synopsis[0:250]
    arg = anime['name'], anime['status'], anime['next-chapter'], category
    args['caption'] = text.format(*arg, votes, len(chapters), synopsis)
    args['caption'] = emoji.emojize(args['caption'])
    args['reply_markup'] = InlineKeyboardMarkup().add(*[
        InlineKeyboardButton(text='Seleccionar', callback_data=anime['id'])
    ])
    return args


def anime_selected(anime: dict, chapter_count):
    kwargs = {'resize_keyboard': True, 'one_time_keyboard': True}
    chapters = anime['chapters']
    anime = {**anime_details(anime), 'reply_markup': ReplyKeyboardMarkup(**kwargs)}
    buttons = [KeyboardButton(text=chapter.split('-')[-1]) for chapter in chapters]
    anime['reply_markup'].add(*buttons)
    if len(chapters) > chapter_count: anime.pop('reply_markup')
    return anime


def chapter_details(getter: requests, chapter: dict):
    anime_api, markup = AnimeFLV(), InlineKeyboardMarkup()
    anime_api.cloud_scraper = getter
    chapter = anime_api.chapter_page(chapter['url'])
    anime = anime_api.anime_page(chapter['anime-url'])
    # Reformat the caption text for chapter.
    args = anime_details(anime)['caption'].split('\n')
    [args.pop(3) for x in range(3)]
    args[0] = chapter['name']
    args = '\n'.join(line for line in args)
    args = {'photo': chapter['image'], 'caption': args}
    def call(i): return [chapter['id'], i]
    args['reply_markup'] = markup.add(*[InlineKeyboardButton(
        text=u["server"], callback_data=json.dumps(call(i))
    ) for i, u in enumerate(chapter['urls'])])
    return args, {chapter['id']: chapter['urls']}

