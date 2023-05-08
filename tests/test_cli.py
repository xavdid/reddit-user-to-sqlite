import pytest
from click.testing import CliRunner
from sqlite_utils import Database

from reddit_user_to_sqlite.cli import cli
from tests.conftest import MockFunc


@pytest.mark.parametrize("username", ["xavdid", "/u/xavdid", "u/xavdid"])
def test_load_data_for_user(
    tmp_db_path: str,
    tmp_db: Database,
    mock_request: MockFunc,
    username,
    comment_response,
    all_posts_response,
    stored_comment,
    stored_self_post,
    stored_external_post,
    stored_removed_post,
):
    comment_response = mock_request(resource="comments", json=comment_response)
    post_response = mock_request(resource="submitted", json=all_posts_response)

    result = CliRunner().invoke(cli, ["user", username, "--db", tmp_db_path])
    assert not result.exception, result.exception

    assert {
        "subreddits",
        "users",
        "comments",
        "comments_fts",
        "posts",
        "posts_fts",
    }.issubset(tmp_db.table_names())

    assert list(tmp_db["subreddits"].rows) == [
        {"id": "2t3ad", "name": "patientgamers", "type": "public"},
        {"id": "32u6q", "name": "KeybaseProofs", "type": "public"},
    ]
    assert list(tmp_db["users"].rows) == [{"id": "np8mb41h", "username": "xavdid"}]
    assert list(tmp_db["comments"].rows) == [stored_comment]
    assert list(tmp_db["posts"].rows) == [
        stored_self_post,
        stored_removed_post,
        stored_external_post,
    ]

    assert comment_response.call_count == 1
    assert post_response.call_count == 1


@pytest.mark.live
def test_load_live_data(
    tmp_db_path: str, tmp_db: Database, stored_comment, stored_self_post
):
    result = CliRunner().invoke(cli, ["user", "xavdid", "--db", tmp_db_path])
    assert not result.exception, result.exception

    assert {"subreddits", "users", "comments", "comments_fts"}.issubset(
        tmp_db.table_names()
    )

    assert {"id": "2t3ad", "name": "patientgamers", "type": "public"} in list(
        tmp_db["subreddits"].rows
    )
    assert list(tmp_db["users"].rows) == [{"id": "np8mb41h", "username": "xavdid"}]

    comments = list(tmp_db["comments"].rows)
    assert (
        len(comments) <= 1000
    ), "this test will start to fail if/when I've made 1k comments on this account"
    assert stored_comment in comments

    posts = list(tmp_db["posts"].rows)
    assert (
        len(posts) <= 1000
    ), "this test will start to fail if/when I've made 1k posts on this account"
    assert stored_self_post["id"] in {p["id"] for p in posts}


def test_missing_user_errors(tmp_db_path: str, mock_request: MockFunc):
    mock_request(
        resource="comments", json={"error": 404, "message": "no user by that name"}
    )
    result = CliRunner().invoke(cli, ["user", "xavdid", "--db", tmp_db_path])

    assert result.exception
    assert (
        str(result.exception)
        == "Received API error from Reddit (code 404): no user by that name"
    )


def test_no_data(tmp_db_path: str, mock_request: MockFunc, empty_response):
    mock_request(resource="comments", json=empty_response)
    mock_request(resource="submitted", json=empty_response)

    result = CliRunner().invoke(cli, ["user", "xavdid", "--db", tmp_db_path])

    assert result.exit_code == 1
    assert result.stdout  # not sure why it's it "out" not "err"
    assert "Error: no data found for username: xavdid" in result.stdout


def test_comments_but_no_posts(
    tmp_db_path: str,
    tmp_db: Database,
    mock_request: MockFunc,
    empty_response,
    comment_response,
    stored_comment,
):
    mock_request(resource="comments", json=comment_response)
    mock_request(resource="submitted", json=empty_response)

    result = CliRunner().invoke(cli, ["user", "xavdid", "--db", tmp_db_path])
    assert not result.exception, result.exception

    assert list(tmp_db["users"].rows) == [{"id": "np8mb41h", "username": "xavdid"}]
    assert list(tmp_db["posts"].rows) == []
    assert list(tmp_db["comments"].rows) == [stored_comment]


def test_posts_but_no_comments(
    tmp_db_path: str,
    tmp_db: Database,
    mock_request: MockFunc,
    empty_response,
    self_post_response,
    stored_self_post,
):
    mock_request(resource="comments", json=empty_response)
    mock_request(resource="submitted", json=self_post_response)

    result = CliRunner().invoke(cli, ["user", "xavdid", "--db", tmp_db_path])
    assert not result.exception, result.exception

    assert list(tmp_db["users"].rows) == [{"id": "np8mb41h", "username": "xavdid"}]
    assert list(tmp_db["comments"].rows) == []
    assert list(tmp_db["posts"].rows) == [stored_self_post]
