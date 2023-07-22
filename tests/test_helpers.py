import pytest

from reddit_user_to_sqlite.helpers import clean_username, find_user_details_from_items


@pytest.mark.parametrize(
    "username, expected",
    [
        ("/u/xavdid", "xavdid"),
        ("u/xavdid", "xavdid"),
        ("xavdid", "xavdid"),
        ("unbelievable", "unbelievable"),
    ],
)
def test_clean_username(username, expected):
    assert clean_username(username) == expected


# to verify that fixtures that modify previous fixture results don't mutate them
def test_fixture_modifications(self_post, removed_post):
    assert self_post != removed_post


def test_unique_fixture_ids(self_post, removed_post, external_post):
    # all post types should have unique ids
    assert len({p["id"] for p in [self_post, removed_post, external_post]}) == 3


def test_find_user_details_from_items():
    assert find_user_details_from_items(
        [
            {"asdf": 1},
            {"author_fullname": "t2_abc123", "author": "xavdid"},
        ]
    ) == ("xavdid", "t2_abc123")


def test_fail_to_find_user_details_from_items():
    assert find_user_details_from_items([{"asdf": 1}, {"author": "xavdid"}]) is None
