import pytest

from reddit_user_to_sqlite.helpers import clean_username


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
