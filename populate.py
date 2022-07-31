import argparse
import sys

from database import Database
from scraper import IMDBSeleniumScraper


parser = argparse.ArgumentParser('Extracts TV Show data to AWS RDB.')
parser.add_argument('show_title', help='TV Show title for scraping.')
args = parser.parse_args(sys.argv[1:])

if args.show_title:
    with Database() as dc:
        with IMDBSeleniumScraper(max_seasons=2) as scraper:
            series = scraper.search_media(args.show_title)

            if dc.has_series(series.series_id):
                print(f'ERROR. Scraping stopped. "{args.show_title}" is already in the database.')
                exit()
            else:
                series = scraper.scrape_series_page(series)

            dc.write_series(series)
