from .config import settings
from .data import Formatter
from .log import logger

import argparse

from omniapy import Omnia, StreamType


def app():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tv", action="store_true", help="update tv")
    parser.add_argument("--radio", action="store_true", help="update radio")
    args = parser.parse_args()

    if not args.tv and not args.radio:
        logger.error("whether tv nor radio update requested by flags")

    formatter = Formatter()
    omnia = Omnia(settings.domain_id, settings.api_secret, settings.session_id)

    if args.tv:
        logger.info("update TV")
        omnia.update(
            StreamType.LIVE,
            settings.tv_id,
            {
                "description": formatter.tv_description(),
            }
        )
    if args.radio:
        logger.info("update radio")
        omnia.update(
            StreamType.RADIO,
            settings.radio_id,
            {
                "title": formatter.radio_title(),
                "description": formatter.radio_description(),
            }
        )
