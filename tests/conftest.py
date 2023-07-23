from pathlib import Path
from typing import Any, Literal, Optional, Protocol, Union

import pytest
import responses
from responses import BaseResponse, RequestsMock, matchers
from sqlite_utils import Database

from reddit_user_to_sqlite.reddit_api import (
    USER_AGENT,
    ErrorHeaders,
    PagedResponse,
    Post,
)
from reddit_user_to_sqlite.sqlite_helpers import CommentRow, PostRow, UserRow


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


def _wrap_response(*children) -> PagedResponse:
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
        "total_awards_received": 3,
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
def modify_comment(comment):
    def _modify(d):
        return {**comment, **d}

    return _modify


@pytest.fixture
def modify_post(self_post):
    def _modify(d):
        return {**self_post, **d}

    return _modify


@pytest.fixture
def removed_comment():
    return {
        "total_awards_received": 0,
        "approved_at_utc": None,
        "author_is_blocked": False,
        "comment_type": None,
        "edited": False,
        "mod_reason_by": None,
        "banned_by": None,
        "removal_reason": None,
        "link_id": "t3_puwue",
        "author_flair_template_id": None,
        "likes": None,
        "replies": "",
        "user_reports": [],
        "saved": False,
        "id": "c3sgfl4",
        "banned_at_utc": None,
        "mod_reason_title": None,
        "gilded": 0,
        "archived": True,
        "collapsed_reason_code": "DELETED",
        "no_follow": True,
        "author": "[deleted]",
        "can_mod_post": False,
        "created_utc": 1329550785.0,
        "send_replies": True,
        "parent_id": "t1_c3sgeij",
        "score": -1,
        "approved_by": None,
        "mod_note": None,
        "all_awardings": [],
        "subreddit_id": "t5_2qm4e",
        "body": "[removed]",
        "awarders": [],
        "author_flair_css_class": None,
        "name": "t1_c3sgfl4",
        "downs": 0,
        "is_submitter": False,
        "body_html": '<div class="md"><p>[removed]</p>\n</div>',
        "gildings": {},
        "collapsed_reason": None,
        "distinguished": None,
        "associated_award": None,
        "stickied": False,
        "can_gild": True,
        "top_awarded_type": None,
        "unrepliable_reason": None,
        "author_flair_text_color": "dark",
        "score_hidden": False,
        "permalink": "/r/askscience/comments/asdf/why_do_birds_fly/",
        "num_reports": None,
        "locked": False,
        "report_reasons": None,
        "created": 1329550785.0,
        "subreddit": "askscience",
        "author_flair_text": None,
        "treatment_tags": [],
        "collapsed": True,
        "subreddit_name_prefixed": "r/askscience",
        "controversiality": 0,
        "author_flair_background_color": "",
        "collapsed_because_crowd_control": None,
        "mod_reports": [],
        "subreddit_type": "public",
        "ups": -1,
    }


@pytest.fixture
def removed_comment_response(removed_comment):
    return _wrap_response(removed_comment)


@pytest.fixture
def all_comments_response(comment, removed_comment):
    return _wrap_response(comment, removed_comment)


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
        "num_awards": 3,
    }


@pytest.fixture
def stored_removed_comment() -> CommentRow:
    return {
        "controversiality": 0,
        "id": "c3sgfl4",
        "is_submitter": 0,
        "permalink": "https://old.reddit.com/r/askscience/comments/asdf/why_do_birds_fly/?context=10",
        "score": -1,
        "subreddit": "2qm4e",
        "text": "[removed]",
        "timestamp": 1329550785,
        # manually added this - if it's stored, I must have found a user
        "user": "np8mb41h",
        "num_awards": 0,
    }


@pytest.fixture
def stored_removed_comment_placeholder_user() -> CommentRow:
    return {
        "controversiality": 0,
        "id": "c3sgfl4",
        "is_submitter": 0,
        "permalink": "https://old.reddit.com/r/askscience/comments/asdf/why_do_birds_fly/?context=10",
        "score": -1,
        "subreddit": "2qm4e",
        "text": "[removed]",
        "timestamp": 1329550785,
        "user": "1234567",
        "num_awards": 0,
    }


