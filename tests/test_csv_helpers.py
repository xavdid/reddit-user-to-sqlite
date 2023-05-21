from pathlib import Path
import pytest
from sqlite_utils import Database

from reddit_user_to_sqlite.csv_helpers import (
    get_username_from_archive,
    load_ids_from_file,
    validate_and_build_path,
)


def test_validate_and_build_path(archive_dir, stats_file):
    assert validate_and_build_path(archive_dir, "statistics") == stats_file


def test_validate_and_build_fails(archive_dir: Path):
    with pytest.raises(ValueError) as err:
        validate_and_build_path(archive_dir, "posts")

    err_msg = str(err.value)

    assert str(archive_dir) in err_msg
    assert "posts.csv not found" in err_msg


def test_load_comment_ids_from_file_empty_db(
    tmp_db: Database, archive_dir, comments_file
):
    assert load_ids_from_file(tmp_db, archive_dir, "comments") == [
        "t1_a",
        "t1_b",
        "t1_c",
    ]


def test_load_comment_ids_from_file_some_db(
    tmp_db: Database, archive_dir, comments_file
):
    tmp_db["comments"].insert({"id": "a"})  # type: ignore

    assert load_ids_from_file(tmp_db, archive_dir, "comments") == [
        "t1_b",
        "t1_c",
    ]


def test_load_comment_ids_missing_files(tmp_db: Database, archive_dir):
    with pytest.raises(ValueError) as err:
        load_ids_from_file(tmp_db, archive_dir, "comments")

    err_msg = str(err)
    assert "comments.csv not found" in err_msg


def test_load_post_ids_from_file_empty_db(tmp_db: Database, archive_dir, posts_file):
    assert load_ids_from_file(tmp_db, archive_dir, "posts") == [
        "t3_d",
        "t3_e",
        "t3_f",
    ]


def test_load_post_ids_from_file_some_db(tmp_db: Database, archive_dir, posts_file):
    tmp_db["posts"].insert({"id": "e"})  # type: ignore

    assert load_ids_from_file(tmp_db, archive_dir, "posts") == [
        "t3_d",
        "t3_f",
    ]


def test_load_post_ids_missing_files(tmp_db: Database, archive_dir):
    with pytest.raises(ValueError) as err:
        load_ids_from_file(tmp_db, archive_dir, "posts")

    assert "posts.csv not found" in str(err.value)


def test_get_username_from_archive(archive_dir, stats_file):
    assert get_username_from_archive(archive_dir) == "xavdid"


def test_get_username_from_archive_no_name(archive_dir: Path):
    (archive_dir / "statistics.csv").touch()
    assert get_username_from_archive(archive_dir) == None


def test_get_username_from_archive_missing_file(archive_dir):
    with pytest.raises(ValueError) as err:
        get_username_from_archive(archive_dir)

    assert "statistics.csv not found" in str(err.value)
