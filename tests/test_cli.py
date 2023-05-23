from traceback import print_tb
import pytest
from click.testing import CliRunner
import responses
from sqlite_utils import Database

from reddit_user_to_sqlite.cli import add_missing_user_fragment, cli
from tests.conftest import (
    MockInfoFunc,
    MockPagedFunc,
    _wrap_response,
    _build_test_file,
    _build_mock_info_req,
    _build_mock_paged_req,
    _build_mock_user_request,
)


@pytest.mark.parametrize("username", ["xavdid", "/u/xavdid", "u/xavdid"])
def test_load_data_for_user(
    tmp_db_path: str,
    tmp_db: Database,
    mock_paged_request: MockPagedFunc,
    username,
    comment,
    all_posts_response,
    stored_comment,
    stored_self_post,
    stored_external_post,
    # stored_removed_post,
    stored_user,
    removed_comment,
):
    comment_response = mock_paged_request(
        resource="comments", json=_wrap_response(comment, removed_comment)
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


def test_cold_load_data_from_archive(
    tmp_db_path,
    mock_info_request: MockInfoFunc,
    modify_comment,
    modify_post,
    archive_dir,
    tmp_db: Database,
    stored_user,
    stored_comment,
    stored_self_post,
    # needed for side effects
    comments_file,
    posts_file,
):
    mock_info_request(
        "t1_a,t1_b,t1_c",
        json=_wrap_response(*(modify_comment({"id": i}) for i in "abc")),
    )
    mock_info_request(
        "t3_d,t3_e,t3_f",
        json=_wrap_response(*(modify_post({"id": i}) for i in "def")),
    )

    result = CliRunner().invoke(cli, ["archive", str(archive_dir), "--db", tmp_db_path])
    assert not result.exception

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
    assert list(tmp_db["comments"].rows) == [{**stored_comment, "id": i} for i in "abc"]
    assert list(tmp_db["posts"].rows) == [{**stored_self_post, "id": i} for i in "def"]


def test_cold_load_comments_only_from_archive(
    tmp_db_path,
    mock_info_request: MockInfoFunc,
    modify_comment,
    empty_file_at_path,
    archive_dir,
    tmp_db: Database,
    stored_comment,
    stored_user,
    # needed for side effects
    comments_file,
):
    mock_info_request(
        "t1_a,t1_b,t1_c",
        json=_wrap_response(*(modify_comment({"id": i}) for i in "abc")),
    )
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
    assert list(tmp_db["comments"].rows) == [{**stored_comment, "id": i} for i in "abc"]
    assert list(tmp_db["posts"].rows) == []


def test_cold_load_posts_only_from_archive(
    tmp_db_path,
    mock_info_request: MockInfoFunc,
    modify_post,
    empty_file_at_path,
    archive_dir,
    tmp_db: Database,
    stored_self_post,
    stored_user,
    # needed for side effects
    posts_file,
):
    empty_file_at_path("comments.csv")
    mock_info_request(
        "t3_d,t3_e,t3_f",
        json=_wrap_response(*(modify_post({"id": i}) for i in "def")),
    )

    result = CliRunner().invoke(cli, ["archive", str(archive_dir), "--db", tmp_db_path])
    assert not result.exception

    assert {"subreddits", "users", "posts", "posts_fts"} <= set(tmp_db.table_names())
    assert list(tmp_db["subreddits"].rows) == [
        {"id": "32u6q", "name": "KeybaseProofs", "type": "public"}
    ]
    assert list(tmp_db["users"].rows) == [stored_user]
    assert list(tmp_db["comments"].rows) == []
    assert list(tmp_db["posts"].rows) == [{**stored_self_post, "id": i} for i in "def"]


def test_loads_data_from_both_sources_api_first(
    tmp_db_path,
    # mock_info_request: MockInfoFunc,
    # mock_paged_request: MockPagedFunc,
    comment_response,
    self_post_response,
    modify_comment,
    modify_post,
    archive_dir,
    tmp_db: Database,
    stored_comment,
    stored_self_post,
    stored_user,
):
    # have to do everything in a single mock;
    # might be able to turn that into a fixture so this plays more nicely, but this works
    with responses.RequestsMock() as mock:
        mock_paged_request = _build_mock_paged_req(mock)
        mock_info_request = _build_mock_info_req(mock)

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
        mock_info_request(
            "t1_a,t1_c",
            json=_wrap_response(*(modify_comment({"id": i}) for i in "ac")),
        )
        mock_info_request(
            "t3_d,t3_f",
            json=_wrap_response(*(modify_post({"id": i}) for i in "df")),
        )

        _build_test_file(
            archive_dir, "comments.csv", ["id", "a", "c", stored_comment["id"]]
        )
        _build_test_file(
            archive_dir, "posts.csv", ["id", "d", "f", stored_self_post["id"]]
        )

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
    # mock_info_request: MockInfoFunc,
    # mock_paged_request: MockPagedFunc,
    comment_response,
    self_post_response,
    modify_comment,
    modify_post,
    archive_dir,
    tmp_db: Database,
    stored_comment,
    stored_self_post,
    stored_user,
):
    # have to do everything in a single mock;
    # might be able to turn that into a fixture so this plays more nicely, but this works
    with responses.RequestsMock() as mock:
        mock_paged_request = _build_mock_paged_req(mock)
        mock_info_request = _build_mock_info_req(mock)

        # second pass
        mock_info_request(
            "t1_a,t1_c",
            json=_wrap_response(*(modify_comment({"id": i}) for i in "ac")),
        )
        mock_info_request(
            "t3_d,t3_f",
            json=_wrap_response(*(modify_post({"id": i}) for i in "df")),
        )

        _build_test_file(archive_dir, "comments.csv", ["id", "a", "c"])
        _build_test_file(archive_dir, "posts.csv", ["id", "d", "f"])

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
        assert list(tmp_db["comments"].rows) == [
            {**stored_comment, "id": i} for i in "ac"
        ]
        assert list(tmp_db["posts"].rows) == [
            {**stored_self_post, "id": i} for i in "df"
        ]

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
    comment,
    removed_comment,
    self_post,
    removed_post,
    archive_dir,
    tmp_db_path,
    tmp_db: Database,
    stored_user,
    stored_comment,
    stored_removed_comment,
    stored_self_post,
    stored_removed_post,
):
    with responses.RequestsMock() as mock:
        mock_info_request = _build_mock_info_req(mock)

        mock_info_request(
            "t1_jj0ti6f,t1_c3sgfl4", json=_wrap_response(comment, removed_comment)
        )
        mock_info_request(
            "t3_uypaav,t3_1f55rr", json=_wrap_response(self_post, removed_post)
        )

        _build_test_file(archive_dir, "comments.csv", ["id", "jj0ti6f", "c3sgfl4"])
        _build_test_file(archive_dir, "posts.csv", ["id", "uypaav", "1f55rr"])

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
        assert list(tmp_db["posts"].rows) == [stored_self_post, stored_removed_post]


