from traceback import print_tb

import pytest
from click.testing import CliRunner
from sqlite_utils import Database

from reddit_user_to_sqlite.cli import cli
from tests.conftest import (
    MockInfoFunc,
    MockPagedFunc,
    MockUserFunc,
    WriteArchiveFileFunc,
)


@pytest.mark.parametrize("username", ["xavdid", "/u/xavdid", "u/xavdid"])
def test_load_data_for_user(
    tmp_db_path: str,
    tmp_db: Database,
    mock_paged_request: MockPagedFunc,
    username,
    all_posts_response,
    stored_comment,
    stored_self_post,
    stored_external_post,
    # stored_removed_post,
    stored_user,
    all_comments_response,
):
    comment_response = mock_paged_request(
        resource="comments", json=all_comments_response
    )
    post_response = mock_paged_request(resource="submitted", json=all_posts_response)

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
        {"id": "2qm4e", "name": "askscience", "type": "public"},
        {"id": "32u6q", "name": "KeybaseProofs", "type": "public"},
        {"id": "2qh1e", "name": "videos", "type": "public"},
    ]
    assert list(tmp_db["users"].rows) == [stored_user]
    assert list(tmp_db["comments"].rows) == [stored_comment]
    assert list(tmp_db["posts"].rows) == [
        stored_self_post,
        # stored_removed_post, # posts without authors are skipped
        stored_external_post,
    ]

    assert comment_response.call_count == 1
    assert post_response.call_count == 1


@pytest.mark.live
def test_load_live_data(
    tmp_db_path: str, tmp_db: Database, stored_comment, stored_self_post, stored_user
):
    result = CliRunner().invoke(cli, ["user", "xavdid", "--db", tmp_db_path])
    assert not result.exception, result.exception

    assert {"subreddits", "users", "comments", "comments_fts"} <= set(
        tmp_db.table_names()
    )

    assert {"id": "2t3ad", "name": "patientgamers", "type": "public"} in list(
        tmp_db["subreddits"].rows
    )
    assert list(tmp_db["users"].rows) == [stored_user]

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


def test_missing_user_errors(tmp_db_path: str, mock_paged_request: MockPagedFunc):
    mock_paged_request(
        resource="comments", json={"error": 404, "message": "no user by that name"}
    )
    result = CliRunner().invoke(cli, ["user", "xavdid", "--db", tmp_db_path])

    assert result.exception
    assert (
        str(result.exception)
        == "Received API error from Reddit (code 404): no user by that name"
    )


def test_no_data(tmp_db_path: str, mock_paged_request: MockPagedFunc, empty_response):
    mock_paged_request(resource="comments", json=empty_response)
    mock_paged_request(resource="submitted", json=empty_response)

    result = CliRunner().invoke(cli, ["user", "xavdid", "--db", tmp_db_path])

    assert result.exit_code == 1
    assert result.stdout  # not sure why it's in "out" not "err"
    assert "Error: no data found for username: xavdid" in result.stdout


def test_comments_but_no_posts(
    tmp_db_path: str,
    tmp_db: Database,
    mock_paged_request: MockPagedFunc,
    empty_response,
    comment_response,
    stored_comment,
    stored_user,
):
    mock_paged_request(resource="comments", json=comment_response)
    mock_paged_request(resource="submitted", json=empty_response)

    result = CliRunner().invoke(cli, ["user", "xavdid", "--db", tmp_db_path])
    assert not result.exception, result.exception

    assert list(tmp_db["users"].rows) == [stored_user]
    assert list(tmp_db["posts"].rows) == []
    assert list(tmp_db["comments"].rows) == [stored_comment]


def test_posts_but_no_comments(
    tmp_db_path: str,
    tmp_db: Database,
    mock_paged_request: MockPagedFunc,
    empty_response,
    self_post_response,
    stored_self_post,
    stored_user,
):
    mock_paged_request(resource="comments", json=empty_response)
    mock_paged_request(resource="submitted", json=self_post_response)

    result = CliRunner().invoke(cli, ["user", "xavdid", "--db", tmp_db_path])
    assert not result.exception, result.exception

    assert list(tmp_db["users"].rows) == [stored_user]
    assert list(tmp_db["comments"].rows) == []
    assert list(tmp_db["posts"].rows) == [stored_self_post]


