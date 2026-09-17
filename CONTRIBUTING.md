# Contributing

Thanks for your interest in BankCall España. This document explains how to
set up a development environment and what is expected of a contribution.

## Setup

```bash
git clone https://github.com/Huntsman1756/bankcall-es.git
cd bankcall-es
pip install -e ".[dev]"
```

Requires Python >= 3.11.

## Repository layout

| Path | What it is |
| --- | --- |
| `bankcall/` | the product: CLI, ingest, DuckDB/Parquet store |
| `tests/bankcall/` | product tests over a synthetic in-memory corpus |
| `scripts/g1/`, `tests/g1/` | frozen evidence producers that generated the corpus methodology results — provenance code, kept runnable but not actively maintained |
| `g0_acquisition/` | acquisition probe and the frozen corpus (mostly gitignored) |
| `evidence/g1/` | hash-pinned evidence artifacts and reports |
| `methodology/` | the G1 contract and architecture decisions |
| `data/` | generated parquet output of `bankcall ingest` (gitignored) |

## Running the tests

```bash
python -m pytest tests/ -q
```

The product tests build a synthetic corpus in a temporary directory and do
**not** require the real BdE corpus. The `tests/g1/` suite exercises the
frozen evidence scripts and needs the `dev` extra (arelle, requests,
defusedxml).

## Lint

```bash
ruff check .
```

Lint covers the maintained product code (`bankcall/`, `tests/bankcall/`).
The frozen evidence producers are excluded on purpose; do not reformat them.

## Making a change

1. Open an issue first for anything non-trivial.
2. Write a failing test for bugs; add coverage for new behavior.
3. Keep the product code boring: no silent aggregation of XBRL facts, no
   fuzzy concept matching, fail closed on ambiguity.
4. Run `pytest` and `ruff check .` before opening a pull request.

### Invariants that must not be broken

- A bank code is a reporting slot, not a legal entity. Never splice a series
  across a documented ownership transfer.
- Facts are dimensional. Never sum or aggregate across dimension
  combinations implicitly.
- `decimals` is XBRL precision metadata, not a scale. Never rescale reported
  values.
- Parse XML/XBRL with external entity resolution and network access
  disabled.
- Never commit secrets, cookies, session tokens or local captures
  (`g0_acquisition/curl.txt` stays gitignored).

## Corpus data

The frozen corpus is not committed to git (see README → *The frozen
corpus*). Product contributions should not depend on it — the synthetic
fixtures in `tests/bankcall/conftest.py` cover the CLI contract.
