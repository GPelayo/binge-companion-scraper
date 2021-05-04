import os
from selenium import webdriver

SELENIUM_WEBDRIVER_TYPE = webdriver.Chrome
WEBDRIVER_APP = 'chromedriver.exe' if 'nt' == os.name else 'chromedriver'
WEBDRIVER_PATH = os.path.join(os.path.dirname(__file__), 'webdriver', WEBDRIVER_APP)

BACKEND_API_URL = ''
BACKEND_API_TOKEN = ''
