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
    comment_response,
    username,
    stored_comment,
):
    response = mock_request(json=comment_response)
    result = CliRunner().invoke(cli, ["user", username, "--db", tmp_db_path])
    assert not result.exception, result.exception

    assert {"subreddits", "users", "comments", "comments_fts"}.issubset(
        tmp_db.table_names()
    )

    assert list(tmp_db["subreddits"].rows) == [
        {"id": "t5_2t3ad", "name": "patientgamers", "type": "public"}
    ]
    assert list(tmp_db["users"].rows) == [{"id": "t2_np8mb41h", "username": "xavdid"}]
    assert list(tmp_db["comments"].rows) == [stored_comment]

    assert response.call_count == 1


@pytest.mark.live
def test_load_live_data(tmp_db_path: str, tmp_db: Database, stored_comment):
    result = CliRunner().invoke(cli, ["user", "xavdid", "--db", tmp_db_path])
    assert not result.exception, result.exception

    assert {"subreddits", "users", "comments", "comments_fts"}.issubset(
        tmp_db.table_names()
    )

    assert {"id": "t5_2t3ad", "name": "patientgamers", "type": "public"} in list(
        tmp_db["subreddits"].rows
    )
    assert list(tmp_db["users"].rows) == [{"id": "t2_np8mb41h", "username": "xavdid"}]

    comments = list(tmp_db["comments"].rows)
    assert (
        len(comments) <= 1000
    ), "this test will start to fail if/when I've made 1k comments on this account"
    assert stored_comment in comments


def test_missing_user_errors(tmp_db_path: str, mock_request: MockFunc):
    mock_request(json={"error": 500, "message": "you broke reddit"})
    result = CliRunner().invoke(cli, ["user", "xavdid", "--db", tmp_db_path])

    assert result.exception
    assert (
        str(result.exception)
        == "Received API error from Reddit (code 500): you broke reddit"
    )


def test_no_comments(tmp_db_path: str, mock_request: MockFunc):
    mock_request(
        json={
            "kind": "Listing",
            "data": {
                "after": None,
                "dist": 0,
                "modhash": "xrteabn7vrfa2b62629fa00880e79b9565c07398e89fb3443b",
                "geo_filter": "",
                "children": [],
                "before": None,
            },
        }
    )
    result = CliRunner().invoke(cli, ["user", "xavdid", "--db", tmp_db_path])

    assert result.exit_code == 1
    assert result.stdout  # not sure why it's it "out" not "err"
    assert "Error: no data found for username xavdid" in result.stdout
