from typing import Any, Sequence, TypedDict, cast

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


def comment_to_subreddit_row(comment: SubredditFragment) -> SubredditRow:
    return {
        "id": comment["subreddit_id"][3:],
        "name": comment["subreddit"],
        "type": comment["subreddit_type"],
    }


def insert_subreddits(db: Database, subreddits: Sequence[SubredditFragment]):
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


def comment_to_user_row(comment: UserFragment) -> UserRow:
    return {"id": comment["author_fullname"][3:], "username": comment["author"]}


def insert_user(db: Database, user: UserFragment):
    db["users"].insert(  # type: ignore
        cast(dict[str, Any], comment_to_user_row(user)),
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


def comment_to_comment_row(comment: Comment) -> CommentRow:
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


def upsert_comments(db: Database, comments: list[Comment]):
    db["comments"].insert_all(  # type: ignore
        map(comment_to_comment_row, comments),
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


def post_to_post_row(post: Post) -> PostRow:
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


def upsert_posts(db: Database, posts: list[Post]):
    db["posts"].insert_all(  # type: ignore
        map(post_to_post_row, posts),
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


def ensure_fts(db: Database):
    table_names = set(db.table_names())
    if "comments" in table_names and "comments_fts" not in table_names:
        db["comments"].enable_fts(["text"], create_triggers=True)
    if "posts" in table_names and "posts_fts" not in table_names:
        db["posts"].enable_fts(["title", "text"], create_triggers=True)
