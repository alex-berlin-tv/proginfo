from .config import settings

import logging


logging.basicConfig(
    level=str(settings.log_level).upper(), 
    format="%(asctime)s;%(levelname)s:%(message)s",
)

logger = logging.getLogger()