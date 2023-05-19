from csv import DictReader
from itertools import chain
from pathlib import Path
from pprint import pprint
from typing import cast

import click
from sqlite_utils import Database
from tqdm import tqdm

from reddit_user_to_sqlite.helpers import batched, clean_username
from reddit_user_to_sqlite.reddit_api import (
    Comment,
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

    click.echo("fetching (up to 10 pages of) comments")
    comments = load_comments_for_user(username)

    db = Database(db_path)
    if comments:
        insert_user(db, comments[0])
        insert_subreddits(db, comments)
        upsert_comments(db, comments)

    click.echo("\nfetching (up to 10 pages of) posts")

    posts = load_posts_for_user(username)
    if posts:
        insert_user(db, posts[0])
        insert_subreddits(db, posts)
        upsert_posts(db, posts)

    if not (comments or posts):
        raise click.ClickException(f"no data found for username: {username}")

    ensure_fts(db)


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
    if not (comments_file := archive_path / "comments.csv").exists():
        raise ValueError(
            f'Ensure path "{archive_path}" points to an unzipped Reddit GDPR archive; comments.csv not found in the expected post.'
        )

    db = Database(db_path)
    existing_ids = {row["id"] for row in db["comments"].rows}

    with open(comments_file) as comment_archive_rows:
        comments_to_fetch = [
            f't1_{c["id"]}'
            for c in DictReader(comment_archive_rows)
            if c["id"] not in existing_ids
        ]

    # comments_to_fetch = comments_to_fetch[:50]

    comments = cast(
        list[Comment],
        list(
            chain.from_iterable(
                load_info(batch) for batch in batched(tqdm(comments_to_fetch), 100)
            )
        ),
    )

    if comments:
        # TODO: handle all rows having bad data
        insert_user(db, next(c for c in comments if "author_fullname" in c))
        insert_subreddits(db, comments)
        upsert_comments(db, comments)
