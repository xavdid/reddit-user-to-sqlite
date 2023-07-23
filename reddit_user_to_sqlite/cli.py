from functools import partial
from pathlib import Path
from typing import Callable, Iterable, Optional, TypeVar, cast

import click
from sqlite_utils import Database

from reddit_user_to_sqlite.csv_helpers import (
    PrefixType,
    get_username_from_archive,
    load_unsaved_ids_from_file,
)
from reddit_user_to_sqlite.helpers import clean_username, find_user_details_from_items
from reddit_user_to_sqlite.reddit_api import (
    Comment,
    Post,
    add_missing_user_fragment,
    get_user_id,
    load_comments_for_user,
    load_info,
    load_posts_for_user,
)
from reddit_user_to_sqlite.sqlite_helpers import (
    ensure_fts,
    insert_users,
    upsert_comments,
    upsert_posts,
    upsert_subreddits,
)


@click.group()
@click.version_option()
def cli():
    "Save data from Reddit to a SQLite database"


DB_PATH_HELP = "A path to a SQLite database file. If it doesn't exist, it will be created. It can have any extension, `.db` or `.sqlite` is recommended."
DEFAULT_DB_NAME = "reddit.db"

DELETED_USERNAME = "__DeletedUser__"
DELETED_USER_FULLNAME = "t2_1234567"

T = TypeVar("T", Comment, Post)


def _save_items(
    db: Database,
    items: list[T],
    upsert_func: Callable[[Database, Iterable[T], Optional[PrefixType]], int],
    table_prefix: Optional[PrefixType] = None,
) -> int:
    if not items:
        return 0

    insert_users(db, items)
    upsert_subreddits(db, items)
    return upsert_func(db, items, table_prefix)


save_comments = partial(_save_items, upsert_func=upsert_comments)
save_posts = partial(_save_items, upsert_func=upsert_posts)


def load_data_from_files(
    db: Database,
    archive_path: Path,
    own_data=True,
    tables_prefix: Optional[PrefixType] = None,
):
    """
    if own data is true, requires a username to save. Otherwise, will add a placeholder
    (for external data)
    """
    new_comment_ids = load_unsaved_ids_from_file(
        db, archive_path, "comments", prefix=tables_prefix
    )
    click.echo(f"\nFetching info about {'your' if own_data else 'saved'} comments")
    comments = cast(list[Comment], load_info(new_comment_ids))

    post_ids = load_unsaved_ids_from_file(
        db, archive_path, "posts", prefix=tables_prefix
    )
    click.echo(f"\nFetching info about {'your' if own_data else 'saved'} posts")
    posts = cast(list[Post], load_info(post_ids))

    username = None
    user_fullname = None

    if own_data:
        # find the username, first from any of the loaded comments/posts
        if user_details := (
            find_user_details_from_items(comments)
            or find_user_details_from_items(posts)
        ):
            username, user_fullname = user_details
        # if all loaded posts are removed (which could be the case on subsequent runs),
        # then try to load from archive
        elif username := get_username_from_archive(archive_path):
            user_fullname = f"t2_{get_user_id(username)}"
        # otherwise, your posts without a username won't be saved;
        # this only happens for malformed archives
        else:
            click.echo(
                "\nUnable to guess username from API content or archive; some data will not be saved.",
                err=True,
            )
    else:
        username = DELETED_USERNAME
        user_fullname = DELETED_USER_FULLNAME

    if username and user_fullname:
        comments = add_missing_user_fragment(comments, username, user_fullname)
        posts = add_missing_user_fragment(posts, username, user_fullname)

    num_comments_written = save_comments(db, comments, table_prefix=tables_prefix)
    num_posts_written = save_posts(db, posts, table_prefix=tables_prefix)

    messages = [
        "\nDone!",
        f" - saved {num_comments_written} new comments",
        f" - saved {num_posts_written} new posts",
    ]

    if missing_comments := len(comments) - num_comments_written:
        messages.append(
            f" - failed to find {missing_comments} missing comments; ignored for now"
        )
    if missing_posts := len(post_ids) - num_posts_written:
        messages.append(
            f" - failed to find {missing_posts} missing posts; ignored for now"
        )

    click.echo("\n".join(messages))


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
@click.option(
    "--skip-saved",
    is_flag=True,
    default=False,
    help="Skip hydrating data about your saved posts and comments.",
)
def archive(archive_path: Path, db_path: str, skip_saved: bool):
    click.echo(f"loading data found in archive at {archive_path} into {db_path}")

    db = Database(db_path)

    load_data_from_files(db, archive_path)

    # I don't love this double negative, but it is what it is
    if not skip_saved:
        load_data_from_files(db, archive_path, own_data=False, tables_prefix="saved_")

    ensure_fts(db)
