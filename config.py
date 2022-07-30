import os
import dotenv

dotenv.load_dotenv()

CHROME_BINARY_LOCATION = os.environ.get('CHROME_BINARY_LOCATION')
CHROMEDRIVER_LOCATION = os.environ.get('CHROMEDRIVER_LOCATION')
