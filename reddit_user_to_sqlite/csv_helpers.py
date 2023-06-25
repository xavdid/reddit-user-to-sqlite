from csv import DictReader
from pathlib import Path
from typing import Literal, Optional

from sqlite_utils import Database

ItemType = Literal["comments", "posts"]
PrefixType = Literal["saved_"]

FULLNAME_PREFIX: dict[ItemType, str] = {
    "comments": "t1",
    "posts": "t3",
}


def build_table_name(
    table_name: ItemType, table_prefix: Optional[PrefixType] = None
) -> str:
    return f"{table_prefix or ''}{table_name}"


def validate_and_build_path(archive_path: Path, item_type: str) -> Path:
    filename = f"{item_type}.csv"
    if not (file := archive_path / filename).exists():
        raise ValueError(
            f'Ensure path "{archive_path}" points to an unzipped Reddit GDPR archive folder; "{filename}" not found in the expected spot.'
        )
    return file


def load_unsaved_ids_from_file(
    db: Database,
    archive_path: Path,
    item_type: ItemType,
    prefix: Optional[PrefixType] = None,
) -> list[str]:
    filename = build_table_name(item_type, prefix)
    # we save each file into a matching table
    saved_ids = {row["id"] for row in db[filename].rows}

    with open(
        validate_and_build_path(archive_path, filename), encoding="utf-8"
    ) as archive_rows:
        return [
            f'{FULLNAME_PREFIX[item_type]}_{c["id"]}'
            for c in DictReader(archive_rows)
            if c["id"] not in saved_ids
        ]


def get_username_from_archive(archive_path: Path) -> Optional[str]:
    with open(validate_and_build_path(archive_path, "statistics")) as stat_rows:
        try:
            return next(
                row["value"]
                for row in DictReader(stat_rows)
                if row["statistic"] == "account name"
            )
        except StopIteration:
            pass