@pytest.fixture
def comment_response(comment) -> PagedResponse:
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
def removed_post():
    """
    A raw (unwrapped) removed post object from the Reddit API
    """
    return {
        "approved_at_utc": None,
        "subreddit": "videos",
        "selftext": "[deleted]",
        "user_reports": [],
        "saved": False,
        "mod_reason_title": None,
        "gilded": 0,
        "clicked": False,
        "title": "Tommy Wiseau Wishes YOU A Happy Memorial Day! — Urban Outfitters",
        "link_flair_richtext": [],
        "subreddit_name_prefixed": "r/videos",
        "hidden": False,
        "pwls": 6,
        "link_flair_css_class": None,
        "downs": 0,
        "thumbnail_height": 52,
        "top_awarded_type": None,
        "hide_score": False,
        "name": "t3_1f55rr",
        "quarantine": False,
        "link_flair_text_color": "dark",
        "upvote_ratio": 1,
        "author_flair_background_color": "",
        "subreddit_type": "public",
        "ups": 1,
        "total_awards_received": 0,
        "media_embed": {},
        "thumbnail_width": 70,
        "author_flair_template_id": None,
        "is_original_content": False,
        "secure_media": None,
        "is_reddit_media_domain": False,
        "is_meta": False,
        "category": None,
        "secure_media_embed": {},
        "link_flair_text": None,
        "can_mod_post": False,
        "score": 1,
        "approved_by": None,
        "is_created_from_ads_ui": False,
        "thumbnail": "default",
        "edited": False,
        "author_flair_css_class": None,
        "gildings": {},
        "content_categories": None,
        "is_self": False,
        "mod_note": None,
        "created": 1369671390.0,
        "link_flair_type": "text",
        "wls": 6,
        "removed_by_category": None,
        "banned_by": None,
        "domain": "",
        "allow_live_comments": False,
        "selftext_html": '<!-- SC_OFF --><div class="md"><p>[deleted]</p>\n</div><!-- SC_ON -->',
        "likes": None,
        "suggested_sort": None,
        "banned_at_utc": None,
        "url_overridden_by_dest": "",
        "view_count": None,
        "archived": False,
        "no_follow": True,
        "is_crosspostable": False,
        "pinned": False,
        "over_18": False,
        "all_awardings": [],
        "awarders": [],
        "media_only": False,
        "can_gild": False,
        "spoiler": False,
        "locked": False,
        "author_flair_text": None,
        "treatment_tags": [],
        "visited": False,
        "removed_by": None,
        "num_reports": None,
        "distinguished": None,
        "subreddit_id": "t5_2qh1e",
        "author_is_blocked": False,
        "mod_reason_by": None,
        "removal_reason": None,
        "link_flair_background_color": "",
        "id": "1f55rr",
        "is_robot_indexable": False,
        "report_reasons": None,
        "author": "[deleted]",
        "discussion_type": None,
        "num_comments": 0,
        "send_replies": False,
        "whitelist_status": "all_ads",
        "contest_mode": False,
        "mod_reports": [],
        "author_flair_text_color": "dark",
        "permalink": "/r/videos/comments/1f55rr/tommy_wiseau_wishes_you_a_happy_memorial_day/",
        "parent_whitelist_status": "all_ads",
        "stickied": False,
        "url": "",
        "subreddit_subscribers": 26688085,
        "created_utc": 1369671390.0,
        "num_crossposts": 0,
        "media": None,
        "is_video": False,
    }


@pytest.fixture
def stored_removed_post() -> PostRow:
    return {
        "external_url": "",
        "id": "1f55rr",
        "is_removed": 0,
        "num_awards": 0,
        "num_comments": 0,
        "permalink": "https://old.reddit.com/r/videos/comments/1f55rr/tommy_wiseau_wishes_you_a_happy_memorial_day/",
        "score": 1,
        "subreddit": "2qh1e",
        "text": "[deleted]",
        "timestamp": 1369671390,
        "title": "Tommy Wiseau Wishes YOU A Happy Memorial Day! — Urban Outfitters",
        "upvote_ratio": 1,
        # manually added this - if it's stored, I must have found a user
        "user": "np8mb41h",
    }