def test_load_username_from_file(
    tmp_db: Database,
    tmp_db_path,
    user_response,
    archive_dir,
    removed_comment,
    removed_post_response,
    stored_removed_comment,
    stored_removed_post,
    stored_user,
    # needed for side effects
    stats_file,
):
    with responses.RequestsMock() as mock:
        mock_user_request = _build_mock_user_request(mock)
        mock_info_request = _build_mock_info_req(mock)

        mock_info_request("t1_c3sgfl4", json=_wrap_response(removed_comment))
        mock_info_request("t3_1f55rr", json=removed_post_response)

        mock_user_request("xavdid", json=user_response)

        _build_test_file(archive_dir, "comments.csv", ["id", "c3sgfl4"])
        _build_test_file(archive_dir, "posts.csv", ["id", "1f55rr"])

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
    removed_comment,
    removed_post_response,
    empty_file_at_path,
):
    with responses.RequestsMock() as mock:
        mock_info_request = _build_mock_info_req(mock)

        mock_info_request("t1_c3sgfl4", json=_wrap_response(removed_comment))
        mock_info_request("t3_1f55rr", json=removed_post_response)

        empty_file_at_path("statistics.csv")

        _build_test_file(archive_dir, "comments.csv", ["id", "c3sgfl4"])
        _build_test_file(archive_dir, "posts.csv", ["id", "1f55rr"])

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
