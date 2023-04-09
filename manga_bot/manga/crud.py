import datetime
import os
import re

from bs4 import BeautifulSoup
from cloudscraper import create_scraper

from manga_bot.manga.exceptions import LectorMOExceptions


class LectorMO:
    def __int__(self):
        self.exceptions = LectorMOExceptions()
        self.base_url = 'https://lectortmo.com/'
        self.scraper = create_scraper()
        self.scraper.headers['Referer'] = self.base_url

    def get_manga(self, raw_text: BeautifulSoup):
        script = raw_text.find('style').text
        expression = r"(?P<url>https?://[^\s]+)'\);"
        background = re.search(expression, script)
        background = background.group("url")
        title = raw_text.find('h4', 'text-truncate').text
        demography = {'class': 'demography'}
        demography = raw_text.find('span', demography).text
        book_type = {'class': 'book-type'}
        book_type = raw_text.find('span', book_type).text
        score = {'class': 'score'}
        score = float(raw_text.find('span', score).text)
        return {
            'id': raw_text['href'].split('/')[-2],
            'title': title, 'book-type': book_type,
            'demography': demography, 'image': background,
            'score': score, 'url': raw_text['href']
        }

    def get_pill(self, tab_name: str, content: bytes) -> list:
        soup = BeautifulSoup(content, 'html.parser')
        container_data = {'class': 'container-fluid'}
        container = soup.find('main', container_data)
        tab = container.find('div', {'id': f'pills-{tab_name}'})
        if tab is None: return []
        manga_list = tab.find_all('a')[:-1]
        return [self.get_manga(manga) for manga in manga_list]

    def search(self, query: str) -> list:
        query = query.replace(' ', '+')
        url = f'{self.base_url}library?_pg=1&title={query}'
        content = self.scraper.get(url).content
        soup = BeautifulSoup(content, 'html.parser')
        container = soup.find_all('div', {'class': 'row'})[1]
        content = container.find('div', {'class': 'col-xl-9'})
        row = content.find_all('div', {'class': 'row'})[1]
        return [self.get_manga(a) for a in row.find_all('a')]

    def get_hashtag(self, url):
        content = self.scraper.get(url).content
        soup = BeautifulSoup(content, 'html.parser')
        card = soup.find('div', {'class': 'clearfix'})
        return [a.text for a in card.find_all('a')]

    def get_memes(self, content: bytes):
        soup = BeautifulSoup(content, 'html.parser')
        container_data = {'class': 'container-fluid'}
        container = soup.find('main', container_data)
        memes_container = container.find_all('div', {'class': 'row'})[16]
        memes_data = {'class': 'col-12 col-md-4 mt-2'}
        memes = memes_container.find_all('div', memes_data)
        return [{
            'url': meme.find('a')['href'],
            'img': meme.find('img')['src'],
            'hashtags': self.get_hashtag(meme.find('a')['href'])
        } for meme in memes]

    def get_scan(self, chapter: BeautifulSoup):
        scan_list = []
        for scan in chapter.find_all('li'):
            date = scan.find('span', {'class': 'badge'})
            date = date.text.strip()
            date = [int(i) for i in date.split('-')]
            date = datetime.date(*date).strftime('%d-%m-%Y')
            scan_list.append({
                'scan-name': scan.find('a').text, 'date': date,
                'url': scan.find('a', {'class': 'btn'})['href']
            })
        return scan_list

    def one_shot(self, raw_text: BeautifulSoup):
        data = {'class': 'chapter-list-element'}
        container = raw_text.find('div', data)
        li = self.get_scan(container)
        return dict(number='one shot', title='', scans=li)

    def get_chapters(self, raw_text: BeautifulSoup):
        container = raw_text.find('div', {'id': 'chapters'})
        chapters_data = {'class': 'upload-link'}
        if container is None: return [self.one_shot(raw_text)]
        chapters: list = container.find_all('li', chapters_data)
        for index, chapter in enumerate(chapters):
            title = chapter.find('a').text.strip()
            number = title.split(' ')[1]
            title = title[title.index(number) + len(number) + 1:]
            chapters[index] = {'number': number, 'title': title,
                               'scans': self.get_scan(chapter)}
        return [*reversed(chapters)]

    def manga_details(self, url: str):
        content = create_scraper().get(url).content
        soup = BeautifulSoup(content, 'html.parser')
        title_class = {'class': 'element-title'}
        exception = self.exceptions.too_many_request
        title = soup.find('h1', title_class)
        if title is None: raise exception()
        title = title.text.strip().replace('\n', ' ')
        subtitle_class = {'class': 'element-subtitle'}
        subtitle = soup.find('h2', subtitle_class)
        subtitle = subtitle.text
        synopsis_class = {'class': 'element-description'}
        synopsis = soup.find('p', synopsis_class).text
        genres = [h6.text for h6 in soup.find_all('h6')]
        return {
            'id': url.split('/')[-2], 'title': title,
            'subtitle': subtitle, 'genres': genres,
            'synopsis': synopsis, 'chapters': self.get_chapters(soup)
        }

    def get_images(self, url):
        url = self.scraper.get(url).url
        mode = url.split('/')[-1]
        url = url.replace(mode, 'cascade')

        content = self.scraper.get(url).content
        soup = BeautifulSoup(content, 'html.parser')
        image_data = {'class': 'viewer-img'}
        images = soup.find_all('img', image_data)
        images = [img['data-src'] for img in images]
        image = []
        [image.append(i) for i in images if i not in image]
        return image
