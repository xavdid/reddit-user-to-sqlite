from typing import TypedDict, final

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


# limit is 100
PAGE_SIZE = 100


def load_comments_for_user(username: str) -> list[Comment]:
    comments: list[Comment] = []
    after = None
    print("startig")
    # max number of pages we can fetch
    for _ in tqdm(range(10)):
        print("getting")
        response: CommentsResponse | ErorrResponse = requests.get(
            f"https://www.reddit.com/user/{username}/comments.json",
            {"limit": PAGE_SIZE, "raw_json": 1, "after": after},
            headers={"user-agent": "reddit-to-sqlite"},
        ).json()

        print("got")
        if "error" in response:
            print("err")
            raise ValueError(
                f'Received API error from Reddit (code {response["error"]}): {response["message"]}'
            )

        if len(response["data"]["children"]) < PAGE_SIZE:
            print("done?")
            break

        comments += [c["data"] for c in response["data"]["children"]]
        after = response["data"]["after"]
        print("end of loop")

    return comments
