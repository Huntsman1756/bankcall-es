# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Dependabot configuration for Python and GitHub Actions dependencies.
- CodeQL static analysis for Python on pull requests, `main`, and a weekly
  schedule.
- GitHub issue-template configuration that directs security reports to the
  private vulnerability-reporting flow.

### Changed

- CI now uses least-privilege `contents: read`, concurrency cancellation,
  timeouts, SHA-pinned current GitHub Actions, and validates built wheel/sdist
  metadata with `python -m build` + `twine check`.
- README now distinguishes frozen G1-C/G1-D evidence from the authoritative
  corrected G1-CR/G1-DR layers and documents the complete reconstruction
  sequence.
- Package metadata now links directly to the changelog and security policy.

## [0.1.1] - 2026-09-17

### Added

- **G1-CR**: corrected, collision-aware revalidation of the frozen G1-C
  taxonomy mapping (`scripts/g1/taxonomy_classify_cr.py`,
  `scripts/g1/taxonomy_g1cr.py`; evidence in `evidence/g1/g1-cr-*.json`
  and `evidence/g1/G1-CR-REPORT.md`). G1-C v1.0 artifacts are preserved
  byte-for-byte. Corrected verdicts: 24 `STRUCTURALLY_CHANGED` +
  1 `EXACT_EQUIVALENT` (`REC`) fail-closed to `NOT_COMPARABLE`, and
  `tgPC_2` upgraded to `EXACT_EQUIVALENT` on identity evidence.
- **G1-DR**: revalidation of the frozen G1-D integration
  (`scripts/g1/g1dr_revalidate.py`; `evidence/g1/g1-dr-evidence.json`,
  `evidence/g1/G1-DR-REPORT.md`). Verdict:
  `REVALIDATED_PASS_WITH_CORRECTED_MAPPING` — the seven non-taxonomy
  gates are inherited byte-for-byte from G1-D; the two taxonomy gates
  are adjudicated by G1-CR.
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
- `ingest` prefers `evidence/g1/g1-cr-mapping.json` (corrected mapping)
  over the frozen `concept-mapping.json` when present, so `changes`
  drift flags reflect the fail-closed G1-CR verdicts.
- Ingest fails with a clear message when the frozen corpus or an evidence
  file is missing, instead of a bare `FileNotFoundError`.
- XBRL parsing during ingest explicitly disables external entity resolution
  and network access (was already the lxml default; now enforced).

### Security

- `.opencode/` (local AI-agent configuration, which may contain API keys)
  is now gitignored.