@pytest.mark.usefixtures("comments_file", "posts_file")
def test_cold_load_data_from_archive(
    tmp_db_path,
    mock_info_request: MockInfoFunc,
    archive_dir,
    tmp_db: Database,
    stored_user,
    stored_comment,
    stored_self_post,
    comment_info_response,
    post_info_response,
):
    mock_info_request("t1_a,t1_c", json=comment_info_response)
    mock_info_request("t3_d,t3_f", json=post_info_response)

    result = CliRunner().invoke(cli, ["archive", str(archive_dir), "--db", tmp_db_path])
    assert not result.exception, print(result.exception)

    assert {
        "subreddits",
        "users",
        "comments",
        "comments_fts",
        "posts",
        "posts_fts",
    } <= set(tmp_db.table_names())

    assert list(tmp_db["subreddits"].rows) == [
        {"id": "2t3ad", "name": "patientgamers", "type": "public"},
        {"id": "32u6q", "name": "KeybaseProofs", "type": "public"},
    ]
    assert list(tmp_db["users"].rows) == [stored_user]
    assert list(tmp_db["comments"].rows) == [{**stored_comment, "id": i} for i in "ac"]
    assert list(tmp_db["posts"].rows) == [{**stored_self_post, "id": i} for i in "df"]


@pytest.mark.usefixtures("comments_file")
def test_cold_load_comments_only_from_archive(
    tmp_db_path,
    mock_info_request: MockInfoFunc,
    empty_file_at_path,
    archive_dir,
    tmp_db: Database,
    stored_comment,
    stored_user,
    comment_info_response,
):
    mock_info_request("t1_a,t1_c", json=comment_info_response)
    empty_file_at_path("posts.csv")

    result = CliRunner().invoke(cli, ["archive", str(archive_dir), "--db", tmp_db_path])
    assert not result.exception

    assert {"subreddits", "users", "comments", "comments_fts"} <= set(
        tmp_db.table_names()
    )
    assert list(tmp_db["subreddits"].rows) == [
        {"id": "2t3ad", "name": "patientgamers", "type": "public"}
    ]
    assert list(tmp_db["users"].rows) == [stored_user]
    assert list(tmp_db["comments"].rows) == [{**stored_comment, "id": i} for i in "ac"]
    assert list(tmp_db["posts"].rows) == []


@pytest.mark.usefixtures("posts_file")
def test_cold_load_posts_only_from_archive(
    tmp_db_path,
    mock_info_request: MockInfoFunc,
    empty_file_at_path,
    archive_dir,
    tmp_db: Database,
    stored_self_post,
    stored_user,
    post_info_response,
):
    empty_file_at_path("comments.csv")
    mock_info_request("t3_d,t3_f", json=post_info_response)

    result = CliRunner().invoke(cli, ["archive", str(archive_dir), "--db", tmp_db_path])
    assert not result.exception

    assert {"subreddits", "users", "posts", "posts_fts"} <= set(tmp_db.table_names())
    assert list(tmp_db["subreddits"].rows) == [
        {"id": "32u6q", "name": "KeybaseProofs", "type": "public"}
    ]
    assert list(tmp_db["users"].rows) == [stored_user]
    assert list(tmp_db["comments"].rows) == []
    assert list(tmp_db["posts"].rows) == [{**stored_self_post, "id": i} for i in "df"]


