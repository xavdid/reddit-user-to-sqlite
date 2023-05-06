from typing import Optional

import pytest
from sqlite_utils import Database
from sqlite_utils.db import ForeignKey

from reddit_to_sqlite.sqlite_helpers import (
    CommentRow,
    SubredditRow,
    UserRow,
    insert_subreddits,
    insert_user,
    upsert_comments,
)


@pytest.fixture
def make_sr():
    def make_subreddit(name: str, id_=None, type_="public"):
        return SubredditRow(id=id_ or name, name=name, type=type_)

    return make_subreddit


@pytest.fixture
def make_user():
    def _make_user(name: str, id_: Optional[str] = None):
        return UserRow(id=id_ or name[::-1], username=name)

    return _make_user


def test_insert_subreddits(tmp_db: Database, make_sr):
    insert_subreddits(
        tmp_db,
        [
            make_sr("Games"),
            make_sr("JRPG", type_="private"),
        ],
    )

    assert "subreddits" in tmp_db.table_names()
    assert list(tmp_db["subreddits"].rows) == [
        {"id": "Games", "name": "Games", "type": "public"},
        {"id": "JRPG", "name": "JRPG", "type": "private"},
    ]


def test_repeat_subs_ignored(tmp_db: Database, make_sr):
    insert_subreddits(
        tmp_db,
        [
            make_sr("Games"),
            make_sr("JRPG", type_="private"),
        ],
    )

    # updates are ignored
    insert_subreddits(
        tmp_db,
        [
            make_sr("ames", id_="Games"),
            make_sr("RPG", id_="JRPG"),
            make_sr("Apple"),
        ],
    )

    assert "subreddits" in tmp_db.table_names()
    assert list(tmp_db["subreddits"].rows) == [
        {"id": "Games", "name": "Games", "type": "public"},
        {"id": "JRPG", "name": "JRPG", "type": "private"},
        {"id": "Apple", "name": "Apple", "type": "public"},
    ]


def test_insert_users(tmp_db: Database, make_user):
    insert_user(tmp_db, make_user("xavdid"))

    assert "users" in tmp_db.table_names()
    assert list(tmp_db["users"].rows) == [
        {"id": "didvax", "username": "xavdid"},
    ]


def test_upsert_comments(tmp_db: Database, make_sr, make_user):
    sr: SubredditRow = make_sr("Games")
    insert_subreddits(tmp_db, [sr])

    user: UserRow = make_user("xavdid")
    insert_user(tmp_db, user)

    comment = {
        "id": "abc",
        "timestamp": 12345,
        "score": 5,
        "text": "cool",
        "user": user.id,
        "is_submitter": 0,
        "subreddit": sr.id,
        "permalink": "https://reddit.com/r/whatever/asdf",
        "controversiality": 0,
    }

    upsert_comments(tmp_db, [CommentRow(**comment)])

    assert "subreddits" in tmp_db.table_names()
    assert "users" in tmp_db.table_names()
    assert "comments" in tmp_db.table_names()

    assert list(tmp_db["comments"].rows) == [comment]

    assert tmp_db["comments"].foreign_keys == [
        ForeignKey("comments", "subreddit", "subreddits", "id"),
        ForeignKey("comments", "user", "users", "id"),
    ]
