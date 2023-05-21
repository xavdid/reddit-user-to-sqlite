from csv import DictReader
from pathlib import Path
from typing import Literal

from sqlite_utils import Database

ItemType = Literal["comments", "posts"]
PREFIX: dict[ItemType, str] = {"comments": "t1", "posts": "t3"}


def validate_and_build_path(archive_path: Path, item_type: str) -> Path:
    filename = f"{item_type}.csv"
    if not (file := archive_path / filename).exists():
        raise ValueError(
            f'Ensure path "{archive_path}" points to an unzipped Reddit GDPR archive folder; {filename} not found in the expected spot.'
        )
    return file


def load_ids_from_file(
    db: Database, archive_path: Path, item_type: ItemType
) -> list[str]:
    saved_ids = {row["id"] for row in db[item_type].rows}

    with open(validate_and_build_path(archive_path, item_type)) as comment_archive_rows:
        return [
            f'{PREFIX[item_type]}_{c["id"]}'
            for c in DictReader(comment_archive_rows)
            if c["id"] not in saved_ids
        ]


def get_username_from_archive(archive_path: Path) -> str | None:
    with open(validate_and_build_path(archive_path, "statistics")) as stat_rows:
        try:
            return next(
                row["value"]
                for row in DictReader(stat_rows)
                if row["statistic"] == "account name"
            )
        except StopIteration:
            pass
