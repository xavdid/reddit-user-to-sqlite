# reddit-user-to-sqlite

Stores all the content from a specific user in a SQLite database. This includes their comments and their posts.

## Install

The PyPI package is `reddit-user-to-sqlite` ([PyPI Link](https://pypi.org/project/reddit-user-to-sqlite/)). Install it globally using [pipx](https://pypa.github.io/pipx/):

```bash
pipx install reddit-user-to-sqlite
```

## Usage

The CLI currently exposes two commands: `user` and `archive`. They allow you to archive recent comments/posts from the API or _all_ posts (as read from a CSV file).

### user

Fetches all comments and posts for a specific user.

```bash
reddit-user-to-sqlite user your_username
reddit-user-to-sqlite user your_username --db my-reddit-data.db
```

#### Params

> Note: the argument order is reversed from most dogsheep packages (which take db_path first). This method allows for use of a default db name, so I prefer it.

1. `username`: a case-insensitive string. The leading `/u/` is optional (and ignored if supplied).
2. (optional) `--db`: the path to a sqlite file, which will be created or updated as needed. Defaults to `reddit.db`.

### archive

Reads the output of a [Reddit GDPR archive](https://support.reddithelp.com/hc/en-us/articles/360043048352-How-do-I-request-a-copy-of-my-Reddit-data-and-information-) and fetches additional info from the Reddit API (where possible). This allows you to store more than 1k posts/comments.

> FYI: this behavior is built with the assumption that the archive that Reddit provides has the same format regardless of if you select `GDPR` or `CCPA` as the request type. But, just to be on the safe side, I recommend selecting `GDPR` during the export process until I'm able to confirm.

#### Params

> Note: the argument order is reversed from most dogsheep packages (which take db_path first). This method allows for use of a default db name, so I prefer it.

1. `archive_path`: the path to the (unzipped) archive directory on your machine. Don't rename/move the files that Reddit gives you.
2. (optional) `--db`: the path to a sqlite file, which will be created or updated as needed. Defaults to `reddit.db`.

## Viewing Data

The resulting SQLite database pairs well with [Datasette](https://datasette.io/), a tool for viewing SQLite in the web. Below is my recommended configuration.

First, install `datasette`:

```bash
pipx install datasette
```

Then, add the recommended plugins (for rendering timestamps and markdown):

```bash
pipx inject datasette datasette-render-markdown datasette-render-timestamps
```

Finally, create a `metadata.json` file with the following:

```json
{
  "databases": {
    "reddit": {
      "tables": {
        "comments": {
          "sort_desc": "timestamp",
          "plugins": {
            "datasette-render-markdown": {
              "columns": ["text"]
            },
            "datasette-render-timestamps": {
              "columns": ["timestamp"]
            }
          }
        },
        "posts": {
          "sort_desc": "timestamp",
          "plugins": {
            "datasette-render-markdown": {
              "columns": ["text"]
            },
            "datasette-render-timestamps": {
              "columns": ["timestamp"]
            }
          }
        },
        "subreddits": {
          "sort": "name"
        }
      }
    }
  }
}
```

Now when you run

```bash
datasette reddit.db --metadata metadata.json
```

You'll get a nice, formatted output:

![](https://cdn.zappy.app/93b1760ab541a8b68c2ee2899be5e079.png)

![](https://cdn.zappy.app/5850a782196d1c7a83a054400c0a5dc4.png)

## Motivation

I got nervous when I saw Reddit's [notification of upcoming API changes](https://old.reddit.com/r/reddit/comments/12qwagm/an_update_regarding_reddits_api/). To ensure I could always access data I created, I wanted to make sure I had a backup in place before anything changed in a big way.

## FAQs

### Why do some of my posts say `[removed]` even though I can see them?

If a post is removed, only the mods and the user who posted it can see its text. Since this tool currently runs without any authentication, those removed posts can't be fetched via the API.

To fetch data about your own removed posts, use the GDPR archive import
This will be fixed in a future release, either by:

### Why is the database missing data returned by the Reddit API?

While most [Dogsheep](https://github.com/dogsheep) projects grab the raw JSON output of their source APIs, Reddit's API has a lot of junk in it. So, I opted for a slimmed down approach.

If there's a field missing that you think would be useful, feel free to open an issue!

### Does this tool refetch old data?

When running the `user` command, yes. It fetches and updates up to 1k each of comments and posts and updates the local copy.

When running the `archive` command, no. To cut down on API requests, it only fetches data about comments/posts that aren't yet in the database (since the archive may include many items).

Both of these may change in the future to be more in line with [Reddit's per-subreddit archiving guidelines](https://www.reddit.com/r/modnews/comments/py2xy2/voting_commenting_on_archived_posts/).

## Development

This section is people making changes to this package.

When in a virtual environment, run the following:

```bash
pip install -e '.[test]'
```

This installs the package in `--edit` mode and makes its dependencies available. You can now run `reddit-user-to-sqlite` to invoke the CLI.

### Running Tests

In your virtual environment, a simple `pytest` should run the unit test suite. You can also run `pyright` for type checking.

### Releasing New Versions

> these notes are mostly for myself (or other contributors)

0. ensure tests pass (`pytest`)
1. install release tooling (`pip install -e '.[release]'`)
2. build the package (`python -m build`)
3. upload the release (`python -m twine upload dist/*`)
   1. give your username as `__token__`
   2. give your password as your stored API key
   3. If you're getting invalid password, verify that `~/.pypirc` is empty
