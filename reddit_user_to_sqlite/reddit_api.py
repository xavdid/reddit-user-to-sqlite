from typing import Literal, Optional, TypedDict, final

import requests
from tqdm import tqdm

USER_AGENT = "reddit-to-sqlite"


class SubredditFragment(TypedDict):
    ## SUBREDDIT
    # "consoledeals"
    subreddit: str
    # ID
    subreddit_id: str
    # "public"
    subreddit_type: str


class UserFragment(TypedDict):
    # comment author username
    author: str
    # comment author prefixed id
    author_fullname: str


class Comment(SubredditFragment, UserFragment):
    # this is only the relevant fields from the response

    ## COMMENT
    # short ID
    id: str
    # full ID
    name: str

    total_awards_received: int
    gilded: int

    # the ID of a post or comment
    parent_id: str
    score: int

    # maybe always 0? or i'm just boring
    controversiality: int
    # plaintext (or markdown?)
    body: str
    body_html: str
    # is the commenter OP?
    is_submitter: bool
    # 1682464342.0,
    created: float
    # "/r/x/comments/...
    permalink: str

    ## POST
    # post title
    link_title: str
    num_comments: int
    # post ID
    link_id: str
    link_permalink: str
    # "r/consoledeals",
    subreddit_name_prefixed: str


@final
class CommentWrapper(TypedDict):
    kind: str
    data: Comment


@final
class CommentBody(TypedDict):
    before: Optional[str]
    after: Optional[str]
    modhash: str
    geo_filter: str
    dist: int
    children: list[CommentWrapper]


@final
class CommentsResponse(TypedDict):
    data: CommentBody
    kind: Literal["Listing"]


@final
class ErorrResponse(TypedDict):
    message: str
    error: int


# max page size is 100
PAGE_SIZE = 100


def load_comments_for_user(username: str) -> list[Comment]:
    comments: list[Comment] = []
    after = None
    # max number of pages we can fetch
    for _ in tqdm(range(10)):
        response: CommentsResponse | ErorrResponse = requests.get(
            f"https://www.reddit.com/user/{username}/comments.json",
            {"limit": PAGE_SIZE, "raw_json": 1, "after": after},
            headers={"user-agent": USER_AGENT},
        ).json()

        if "error" in response:
            raise ValueError(
                f'Received API error from Reddit (code {response["error"]}): {response["message"]}'
            )

        comments += [c["data"] for c in response["data"]["children"]]
        after = response["data"]["after"]

        if len(response["data"]["children"]) < PAGE_SIZE:
            break

    return comments
