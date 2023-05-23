from functools import partial
from pathlib import Path
from typing import Callable, Iterable, TypeVar, cast

import click
from sqlite_utils import Database

from reddit_user_to_sqlite.csv_helpers import (
    get_username_from_archive,
    load_ids_from_file,
)
from reddit_user_to_sqlite.helpers import clean_username, find_user_details_from_items
from reddit_user_to_sqlite.reddit_api import (
    Comment,
    Post,
    get_user_id,
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
) -> int:
    if not items:
        return 0

    insert_user(db, items[0])
    insert_subreddits(db, items)
    return upsert_func(db, items)


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
    click.echo(f"loading data about /u/{username} into {db_path}")

    db = Database(db_path)

    click.echo("\nfetching (up to 10 pages of) comments")
    comments = load_comments_for_user(username)
    save_comments(db, comments)
    click.echo(f"saved/updated {len(comments)} comments")

    click.echo("\nfetching (up to 10 pages of) posts")
    posts = load_posts_for_user(username)
    save_posts(db, posts)
    click.echo(f"saved/updated {len(posts)} posts")

    if not (comments or posts):
        raise click.ClickException(f"no data found for username: {username}")

    ensure_fts(db)


def add_missing_user_fragment(
    items: list[T], username: str, user_fullname: str
) -> list[T]:
    """
    If an item lacks user details, this adds them. Otherwise the item passes through untouched.
    """
    return [
        cast(T, {**i, "author": username, "author_fullname": user_fullname})
        if "author_fullname" not in i
        else i
        for i in items
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
    click.echo(f"loading data found in archive at {archive_path} into {db_path}")

    db = Database(db_path)

    comment_ids = load_ids_from_file(db, archive_path, "comments")
    click.echo("\nFetching info about comments")
    comments = cast(list[Comment], load_info(comment_ids))

    post_ids = load_ids_from_file(db, archive_path, "posts")
    click.echo("\nFetching info about posts")
    posts = cast(list[Post], load_info(post_ids))

    if user_details := (
        find_user_details_from_items(comments) or find_user_details_from_items(posts)
    ):
        username, user_fullname = user_details

        comments = add_missing_user_fragment(comments, username, user_fullname)
        posts = add_missing_user_fragment(posts, username, user_fullname)
    elif username := get_username_from_archive(archive_path):
        user_fullname = f"t2_{get_user_id(username)}"

        comments = add_missing_user_fragment(comments, username, user_fullname)
        posts = add_missing_user_fragment(posts, username, user_fullname)
    else:
        click.echo(
            "\nUnable to guess username from API content or archive; some posts will not be saved.",
            err=True,
        )

    num_comments_written = save_comments(db, comments)
    num_posts_written = save_posts(db, posts)
    ensure_fts(db)

    messages = [
        "\nDone!",
        f" - saved {num_comments_written} new comments",
        f" - saved {num_posts_written} new posts",
    ]

    if missing_comments := len(comment_ids) - num_comments_written:
        messages.append(
            f" - failed to find {missing_comments} missing comments; ignored for now"
        )
    if missing_posts := len(post_ids) - num_posts_written:
        messages.append(
            f" - failed to find {missing_posts} missing posts; ignored for now"
        )

    click.echo("\n".join(messages))
