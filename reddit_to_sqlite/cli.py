import click
import sqlite_utils
import tqdm

from reddit_to_sqlite.data import load_reddit_data
from reddit_to_sqlite.helpers import load_db


@click.group()
@click.version_option()
def cli():
    "Save data from Reddit to a SQLite database"


@cli.command()
@click.argument("username")
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    default="reddit.db",
)
def user(db_path, username):
    click.echo(f"loading data about /u/{username} into {db_path}")

    # db = load_db(db_path)
