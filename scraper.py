from typing import List
import hashlib
import json
import re
from urllib.parse import urlencode, urlparse, urlunparse

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException

import settings
from exceptions import NoResultsException


class BingeObject:
    def serialize(self, as_dict=False) -> str:
        serial_dict = {}
        for k, v in self.__dict__.items():
            if isinstance(v, list) and len(v) > 0 and isinstance(v[0], BingeObject):
                serial_dict[k] = list(map(lambda x: x.serialize(as_dict=True), v))
            else:
                serial_dict[k] = v

        return serial_dict if as_dict else json.dumps(serial_dict)


class Trivia(BingeObject):
    def __init__(self, trivia_id: str, text: str):
        self.trivia_id = trivia_id
        self.score = -1
        self.score_denominator = 1
        self.text = text
        self.tag = []


class Episode(BingeObject):
    def __init__(self, episode_id, name: str, season: int):
        self.episode_id = episode_id
        self.name = name
        self.season = season
        self.trivia_set = []


class Series(BingeObject):
    def __init__(self, series_id: str, name: str):
        self.series_id = series_id
        self.name = name
        self.season_count = -1
        self.thumbnail_url = None
        self.episode_set = []
        self.trivia_set = []

    def get_episodes_from_season(self, season: int) -> List[Episode]:
        return filter(lambda x: x.season == season, self.episode_set)


class IMDBSeleniumScraper:
    driver_type = settings.SELENIUM_WEBDRIVER_TYPE

    def __init__(self, browser: WebDriver = None, will_get_trivia: bool = True):
        options = Options()
        options.headless = True
        self.default_browser = browser or self.driver_type(options=options, executable_path=settings.WEBDRIVER_PATH)
        self.will_get_trivia = will_get_trivia

    def search_media(self, title: str) -> Series:
        url_pieces = list(urlparse('http://www.imdb.com/find'))
        url_pieces[4] = urlencode({'q': title})
        url = urlunparse(url_pieces)
        self.default_browser.get(url)

        try:
            title_section = self.default_browser.find_element_by_xpath('//div[@class="findSection"]/h3/a[@name="tt"]/../..')
        except NoSuchElementException:
            raise NoResultsException(f'{title} has no results in IMDB')

        episode_element = title_section.find_elements_by_xpath('//tr/td[@class="result_text"]/a')[0]
        show_url = episode_element.get_attribute('href')
        series_id = re.findall(r'(?<=title/)tt.+(?=/\?ref)', show_url)[0]
        series = Series(series_id, episode_element.text)
        if 'title/tt' in show_url:
            thumb_links = episode_element.find_elements_by_xpath('../..//td[@class="primary_photo"]/a/img')
            series.thumbnail_url = thumb_links[0].get_attribute('src') if thumb_links else None
        season_link = f'http://www.imdb.com/title/{series.series_id}/episodes'
        series.trivia_set += self.extract_trivia_page(f'https://www.imdb.com/title/{series.series_id}/trivia')
        self.default_browser.get(season_link)
        series.season_count = len(self.default_browser.find_elements_by_xpath('//select[@id="bySeason"]/option'))
        for season in range(1, series.season_count+1):
            self.default_browser.get(season_link + f'?season={season}')
            for ep_element in self.default_browser.find_elements_by_xpath('//strong/a[@itemprop="name"]'):
                ep_url = ep_element.get_attribute('href')
                ep_id = re.findall(r'(?<=title/)tt.+(?=/\?ref)', ep_url)[0]
                new_ep = Episode(ep_id, ep_element.text, season)
                series.episode_set.append(new_ep)
            for e in series.episode_set:
                ep_trivia = self.extract_trivia_page(f'https://www.imdb.com/title/{e.episode_id}/trivia')
                series.trivia_set += ep_trivia
                e.trivia_set = ep_trivia
        return series

    def extract_trivia_page(self, url: str) -> List[Trivia]:
        trivia_set = []
        self.default_browser.get(url)
        trivia_divs = self.default_browser.find_elements_by_xpath('//div[contains(@id,"tr")]/div[@class="sodatext"]')
        for trivia_div in trivia_divs:
            trivia_id = hashlib.md5((trivia_div.text+url).encode('utf-8')).hexdigest()
            tr = Trivia(trivia_id, trivia_div.text)
            score_div = trivia_div.find_element_by_xpath('../div[@class="did-you-know-actions"]/a')
            score_str = re.findall('^[0-9]+', score_div.text)
            if score_str:
                tr.score = int(score_str[0]) if int(score_str[0]) > 0 else 1
                tr.score_denominator = int(re.findall('(?<=of )[0-9]+', score_div.text)[0])
                tr.score = tr.score if tr.score >= 0 else 0
            tr.score_denominator = tr.score_denominator if tr.score_denominator > 0 else 100
            trivia_set.append(tr)
        return trivia_set

    def __del__(self):
        if self.default_browser:
            self.default_browser.close()