def test_loads_data_from_both_sources_api_first(
    tmp_db_path,
    mock_info_request: MockInfoFunc,
    mock_paged_request: MockPagedFunc,
    comment_response,
    self_post_response,
    archive_dir,
    tmp_db: Database,
    stored_comment,
    stored_self_post,
    stored_user,
    comment_info_response,
    post_info_response,
    write_archive_file: WriteArchiveFileFunc,
):
    mock_paged_request("comments", json=comment_response)
    mock_paged_request("submitted", json=self_post_response)

    api_result = CliRunner().invoke(cli, ["user", "xavdid", "--db", tmp_db_path])
    assert not api_result.exception

    assert {
        "subreddits",
        "users",
        "comments",
        "comments_fts",
        "posts",
        "posts_fts",
    } <= set(tmp_db.table_names())
    assert list(tmp_db["subreddits"].rows) == [
        {"id": "2t3ad", "name": "patientgamers", "type": "public"},
        {"id": "32u6q", "name": "KeybaseProofs", "type": "public"},
    ]
    assert list(tmp_db["comments"].rows) == [stored_comment]
    assert list(tmp_db["posts"].rows) == [stored_self_post]

    # second pass
    mock_info_request("t1_a,t1_c", json=comment_info_response)
    mock_info_request("t3_d,t3_f", json=post_info_response)

    write_archive_file("comments.csv", ["id", "a", "c", stored_comment["id"]])
    write_archive_file("posts.csv", ["id", "d", "f", stored_self_post["id"]])

    archive_result = CliRunner().invoke(
        cli, ["archive", str(archive_dir), "--db", tmp_db_path]
    )
    assert not archive_result.exception, print(archive_result.exception)

    assert list(tmp_db["users"].rows) == [stored_user]
    assert list(tmp_db["comments"].rows) == [
        stored_comment,
        *({**stored_comment, "id": i} for i in "ac"),
    ]
    assert list(tmp_db["posts"].rows) == [
        stored_self_post,
        *({**stored_self_post, "id": i} for i in "df"),
    ]


def test_loads_data_from_both_sources_archive_first(
    tmp_db_path,
    mock_info_request: MockInfoFunc,
    mock_paged_request: MockPagedFunc,
    comment_response,
    self_post_response,
    archive_dir,
    tmp_db: Database,
    stored_comment,
    stored_self_post,
    stored_user,
    comment_info_response,
    post_info_response,
    write_archive_file: WriteArchiveFileFunc,
):
    # second pass
    mock_info_request("t1_a,t1_c", json=comment_info_response)
    mock_info_request("t3_d,t3_f", json=post_info_response)

    write_archive_file("comments.csv", ["id", "a", "c"])
    write_archive_file("posts.csv", ["id", "d", "f"])

    archive_result = CliRunner().invoke(
        cli, ["archive", str(archive_dir), "--db", tmp_db_path]
    )
    assert not archive_result.exception, print(archive_result.exception)

    assert {
        "subreddits",
        "users",
        "comments",
        "comments_fts",
        "posts",
        "posts_fts",
    } <= set(tmp_db.table_names())

    assert list(tmp_db["users"].rows) == [stored_user]
    assert list(tmp_db["comments"].rows) == [{**stored_comment, "id": i} for i in "ac"]
    assert list(tmp_db["posts"].rows) == [{**stored_self_post, "id": i} for i in "df"]

    mock_paged_request("comments", json=comment_response)
    mock_paged_request("submitted", json=self_post_response)

    api_result = CliRunner().invoke(cli, ["user", "xavdid", "--db", tmp_db_path])
    assert not api_result.exception, print_tb(api_result.exception.__traceback__)

    assert list(tmp_db["subreddits"].rows) == [
        {"id": "2t3ad", "name": "patientgamers", "type": "public"},
        {"id": "32u6q", "name": "KeybaseProofs", "type": "public"},
    ]
    assert list(tmp_db["comments"].rows) == [
        *({**stored_comment, "id": i} for i in "ac"),
        stored_comment,
    ]
    assert list(tmp_db["posts"].rows) == [
        *({**stored_self_post, "id": i} for i in "df"),
        stored_self_post,
    ]


