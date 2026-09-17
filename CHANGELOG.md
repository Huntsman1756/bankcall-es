# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `bankcall --version`.
- `pl` and `pl-cons` statement aliases (the README documented `pl`; `pnl`
  keeps working).
- `BANKCALL_ROOT` and `BANKCALL_DATA_DIR` environment variables to locate
  the corpus and the generated data outside the repository checkout.
- `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md` and GitHub issue/PR
  templates.
- Ruff lint in CI; Python 3.13 added to the test matrix.

### Changed

- `bankcall` now resolves the corpus and `data/` relative to the current
  directory (or `BANKCALL_ROOT`) instead of the package install location, so
  non-editable installs work correctly.
- Invalid bank codes, periods and `--from`/`--to` ranges now fail with a
  clean error instead of a Python traceback.
- `changes` rejects `--from >= --to`.
- `statement --consolidated` on a raw statement id warns instead of silently
  ignoring the flag.
- `history` resolves legal owners in one query instead of one query per row.
- Ingest fails with a clear message when the frozen corpus or an evidence
  file is missing, instead of a bare `FileNotFoundError`.
- XBRL parsing during ingest explicitly disables external entity resolution
  and network access (was already the lxml default; now enforced).

### Security

- `.opencode/` (local AI-agent configuration, which may contain API keys)
  is now gitignored.
