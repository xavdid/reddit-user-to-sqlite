from typing import cast

from sqlite_utils import Database
from sqlite_utils.db import Table


def load_db(db_path: str):
    db = Database(db_path)
    ensure_tables(db)
    return db


def clean_username(username: str) -> str:
    """
    strips the leading `/u/` off the front of a username, if present
    """
    pass


def _get_table(db: Database, name: str) -> Table:
    return cast(Table, db[name])


def ensure_tables(db: Database):
    """
    create sqlite db tables
    """
    if "subreddits" not in db.table_names():
        _get_table(db, "subreddits").create(
            {
                "id": str,
                "name": str,
                "type": str,
            },
            pk="id",
        ).create_index(["id"], unique=True, if_not_exists=True)

    if "users" not in db.table_names():
        _get_table(db, "users").create(
            {
                "id": str,
                "username": str,
            },
            pk="id",
        ).create_index(["id"], unique=True, if_not_exists=True)

    if "comments" not in db.table_names():
        _get_table(db, "comments").create(
            {
                "id": str,
                "timestamp": int,
                "score": int,
                "text": str,
                "user": str,
                "is_submitter": int,
                "subreddit": str,
                "permalink": str,
                "controversiality": int,
            },
            pk="id",
            foreign_keys=[
                (
                    "subreddit",
                    "subreddits",
                    "id",
                ),
                (
                    "user",
                    "users",
                    "id",
                ),
            ],
        ).create_index(["id"], unique=True, if_not_exists=True)

    # if "posts" not in db.table_names():
    #     _get_table(db, "posts").create()


def ensure_fts(db: Database):
    table_names = set(db.table_names())
    if "comments" in table_names and "comments_fts" not in table_names:
        db["comments"].enable_fts(["text"], create_triggers=True)
    if "posts" in table_names and "posts_fts" not in table_names:
        db["posts"].enable_fts(["title", "text"], create_triggers=True)
