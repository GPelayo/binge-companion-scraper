from abc import ABC

from selenium.webdriver import ChromeOptions, Chrome

from config import CHROME_BINARY_LOCATION, CHROMEDRIVER_LOCATION


class WebDriverFactory(ABC):
    def get_webdriver(self):
        pass


class ChromeWebDriverFactory(WebDriverFactory):
    def get_webdriver(self):
        chrome_options = ChromeOptions()
        chrome_options.headless = True
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument('--single-process')
        chrome_options.binary_location = CHROME_BINARY_LOCATION
        chromedriver_location = CHROMEDRIVER_LOCATION
        return Chrome(executable_path=chromedriver_location, options=chrome_options)
