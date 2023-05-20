from unittest.mock import patch

import pytest

from reddit_user_to_sqlite.reddit_api import (
    SuccessResponse,
    load_comments_for_user,
    load_info,
    load_posts_for_user,
)
from tests.conftest import MockInfoFunc, MockPagedFunc


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
    mock_paged_request: MockPagedFunc, comment_response: SuccessResponse, comment
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
    mock_info_request("e,f", json=comment_response, limit=2)

    assert load_info(["a", "b", "c", "d", "e", "f"]) == [comment] * 3
