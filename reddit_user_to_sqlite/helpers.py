import re
from itertools import islice
from typing import Iterable, Optional, TypeVar

T = TypeVar("T")


# https://docs.python.org/3.11/library/itertools.html#itertools-recipes
# available natively in 3.12
def batched(iterable: Iterable[T], n: int) -> Iterable[tuple[T]]:
    "Batch data into tuples of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch


def clean_username(username: str) -> str:
    """
    strips the leading `/u/` off the front of a username, if present
    """
    if re.match(r"/?u/", username):
        return username.strip().strip("/u")
    return username


def find_user_details_from_items(items) -> Optional[tuple[str, str]]:
    """
    Returns a 2-tuple of prefixed user_id and username if found, otherwise None
    """
    try:
        return next(
            (c["author"], c["author_fullname"]) for c in items if "author_fullname" in c
        )
    except StopIteration:
        return None
