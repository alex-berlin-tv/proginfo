from .config import settings

import csv
from datetime import datetime, timedelta
from io import StringIO
from typing import Optional

from attrs import define
import requests


DATE_FORMAT = "%d.%m.%Y"
TIME_FORMAT = "%H:%M:%S"


@define
class Data:
    root: list["Entry"]

    @classmethod
    def from_url(cls, url: str):
        raw = cls.download_text(url)
        reader = csv.reader(StringIO(raw), delimiter="|")
        rsl: list["Entry"] = []
        for row in reader:
            rsl.append(Entry.from_row(row))
        rsl = sorted(rsl, key=lambda entry: entry.when)
        return cls(rsl)

    @staticmethod
    def download_text(url: str) -> str:
        response = requests.get(url)
        response.raise_for_status()
        return response.content.decode(settings.data_encoding)

    def current_and_next(self, follower_count: int) -> list["Entry"]:
        current_time = datetime.now()
        rsl: list["Entry"] = []
        i = 0
        for entry in self.root:
            if entry.is_current(current_time):
                rsl = [entry]
                break
            i += 1
        if len(rsl) == 0:
            raise ValueError("no entry for current time found")
        for j in range(i+1, i+follower_count):
            if len(self.root) - 1 >= j:
                rsl.append(self.root[j])
        return rsl


@define
class Entry:
    when: datetime
    duration: timedelta
    title: str
    description: str
    url: Optional[str]

    @classmethod
    def from_row(cls, row: list[str]):
        if len(row) != 8:
            raise ValueError(
                f"input data row should have 8 fields got {len(row)} instead, data: {row}")
        date = datetime.strptime(row[2], DATE_FORMAT)
        time = datetime.strptime(row[3], TIME_FORMAT)
        date = date.replace(
            hour=time.hour, minute=time.minute, second=time.second)

        return Entry(
            when=date,
            duration=timedelta(minutes=int(row[4])),
            title=row[5],
            description=row[6],
            url=row[1],
        )

    def is_current(self, moment: datetime) -> bool:
        return moment > self.when and moment < (self.when + self.duration)
