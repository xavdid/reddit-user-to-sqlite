from typing import Any, Literal, NotRequired, Optional, Sequence, TypedDict, final

import requests
from tqdm import tqdm, trange

from reddit_user_to_sqlite.helpers import batched

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
    author_fullname: NotRequired[str]


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


class Post(SubredditFragment, UserFragment):
    # no prefix
    id: str

    title: str

    # markdown content of the post; could be empty
    selftext: str
    # external link (or self link)
    url: str
    # link to reddit thread (sans domain)
    permalink: str

    upvote_ratio: float
    score: int
    total_awards_received: int

    num_comments: int
    over_18: bool

    # timestamp
    created: float


# class Subreddit(TypedDict):
#     should_archive_posts: bool


@final
class ResourceWrapper(TypedDict):
    kind: str
    data: Comment | Post


@final
class ResponseBody(TypedDict):
    before: Optional[str]
    after: Optional[str]
    modhash: str
    geo_filter: str
    dist: int
    children: Sequence[ResourceWrapper]


@final
class SuccessResponse(TypedDict):
    data: ResponseBody
    kind: Literal["Listing"]


@final
class ErorrResponse(TypedDict):
    message: str
    error: int


# max page size is 100
PAGE_SIZE = 100


def _raise_reddit_error(response):
    if "error" in response:
        raise ValueError(
            f'Received API error from Reddit (code {response["error"]}): {response["message"]}'
        )


def _call_reddit_api(url: str, params: dict[str, Any] | None = None) -> SuccessResponse:
    response = requests.get(
        url,
        {"limit": PAGE_SIZE, "raw_json": 1, **(params or {})},
        headers={"user-agent": USER_AGENT},
    ).json()

    _raise_reddit_error(response)

    return response


def _load_paged_resource(resource: Literal["comments", "submitted"], username: str):
    result = []
    after = None
    # max number of pages we can fetch
    for _ in trange(10):
        response = _call_reddit_api(
            f"https://www.reddit.com/user/{username}/{resource}.json",
            params={"after": after},
        )
        result += [c["data"] for c in response["data"]["children"]]
        after = response["data"]["after"]

        if len(response["data"]["children"]) < PAGE_SIZE:
            break

    return result


def load_comments_for_user(username: str) -> list[Comment]:
    return _load_paged_resource("comments", username)


def load_posts_for_user(username: str) -> list[Post]:
    return _load_paged_resource("submitted", username)


def load_info(resources: Sequence[str]) -> list[Comment | Post]:
    result = []

    for batch in batched(tqdm(resources), PAGE_SIZE):
        response = _call_reddit_api(
            "https://www.reddit.com/api/info.json", params={"id": ",".join(batch)}
        )
        result += [c["data"] for c in response["data"]["children"]]

    return result


def get_user_id(username: str) -> str:
    response = requests.get(
        f"https://www.reddit.com/user/{username}/about.json",
        headers={"user-agent": USER_AGENT},
    ).json()

    _raise_reddit_error(response)

    return response["data"]["id"]
