import os
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

USER_AGENT = "reddit-user-to-sqlite"


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


class SuccessResponse(TypedDict):
    kind: Literal["Listing", "t2"]


@final
class PagedResponseBody(TypedDict):
    before: Optional[str]
    after: Optional[str]
    modhash: str
    geo_filter: str
    dist: int
    children: Sequence[ResourceWrapper]


@final
class PagedResponse(SuccessResponse):
    data: PagedResponseBody


@final
class UserData(TypedDict):
    id: str


@final
class UserResponse(SuccessResponse):
    data: UserData


@final
class ErorrResponse(TypedDict):
    message: str
    error: int


ErrorHeaders = TypedDict(
    "ErrorHeaders",
    {
        "x-ratelimit-used": str,
        "x-ratelimit-remaining": str,
        "x-ratelimit-reset": str,
    },
)

# max API page size is 100
PAGE_SIZE = 100


class RedditRateLimitException(Exception):
    """
    more info: https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki
    """

    def __init__(self, headers: ErrorHeaders) -> None:
        super().__init__("Rate limited by Reddit")

        self.used = int(headers["x-ratelimit-used"])
        self.remaining = int(headers["x-ratelimit-remaining"])
        self.window_total = self.used + self.remaining
        self.reset_after_seconds = int(headers["x-ratelimit-reset"])

    @property
    def stats(self) -> str:
        return f"Used {self.used}/{self.window_total} requests (resets in {self.reset_after_seconds} seconds)"


def _unwrap_response_and_raise(response: requests.Response):
    result = response.json()

    if "error" in result:
        if result["error"] == 429:
            raise RedditRateLimitException(cast(ErrorHeaders, response.headers))

        raise ValueError(
            f'Received API error from Reddit (code {result["error"]}): {result["message"]}'
        )

    return result


def _call_reddit_api(url: str, params: Optional[dict[str, Any]] = None):
    return _unwrap_response_and_raise(
        requests.get(
            url,
            {"raw_json": 1, "limit": PAGE_SIZE, **(params or {})},  # type: ignore
            headers={"user-agent": USER_AGENT},
        )
    )


def _rate_limit_message(e: RedditRateLimitException) -> str:
    return f"Rate limited by reddit; try again in {e.reset_after_seconds} seconds. Until then, saving what we have"


def _load_paged_resource(resource: Literal["comments", "submitted"], username: str):
    """
    handles paging logic for arbitrary-length queries with an "after" param
    """
    result = []
    after = None
    # max number of pages we can fetch
    for _ in trange(10):
        try:
            response: PagedResponse = _call_reddit_api(
                f"https://www.reddit.com/user/{username}/{resource}.json",
                params={"after": after},
            )

            result += [c["data"] for c in response["data"]["children"]]
            after = response["data"]["after"]
            if len(response["data"]["children"]) < PAGE_SIZE:
                break
        except RedditRateLimitException as e:
            click.echo(_rate_limit_message(e), err=True)
            break

    return result


def load_comments_for_user(username: str) -> list[Comment]:
    return _load_paged_resource("comments", username)


def load_posts_for_user(username: str) -> list[Post]:
    return _load_paged_resource("submitted", username)


def load_info(resources: Sequence[str]) -> list[Union[Comment, Post]]:
    """
    calls the `/info` endpoint to fetch data about a sequence of resources that include the type prefix
    """
    result = []
    for batch in batched(
        tqdm(resources, disable=bool(os.environ.get("DISABLE_PROGRESS"))), PAGE_SIZE
    ):
        try:
            response: PagedResponse = _call_reddit_api(
                "https://www.reddit.com/api/info.json",
                params={"id": ",".join(batch)},
            )
            result += [c["data"] for c in response["data"]["children"]]
        except RedditRateLimitException as e:
            click.echo(_rate_limit_message(e), err=True)
            break

    return result


def get_user_id(username: str) -> str:
    response: UserResponse = _call_reddit_api(
        f"https://www.reddit.com/user/{username}/about.json"
    )

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
