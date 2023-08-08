import emoji
import telebot

from base_bot.external.manager import CentralApi


class TalkerManager:
    def __init__(self, bot: telebot.TeleBot):
        self.bot = bot
        self.external = CentralApi()

    def talk(self, chat_id, key, lang):
        bot_id = self.bot.get_me().id
        arguments = bot_id, key, lang

        for text in self.external.get_text(*arguments):
            if emoji.emoji_count(text[0]) == 0:
                self.bot.send_message(chat_id, text)
                continue
            args = self.bot.get_me().id, None, text[0]
            sticker = self.external.get_sticker(*args)
            if sticker is not None:
                self.bot.send_sticker(chat_id, sticker)
