from click.testing import CliRunner
from sqlite_utils import Database

from reddit_user_to_sqlite.cli import cli
from tests.conftest import MockFunc


def test_load_data_for_user(
    tmp_db_path: str, tmp_db: Database, mock_request: MockFunc, comment_response
):
    response = mock_request(json=comment_response)
    result = CliRunner().invoke(cli, ["user", "xavdid", "--db", tmp_db_path])
    assert not result.exception, result.exception

    assert {"subreddits", "users", "comments", "comments_fts"}.issubset(
        tmp_db.table_names()
    )

    assert list(tmp_db["subreddits"].rows) == [
        {"id": "t5_2t3ad", "name": "patientgamers", "type": "public"}
    ]
    assert list(tmp_db["users"].rows) == [{"id": "t2_np8mb41h", "username": "xavdid"}]
    assert list(tmp_db["comments"].rows) == [
        {
            "controversiality": 0,
            "id": "jj0ti6f",
            "is_submitter": 0,
            "permalink": "https://www.reddit.com/r/patientgamers/comments/1371yrv/what_games_do_you_guys_love_to_replay_or_never/jj0ti6f/?context=10",
            "score": 1,
            "subreddit": "t5_2t3ad",
            "text": '&lt;div class="md"&gt;&lt;p&gt;Such a great game to pick up for a run every couple of months. Every time I think I&amp;#39;m done, it pulls be back in.&lt;/p&gt;\n&lt;/div&gt;',
            "timestamp": 1683327131,
            "user": "t2_np8mb41h",
        }
    ]

    assert response.call_count == 1


def test_missing_user_errors(tmp_db_path: str, mock_request: MockFunc):
    mock_request(json={"error": 500, "message": "you broke reddit"})
    result = CliRunner().invoke(cli, ["user", "xavdid", "--db", tmp_db_path])

    assert result.exception
    assert (
        str(result.exception)
        == "Received API error from Reddit (code 500): you broke reddit"
    )
