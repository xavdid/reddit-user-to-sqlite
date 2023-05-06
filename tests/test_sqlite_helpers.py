from typing import Optional

import pytest
from sqlite_utils import Database
from sqlite_utils.db import ForeignKey, NotFoundError

from reddit_user_to_sqlite.reddit_api import SubredditFragment, UserFragment
from reddit_user_to_sqlite.sqlite_helpers import (
    CommentRow,
    insert_subreddits,
    insert_user,
    upsert_comments,
)


@pytest.fixture
def make_sr():
    def make_subreddit(name: str, id_=None, type_="public") -> SubredditFragment:
        # returns the relevant sub-portions of
        return {
            "subreddit": name,
            "subreddit_id": f"t5_{id_ or name}",
            "subreddit_type": type_,
        }

    return make_subreddit


@pytest.fixture
def make_user():
    def _make_user(name: str, id_: Optional[str] = None) -> UserFragment:
        return {"author_fullname": f"t2_{id_ or name[::-1]}", "author": name}

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


def test_upsert_comments(tmp_db: Database, comment, stored_comment: CommentRow):
    insert_subreddits(tmp_db, [comment])
    insert_user(tmp_db, comment)

    upsert_comments(tmp_db, [comment])

    assert {"subreddits", "users", "comments"}.issubset(tmp_db.table_names())

    assert list(tmp_db["comments"].rows) == [stored_comment]

    assert tmp_db["comments"].foreign_keys == [  # type: ignore
        ForeignKey("comments", "subreddit", "subreddits", "id"),
        ForeignKey("comments", "user", "users", "id"),
    ]

    failure_reasons = []
    for k in ["user", "subreddit"]:
        try:
            tmp_db[f"{k}s"].get(stored_comment[k])
        except NotFoundError:
            failure_reasons.append(f"broken foreign key relationship for comment.{k}")

    if failure_reasons:
        pytest.fail(", ".join(failure_reasons))
