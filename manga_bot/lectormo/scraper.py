import datetime
import re

from bs4 import BeautifulSoup
from requests import Session

from manga_bot.lectormo.exceptions import LectorMOExceptions


class LectorMO:
    def __init__(self):
        self.exceptions = LectorMOExceptions()
        self.base_url = 'https://lectortmo.com/'
        self.scraper = Session()
        self.scraper.headers['Referer'] = self.base_url
        agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0'
        self.scraper.headers['User-Agent'] = agent

    def _get_manga(self, raw_text: BeautifulSoup):
        # Extract background image URL from the style script.
        script = raw_text.find('style').text
        expression = r"(?P<url>https?://[^\s]+)'\);"
        background = re.search(expression, script)
        background = background.group("url")

        # Extract manga title, demography, book type, and score.
        title = raw_text.find('h4', 'text-truncate').text
        demography = {'class': 'demography'}
        demography = raw_text.find('span', demography).text
        book_type = {'class': 'book-type'}
        book_type = raw_text.find('span', book_type).text
        score = {'class': 'score'}
        score = float(raw_text.find('span', score).text)

        # Create and return a dictionary containing the manga
        # information.
        return {
            'id': raw_text['href'].split('/')[-2],
            'title': title, 'book-type': book_type,
            'demography': demography, 'image': background,
            'score': score, 'url': raw_text['href']
        }

    def get_pill(self, tab_name: str, content: bytes) -> list:
        soup = BeautifulSoup(content, 'html.parser')
        # Find the main container for the tab content.
        container_data = {'class': 'container-fluid'}
        container = soup.find('main', container_data)
        # Find the specific tab element based on the given name.
        tab = container.find('div', {'id': f'pills-{tab_name}'})
        if tab is None: return []
        manga_list = tab.find_all('a')[:-1]
        # Create a list of mangas information if the tab is not
        # None.
        return [self._get_manga(manga) for manga in manga_list]

    def search(self, query: str) -> list:
        query = query.replace(' ', '+')
        # Create the URL to search for manga based on the query.
        url = f'{self.base_url}library?_pg=1&title={query}'
        content = self.scraper.get(url).content
        # Find the main container for the search results.
        soup = BeautifulSoup(content, 'html.parser')
        container = soup.find_all('div', {'class': 'row'})[1]
        content = container.find('div', {'class': 'col-xl-9'})
        row = content.find_all('div', {'class': 'row'})[1]
        # Create a list of mangas information.
        return [self._get_manga(a) for a in row.find_all('a')]

    def _get_hashtag(self, url):
        # Use the scraper to get the html content and
        # parse it.
        content = self.scraper.get(url).content
        soup = BeautifulSoup(content, 'html.parser')
        card = soup.find('div', {'class': 'clearfix'})
        # Get a list of hashtags present in the url.
        return [a.text for a in card.find_all('a')]

    def get_memes(self, content: bytes):
        soup = BeautifulSoup(content, 'html.parser')
        # Find the container that holds the memes.
        container_data = {'class': 'container-fluid'}
        container = soup.find('main', container_data)
        # Find all the memes within the container.
        memes_container = container.find_all('div', {'class': 'row'})[16]
        memes_data = {'class': 'col-12 col-md-4 mt-2'}
        # Return a list of dictionaries, each representing a meme.
        return [{
            'url': meme.find('a')['href'],
            'img': meme.find('img')['src'],
            'hashtags': self._get_hashtag(meme.find('a')['href'])
        } for meme in memes_container.find_all('div', memes_data)]

    def get_scan(self, chapter: BeautifulSoup):
        scan_list = []
        # Loop through each 'li' element within the container.
        for scan in chapter.find_all('li'):
            # Extract the date and convert it into date object.
            date = scan.find('span', {'class': 'badge'})
            date = date.text.strip()
            date = [int(i) for i in date.split('-')]
            date = datetime.date(*date).strftime('%d-%m-%Y')
            # Create a dictionary and append to it to scan_list.
            scan_list.append({
                'scan-name': scan.find('a').text, 'date': date,
                'url': scan.find('a', {'class': 'btn'})['href']
            })
        return scan_list

    def one_shot(self, raw_text: BeautifulSoup):
        data = {'class': 'chapter-list-element'}
        container = raw_text.find('div', data)
        # Get the one_shot chapter (nothing to say).
        li = self.get_scan(container)
        return dict(number='one shot', title='', scans=li)

    def get_chapters(self, raw_text: BeautifulSoup):
        # Get the chapter list and the scans in each of this.
        container = raw_text.find('div', {'id': 'chapters'})
        chapters_data = {'class': 'upload-link'}
        # If the manga is a one-shot return the only chapter.
        if container is None: return [self.one_shot(raw_text)]
        chapters: list = container.find_all('li', chapters_data)
        # Loop through each chapter in the chapter list.
        for index, chapter in enumerate(chapters):
            title = chapter.find('a').text.strip()
            number = title.split(' ')[1]
            title = title[title.index(number) + len(number) + 1:]
            chapters[index] = {'number': number, 'title': title,
                               'scans': self.get_scan(chapter)}
        return [*reversed(chapters)]

    def manga_details(self, url: str):
        content = self.scraper.get(url).content
        soup = BeautifulSoup(content, 'html.parser')
        title_class = {'class': 'element-title'}
        # If the title is not found, raise an exception (too many requests).
        exception = self.exceptions.too_many_request
        title = soup.find('h1', title_class)
        if title is None: raise exception()
        # Find the manga image url, title, subtitle, synopsis, genres and
        # score using their respective tags.
        image = soup.find('img', {'class': 'book-thumbnail'})
        title = title.text.strip().replace('\n', ' ')
        subtitle_class = {'class': 'element-subtitle'}
        subtitle = soup.find('h2', subtitle_class)
        subtitle, image = subtitle.text, image['src']
        synopsis_class = {'class': 'element-description'}
        synopsis = soup.find('p', synopsis_class).text
        genres = [h6.text for h6 in soup.find_all('h6')]
        score = soup.find('div', {'class': 'score'}).text.strip()
        return {
            'id': url.split('/')[-2], 'title': title, 'image': image,
            'subtitle': subtitle, 'genres': genres, 'score': score,
            'synopsis': synopsis, 'chapters': self.get_chapters(soup)
        }

    def get_images(self, url):
        # Get all images in one page.
        url = self.scraper.get(url).url
        mode = url.split('/')[-1]
        url = url.replace(mode, 'cascade')

        content = self.scraper.get(url).content
        soup = BeautifulSoup(content, 'html.parser')
        image_data = {'class': 'viewer-img'}

        # List all images and save the urls.
        images = soup.find_all('img', image_data)
        images = [img['data-src'] for img in images]
        image = []

        # Filter the duplicated images without change the
        # order.
        [image.append(i) for i in images if i not in image]
        return image
