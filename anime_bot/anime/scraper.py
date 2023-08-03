import datetime
import json

import re

from bs4 import BeautifulSoup
from requests import Session


def list_videos(content: str) -> list[dict]:
    urls = re.search(r'var videos = (?P<videos>\{.+});', content)
    urls = json.loads(urls.group(1))['SUB']
    return [dict(name=u['server'], url=u['code']) for u in urls]


def list_episodes(anime_url: str, content: str) -> list[str]:
    episodes = re.search(r'var episodes = (?P<chapters>\[.+]);', content)
    episodes = json.loads(episodes[0].replace('var episodes = ', '')[:-1])
    return [anime_url.replace('anime/', 'ver/') + f'-{e[0]}' for e in episodes]


def get_genres(content: BeautifulSoup) -> list[str]:
    genres = content.find('nav', {'class': 'Nvgnrs'})
    return [genre.text for genre in genres.find_all('a')]


class AnimeFLV:
    def __init__(self):
        self.base_url = 'https://www3.animeflv.net'
        self.scraper = Session()
        agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0'
        self.scraper.headers['User-Agent'] = agent
        self.scraper.headers['referer'] = self.base_url

    def get_images(self, anime_id: int) -> tuple:
        url = f'{self.base_url}/uploads/animes/covers/'
        url += str(anime_id) + '.jpg'
        return url, url.replace('covers', 'thumbs')

    def get_anime(self, content: BeautifulSoup) -> dict:
        title, c_name = content.find('h3').text.strip(), {'class': 'Estreno'}
        points = float(content.find('span', {'class': 'fa-star'}).text)
        is_new = True if content.find('span', c_name) is not None else False
        anime_type = content.find('span', {'class': 'Type'}).text
        synopsis = content.find('div', {'class': 'Description'}).find_all('p')[-1]
        synopsis, url = synopsis.text, self.base_url + content.find('a')['href']
        anime_id = int(content.find('img')['src'].split('/')[-1].replace('.jpg', ''))
        images = self.get_images(anime_id)
        details = dict(is_new=is_new, type=anime_type, points=points, images=images)
        return dict(id=anime_id, title=title, synopsis=synopsis, url=url, **details)

    def list_animes(self, url) -> list[dict]:
        soup = BeautifulSoup(self.scraper.get(url).content, 'html.parser')
        anime_container = soup.find('ul', {'class': 'ListAnimes'})
        return [self.get_anime(li) for li in anime_container.find_all('li')]

    def anime_details(self, url) -> dict:
        content = self.scraper.get(url).text
        soup, next_chapter = BeautifulSoup(content, 'html.parser'), None
        synopsis = soup.find('meta', {'name': 'description'})['content']
        details = re.search(r'var anime_info = (?P<detail>\[.+])', content)
        details = json.loads(details[0].replace('var anime_info = ', ''))
        score = float(soup.find('span', {'id': 'votes_prmd'}).text)
        episodes, genres = list_episodes(url, content), get_genres(soup)
        images = self.get_images(details[0])
        if len(details) == 4:
            next_chapter = datetime.datetime.strptime(details[3], "%Y-%m-%d")
        related = soup.find('ul', {'class': 'ListAnmRel'})
        related_list = related.find_all('li') if related is not None else []
        data = dict(chapters=episodes[::-1], next=next_chapter, genres=genres)
        data = dict(**data, images=images, points=score, related=related_list)
        data['type'] = soup.find('span', {'class': 'Type'}).text
        return dict(id=details[0], title=details[1], synopsis=synopsis, **data)

    def chapter_details(self, url):
        content = self.scraper.get(url).text

        soup = BeautifulSoup(content, 'html.parser')
        title = soup.find('meta', {'property': 'og:title'})['content']

        chapter_id = re.search(r'var episode_id = (?P<id>[0-9]+);', content).group(1)
        anime_id = int(re.search(r'var anime_id = (?P<id>[0-9]+);', content).group(1))
        image, urls = self.get_images(anime_id)[-1], list_videos(content)
        return dict(id=int(chapter_id), title=title, image=image, urls=urls)

    def find_anime(self, query) -> list[dict]:
        url, anime_list = f'{self.base_url}/browse', []
        content = self.scraper.get(url, params={'q': query}).content
        soup = BeautifulSoup(content, 'html.parser')
        pagination = soup.find('ul', {'class': 'pagination'})
        if pagination is None or len(pagination.find_all('li')) < 3:
            return self.list_animes(url + f'?q={query}')
        pagination = pagination.find_all('li')[-2].find('a')
        for i in range(int(pagination.text))[1:]:
            anime_list.extend(self.list_animes(f'{url}?page={i}'))
        return anime_list

    def main_page(self):
        response = self.scraper.get(self.base_url).content
        soup = BeautifulSoup(response, 'html.parser')
        chapter_list = []
        for chapter in soup.find_all('a', {'class': 'fa-play'}):
            image = self.base_url + chapter.find_all('img')[-1]['src']
            title = chapter.find('strong', {'class': 'Title'}).string
            url = self.base_url + chapter['href']
            chapter = chapter.find('span', {'class': 'Capi'}).string
            anime_id = image.split('/')[-1].replace('.jpg', '')
            details = dict(image=image, url=url, chapter=chapter)
            details = dict(id=int(anime_id), title=title, **details)
            chapter_list.append(details)
        return chapter_list, self.list_animes(self.base_url)
