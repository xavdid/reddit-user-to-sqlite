from unittest.mock import MagicMock, patch

import pytest

from reddit_user_to_sqlite.reddit_api import (
    PagedResponse,
    RedditRateLimitException,
    _unwrap_response_and_raise,
    add_missing_user_fragment,
    get_user_id,
    load_comments_for_user,
    load_info,
    load_posts_for_user,
)
from tests.conftest import MockInfoFunc, MockPagedFunc, MockUserFunc


def test_load_comments(mock_paged_request: MockPagedFunc, comment_response, comment):
    response = mock_paged_request(resource="comments", json=comment_response)

    assert load_comments_for_user("xavdid") == [comment]

    assert response.call_count == 1


def test_load_posts(mock_paged_request: MockPagedFunc, self_post_response, self_post):
    response = mock_paged_request(resource="submitted", json=self_post_response)

    assert load_posts_for_user("xavdid") == [self_post]
    assert response.call_count == 1


@patch("reddit_user_to_sqlite.reddit_api.PAGE_SIZE", new=1)
def test_loads_10_pages(mock_paged_request: MockPagedFunc, comment_response, comment):
    response = mock_paged_request(
        resource="comments", params={"limit": 1}, json=comment_response
    )

    assert load_comments_for_user("xavdid") == [comment] * 10

    assert response.call_count == 10


@patch("reddit_user_to_sqlite.reddit_api.PAGE_SIZE", new=1)
def test_loads_multiple_pages(
    mock_paged_request: MockPagedFunc, comment_response: PagedResponse, comment
):
    comment_response["data"]["after"] = "abc"
    first_request = mock_paged_request(
        resource="comments", params={"limit": 1}, json=comment_response
    )

    comment_response["data"]["after"] = "def"
    second_request = mock_paged_request(
        resource="comments", params={"limit": 1, "after": "abc"}, json=comment_response
    )

    comment_response["data"]["children"] = []
    third_request = mock_paged_request(
        resource="comments", params={"limit": 1, "after": "def"}, json=comment_response
    )

    comments = load_comments_for_user("xavdid")

    assert first_request.call_count == 1
    assert second_request.call_count == 1
    assert third_request.call_count == 1

    assert comments == [comment, comment]


def test_error_response(mock_paged_request: MockPagedFunc):
    mock_paged_request(
        resource="comments", json={"error": 500, "message": "you broke reddit"}
    )

    with pytest.raises(ValueError) as err:
        load_comments_for_user("xavdid")

    assert (
        str(err.value) == "Received API error from Reddit (code 500): you broke reddit"
    )


def test_load_info(mock_info_request: MockInfoFunc, comment_response, comment):
    mock_info_request("a,b,c", json=comment_response)

    assert load_info(["a", "b", "c"]) == [comment]


@patch("reddit_user_to_sqlite.reddit_api.PAGE_SIZE", new=2)
def test_load_info_pages(mock_info_request: MockInfoFunc, comment_response, comment):
    mock_info_request("a,b", json=comment_response, limit=2)
    mock_info_request("c,d", json=comment_response, limit=2)
    mock_info_request("e", json=comment_response, limit=2)

    assert load_info(["a", "b", "c", "d", "e"]) == [comment] * 3


def test_load_info_empty(mock_info_request: MockInfoFunc, empty_response):
    mock_info_request("a,b,c,d,e,f,g,h", json=empty_response)

    assert load_info(["a", "b", "c", "d", "e", "f", "g", "h"]) == []


def test_unwrap_and_raise_passes_good_responses_through():
    response = {"neat": True}
    assert _unwrap_response_and_raise(MagicMock(json=lambda: response)) == response


def test_unwrap_and_raise_raises_unknown_errors():
    with pytest.raises(ValueError) as err:
        _unwrap_response_and_raise(
            MagicMock(json=lambda: {"error": 123, "message": "cool"})
        )
    assert str(err.value) == "Received API error from Reddit (code 123): cool"


def test_unwrap_and_raise_raises_rate_limit_errors():
    with pytest.raises(RedditRateLimitException) as err:
        _unwrap_response_and_raise(
            MagicMock(
                json=lambda: {"error": 429, "message": "cool"},
                headers={
                    "x-ratelimit-used": "4",
                    "x-ratelimit-remaining": "6",
                    "x-ratelimit-reset": "20",
                },
            )
        )

    e = err.value

    assert e.used == 4
    assert e.remaining == 6
    assert e.window_total == 10
    assert e.reset_after_seconds == 20
    assert e.stats == "Used 4/10 requests (resets in 20 seconds)"


def test_get_user_id(mock_user_request: MockUserFunc, user_response):
    mock_user_request("xavdid", json=user_response)

    assert get_user_id("xavdid") == "np8mb41h"


def test_get_user_id_unknown_user(mock_user_request: MockUserFunc):
    mock_user_request("xavdid", json={"message": "Not Found", "error": 404})
    with pytest.raises(ValueError):
        get_user_id("xavdid")


def test_add_missing_user_fragment():
    items = [{"a": 1}, {"a": 2}, {"a": 3}]
    assert add_missing_user_fragment(items, "xavdid", "t2_abc123") == [  # type: ignore
        {"a": 1, "author": "xavdid", "author_fullname": "t2_abc123"},
        {"a": 2, "author": "xavdid", "author_fullname": "t2_abc123"},
        {"a": 3, "author": "xavdid", "author_fullname": "t2_abc123"},
    ]


def test_add_missing_user_fragment_no_overwrite():
    items = [{"a": 1}, {"author": "david", "author_fullname": "t2_def456"}]

    assert add_missing_user_fragment(items, "xavdid", "t2_abc123") == [  # type: ignore
        {"a": 1, "author": "xavdid", "author_fullname": "t2_abc123"},
        {"author": "david", "author_fullname": "t2_def456"},
    ]
