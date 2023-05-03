from typing import TypedDict, final, reveal_type

import requests
from tqdm import tqdm


@final
class Comment(TypedDict):
    ## COMMENT
    # short ID
    id: str
    # full ID
    name: str

    total_awards_received: int
    gilded: int
    # comment author
    author: str
    # the ID of a post or comment
    parent_id: str
    score: int
    # id of author
    author_fullname: str
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

    ## SUBREDDIT
    # "consoledeals"
    subreddit: str
    # ID
    subreddit_id: str
    # "public"
    subreddit_type: str


@final
class CommentWrapper(TypedDict):
    kind: str
    data: Comment


@final
class CommentBody(TypedDict):
    after: str
    dist: int
    children: list[CommentWrapper]


@final
class CommentsResponse(TypedDict):
    data: CommentBody


@final
class ErorrResponse(TypedDict):
    message: str
    error: int


def load_reddit_data(username: str):
    comments: list[Comment] = []
    after = None

    # max number of pages we can fetch
    # TODO: we can also do different sorts to include more from each category?
    # i'll do that if my archive doesn't pan out
    for _ in tqdm(range(10)):
        response: CommentsResponse | ErorrResponse = requests.get(
            f"https://www.reddit.com/user/{username}/comments.json",
            {"limit": 100, "raw_json": 1, "after": after},
            headers={"user-agent": "reddit-to-sqlite"},
        ).json()

        if "error" in response:
            raise ValueError(
                f'Received API error from Reddit (code {response["error"]}): {response["message"]}'
            )

        if not response["data"]["children"]:
            break

        comments += [c["data"] for c in response["data"]["children"]]
        after = response["data"]["after"]

    return comments
