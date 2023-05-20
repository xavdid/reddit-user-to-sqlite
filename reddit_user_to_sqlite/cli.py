from csv import DictReader
from functools import partial
from itertools import chain
from pathlib import Path
from pprint import pprint
from typing import Callable, Iterable, Literal, TypeVar, cast

import click
from sqlite_utils import Database
from tqdm import tqdm

from reddit_user_to_sqlite.helpers import batched, clean_username
from reddit_user_to_sqlite.reddit_api import (
    Comment,
    Post,
    load_comments_for_user,
    load_info,
    load_posts_for_user,
)
from reddit_user_to_sqlite.sqlite_helpers import (
    ensure_fts,
    insert_subreddits,
    insert_user,
    upsert_comments,
    upsert_posts,
)


@click.group()
@click.version_option()
def cli():
    "Save data from Reddit to a SQLite database"


DB_PATH_HELP = "A path to a SQLite database file. If it doesn't exist, it will be created. It can have any extension, but I'd recommend `.db` or `.sqlite`."
DEFAULT_DB_NAME = "reddit.db"

T = TypeVar("T", Comment, Post)


def _save_items(
    db: Database, items: list[T], upsert_func: Callable[[Database, Iterable[T]], int]
):
    if items:
        # TODO: handle no items have a user_fullname
        # insert_user(db, next(c for c in comments if "author_fullname" in c))
        insert_user(db, items[0])
        insert_subreddits(db, items)
        upsert_func(db, items)


save_comments = partial(_save_items, upsert_func=upsert_comments)
save_posts = partial(_save_items, upsert_func=upsert_posts)


@cli.command()
@click.argument("username")
@click.option(
    "--db",
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    default=DEFAULT_DB_NAME,
    help=DB_PATH_HELP,
)
def user(db_path: str, username: str):
    username = clean_username(username)
    click.echo(f"loading data about /u/{username} into {db_path}\n")

    db = Database(db_path)

    click.echo("fetching (up to 10 pages of) comments")
    comments = load_comments_for_user(username)
    save_comments(db, comments)

    click.echo("\nfetching (up to 10 pages of) posts")
    posts = load_posts_for_user(username)
    save_posts(db, posts)

    if not (comments or posts):
        raise click.ClickException(f"no data found for username: {username}")

    ensure_fts(db)


ItemType = Literal["comments", "posts"]


def load_ids_from_file(
    db: Database, archive_path: Path, item_type: ItemType
) -> list[str]:
    filename = f"{item_type}.csv"
    if not (file := archive_path / filename).exists():
        raise ValueError(
            f'Ensure path "{archive_path}" points to an unzipped Reddit GDPR archive folder; {filename} not found in the expected spot.'
        )

    saved_ids = {row["id"] for row in db[item_type].rows}

    with open(file) as comment_archive_rows:
        return [
            f't1_{c["id"]}'
            for c in DictReader(comment_archive_rows)
            if c["id"] not in saved_ids
        ]


@cli.command()
@click.argument(
    "archive_path",
    type=click.Path(file_okay=False, dir_okay=True, allow_dash=False, path_type=Path),
)
@click.option(
    "--db",
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    default=DEFAULT_DB_NAME,
    help=DB_PATH_HELP,
)
def archive(archive_path: Path, db_path: str):
    # TODO: add text
    db = Database(db_path)

    comment_ids = load_ids_from_file(db, archive_path, "comments")
    comments = cast(list[Comment], load_info(comment_ids))
    num_written = save_comments(db, comments)

    post_ids = load_ids_from_file(db, archive_path, "posts")
    posts = cast(list[Post], load_info(post_ids))
    num_written = save_posts(db, posts)
