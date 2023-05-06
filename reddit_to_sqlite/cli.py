import click
from sqlite_utils import Database

from reddit_to_sqlite.helpers import clean_username
from reddit_to_sqlite.reddit_api import load_comments_for_user
from reddit_to_sqlite.sqlite_helpers import (
    CommentRow,
    SubredditRow,
    UserRow,
    ensure_fts,
    insert_subreddits,
    insert_user,
    upsert_comments,
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
    click.echo(f"loading data about /u/{username} into {db_path}")

    comments = load_comments_for_user(username)
    db = Database(db_path)

    if not comments:
        # TODO: error? print message?
        return

    insert_user(
        db,
        UserRow(
            id=comments[0]["author_fullname"],
            username=comments[0]["author"],
        ),
    )

    insert_subreddits(
        db,
        [
            SubredditRow(
                id=comment["subreddit_id"],
                name=comment["subreddit"],
                type=comment["subreddit_type"],
            )
            for comment in comments
        ],
    )

    upsert_comments(
        db,
        [
            CommentRow(
                id=comment["id"],
                timestamp=int(comment["created"]),
                score=comment["score"],
                text=comment["body_html"],
                user=comment["author_fullname"],
                subreddit=comment["subreddit_id"],
                permalink=f'https://www.reddit.com{comment["permalink"]}?context=10',
                is_submitter=int(comment["is_submitter"]),
                controversiality=comment["controversiality"],
            )
            for comment in comments
        ],
    )

    ensure_fts(db)
