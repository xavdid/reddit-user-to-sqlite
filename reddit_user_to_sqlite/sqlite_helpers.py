from typing import Callable, Iterable, Optional, Sequence, TypedDict, TypeVar

from sqlite_utils import Database

from reddit_user_to_sqlite.csv_helpers import PrefixType, build_table_name
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


def item_to_subreddit_row(item: SubredditFragment) -> SubredditRow:
    return {
        "id": item["subreddit_id"][3:],
        "name": item["subreddit"],
        "type": item["subreddit_type"],
    }


def upsert_subreddits(db: Database, subreddits: Iterable[SubredditFragment]):
    # upserts are actually important here, since subs are going private/public a lot
    # https://github.com/simonw/sqlite-utils/issues/554
    db["subreddits"].upsert_all(  # type: ignore
        map(item_to_subreddit_row, subreddits),
        # ignore=True,  # type: ignore
        # only relevant if creating the table
        pk="id",  # type: ignore
        not_null=["id", "name"],  # type: ignore
    )


class UserRow(TypedDict):
    id: str
    username: str


def item_to_user_row(item: UserFragment) -> Optional[UserRow]:
    if "author_fullname" in item:
        return {"id": item["author_fullname"][3:], "username": item["author"]}


def insert_users(db: Database, users: Sequence[UserFragment]):
    existing_users = {u["id"] for u in db["users"].rows}

    unique_new_users = {
        # needs to be hashable so it's deduped
        (u["id"], u["username"])
        for user in users
        if (u := item_to_user_row(user)) and u["id"] not in existing_users
    }

    new_users = [{"id": user[0], "username": user[1]} for user in unique_new_users]

    db["users"].insert_all(  # type: ignore
        new_users,
        # ignore any write error
        # ignore=True,
        # only relevant if creating the table
        pk="id",  # type: ignore
        not_null=["id", "username"],  # type: ignore
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
    num_awards: int


def comment_to_comment_row(comment: Comment) -> Optional[CommentRow]:
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
        "num_awards": comment["total_awards_received"],
    }


T = TypeVar("T")
U = TypeVar("U")


def apply_and_filter(
    filterer: Callable[[T], Optional[U]], items: Iterable[T]
) -> list[U]:
    return [c for c in map(filterer, items) if c]


def upsert_comments(
    db: Database, comments: Iterable[Comment], table_prefix: Optional[PrefixType] = None
) -> int:
    comment_rows = apply_and_filter(comment_to_comment_row, comments)
    db[build_table_name("comments", table_prefix)].upsert_all(  # type: ignore
        comment_rows,
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


def post_to_post_row(post: Post) -> Optional[PostRow]:
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
        "num_awards": post["total_awards_received"],
        "is_removed": int(post["selftext"] == "[removed]"),
    }


def upsert_posts(
    db: Database, posts: Iterable[Post], table_prefix: Optional[PrefixType] = None
) -> int:
    post_rows = apply_and_filter(post_to_post_row, posts)
    db[build_table_name("posts", table_prefix)].insert_all(  # type: ignore
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


FTS_INSTRUCTIONS: list[tuple[str, list[str]]] = [
    ("comments", ["text"]),
    ("posts", ["title", "text"]),
    ("saved_comments", ["text"]),
    ("saved_posts", ["title", "text"]),
]


def ensure_fts(db: Database):
    table_names = set(db.table_names())
    for table, columns in FTS_INSTRUCTIONS:
        if table in table_names and f"{table}_fts" not in table_names:
            db[table].enable_fts(columns, create_triggers=True)
