"""DuckDB access layer over the ingested Parquet tables.

Layout is resolved at import time:

  BANKCALL_ROOT      root of a corpus checkout (g0_acquisition/, evidence/);
                     defaults to the current working directory.
  BANKCALL_DATA_DIR  where data/*.parquet lives; defaults to
                     $BANKCALL_ROOT/data.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import duckdb

ROOT = Path(os.environ.get("BANKCALL_ROOT", ".")).resolve()
DATA = Path(os.environ.get("BANKCALL_DATA_DIR", str(ROOT / "data")))

PERIODS = ["201803", "201809", "201812", "202012", "202103",
           "202109", "202212", "202303", "202506", "202606"]
PERIOD_LABELS = dict(zip(PERIODS,
    ["2018Q1", "2018Q3", "2018Q4", "2020Q4", "2021Q1",
     "2021Q3", "2022Q4", "2023Q1", "2025Q2", "2026Q2"]))

STATEMENT_ALIASES = {
    "balance": ["2701", "2702", "2703"],
    "balance-cons": ["6611", "6612", "6613"],
    "pnl": ["4701", "4702"],
    "pl": ["4701", "4702"],
    "pnl-cons": ["6602", "6603"],
    "pl-cons": ["6602", "6603"],
    "equity": ["6794"],
    "equity-cons": ["6604"],
    "cashflow": ["7701"],
    "cashflow-cons": ["6605"],
    "branches-eee": ["2310"],
}


def norm_period(value: str) -> str:
    """Accept '2026Q2', '202606', or a bare year ('2020' -> first that-year
    corpus period)."""
    v = value.strip().upper().replace("-", "")
    if v in PERIODS:
        return v
    if v in PERIOD_LABELS.values():
        return next(p for p, l in PERIOD_LABELS.items() if l == v)
    if v.isdigit() and len(v) == 4:
        cand = [p for p in PERIODS if p.startswith(v)]
        if cand:
            return cand[0]
    raise ValueError(f"period '{value}' not in frozen corpus "
                     f"({', '.join(PERIOD_LABELS.values())})")


def norm_code(value: str) -> str:
    """Normalize a bank code or raw SIFDIFU key to a 4-digit bank code."""
    v = value.strip().upper()
    if "(" in v:
        v = v.split("(", 1)[0]
    v = v.removeprefix("ES")
    v = v.zfill(4)
    if not re.fullmatch(r"\d{4}", v):
        raise ValueError(f"invalid bank code '{value}' "
                         "(expected 4 digits, e.g. '0049')")
    return v


def connect() -> duckdb.DuckDBPyConnection:
    for name in ("facts", "slots", "transfers", "concepts", "concept_pairs"):
        if not (DATA / f"{name}.parquet").exists():
            raise SystemExit(
                f"data/{name}.parquet missing — run `bankcall ingest` first")
    con = duckdb.connect()
    for p in DATA.glob("*.parquet"):
        lit = str(p).replace("\\", "/").replace("'", "''")
        con.execute(
            f"CREATE VIEW {p.stem} AS SELECT * FROM read_parquet('{lit}')")
    return con
