import sqlite_utils


def load_db(db_path: str):
    db = sqlite_utils.Database(db_path)
    ensure_tables(db)
    return db


def clean_username(username: str) -> str:
    """
    strips the leading `/u/` off the front of a username, if present
    """
    pass


def ensure_tables(db):
    """
    create sqlite db tables
    """
    pass
