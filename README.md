# reddit-to-sqlite

Stores all the content from a specific user in a SQLite database. This includes both their posts and comments.

## Install

The PyPI package is `reddit-to-sqlite` ([PyPI Link]()). Install it globally using [pipx](https://pypa.github.io/pipx/) or `pip` (for programmatic use):

```bash
pipx install reddit-to-sqlite
```

## Usage

The CLI currently exposes a single command, but more could be added in the future.

### user

Fetches all comments and posts for a specific user.

```bash
reddit-to-sqlite user some_username
reddit-to-sqlite user some_username my-reddit-data.db
```

#### Params

> Note: the argument order is reversed from most dogsheep packages (which take db_path first). This allows for use of a default db name, so I prefer it.

1. `username`: a case-insensitive string. The leading `/u/` is optional (and ignored if supplied)
2. (optional) `db_path`: the path to a sqlite file, which will be created or updated as needed. Defaults to `reddit.db`.

### A Note on Stored Data

While most [Dogsheep](https://github.com/dogsheep) projects grab the raw JSON output of their source APIs, Reddit's API has a lot of junk in it. So, I opted for a slimmed down approach.

## Development

This section is people making changes to this package.

When in a virtual environment, run the following:

```bash
pip install -e '.[test]'
```

This installs the package in `--edit` mode and makes its dependencies available.

### Running Tests

In your virtual environment, a simple `pytest` should run the unit test suite.

## Motivation

I got nervous when I saw Reddit's [notification of upcoming API changes](https://old.reddit.com/r/reddit/comments/12qwagm/an_update_regarding_reddits_api/). To ensure I could always access data I created, I wanted to make sure I had a backup in place before anything changed in a big way.
