# Changelog

This project uses [SemVer](https://semver.org/) for versioning. Its public APIs, runtime support, and documented file locations won't change incompatibly outside of major versions (once version 1.0.0 has been released). There may be breaking schema changes in minor releases before 1.0.0 and will be noted in these release notes.

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
