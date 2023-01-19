import json

import cloudscraper
import re

from bs4 import BeautifulSoup


class AnimeFLV:
    def __init__(self):
        self.base_url = 'https://www3.animeflv.net'
        self.cloud_scraper = cloudscraper.create_scraper()

    def main_page(self):
        error_text = "Failed to jump to CloudFlare"
        response = self.cloud_scraper.get(self.base_url)
        if response.status_code != 200: raise error_text
        soup = BeautifulSoup(response.content, 'html.parser')

        anime_raw = soup.find('ul', {'class': 'ListSdbr'}).find_all('a')
        chapters_raw = soup.find_all('a', {'class': 'fa-play'})

        class GroupList:
            anime_list = [{
                'url': self.base_url + anime['href'],
                'type': anime.find('span').text,
                'name': anime.text.replace(anime.find('span').text, '')
            } for anime in anime_raw]

            chapter_list = [{
                'url': self.base_url + chapter['href'],
                'image': self.base_url + chapter.find_all('img')[-1]['src'],
                'title': chapter.find('strong', {'class': 'Title'}).string,
                'chapter': chapter.find('span', {'class': 'Capi'}).string
            } for chapter in chapters_raw]

        return GroupList

    def chapter_page(self, url):
        response = self.cloud_scraper.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('div', {'id': 'DwsldCn'}).find('table')
        anime_url = soup.find('nav', {'class': 'Brdcrmb'}).find_all('a')[1]['href']
        chapter_id = re.search(r'var episode_id = (?P<id>[0-9]+);', response.text)
        anime_id = re.search(r'var anime_id = (?P<id>[0-9]+);', response.text)
        episode_number = re.search(r'var episode_number = (?P<number>[0-9]+);', response.text)
        urls = [{
            'server': link.find_all('td')[0].string,
            'url': link.find_all('td')[3].find('a')['href']
        } for link in table.find('tbody').find_all('tr')]
        return {
            'id': int(chapter_id.groups()[0]),
            'name': soup.find('div', {'class': 'CapiTop'}).find('h1')['title'],
            'image': f'{self.base_url}/uploads/animes/thumbs/{anime_id.group("id")}.jpg',
            'urls': urls,
            'anime-url': self.base_url + anime_url,
            'episode-number': episode_number.groups()[0]
        }

    def anime_page(self, url):
        response = self.cloud_scraper.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        anime_info = re.search(r'var anime_info = (?P<details>\[.+\])', response.text)
        anime_info = json.loads(anime_info.groups()[0])
        episodes = re.search(r'var episodes = (?P<chapters>\[.+\]);', response.text)
        episodes = [episode[0] for episode in json.loads(episodes.groups()[0])]
        episodes.sort()
        episodes_url = [f'{self.base_url}/ver/{anime_info[2]}-{episode}' for episode in episodes]
        related_list = soup.find('ul', {'class': 'ListAnmRel'})
        anime_related = related_list.find_all('li') if related_list is not None else []
        category_list = soup.find('nav', {'class': 'Nvgnrs'}).find_all('a')
        image = soup.find('div', {'class': 'Image'}).find_all('img')[-1]['src']
        return {
            'id': int(anime_info[0]),
            'name': anime_info[1],
            'category-list': list(category.string for category in category_list),
            'synopsis': soup.find('div', {'class': 'Description'}).find('p').string,
            'next-chapter': anime_info[3] if len(anime_info) == 4 else None,
            'image': self.base_url + image,
            'status': soup.find('p', {'class': 'AnmStts'}).find('span').string,
            'related': list(anime.text for anime in anime_related),
            'chapters': episodes_url,
            'votes': float(soup.find('span', {'id': 'votes_prmd'}).string),
        }

    def find_anime(self, search):
        url = f'{self.base_url}/browse?q={search}'
        response = self.cloud_scraper.get(url).content
        soup = BeautifulSoup(response, 'html.parser')
        paginator = soup.find('ul', {'class': 'pagination'}).find_all('li')
        anime_result = []
        next_url = paginator[len(paginator) - 1].find('a')['href']
        while True:
            anime_result += [
                self.base_url + anime.find('a')['href']
                for anime in soup.find('ul', {'class': 'ListAnimes'}).find_all('li')
            ]
            if next_url == '#' or '&page=1' in next_url:
                break
            response = self.cloud_scraper.get(self.base_url + next_url).content
            soup = BeautifulSoup(response, 'html.parser')
            paginator = soup.find('ul', {'class': 'pagination'}).find_all('li')
            next_url = paginator[len(paginator) - 1].find('a')['href']
        return anime_result