@pytest.fixture
def stored_removed_post_placeholder_user() -> PostRow:
    return {
        "external_url": "",
        "id": "1f55rr",
        "is_removed": 0,
        "num_awards": 0,
        "num_comments": 0,
        "permalink": "https://old.reddit.com/r/videos/comments/1f55rr/tommy_wiseau_wishes_you_a_happy_memorial_day/",
        "score": 1,
        "subreddit": "2qh1e",
        "text": "[deleted]",
        "timestamp": 1369671390,
        "title": "Tommy Wiseau Wishes YOU A Happy Memorial Day! — Urban Outfitters",
        "upvote_ratio": 1,
        "user": "1234567",
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


@pytest.fixture()
def mock():
    with responses.RequestsMock() as mock_requests:
        yield mock_requests


class MockPagedFunc(Protocol):
    def __call__(
        self,
        resource: Literal["comments", "submitted"],
        json: Any,
        params: Optional[dict[str, Union[str, int]]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> BaseResponse:
        ...


@pytest.fixture
def mock_paged_request(mock: RequestsMock) -> MockPagedFunc:
    """
    call this to mock a list of items for a user
    """

    def _mock_request(
        resource: Literal["comments", "submitted"],
        json: Any,
        params: Optional[dict[str, Union[str, int]]] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        params = {"limit": 100, "raw_json": 1, **(params or {})}

        return mock.get(
            f"https://www.reddit.com/user/xavdid/{resource}.json",
            match=[
                matchers.query_param_matcher(params),
                matchers.header_matcher({"user-agent": USER_AGENT}),
            ],
            json=json,
            headers=headers,
        )

    return _mock_request


class MockInfoFunc(Protocol):
    def __call__(
        self, ids: str, json: Any, headers: Optional[dict[str, str]] = None, limit=100
    ) -> BaseResponse:
        ...


# need to extract this so I can call it manually
# def _build_mock_info_req(mock: RequestsMock) -> MockInfoFunc:


@pytest.fixture
def mock_info_request(mock: RequestsMock) -> MockInfoFunc:
    """
    call this to mirror loading info about a sequence of fullnames (type-prefixed ids)
    """

    def _mock_request(
        ids: str,
        json: Any,
        headers: Optional[dict[str, str]] = None,
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
            headers=headers,
        )

    return _mock_request


@pytest.fixture
def comment_info_response(modify_comment):
    return _wrap_response(*(modify_comment({"id": i}) for i in "ac"))


@pytest.fixture
def post_info_response(modify_post):
    return _wrap_response(*(modify_post({"id": i}) for i in "df"))


@pytest.fixture
def stored_user() -> UserRow:
    return {"id": "np8mb41h", "username": "xavdid"}


@pytest.fixture
def deleted_user() -> UserRow:
    return {"id": "1234567", "username": "__DeletedUser__"}


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


@pytest.fixture
def rate_limit_headers() -> ErrorHeaders:
    return {
        "x-ratelimit-used": "4",
        "x-ratelimit-remaining": "6",
        "x-ratelimit-reset": "20",
    }


class MockUserFunc(Protocol):
    def __call__(self, username: str, json: Any) -> BaseResponse:
        ...


@pytest.fixture
def mock_user_request(mock: RequestsMock) -> MockUserFunc:
    """
    call this to mirror loading info about a sequence of fullnames (type-prefixed ids)
    """

    def _mock_request(username: str, json: Any):
        return mock.get(
            f"https://www.reddit.com/user/{username}/about.json",
            match=[
                matchers.header_matcher({"user-agent": USER_AGENT}),
            ],
            json=json,
        )

    return _mock_request


@pytest.fixture
def archive_dir(tmp_path: Path):
    (archive_dir := tmp_path / "archive").mkdir()
    return archive_dir


class WriteArchiveFileFunc(Protocol):
    def __call__(self, filename: str, lines: list[str]) -> Path:
        ...


@pytest.fixture
def write_archive_file(archive_dir: Path) -> WriteArchiveFileFunc:
    """
    write `lines` into `archive_dir/filename`.
    """

    def _write_file(filename: str, lines: list[str]):
        (new_file := archive_dir / filename).write_text("\n".join(lines))
        return new_file

    return _write_file


@pytest.fixture
def stats_file(write_archive_file: WriteArchiveFileFunc):
    """
    write a basic statistics file into the archive directory
    """

    return write_archive_file(
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
def comments_file(write_archive_file: WriteArchiveFileFunc):
    return write_archive_file("comments.csv", ["id", "a", "c"])


@pytest.fixture
def saved_comments_file(write_archive_file: WriteArchiveFileFunc):
    return write_archive_file("saved_comments.csv", ["id", "g", "h"])


@pytest.fixture
def posts_file(write_archive_file: WriteArchiveFileFunc):
    return write_archive_file("posts.csv", ["id", "d", "f"])


@pytest.fixture
def saved_posts_file(write_archive_file: WriteArchiveFileFunc):
    return write_archive_file("saved_posts.csv", ["id", "j", "k"])


@pytest.fixture
def empty_file_at_path(write_archive_file: WriteArchiveFileFunc):
    def _empty_file(filename: str):
        return write_archive_file(filename, [])

    return _empty_file


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
