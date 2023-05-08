# reddit-user-to-sqlite

Stores all the content from a specific user in a SQLite database. This includes their comments and their posts.

## Install

The PyPI package is `reddit-user-to-sqlite` ([PyPI Link](https://pypi.org/project/reddit-user-to-sqlite/)). Install it globally using [pipx](https://pypa.github.io/pipx/):

```bash
pipx install reddit-user-to-sqlite
```

## Usage

The CLI currently exposes a single command: `user`. An `archive` command is planned.

### user

Fetches all comments and posts for a specific user.

```bash
reddit-user-to-sqlite user your_username
reddit-user-to-sqlite user your_username --db my-reddit-data.db
```

#### Params

> Note: the argument order is reversed from most dogsheep packages (which take db_path first). This method allows for use of a default db name, so I prefer it.

1. `username`: a case-insensitive string. The leading `/u/` is optional (and ignored if supplied)
2. (optional) `--db`: the path to a sqlite file, which will be created or updated as needed. Defaults to `reddit.db`.

### A Note on Stored Data

While most [Dogsheep](https://github.com/dogsheep) projects grab the raw JSON output of their source APIs, Reddit's API has a lot of junk in it. So, I opted for a slimmed down approach.

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

## FAQs

### Why do some of my posts say `[removed]` even though I can see them?

If a post is removed, only the mods and the user who posted it can see its text. Since this tool currently runs without any authentication, those removed posts can't be fetched via the API.

This will be fixed in a future release, either by:

- (planned) being able to pull data from a GDPR archive
- (maybe) adding support for authentication, so you can see your own posts
