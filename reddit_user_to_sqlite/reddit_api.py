import logging
import os
import time
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Optional,
    Sequence,
    TypedDict,
    TypeVar,
    Union,
    cast,
    final,
)

import click
import requests
from tqdm import tqdm, trange

from reddit_user_to_sqlite.helpers import batched

if TYPE_CHECKING:
    from typing import NotRequired

USER_AGENT = "reddit-to-sqlite"

# per https://www.reddit.com/r/redditdev/comments/14nbw6g/updated_rate_limits_going_into_effect_over_the/
# free api limited at 10 queries per minute, or 6 seconds between requests
API_DELAY = 6
MAX_RETRIES = 8


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
    author_fullname: "NotRequired[str]"


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
    data: Union[Comment, Post]


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


def _call_reddit_api(
    url: str, params: Optional[dict[str, Any]] = None
) -> SuccessResponse:
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


def load_info(resources: Sequence[str]) -> list[Union[Comment, Post]]:
    result = []
    slowMode = len(resources) > 10000
    if slowMode:
        click.echo(
            "Large data pull detected, enabling slow mode to prevent API rate limiting"
        )
    for batch in batched(
        tqdm(resources, disable=bool(os.environ.get("DISABLE_PROGRESS"))), PAGE_SIZE
    ):
        # API calls are flakey, so be prepared for failure
        for i in range(MAX_RETRIES):
            try:
                response = _call_reddit_api(
                    "https://www.reddit.com/api/info.json",
                    params={"id": ",".join(batch)},
                )
                # break retry loop if successful
                break
            except Exception as e:
                # otherwise log the error and try again.
                logging.exception(e)
                if i == MAX_RETRIES - 1:
                    # if we're out of retries, return what we have
                    click.echo("Max retries exceeded, returning partial result")
                    return result
                # sleep tops out at 256 seconds with MAX_RETRIES = 8
                time.sleep(2**i)

        result += [c["data"] for c in response["data"]["children"]]
        if slowMode:
            # sleep to avoid rate limiting on free API for large requests.  Rate limiting kicks in at 15k requests
            time.sleep(API_DELAY)

    return result


def get_user_id(username: str) -> str:
    response = requests.get(
        f"https://www.reddit.com/user/{username}/about.json",
        headers={"user-agent": USER_AGENT},
    ).json()

    _raise_reddit_error(response)

    return response["data"]["id"]


T = TypeVar("T", Comment, Post)


def add_missing_user_fragment(
    items: list[T], username: str, user_fullname: str
) -> list[T]:
    """
    If an item lacks user details, this adds them. Otherwise the item passes through untouched.
    """
    return [
        cast(T, {**i, "author": username, "author_fullname": user_fullname})
        if "author_fullname" not in i
        else i
        for i in items
    ]
