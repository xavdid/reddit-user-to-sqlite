from typing import Any, Callable, Generator, Optional, Protocol
from unittest.mock import patch

import pytest
import responses
from responses import BaseResponse, RequestsMock, matchers
from sqlite_utils import Database

from reddit_to_sqlite.reddit_api import (
    USER_AGENT,
    CommentsResponse,
    load_comments_for_user,
)


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def tmp_db_path(tmp_path):
    """
    returns a Database in a temp dir
    """
    return str(tmp_path / "test.db")


@pytest.fixture
def tmp_db(tmp_db_path):
    """
    returns a Database in a temp dir
    """
    return Database(tmp_db_path)


@pytest.fixture
def comment():
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
def comment_response(comment) -> CommentsResponse:
    return {
        "kind": "Listing",
        "data": {
            "after": None,
            "dist": 1,
            "modhash": "whatever",
            "geo_filter": "",
            "children": [{"kind": "t1", "data": comment}],
            "before": None,
        },
    }


REDDIT_URL = "https://www.reddit.com/user/xavdid/comments.json"


# def query_params(params=None):


class MockFunc(Protocol):
    def __call__(
        self,
        url=REDDIT_URL,
        params: Optional[dict[str, str | int]] = None,
        json: Any = None,
    ) -> BaseResponse:
        ...


@pytest.fixture
def mock_request() -> Generator[MockFunc, None, None]:
    with responses.RequestsMock() as mock:

        def _mock_request(
            url=REDDIT_URL,
            params: Optional[dict[str, str | int]] = None,
            json: Any = None,
        ):
            params = {"limit": 100, "raw_json": 1, **(params or {})}

            return mock.get(
                url,
                match=[
                    matchers.query_param_matcher(params),
                    matchers.header_matcher({"user-agent": USER_AGENT}),
                ],
                json=json,
            )

        yield _mock_request
