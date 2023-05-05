from dataclasses import asdict, dataclass
from typing import Optional

from sqlite_utils import Database


class BaseRow:
    def as_row(self) -> dict[str, int]:
        # remove None values, since we don't want upserts to remove values
        return {k: v for k, v in asdict(self).items() if v is not None}  # type: ignore


@dataclass
class SubredditRow(BaseRow):
    id: str
    name: str
    type: Optional[str] = None


def insert_subreddits(db: Database, subreddits: list[SubredditRow]):
    db["subreddits"].insert_all(  # type: ignore
        [s.as_row() for s in subreddits],
        ignore=True,  # type: ignore
        # only relevant if creating the table
        pk="id",  # type: ignore
        not_null=["id", "name"],  # type: ignore
    )


@dataclass
class UserRow(BaseRow):
    id: str
    username: str


def insert_user(db: Database, user: UserRow):
    db["users"].insert(  # type: ignore
        user.as_row(),
        ignore=True,
        # only relevant if creating the table
        pk="id",  # type: ignore
        not_null=["id", "username"],
    )


# d = {
#     "id": str,  # csv doesn't have type prepended; should change
#     "timestamp": int,  # have to transform for CSV
#     "score": int,  # nullable
#     "text": str,  # make sure to match style (looks like csv is markdown? does JSON have that at all?)
#     "user": str,  # always me; need to fetch separately in csv
#     "is_submitter": int,  # nullable
#     "subreddit": str,  # json has fk, csv has string
#     "permalink": str,
#     "controversiality": int,  # nullable
# }


@dataclass
class CommentRow(BaseRow):
    id: str
    timestamp: int
    text: str
    user: str
    subreddit: str
    permalink: str
    score: Optional[int] = None
    is_submitter: Optional[int] = None
    controversiality: Optional[int] = None


def upsert_comments(db: Database, comments: list[CommentRow]):
    db["comments"].insert_all(  # type: ignore
        [c.as_row() for c in comments],
        upsert=True,
        pk="id",  # type: ignore
        # update the schema - needed if user does archive first
        # alter=True,
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
        column_order=[  # type: ignore
            "id",
            "timestamp",
            "score",
            "text",
            "user",
            "is_submitter",
            "subreddit",
            "permalink",
            "controversiality",
        ],
        # can re-add or assert this later, but the rows aren't created if this is present
        # see: https://github.com/simonw/sqlite-utils/issues/538
        # not_null=["id", "timestamp", "text", "user", "subreddit", "permalink"],
    )


def ensure_fts(db: Database):
    table_names = set(db.table_names())
    if "comments" in table_names and "comments_fts" not in table_names:
        db["comments"].enable_fts(["text"], create_triggers=True)
    if "posts" in table_names and "posts_fts" not in table_names:
        db["posts"].enable_fts(["title", "text"], create_triggers=True)
