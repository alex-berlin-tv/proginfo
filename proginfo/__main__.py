from .config import settings
from .data import Formatter

from omniapy import Omnia, StreamType


def app():
    formatter = Formatter()
    omnia = Omnia(settings.domain_id, settings.api_secret, settings.session_id)
    omnia.update(
        StreamType.RADIO,
        settings.radio_id,
        {
            "title": formatter.radio_title(),
            "description": formatter.radio_description(),
        }
    )
    omnia.update(
        StreamType.LIVE,
        settings.tv_id,
        {
            "description": formatter.tv_description(),
        }
    )
