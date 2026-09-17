"""build_concepts must prefer the corrected G1-CR mapping over the frozen
G1-C v1.0 artifact when both exist (fail-closed corrected labels win)."""
from __future__ import annotations

import json

import pyarrow.parquet as pq

from bankcall import ingest

FROZEN = {"pairs": {"g1__g2": {"mapping": {
    "{ns}A": {"classification": "EXACT_EQUIVALENT"},
    "{ns}B": {"classification": "EXACT_EQUIVALENT"},
}}}}

CORRECTED = {"pairs": {"g1__g2": {"mapping": {
    "{ns}A": {"classification": "EXACT_EQUIVALENT"},
    "{ns}B": {"classification": "NOT_COMPARABLE"},
}}}}

FP = {"generations": {"g1": {"concepts": {}}, "g2": {"concepts": {}}}}


def _evidence(tmp_path, corrected=True):
    ev = tmp_path / "evidence" / "g1"
    ev.mkdir(parents=True)
    (ev / "dts-fingerprints.json").write_text(json.dumps(FP))
    (ev / "concept-mapping.json").write_text(json.dumps(FROZEN))
    if corrected:
        (ev / "g1-cr-mapping.json").write_text(json.dumps(CORRECTED))
    return ev


def test_prefers_corrected_mapping(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest, "EVIDENCE", _evidence(tmp_path))
    data = tmp_path / "data"
    data.mkdir()
    monkeypatch.setattr(ingest, "DATA", data)
    ingest.build_concepts()
    rows = pq.read_table(tmp_path / "data" / "concept_pairs.parquet") \
        .to_pylist()
    assert rows == [{"pair": "g1__g2", "from_qname": "{ns}B",
                     "to_qname": None,
                     "classification": "NOT_COMPARABLE"}]


def test_falls_back_to_frozen_mapping(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest, "EVIDENCE", _evidence(tmp_path,
                                                    corrected=False))
    data = tmp_path / "data"
    data.mkdir()
    monkeypatch.setattr(ingest, "DATA", data)
    ingest.build_concepts()
    rows = pq.read_table(tmp_path / "data" / "concept_pairs.parquet") \
        .to_pylist()
    assert rows == []          # frozen fixture has only EXACT entries
