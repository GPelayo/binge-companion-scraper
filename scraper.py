from typing import List
import hashlib
import re
from urllib.parse import urlencode, urlparse, urlunparse

from binge_models.models import Series, Episode, Trivia
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from exceptions import NoResultsException
from webdriver import ChromeWebDriverFactory


class IMDBSeleniumScraper:
    def __init__(self, will_get_trivia: bool = True):
        self.browser = None
        self.will_get_trivia = will_get_trivia

    def __enter__(self):
        self.browser = ChromeWebDriverFactory().get_webdriver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.browser.close()

    def open_browser(self):
        self.browser = ChromeWebDriverFactory().get_webdriver()

    def search_media(self, title: str) -> Series:
        url_pieces = list(urlparse('http://www.imdb.com/find'))
        url_pieces[4] = urlencode({'q': title})
        url = urlunparse(url_pieces)
        self.browser.get(url)

        try:
            title_div = self.browser.find_element(By.XPATH, '//div[@class="findSection"]/h3/a[@name="tt"]/../..')
        except NoSuchElementException:
            raise NoResultsException(f'{title} has no results in IMDB')

        show_result_element = title_div.find_elements(By.XPATH, '//tr/td[@class="result_text"]/a')[0]
        show_url = show_result_element.get_attribute('href')
        series_id = re.findall(r'(?<=title/)tt.+(?=/\?ref)', show_url)[0]
        series = Series(series_id, show_result_element.text)
        if 'title/tt' in show_url:
            thumb_links = show_result_element.find_elements(By.XPATH, '../..//td[@class="primary_photo"]/a/img')
            series.thumbnail_url = thumb_links[0].get_attribute('src') if thumb_links else None
        return series

    def scrape_series_page(self, series):
        season_link = f'http://www.imdb.com/title/{series.series_id}/episodes'
        series.series_trivia += self.extract_trivia_page(series.series_id,
                                                         f'https://www.imdb.com/title/{series.series_id}/trivia')

        self.browser.get(season_link)
        series.season_count = len(self.browser.find_elements(By.XPATH, '//select[@id="bySeason"]/option'))
        for season in range(1, series.season_count+1):
            self.browser.get(season_link + f'?season={season}')
            for ep_element in self.browser.find_elements(By.XPATH, '//strong/a[@itemprop="name"]'):
                ep_url = ep_element.get_attribute('href')
                ep_id = re.findall(r'(?<=title/)tt.+(?=/\?ref)', ep_url)[0]
                new_ep = Episode(ep_id, ep_element.text, season, series.series_id)
                series.episodes.append(new_ep)
            for e in series.episodes:
                ep_trivia = self.extract_trivia_page(series.series_id,
                                                     f'https://www.imdb.com/title/{e.episode_id}/trivia')
                series.series_trivia += ep_trivia
                e.trivia_list = ep_trivia
        return series

    def extract_trivia_page(self, series_id: str, url: str) -> List[Trivia]:
        trivia_list = []
        self.browser.get(url)
        trivia_divs = self.browser.find_elements(By.XPATH, '//div[contains(@id,"tr")]/div[@class="sodatext"]')
        for trivia_div in trivia_divs:
            trivia_id = hashlib.md5((trivia_div.text+url).encode('utf-8')).hexdigest()
            tr = Trivia(trivia_id, trivia_div.text, series_id)
            score_div = trivia_div.find_element_by_xpath('../div[@class="did-you-know-actions"]/a')
            score_str = re.findall('^[0-9]+', score_div.text)
            if score_str:
                tr.score = int(score_str[0]) if int(score_str[0]) > 0 else 1
                tr.score_denominator = int(re.findall('(?<=of )[0-9]+', score_div.text)[0])
            tr.score_denominator, tr.score = tr.score_denominator, tr.score if tr.score_denominator > 0 else (0, 1)
            trivia_list.append(tr)
        return trivia_list

    def close_browser(self):
        self.browser.close()
