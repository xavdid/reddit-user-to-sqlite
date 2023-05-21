from pathlib import Path
from typing import Any, Generator, Literal, Optional, Protocol, Sequence

import pytest
import responses
from responses import BaseResponse, matchers
from sqlite_utils import Database

from reddit_user_to_sqlite.reddit_api import USER_AGENT, Post, SuccessResponse
from reddit_user_to_sqlite.sqlite_helpers import CommentRow, PostRow


@pytest.fixture
def tmp_db_path(tmp_path):
    """
    returns a Database path in a temp dir
    """
    return str(tmp_path / "test.db")


@pytest.fixture
def tmp_db(tmp_db_path):
    """
    returns a Database in a temp dir
    """
    return Database(tmp_db_path)


def _wrap_response(*children) -> SuccessResponse:
    return {
        "kind": "Listing",
        "data": {
            "after": None,
            "dist": 1,
            "modhash": "whatever",
            "geo_filter": "",
            "children": [{"kind": "t_", "data": c} for c in children],
            "before": None,
        },
    }


@pytest.fixture
def comment():
    """
    A raw (unwrapped) comment object from the Reddit API
    """
    return {
        "subreddit_id": "t5_2t3ad",
        "approved_at_utc": None,
        "author_is_blocked": False,
        "comment_type": None,
        "link_title": "What games do you guys love to replay or never get bored with?",
        "mod_reason_by": None,
        "banned_by": None,
        "ups": 1,
        "num_reports": None,
        "author_flair_type": "text",
        "total_awards_received": 0,
        "subreddit": "patientgamers",
        "link_author": "DefinitionWest",
        "likes": None,
        "replies": "",
        "user_reports": [],
        "saved": False,
        "id": "jj0ti6f",
        "banned_at_utc": None,
        "mod_reason_title": None,
        "gilded": 0,
        "archived": False,
        "collapsed_reason_code": None,
        "no_follow": True,
        "author": "xavdid",
        "num_comments": 250,
        "can_mod_post": False,
        "send_replies": True,
        "parent_id": "t1_jirew06",
        "score": 1,
        "author_fullname": "t2_np8mb41h",
        "over_18": False,
        "report_reasons": None,
        "removal_reason": None,
        "approved_by": None,
        "controversiality": 0,
        "body": "Such a great game to pick up for a run every couple of months. Every time I think I'm done, it pulls be back in.",
        "edited": False,
        "top_awarded_type": None,
        "downs": 0,
        "author_flair_css_class": None,
        "is_submitter": False,
        "collapsed": False,
        "author_flair_richtext": [],
        "author_patreon_flair": False,
        "body_html": '&lt;div class="md"&gt;&lt;p&gt;Such a great game to pick up for a run every couple of months. Every time I think I&amp;#39;m done, it pulls be back in.&lt;/p&gt;\n&lt;/div&gt;',
        "gildings": {},
        "collapsed_reason": None,
        "distinguished": None,
        "associated_award": None,
        "stickied": False,
        "author_premium": False,
        "can_gild": True,
        "link_id": "t3_1371yrv",
        "unrepliable_reason": None,
        "author_flair_text_color": None,
        "score_hidden": False,
        "permalink": "/r/patientgamers/comments/1371yrv/what_games_do_you_guys_love_to_replay_or_never/jj0ti6f/",
        "subreddit_type": "public",
        "link_permalink": "https://www.reddit.com/r/patientgamers/comments/1371yrv/what_games_do_you_guys_love_to_replay_or_never/",
        "name": "t1_jj0ti6f",
        "author_flair_template_id": None,
        "subreddit_name_prefixed": "r/patientgamers",
        "author_flair_text": None,
        "treatment_tags": [],
        "created": 1683327131.0,
        "created_utc": 1683327131.0,
        "awarders": [],
        "all_awardings": [],
        "locked": False,
        "author_flair_background_color": None,
        "collapsed_because_crowd_control": None,
        "mod_reports": [],
        "quarantine": False,
        "mod_note": None,
        "link_url": "https://www.reddit.com/r/patientgamers/comments/1371yrv/what_games_do_you_guys_love_to_replay_or_never/",
    }


@pytest.fixture
def stored_comment() -> CommentRow:
    """
    a serialized comment row in the db
    """
    return {
        "controversiality": 0,
        "id": "jj0ti6f",
        "is_submitter": 0,
        "permalink": "https://old.reddit.com/r/patientgamers/comments/1371yrv/what_games_do_you_guys_love_to_replay_or_never/jj0ti6f/?context=10",
        "score": 1,
        "subreddit": "2t3ad",
        "text": "Such a great game to pick up for a run every couple of months. Every time I think I'm done, it pulls be back in.",
        "timestamp": 1683327131,
        "user": "np8mb41h",
    }


