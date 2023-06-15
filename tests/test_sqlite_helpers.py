from typing import Callable, Optional

import pytest
from pytest import FixtureRequest
from sqlite_utils import Database
from sqlite_utils.db import ForeignKey, NotFoundError

from reddit_user_to_sqlite.reddit_api import (
    Comment,
    Post,
    SubredditFragment,
    UserFragment,
)
from reddit_user_to_sqlite.sqlite_helpers import (
    CommentRow,
    comment_to_comment_row,
    insert_subreddits,
    insert_users,
    item_to_subreddit_row,
    item_to_user_row,
    post_to_post_row,
    upsert_comments,
    upsert_posts,
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


MakeUserFunc = Callable[[str], UserFragment]


@pytest.fixture
def make_user() -> MakeUserFunc:
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


@pytest.mark.skip(
    "skipped because of a sqlite-utils bug; subreddits to get upserted right now"
)
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


def test_insert_user(tmp_db: Database, make_user: MakeUserFunc):
    insert_users(tmp_db, [make_user("xavdid")])

    assert "users" in tmp_db.table_names()
    assert list(tmp_db["users"].rows) == [
        {"id": "didvax", "username": "xavdid"},
    ]


def test_insert_user_missing(tmp_db: Database, make_user: MakeUserFunc):
    user = make_user("xavdid")
    user.pop("author_fullname")
    insert_users(tmp_db, [user])

    assert "users" not in tmp_db.table_names()


def test_insert_comments(
    tmp_db: Database, comment: Comment, stored_comment: CommentRow
):
    insert_subreddits(tmp_db, [comment])
    insert_users(tmp_db, [comment])

    comment_without_user = comment.copy()
    comment.pop("author_fullname")

    upsert_comments(tmp_db, [comment, comment_without_user])

    assert {"subreddits", "users", "comments"}.issubset(tmp_db.table_names())

    assert list(tmp_db["comments"].rows) == [stored_comment]

    assert tmp_db["comments"].foreign_keys == [  # type: ignore
        ForeignKey("comments", "subreddit", "subreddits", "id"),
        ForeignKey("comments", "user", "users", "id"),
    ]

    failure_reasons = []
    for k in ["user", "subreddit"]:
        try:
            tmp_db[f"{k}s"].get(stored_comment[k])  # type: ignore
        except NotFoundError:
            failure_reasons.append(f"broken foreign key relationship for comment.{k}")

    if failure_reasons:
        pytest.fail(", ".join(failure_reasons))


def test_update_comments(tmp_db: Database, comment: Comment, stored_comment):
    insert_subreddits(tmp_db, [comment])
    insert_users(tmp_db, [comment])
    upsert_comments(tmp_db, [comment])

    assert list(tmp_db["comments"].rows) == [stored_comment]

    assert comment["score"] != 10
    comment["score"] = 10
    upsert_comments(tmp_db, [comment])

    updated_comment = tmp_db["comments"].get(comment["id"])  # type: ignore
    assert updated_comment["score"] == 10


# https://engineeringfordatascience.com/posts/pytest_fixtures_with_parameterize/
@pytest.mark.parametrize(
    ["post_type", "stored_post_type"],
    [
        ("self_post", "stored_self_post"),
        # ("removed_post", "stored_removed_post"),
        ("external_post", "stored_external_post"),
    ],
)
def test_insert_posts(
    tmp_db: Database, request: FixtureRequest, post_type: str, stored_post_type: str
):
    post: Post = request.getfixturevalue(post_type)
    stored_post = request.getfixturevalue(stored_post_type)

    no_user_post = post.copy()
    no_user_post.pop("author_fullname")

    insert_subreddits(tmp_db, [post])
    insert_users(tmp_db, [post])

    upsert_posts(tmp_db, [post, no_user_post])

    assert {"subreddits", "users", "posts"}.issubset(tmp_db.table_names())

    assert list(tmp_db["posts"].rows) == [stored_post]

    assert tmp_db["posts"].foreign_keys == [  # type: ignore
        ForeignKey("posts", "subreddit", "subreddits", "id"),
        ForeignKey("posts", "user", "users", "id"),
    ]

    failure_reasons = []
    for k in ["user", "subreddit"]:
        try:
            tmp_db[f"{k}s"].get(stored_post[k])  # type: ignore
        except NotFoundError:
            failure_reasons.append(f"broken foreign key relationship for comment.{k}")

    if failure_reasons:
        pytest.fail(", ".join(failure_reasons))


@pytest.mark.parametrize(
    ["item", "expected"],
    [
        (
            {"author_fullname": "t1_abc123", "author": "xavdid"},
            {"id": "abc123", "username": "xavdid"},
        ),
        ({"author": "xavdid"}, None),
    ],
)
def test_item_to_user_row(item, expected):
    assert item_to_user_row(item) == expected


@pytest.mark.parametrize(
    ["item", "expected"],
    [
        (
            {
                "subreddit_id": "t3_abc123",
                "subreddit": "Games",
                "subreddit_type": "public",
            },
            {"id": "abc123", "name": "Games", "type": "public"},
        ),
        # ({}, None),
    ],
)
def test_item_to_subreddit_row(item, expected):
    assert item_to_subreddit_row(item) == expected


def test_comment_to_comment_row(comment, stored_comment):
    assert comment_to_comment_row(comment) == stored_comment


def test_comment_to_comment_row_missing_user(comment):
    comment.pop("author_fullname")
    assert comment_to_comment_row(comment) == None


def test_post_to_post_row(self_post, stored_self_post):
    assert post_to_post_row(self_post) == stored_self_post


def test_post_to_post_row_missing_user(self_post):
    self_post.pop("author_fullname")
    assert post_to_post_row(self_post) == None
