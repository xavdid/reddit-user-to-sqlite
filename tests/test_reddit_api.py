from unittest.mock import patch

import pytest

from reddit_to_sqlite.reddit_api import CommentsResponse, load_comments_for_user
from tests.conftest import MockFunc


def test_load_comments(mock_request: MockFunc, comment_response, comment):
    response = mock_request(json=comment_response)

    assert load_comments_for_user("xavdid") == [comment]

    assert response.call_count == 1


@patch("reddit_to_sqlite.reddit_api.PAGE_SIZE", new=1)
def test_loads_10_pages(mock_request: MockFunc, comment_response, comment):
    response = mock_request(params={"limit": 1}, json=comment_response)

    assert load_comments_for_user("xavdid") == [comment] * 10

    assert response.call_count == 10


@patch("reddit_to_sqlite.reddit_api.PAGE_SIZE", new=1)
def test_loads_multiple_pages(
    mock_request: MockFunc, comment_response: CommentsResponse, comment
):
    comment_response["data"]["after"] = "abc"
    first_request = mock_request(params={"limit": 1}, json=comment_response)

    comment_response["data"]["after"] = "def"
    second_request = mock_request(
        params={"limit": 1, "after": "abc"}, json=comment_response
    )

    comment_response["data"]["children"] = []
    third_request = mock_request(
        params={"limit": 1, "after": "def"}, json=comment_response
    )

    comments = load_comments_for_user("xavdid")

    assert first_request.call_count == 1
    assert second_request.call_count == 1
    assert third_request.call_count == 1

    assert comments == [comment, comment]


def test_error_response(mock_request: MockFunc):
    mock_request(json={"error": 500, "message": "you broke reddit"})

    with pytest.raises(ValueError) as err:
        load_comments_for_user("xavdid")

    assert (
        str(err.value) == "Received API error from Reddit (code 500): you broke reddit"
    )
