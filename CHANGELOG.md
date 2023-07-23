# Changelog

This project uses [SemVer](https://semver.org/) for versioning. Its public APIs, runtime support, and documented file locations won't change incompatibly outside of major versions (once version 1.0.0 has been released). There may be breaking schema changes in minor releases before 1.0.0 and will be noted in these release notes.

## 0.4.2

_released `2023-07-23`_

- handle [new rate limiting](https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki) more gracefully (fixes [#23](https://github.com/xavdid/reddit-user-to-sqlite/issues/23) via [#24](https://github.com/xavdid/reddit-user-to-sqlite/pull/24) (by [@piyh](https://github.com/piyh)) and TBD);

## 0.4.1

_released `2023-06-25`_

- specify `utf-8` as the default character encoding, improving windows compatibility (fixes [#10](https://github.com/xavdid/reddit-user-to-sqlite/issues/10))

## 0.4.0

_released `2023-06-14`_

- the `archive` command includes saved posts / comments by default (in their own table). Use the `--skip-saved` flag to opt out of this behavior ([#16](https://github.com/xavdid/reddit-user-to-sqlite/pull/16))
- add support for Python 3.9, verified using `tox` ([#19](https://github.com/xavdid/reddit-user-to-sqlite/pull/19))
- add `num_awards` column to comments (was omitted by accident) ([#18](https://github.com/xavdid/reddit-user-to-sqlite/pull/18))
- added support for disabling the progress bars via the `DISABLE_PROGRESS` env var. Set it to `1` to disable progress bars ([#16](https://github.com/xavdid/reddit-user-to-sqlite/pull/16))

## 0.3.1

_released `2023-06-09`_

- remove dependency on 3.11 by adding `typing-extensions` ([#3](https://github.com/xavdid/reddit-user-to-sqlite/pull/3) by [@changlinli](https://github.com/changlinli))

## 0.3.0

_released `2023-05-23`_

- adds the `archive` command, which loads data from a Reddit GDPR archive ([#1](https://github.com/xavdid/reddit-user-to-sqlite/pull/1))
- added more help text to both commands
- provide more info about the counts of comments/posts saved/updated

## 0.2.0

_released `2023-05-07`_

- improves the `user` command to also fetch submitted posts and store them in a corresponding `posts` table.

## 0.1.0

_released `2023-05-06`_

- Initial public release!
- Adds the `user` command, which currently only fetches comments
