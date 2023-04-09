from manga_bot.manga.crud import LectorMO


class MangaStarter:
    def __int__(self):
        self.lector_api = LectorMO()
        self.lector_api.__int__()
        self.main_page = self.lector_api.scraper
        url = self.lector_api.base_url
        self.main_page = self.main_page.get(url)
        self.main_page = self.main_page.content

    def tab_comics(self, tab: str, genre=None):
        arguments = [tab, self.main_page]
        if genre is not None: arguments[0] += f'-{genre}s'
        return self.lector_api.get_pill(*arguments)

    def trending_comics(self, genre=None):
        return self.tab_comics('trending', genre)

    def popular_comics(self, genre=None):
        return self.tab_comics('populars', genre)