@pytest.fixture
def comment_response(comment) -> SuccessResponse:
    """
    The full response from Reddit with a comment child
    """
    return _wrap_response(comment)


@pytest.fixture
def self_post():
    """
    A raw (unwrapped) self post object from the Reddit API
    """
    return {
        "all_awardings": [],
        "allow_live_comments": False,
        "approved_at_utc": None,
        "approved_by": None,
        "archived": False,
        "author": "xavdid",
        "author_flair_background_color": None,
        "author_flair_css_class": None,
        "author_flair_richtext": [],
        "author_flair_template_id": None,
        "author_flair_text": None,
        "author_flair_text_color": None,
        "author_flair_type": "text",
        "author_fullname": "t2_np8mb41h",
        "author_is_blocked": False,
        "author_patreon_flair": False,
        "author_premium": False,
        "awarders": [],
        "banned_at_utc": None,
        "banned_by": None,
        "can_gild": False,
        "can_mod_post": False,
        "category": None,
        "clicked": False,
        "content_categories": None,
        "contest_mode": False,
        "created": 1653623084,
        "created_utc": 1653623084,
        "discussion_type": None,
        "distinguished": None,
        "domain": "self.KeybaseProofs",
        "downs": 0,
        "edited": False,
        "gilded": 0,
        "gildings": {},
        "hidden": False,
        "hide_score": False,
        "id": "uypaav",
        "is_created_from_ads_ui": False,
        "is_crosspostable": False,
        "is_meta": False,
        "is_original_content": False,
        "is_reddit_media_domain": False,
        "is_robot_indexable": True,
        "is_self": True,
        "is_video": False,
        "likes": None,
        "link_flair_background_color": "",
        "link_flair_css_class": None,
        "link_flair_richtext": [],
        "link_flair_text": None,
        "link_flair_text_color": "dark",
        "link_flair_type": "text",
        "locked": False,
        "media": None,
        "media_embed": {},
        "media_only": False,
        "mod_note": None,
        "mod_reason_by": None,
        "mod_reason_title": None,
        "mod_reports": [],
        "name": "t3_uypaav",
        "no_follow": True,
        "num_comments": 0,
        "num_crossposts": 0,
        "num_reports": None,
        "over_18": False,
        "parent_whitelist_status": "all_ads",
        "permalink": "/r/KeybaseProofs/comments/uypaav/my_keybase_proof_redditxavdid_keybasexavdid/",
        "pinned": False,
        "post_hint": "self",
        "preview": {
            "enabled": False,
            "images": [
                {
                    "id": "-YTScuArtOT7VGFuDeGCZvRtPZZ6N8YNPBBjDIA6KiQ",
                    "resolutions": [
                        {
                            "height": 108,
                            "url": "https://external-preview.redd.it/d8t5K0qquzpFUYxW8QDLgM8lFUUyu6zo_KM_cFv2JjY.jpg?width=108&crop=smart&auto=webp&v=enabled&s=3076e81be7310fd25b111faa85f33dcd722e3e07",
                            "width": 108,
                        },
                        {
                            "height": 216,
                            "url": "https://external-preview.redd.it/d8t5K0qquzpFUYxW8QDLgM8lFUUyu6zo_KM_cFv2JjY.jpg?width=216&crop=smart&auto=webp&v=enabled&s=80217a00e40d70bdf57ebd1510d5ff49a1b1b5a4",
                            "width": 216,
                        },
                        {
                            "height": 320,
                            "url": "https://external-preview.redd.it/d8t5K0qquzpFUYxW8QDLgM8lFUUyu6zo_KM_cFv2JjY.jpg?width=320&crop=smart&auto=webp&v=enabled&s=547611bba1890b9b67fc84e2d31badb682bd25bb",
                            "width": 320,
                        },
                    ],
                    "source": {
                        "height": 360,
                        "url": "https://external-preview.redd.it/d8t5K0qquzpFUYxW8QDLgM8lFUUyu6zo_KM_cFv2JjY.jpg?auto=webp&v=enabled&s=ff41e339b6994c953c13eb917d562e7b0793831e",
                        "width": 360,
                    },
                    "variants": {},
                }
            ],
        },
        "pwls": 6,
        "quarantine": False,
        "removal_reason": None,
        "removed_by": None,
        "removed_by_category": None,
        "report_reasons": None,
        "saved": False,
        "score": 1,
        "secure_media": None,
        "secure_media_embed": {},
        "selftext": "### Keybase proof\n...-----END PGP MESSAGE-----\n",
        "selftext_html": '<!-- SC_OFF --><div class="md"><h3>Keybase proof</h3>\n-----END PGP MESSAGE-----\n</code></pre>\n</div><!-- SC_ON -->',
        "send_replies": True,
        "spoiler": False,
        "stickied": False,
        "subreddit": "KeybaseProofs",
        "subreddit_id": "t5_32u6q",
        "subreddit_name_prefixed": "r/KeybaseProofs",
        "subreddit_subscribers": 7428,
        "subreddit_type": "public",
        "suggested_sort": None,
        "thumbnail": "self",
        "thumbnail_height": None,
        "thumbnail_width": None,
        "title": "My Keybase proof [reddit:xavdid = keybase:xavdid]",
        "top_awarded_type": None,
        "total_awards_received": 0,
        "treatment_tags": [],
        "ups": 1,
        "upvote_ratio": 1,
        "url": "https://www.reddit.com/r/KeybaseProofs/comments/uypaav/my_keybase_proof_redditxavdid_keybasexavdid/",
        "user_reports": [],
        "view_count": None,
        "visited": False,
        "whitelist_status": "all_ads",
        "wls": 6,
    }


