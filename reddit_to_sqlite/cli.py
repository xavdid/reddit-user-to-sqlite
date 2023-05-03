import click
import tqdm

from reddit_to_sqlite.data import load_reddit_data
from reddit_to_sqlite.helpers import ensure_fts, load_db


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

    db = load_db(db_path)
    comments = load_reddit_data(username)

    # upsert author

    if not comments:
        # TODO: error? print message?
        return

    # create author record
    db["users"].upsert(
        {
            "id": comments[0]["author_fullname"],
            "username": comments[0]["author"],
        },
        pk="id",
    )

    for comment in comments:
        # add subreddit
        db["subreddits"].upsert(
            {
                "id": comment["subreddit_id"],
                "name": comment["subreddit"],
                "type": comment["subreddit_type"],
            },
            pk="id",
        )

        db["comments"].upsert(
            {
                "id": comment["id"],
                "timestamp": int(comment["created"]),
                "score": comment["score"],
                "text": comment["body_html"],
                "user": comment["author_fullname"],
                "subreddit": comment["subreddit_id"],
                "permalink": f'https://www.reddit.com{comment["permalink"]}?context=10',
                "is_submitter": int(comment["is_submitter"]),
                "controversiality": comment["controversiality"],
            },
            pk="id",
        )

    ensure_fts(db)
