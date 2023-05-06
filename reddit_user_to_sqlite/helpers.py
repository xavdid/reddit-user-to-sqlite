import re


def clean_username(username: str) -> str:
    """
    strips the leading `/u/` off the front of a username, if present
    """
    if re.match(r"/?u/", username):
        return username.strip().strip("/u")
    return username
