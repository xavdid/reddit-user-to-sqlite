import click
from sqlite_utils import Database

from reddit_user_to_sqlite.helpers import clean_username
from reddit_user_to_sqlite.reddit_api import load_comments_for_user, load_posts_for_user
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


@cli.command()
@click.argument("username")
@click.option(
    "--db",
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    default="reddit.db",
)
def user(db_path, username):
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
