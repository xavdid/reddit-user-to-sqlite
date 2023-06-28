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
3. (optional) `--skip-saved`: a flag for skipping the inclusion of loading saved comments/posts from the archive.

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

Finally, create a `metadata.json` file next to your `reddit.db` with the following:

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

### Why does this post only show 1k recent comments / posts?

Reddit's paging API only shows 1000 items (page 11 is an empty list). If you have more comments (or posts) than than that, you can use the [GDPR archive import feature](#archive) feature to backfill your older data.

### Why are my longer posts truncated in Datasette?

Datasette truncates long text fields by default. You can disable this behavior by using the `truncate_cells_html` flag when running `datasette` ([see the docs](https://docs.datasette.io/en/stable/settings.html#truncate-cells-html)):

```shell
datasette reddit.db --setting truncate_cells_html 0
```

### How do I store a username that starts with `-`?

By default, [click](https://click.palletsprojects.com/en/8.1.x/) (the argument parser this uses) interprets leading dashes on argument as a flag. If you're fetching data for user `-asdf`, you'll get an error saying `Error: No such option: -a`. To ensure the last argument is interpreted positionally, put it after a `--`:

```shell
reddit-user-to-sqlite user -- -asdf
```

### Why do some of my posts say `[removed]` even though I can see them on the web?

If a post is removed, only the mods and the user who posted it can see its text. Since this tool currently runs without any authentication, those removed posts can't be fetched via the API.

To load data about your own removed posts, use the [GDPR archive import feature](#archive).

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

1. Run `just release` while your venv is active
2. paste the stored API key (If you're getting invalid password, verify that `~/.pypirc` is empty)
