import re

from requests import Session, Response


class YourUpload:
    scraper = Session()

    def get_data(self, url) -> dict:
        text = self.scraper.get(url).text
        file = re.search(r"file: '([^']*)", text).group(1)
        return dict(url=file, referer=url)

    def get_file(self, url, **kwargs) -> Response:
        url, self.scraper.headers['referer'] = self.get_data(url).values()
        return self.scraper.get(url, **kwargs)
