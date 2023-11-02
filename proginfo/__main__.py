from .config import settings
from .data import Data

def app():
    dt = Data.from_url(settings.radio_data_url)
    print(dt.current_and_next(4))