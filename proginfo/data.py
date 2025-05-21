from .config import settings
from .log import logger

import csv
from datetime import datetime, time, timedelta
from io import StringIO
from typing import Optional

from attrs import define
import requests

DATE_FORMAT = "%d.%m.%Y"
TIME_FORMAT = "%H:%M:%S"


class Formatter:
    def __init__(self):
        logger.debug("Initializing Formatter with TV and radio data")
        self.tv_data = Data.from_url(settings.tv_data_url)
        self.radio_data = Data.from_url(settings.radio_data_url)

    def tv_title(self) -> str:
        logger.debug("Getting TV title")
        return self.__tv_current().title()

    def tv_description(self) -> str:
        logger.debug("Getting TV description")
        return self.__tv_current().description(None, settings.tv_description_footer)

    def radio_title(self) -> str:
        logger.debug("Getting radio title")
        rsl = self.__radio_current().title()
        logger.debug(f"Radio title: {rsl}")
        return rsl

    def radio_description(self) -> str:
        logger.debug("Getting radio description")
        return self.__radio_current().description(
            settings.radio_description_header,
            settings.radio_description_footer,
        )

    def __tv_current(self) -> "Data":
        logger.debug("Getting current TV data")
        return Data(self.tv_data.current_and_next())

    def __radio_current(self) -> "Data":
        logger.debug("Getting current radio data")
        return Data(self.radio_data.current_and_next())


@define
class Data:
    root: list["Entry"]

    @classmethod
    def from_url(cls, url: str):
        logger.debug(f"Downloading data from URL: {url}")
        raw = cls.download_text(url)
        reader = csv.reader(StringIO(raw), delimiter="|")
        rsl: list["Entry"] = []
        for row in reader:
            rsl.append(Entry.from_row(row))
        rsl = sorted(rsl, key=lambda entry: entry.when)
        logger.debug(f"Loaded {len(rsl)} entries from data source")
        return cls(rsl)

    @staticmethod
    def download_text(url: str) -> str:
        logger.debug(f"Making HTTP request to: {url}")
        response = requests.get(url)
        response.raise_for_status()
        return response.content.decode(settings.data_encoding)

    def current_and_next(self) -> list["Entry"]:
        if settings.next_count < 2:
            raise ValueError(
                f"field next_count in config has to be at least 2, currently {settings.next_count}")
        current_time = datetime.now()
        logger.debug(f"Finding current and next entries for time: {current_time}")
        rsl: list["Entry"] = []
        i = 0
        for entry in self.root:
            if entry.is_current(current_time):
                logger.debug(f"Found current entry: {entry.title} at {entry.when}")
                rsl = [entry]
                break
            i += 1

        if len(rsl) == 0:
            logger.warn(
                "no entry for current time found, will use latest item relative to now")
            last_entry: Optional[Entry] = None
            for entry in self.root:
                if not entry.starts_in_past(current_time):
                    if last_entry is None:
                        raise ValueError(
                            "no entry for current time found and first element is in the future")
                    logger.debug(f"Using last entry before current time: {last_entry.title} at {last_entry.when}")
                    rsl = [last_entry]
                    break
                last_entry = entry

        # Log only once for all next entries
        next_entries = []
        for j in range(i+1, i+settings.next_count):
            if len(self.root) - 1 >= j:
                next_entries.append(self.root[j])
        if next_entries:
            logger.debug(f"Adding {len(next_entries)} next entries starting from: {next_entries[0].title} at {next_entries[0].when}")
            rsl.extend(next_entries)
        return rsl

    def title(self) -> str:
        if len(self.root) < 1:
            raise RuntimeError("tried to call method on empty collection")
        next_entry: Optional[Entry] = None
        if len(self.root) > 1:
            next_entry = self.root[1]
        return self.root[0].format_title(next_entry)

    def description(self, header: str | None, footer: str) -> str:
        if header is not None:
            header = f"{header}\n\n"
        else:
            header = ""
        descriptions = [entry.format_description() for entry in self.root]
        rsl = "\n\n".join(descriptions)
        return f"{header}{rsl}\n---\n{footer}"


@define
class Entry:
    when: datetime
    duration: timedelta
    title: str
    author: str
    description: str
    url: Optional[str]

    @classmethod
    def from_row(cls, row: list[str]):
        if len(row) != 8:
            raise ValueError(
                f"input data row should have 8 fields got {len(row)} instead, data: {row}"
            )
        date = datetime.strptime(row[2], DATE_FORMAT)
        time = datetime.strptime(row[3], TIME_FORMAT)
        date = date.replace(
            hour=time.hour, minute=time.minute, second=time.second)

        return Entry(
            when=date,
            duration=timedelta(minutes=int(row[4])),
            title=cls.clean_string(row[5]),
            author=cls.clean_string(row[6]),
            description=cls.clean_string(row[7]),
            url=cls.clean_string(row[1]),
        )

    def is_current(self, moment: datetime) -> bool:
        return moment > self.when and moment < (self.when + self.duration)

    def starts_in_past(self, moment: datetime) -> bool:
        delta = moment - self.when
        return delta.total_seconds() < 0

    def format_title(self, next_entry: Optional["Entry"]) -> str:
        rsl = f"{settings.radio_prefix}: {self.title}"
        if not self.__show_both_titles() or next_entry is None:
            return rsl
        return f"{rsl} und danach um {next_entry.format_time()} {next_entry.title}"

    def format_description(self) -> str:
        url = ""
        if self.format_url() is not None:
            url = f" Mehr infos unter {self.format_url()}"
        rsl = f"{self.format_time()}: {self.title}. {self.description}{url}"
        return rsl.strip()

    def format_time(self) -> str:
        return self.when.strftime('%H:%M')

    def __show_both_titles(self) -> bool:
        """
        Between certain times, the title field should show the title the current 
        and the next show. This is needed as caching of neon makes it not possible
        to predict when the content in the frontend gets updated.
        """
        current_time = datetime.now().time()
        start_time = time(current_time.hour, 40, 0)
        end_time = time(current_time.hour, 56, 0)
        should_show_both = start_time <= current_time <= end_time
        logger.debug(f"Checking if should show both titles at {current_time}: {should_show_both} (window: {start_time}-{end_time})")
        return should_show_both

    def format_url(self) -> Optional[str]:
        if self.url is None or self.url == "":
            return None
        if self.url.find("alex-berlin.de") >= 0:
            return None
        if self.url.startswith("http"):
            return self.url
        return f"https://{self.url}"

    @staticmethod
    def clean_string(data: str) -> str:
        data = data.strip()
        data = data.replace("\r\n", " ")
        return data.replace("\n", " ")