@pytest.fixture
def stored_self_post() -> PostRow:
    return {
        "external_url": "",
        "id": "uypaav",
        "is_removed": 0,
        "num_awards": 0,
        "permalink": "https://old.reddit.com/r/KeybaseProofs/comments/uypaav/my_keybase_proof_redditxavdid_keybasexavdid/",
        "score": 1,
        "subreddit": "32u6q",
        "text": "### Keybase proof\n...-----END PGP MESSAGE-----\n",
        "timestamp": 1653623084,
        "num_comments": 0,
        "title": "My Keybase proof [reddit:xavdid = keybase:xavdid]",
        "upvote_ratio": 1,
        "user": "np8mb41h",
    }


@pytest.fixture
def self_post_response(self_post):
    return _wrap_response(self_post)


@pytest.fixture
def removed_post(self_post: Post) -> Post:
    """
    A raw (unwrapped) removed post object from the Reddit API
    """
    return {
        **self_post,
        "selftext": "[removed]",
        "id": "asdf",
    }


@pytest.fixture
def stored_removed_post(stored_self_post: PostRow) -> PostRow:
    return {
        **stored_self_post,
        "text": "[removed]",
        "is_removed": 1,
        "id": "asdf",
    }


@pytest.fixture
def removed_post_response(removed_post):
    return _wrap_response(removed_post)


@pytest.fixture
def external_post(self_post: Post) -> Post:
    """
    A raw (unwrapped) external post object from the Reddit API
    """
    return {
        **self_post,
        "selftext": "",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "id": "qwer",
    }


@pytest.fixture
def stored_external_post(stored_self_post: PostRow) -> PostRow:
    return {
        **stored_self_post,
        "text": "",
        "external_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "id": "qwer",
    }


@pytest.fixture
def all_posts_response(self_post, removed_post, external_post):
    return _wrap_response(self_post, removed_post, external_post)


@pytest.fixture
def empty_response():
    return _wrap_response()


class MockPagedFunc(Protocol):
    def __call__(
        self,
        resource: Literal["comments", "submitted"],
        json: Any,
        params: Optional[dict[str, str | int]] = None,
    ) -> BaseResponse:
        ...


@pytest.fixture
def mock_paged_request() -> Generator[MockPagedFunc, None, None]:
    """
    call this to mock a list of items for a user
    """
    with responses.RequestsMock() as mock:

        def _mock_request(
            resource: Literal["comments", "submitted"],
            json: Any,
            params: Optional[dict[str, str | int]] = None,
        ):
            params = {"limit": 100, "raw_json": 1, **(params or {})}

            return mock.get(
                f"https://www.reddit.com/user/xavdid/{resource}.json",
                match=[
                    matchers.query_param_matcher(params),
                    matchers.header_matcher({"user-agent": USER_AGENT}),
                ],
                json=json,
            )

        yield _mock_request


class MockInfoFunc(Protocol):
    def __call__(self, ids: str, json: Any, limit=100) -> BaseResponse:
        ...


@pytest.fixture
def mock_info_request() -> Generator[MockInfoFunc, None, None]:
    """
    call this to mirror loading info about a sequence of fullnames (type-prefixed ids)
    """
    with responses.RequestsMock() as mock:

        def _mock_request(
            ids: str,
            json: Any,
            limit=100,
        ):
            params = {"limit": limit, "raw_json": 1, "id": ids}

            return mock.get(
                "https://www.reddit.com/api/info.json",
                match=[
                    matchers.query_param_matcher(params),
                    matchers.header_matcher({"user-agent": USER_AGENT}),
                ],
                json=json,
            )

        yield _mock_request