def test_adds_username_to_removed_posts_in_mixed_archive(
    archive_dir,
    tmp_db_path,
    tmp_db: Database,
    stored_user,
    stored_comment,
    stored_removed_comment,
    stored_self_post,
    stored_removed_post,
    mock_info_request: MockInfoFunc,
    write_archive_file: WriteArchiveFileFunc,
    all_comments_response,
    all_posts_response,
    stored_external_post,
):
    mock_info_request("t1_jj0ti6f,t1_c3sgfl4", json=all_comments_response)
    mock_info_request("t3_uypaav,t3_1f55rr,t3_qwer", json=all_posts_response)

    write_archive_file("comments.csv", ["id", "jj0ti6f", "c3sgfl4"])
    write_archive_file("posts.csv", ["id", "uypaav", "1f55rr", "qwer"])

    api_result = CliRunner().invoke(
        cli, ["archive", str(archive_dir), "--db", tmp_db_path]
    )
    assert not api_result.exception, print(api_result.exception)

    assert list(tmp_db["subreddits"].rows) == [
        {"id": "2t3ad", "name": "patientgamers", "type": "public"},
        {"id": "2qm4e", "name": "askscience", "type": "public"},
        {"id": "32u6q", "name": "KeybaseProofs", "type": "public"},
        {"id": "2qh1e", "name": "videos", "type": "public"},
    ]
    assert list(tmp_db["users"].rows) == [stored_user]
    assert list(tmp_db["comments"].rows) == [stored_comment, stored_removed_comment]
    assert list(tmp_db["posts"].rows) == [
        stored_self_post,
        stored_removed_post,
        stored_external_post,
    ]


@pytest.mark.usefixtures("stats_file")
def test_load_username_from_file(
    tmp_db: Database,
    tmp_db_path,
    user_response,
    archive_dir,
    removed_post_response,
    stored_removed_comment,
    stored_removed_post,
    stored_user,
    mock_info_request: MockInfoFunc,
    mock_user_request: MockUserFunc,
    write_archive_file: WriteArchiveFileFunc,
    removed_comment_response,
):
    mock_info_request("t1_c3sgfl4", json=removed_comment_response)
    mock_info_request("t3_1f55rr", json=removed_post_response)

    mock_user_request("xavdid", json=user_response)

    write_archive_file("comments.csv", ["id", "c3sgfl4"])
    write_archive_file("posts.csv", ["id", "1f55rr"])

    api_result = CliRunner().invoke(
        cli, ["archive", str(archive_dir), "--db", tmp_db_path]
    )
    assert not api_result.exception, print(api_result.exception)

    assert {
        "subreddits",
        "users",
        "comments",
        "comments_fts",
        "posts",
        "posts_fts",
    } <= set(tmp_db.table_names())

    assert list(tmp_db["subreddits"].rows) == [
        {"id": "2qm4e", "name": "askscience", "type": "public"},
        {"id": "2qh1e", "name": "videos", "type": "public"},
    ]
    assert list(tmp_db["users"].rows) == [stored_user]
    assert list(tmp_db["comments"].rows) == [stored_removed_comment]
    assert list(tmp_db["posts"].rows) == [stored_removed_post]


def test_missing_username_entirely(
    tmp_db: Database,
    tmp_db_path,
    archive_dir,
    removed_post_response,
    empty_file_at_path,
    mock_info_request: MockInfoFunc,
    write_archive_file: WriteArchiveFileFunc,
    removed_comment_response,
):
    mock_info_request("t1_c3sgfl4", json=removed_comment_response)
    mock_info_request("t3_1f55rr", json=removed_post_response)

    empty_file_at_path("statistics.csv")

    write_archive_file("comments.csv", ["id", "c3sgfl4"])
    write_archive_file("posts.csv", ["id", "1f55rr"])

    api_result = CliRunner().invoke(
        cli, ["archive", str(archive_dir), "--db", tmp_db_path]
    )
    assert not api_result.exception, print(api_result.exception)

    assert "Unable to guess username" in api_result.output
    assert "some posts will not be saved." in api_result.output
    assert "ignored for now" in api_result.output

    assert tmp_db.table_names() == ["subreddits"]

    assert list(tmp_db["subreddits"].rows) == [
        {"id": "2qm4e", "name": "askscience", "type": "public"},
        {"id": "2qh1e", "name": "videos", "type": "public"},
    ]
    assert list(tmp_db["users"].rows) == []
    assert list(tmp_db["comments"].rows) == []
    assert list(tmp_db["posts"].rows) == []
