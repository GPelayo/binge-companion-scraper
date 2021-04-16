from typing import List
import json
import re
from urllib.parse import urlencode, urlparse, urlunparse

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
import settings

import pprint


class BingeObject:
    def serialize(self, as_dict=False) -> str:
        serial_dict = {'id': str(id(self))}
        for k, v in self.__dict__.items():
            if isinstance(v, list) and len(v) > 0 and isinstance(v[0], BingeObject):
                serial_dict[k] = list(map(lambda x: x.serialize(as_dict=True), v))
            else:
                serial_dict[k] = v
        pprint.pprint(serial_dict)
        if as_dict:
            return serial_dict
        else:
            return json.dumps(serial_dict)


class Trivia(BingeObject):
    def __init__(self, text: str):
        self.score = -1
        self.score_denominator = 1
        self.text = text
        self.tag = []


class Episode(BingeObject):
    def __init__(self, name: str, season: int):
        self.name = name
        self.season = season
        self.trivia_set = []


class Series(BingeObject):
    def __init__(self, name: str):
        self.name = name
        self.season_count = -1
        self.thumbnail_url = None
        self.episode_set = []

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
        title_section = self.default_browser.find_element_by_xpath('//div[@class="findSection"]/h3/a[@name="tt"]/../..')
        episode_element = title_section.find_elements_by_xpath('//tr/td[@class="result_text"]/a')[0]
        series = Series(episode_element.text)
        show_url = episode_element.get_attribute('href')
        series.imdb_id = re.findall(r'(?<=title\/)tt.+(?=\/\?ref)', show_url)[0]
        if 'title/tt' in show_url:
            thumb_links = episode_element.find_elements_by_xpath('../..//td[@class="primary_photo"]/a/img')
            series.thumbnail_url = thumb_links[0].get_attribute('src') if thumb_links else None
        season_link = f'http://www.imdb.com/title/{series.imdb_id}/episodes'
        self.default_browser.get(season_link)
        series.season_count = len(self.default_browser.find_elements_by_xpath('//select[@id="bySeason"]/option'))
        for season in range(1, series.season_count+1):
            self.default_browser.get(season_link + f'?season={season}')
            for ep_element in self.default_browser.find_elements_by_xpath('//strong/a[@itemprop="name"]'):
                ep_url = ep_element.get_attribute('href')
                ep_id = re.findall(r'(?<=title\/)tt.+(?=\/\?ref)', ep_url)[0]
                new_ep = Episode(ep_element.text, season)
                new_ep.imdb_id = ep_id
                series.episode_set.append(new_ep)
            for e in series.episode_set:
                self.default_browser.get(f'https://www.imdb.com/title/{e.imdb_id}/trivia')
                trivia_divs = self.default_browser.find_elements_by_xpath('//div[contains(@id,"tr")]'
                                                                          '/div[@class="sodatext"]')
                for trivia_div in trivia_divs:
                    tr = Trivia(trivia_div.text)
                    score_div = trivia_div.find_element_by_xpath('../div[@class="did-you-know-actions"]/a')
                    tr.score = int(re.findall('^[0-9]+', score_div.text)[0])
                    tr.score_denominator = int(re.findall('(?<=of )[0-9]+', score_div.text)[0])
                    e.trivia_set.append(tr)
                break
        self.default_browser.close()
        return series