@pytest.fixture
def user_response():
    return {
        "kind": "t2",
        "data": {
            "is_employee": False,
            "is_friend": False,
            "subreddit": {
                "default_set": True,
                "user_is_contributor": None,
                "banner_img": "",
                "allowed_media_in_comments": [],
                "user_is_banned": None,
                "free_form_reports": True,
                "community_icon": None,
                "show_media": True,
                "icon_color": "#51E9F4",
                "user_is_muted": None,
                "display_name": "u_xavdid",
                "header_img": None,
                "title": "",
                "previous_names": [],
                "over_18": False,
                "icon_size": [256, 256],
                "primary_color": "",
                "icon_img": "https://www.redditstatic.com/avatars/defaults/v2/avatar_default_5.png",
                "description": "",
                "submit_link_label": "",
                "header_size": None,
                "restrict_posting": True,
                "restrict_commenting": False,
                "subscribers": 0,
                "submit_text_label": "",
                "is_default_icon": True,
                "link_flair_position": "",
                "display_name_prefixed": "u/xavdid",
                "key_color": "",
                "name": "t5_6fndvc",
                "is_default_banner": True,
                "url": "/user/xavdid/",
                "quarantine": False,
                "banner_size": None,
                "user_is_moderator": None,
                "accept_followers": True,
                "public_description": "",
                "link_flair_enabled": False,
                "disable_contributor_requests": False,
                "subreddit_type": "user",
                "user_is_subscriber": None,
            },
            "snoovatar_size": None,
            "awardee_karma": 0,
            "id": "np8mb41h",
            "verified": True,
            "is_gold": False,
            "is_mod": False,
            "awarder_karma": 0,
            "has_verified_email": True,
            "icon_img": "https://www.redditstatic.com/avatars/defaults/v2/avatar_default_5.png",
            "hide_from_robots": False,
            "link_karma": 1,
            "is_blocked": False,
            "total_karma": 3,
            "pref_show_snoovatar": False,
            "name": "xavdid",
            "created": 1653622688.0,
            "created_utc": 1653622688.0,
            "snoovatar_img": "",
            "comment_karma": 2,
            "accept_followers": True,
            "has_subscribed": False,
        },
    }


class MockUserFunc(Protocol):
    def __call__(self, username: str, json: Any) -> BaseResponse:
        ...


@pytest.fixture
def mock_user_request() -> Generator[MockUserFunc, None, None]:
    """
    call this to mirror loading info about a sequence of fullnames (type-prefixed ids)
    """
    with responses.RequestsMock() as mock:

        def _mock_request(username: str, json: Any):
            return mock.get(
                f"https://www.reddit.com/user/{username}/about.json",
                match=[
                    matchers.header_matcher({"user-agent": USER_AGENT}),
                ],
                json=json,
            )

        yield _mock_request


@pytest.fixture
def archive_dir(tmp_path: Path):
    (archive_dir := tmp_path / "archive").mkdir()
    return archive_dir


def _build_test_file(archive_dir: Path, filename: str, lines: list[str]):
    """
    write `lines` into `archive_dir/filename`.
    """
    (new_file := archive_dir / filename).write_text("\n".join(lines))
    return new_file


@pytest.fixture
def stats_file(archive_dir: Path):
    """
    write a basic statistics file into the archive directory
    """

    return _build_test_file(
        archive_dir,
        "statistics.csv",
        [
            "statistic,value",
            "account name,xavdid",
            "export time,2023-05-02 06:57:14 UTC",
            "is_deleted,False",
            "registration date,2014-05-19 22:02:20 UTC",
            "email verified,True",
            "email address,whatever@gmail.com",
        ],
    )


@pytest.fixture
def comments_file(archive_dir: Path):
    return _build_test_file(archive_dir, "comments.csv", ["id", "a", "b", "c"])


@pytest.fixture
def posts_file(archive_dir: Path):
    return _build_test_file(archive_dir, "posts.csv", ["id", "d", "e", "f"])


# ---


# https://docs.pytest.org/en/latest/example/simple.html#control-skipping-of-tests-according-to-command-line-option


def pytest_addoption(parser):
    parser.addoption(
        "--include-live", action="store_true", default=False, help="run live API tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "live: mark test as hitting the live API")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--include-live"):
        # include-live flag given in cli; do not skip slow tests
        return

    skip_live = pytest.mark.skip(reason="need --include-live flag to run")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)
