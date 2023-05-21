from pprint import pprint
from typing import Any, Callable, Iterable, Sequence, TypeVar, TypedDict, cast

from sqlite_utils import Database

from reddit_user_to_sqlite.reddit_api import (
    Comment,
    Post,
    SubredditFragment,
    UserFragment,
)


class SubredditRow(TypedDict):
    id: str
    name: str
    type: str
    # TODO: handle archiving and updating
    # archives_posts: bool


def comment_to_subreddit_row(comment: SubredditFragment) -> SubredditRow:
    return {
        "id": comment["subreddit_id"][3:],
        "name": comment["subreddit"],
        "type": comment["subreddit_type"],
    }


def insert_subreddits(db: Database, subreddits: Iterable[SubredditFragment]):
    db["subreddits"].insert_all(  # type: ignore
        map(comment_to_subreddit_row, subreddits),
        ignore=True,  # type: ignore
        # only relevant if creating the table
        pk="id",  # type: ignore
        not_null=["id", "name"],  # type: ignore
    )


class UserRow(TypedDict):
    id: str
    username: str


def comment_to_user_row(user: UserFragment) -> dict[str, str] | None:
    if "author_fullname" in user:
        return {"id": user["author_fullname"][3:], "username": user["author"]}


def insert_user(db: Database, user: UserFragment):
    if user_row := comment_to_user_row(user):
        db["users"].insert(  # type: ignore
            user_row,
            # ignore any write error
            ignore=True,
            # only relevant if creating the table
            pk="id",  # type: ignore
            not_null=["id", "username"],
        )


class CommentRow(TypedDict):
    id: str
    timestamp: int
    score: int
    text: str
    user: str
    is_submitter: int
    subreddit: str
    permalink: str
    controversiality: int


def comment_to_comment_row(comment: Comment) -> CommentRow | None:
    if "author_fullname" not in comment:
        return

    return {
        "id": comment["id"],
        "timestamp": int(comment["created"]),
        "score": comment["score"],
        "text": comment["body"],
        "user": comment["author_fullname"][3:],  # strip leading t2_
        "subreddit": comment["subreddit_id"][3:],  # strip leading t5_
        "permalink": f'https://old.reddit.com{comment["permalink"]}?context=10',
        "is_submitter": int(comment["is_submitter"]),
        "controversiality": comment["controversiality"],
    }


T = TypeVar("T")
U = TypeVar("U")


def apply_and_filter(filterer: Callable[[T], U | None], items: Iterable[T]) -> list[U]:
    return [c for c in map(filterer, items) if c]


def upsert_comments(db: Database, comments: Iterable[Comment]) -> int:
    comment_rows = apply_and_filter(comment_to_comment_row, comments)
    db["comments"].insert_all(  # type: ignore
        comment_rows,
        upsert=True,
        pk="id",  # type: ignore
        # update the schema - needed if user does archive first
        alter=True,  # type: ignore
        foreign_keys=[  # type: ignore
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
        # can re-add or assert this later, but the rows aren't created if this is present
        # see: https://github.com/simonw/sqlite-utils/issues/538
        # not_null=["id", "timestamp", "text", "user", "subreddit", "permalink"],
    )
    return len(comment_rows)


class PostRow(TypedDict):
    id: str
    timestamp: int
    score: int
    title: str
    text: str
    external_url: str
    user: str
    subreddit: str
    permalink: str
    upvote_ratio: float
    score: int
    num_comments: int
    num_awards: int
    is_removed: int


def post_to_post_row(post: Post) -> PostRow | None:
    if "author_fullname" not in post:
        return

    return {
        "id": post["id"],
        "timestamp": int(post["created"]),
        "score": post["score"],
        "num_comments": post["num_comments"],
        "title": post["title"],
        "text": post["selftext"],
        "external_url": "" if "reddit.com" in post["url"] else post["url"],
        "user": post["author_fullname"][3:],
        "subreddit": post["subreddit_id"][3:],
        "permalink": f'https://old.reddit.com{post["permalink"]}',
        "upvote_ratio": post["upvote_ratio"],
        "score": post["score"],
        "num_awards": post["total_awards_received"],
        "is_removed": int(post["selftext"] == "[removed]"),
    }


def upsert_posts(db: Database, posts: Iterable[Post]) -> int:
    post_rows = apply_and_filter(post_to_post_row, posts)
    db["posts"].insert_all(  # type: ignore
        post_rows,
        upsert=True,
        pk="id",  # type: ignore
        alter=True,  # type: ignore
        foreign_keys=[  # type: ignore
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
    )
    return len(post_rows)


def ensure_fts(db: Database):
    table_names = set(db.table_names())
    if "comments" in table_names and "comments_fts" not in table_names:
        db["comments"].enable_fts(["text"], create_triggers=True)
    if "posts" in table_names and "posts_fts" not in table_names:
        db["posts"].enable_fts(["title", "text"], create_triggers=True)
