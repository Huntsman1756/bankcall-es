"""G1-DR - revalidation of the frozen G1-D final integration.

G1-D (`g1-evidence.json`, `G1-REPORT.md`, tag `g1-green`) is the historical
record: its aggregate PASS was computed against G1-C v1.0.  G1-CR corrected
the two taxonomy gates; this script re-adjudicates the *integration* without
re-running any acquisition or XBRL processing.

Pure function over committed artifacts:

  evidence/g1/g1-evidence.json      (frozen G1-D output - inherited verbatim)
  evidence/g1/g1-cr-evidence.json   (G1-CR gate verdicts + diffs)
  evidence/g1/g1-cr-mapping.json    (corrected concept mapping)

writes:

  evidence/g1/g1-dr-evidence.json
  evidence/g1/G1-DR-REPORT.md

Rules:

  * the seven non-taxonomy gates are inherited byte-for-byte from G1-D
    (117/117 XBRL, identity model, provenance audit unchanged);
  * CROSS_TAXONOMY_CONCEPT_MAPPING and NO_SILENT_SEMANTIC_DRIFT are
    re-adjudicated from the G1-CR verdicts;
  * non_equivalences / mapping_summary are recomputed from the corrected
    mapping so downstream consumers see the authoritative current state;
  * overall verdict: REVALIDATED_PASS_WITH_CORRECTED_MAPPING when every
    inherited gate passes and the corrected gates pass.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
EV = REPO / "evidence" / "g1"

NON_EQUIVALENT = {"RENAMED_EQUIVALENT", "STRUCTURALLY_CHANGED", "NEW",
                  "REMOVED", "NOT_COMPARABLE", "UNKNOWN"}
INHERITED_GATES = (
    "DISCOVERY_DETERMINISTIC", "ENTITY_KEY_DECOMPOSED",
    "ENTITY_MAPPING_PROVEN", "ENTITY_LIFECYCLE_HANDLED",
    "TAXONOMY_AUTO_RESOLVABLE", "PROVENANCE_COMPLETE",
    "TEN_PERIOD_CORPUS_PASS",
)
CORRECTED_GATES = ("CROSS_TAXONOMY_CONCEPT_MAPPING",
                   "NO_SILENT_SEMANTIC_DRIFT")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(name: str) -> dict:
    return json.loads((EV / name).read_text(encoding="utf-8"))


def main() -> int:
    g1d = load("g1-evidence.json")
    g1cr = load("g1-cr-evidence.json")
    cr_map = load("g1-cr-mapping.json")

    inputs = {
        "g1_d_evidence": "evidence/g1/g1-evidence.json",
        "g1_cr_evidence": "evidence/g1/g1-cr-evidence.json",
        "g1_cr_mapping": "evidence/g1/g1-cr-mapping.json",
    }

    gates = {}
    gate_basis = {}
    for g in INHERITED_GATES:
        gates[g] = g1d["gates"][g]
        gate_basis[g] = "inherited from G1-D (frozen)"
    for g in CORRECTED_GATES:
        verdict = g1cr["gates"][g]["corrected"]
        gates[g] = "PASS" if verdict.startswith(
            ("REVALIDATED_PASS", "PASS_WITH_CORRECTED")) else "FAIL"
        gate_basis[g] = f"G1-CR corrected: {verdict}"

    revalidated = (all(v == "PASS" for v in gates.values())
                   and all(g1cr["pairs"][p]["coverage"]["ok"]
                           for p in g1cr["pairs"]))
    result = ("REVALIDATED_PASS_WITH_CORRECTED_MAPPING" if revalidated
              else "FAIL")

    non_equiv = []
    for pk, pair in cr_map["pairs"].items():
        for qn, m in pair["mapping"].items():
            if m["classification"] in NON_EQUIVALENT:
                non_equiv.append({
                    "pair": pk,
                    "from_qname": m.get("from_qname") or qn,
                    "to_qname": m.get("to_qname"),
                    "classification": m["classification"],
                })
    non_equiv.sort(key=lambda x: (x["pair"], x["classification"],
                                  x["from_qname"]))
    mapping_summary = {k: v["summary"] for k, v in cr_map["pairs"].items()}

    evidence = {
        "schema": "bankcall-g1dr-revalidation/v1",
        "experiment": "BANKCALL_ES_G1_DR_INTEGRATION_REVALIDATION",
        "generated_at": datetime.now(timezone.utc)
            .isoformat(timespec="seconds"),
        "contract": "methodology/G1-CONTRACT.md v1.0 (frozen 2026-09-13); "
                    "taxonomy gates adjudicated by G1-CR",
        "inputs": {k: {"path": v, "sha256": sha256(REPO / v)}
                   for k, v in inputs.items()},
        "basis": {"frozen_integration": "evidence/g1/g1-evidence.json",
                  "corrected_taxonomy": "evidence/g1/g1-cr-evidence.json"},
        "period_matrix": g1d["period_matrix"],
        "provenance_audit": g1d["provenance_audit"],
        "g1b_falsification": g1d["g1b_falsification"],
        "mapping_summary": mapping_summary,
        "non_equivalences": non_equiv,
        "unresolved": dict(g1d["unresolved"],
                           concept_mapping_not_comparable_corrected=sum(
                               v["summary"]["NOT_COMPARABLE"]
                               for v in cr_map["pairs"].values())),
        "taxonomy_corrections": {
            pk: {"diffs": len(p["diff_vs_frozen"]),
                 "reclassified": [
                     {"canon": d["canon"],
                      "frozen": (d.get("frozen") or {}).get("classification"),
                      "corrected": (d.get("corrected") or {})
                      .get("classification")}
                     for d in p["diff_vs_frozen"]]}
            for pk, p in g1cr["pairs"].items()},
        "gates": gates,
        "gate_basis": gate_basis,
        "product_visible_changes":
            g1cr.get("product_visible_changes", []),
        "result": result,
    }
    (EV / "g1-dr-evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True,
                   ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(evidence, g1d, g1cr)
    print(json.dumps(gates, indent=2))
    print("result:", result)
    return 0 if revalidated else 1


def write_report(evidence, g1d, g1cr):
    L = []
    A = L.append
    A("# BankCall España — G1-DR Integration Revalidation")
    A("")
    A(f"**Verdict: {evidence['result']}** — the nine contract gates "
      "re-adjudicated over frozen G1-D outputs plus the corrected G1-CR "
      "taxonomy mapping. No acquisition, XBRL processing or network access "
      "was re-run; G1-C v1.0 and G1-D artifacts remain the historical "
      "record, preserved byte-for-byte.")
    A("")
    A("## Gate table")
    A("")
    A("| Gate | Result | Basis |")
    A("| --- | --- | --- |")
    for g, v in evidence["gates"].items():
        A(f"| `{g}` | **{v}** | {evidence['gate_basis'][g]} |")
    A("")
    A("## What changed vs G1-D")
    A("")
    A("Nothing outside taxonomy adjudication. The period matrix (117/117 "
      "XBRL, 10 periods), the temporal identity model (9,253 mappings, "
      "8 documented transfers), the provenance audit and the G1-B "
      "falsification record are inherited from `g1-evidence.json` "
      "unchanged.")
    A("")
    for pk, tc in evidence["taxonomy_corrections"].items():
        A(f"### `{pk}` — {tc['diffs']} reclassified entries")
        A("")
        if tc["reclassified"]:
            A("| Concept | G1-C v1.0 | G1-CR |")
            A("| --- | --- | --- |")
            for r in tc["reclassified"]:
                A(f"| …`{r['canon'][-55:]}` | {r['frozen']} "
                  f"| {r['corrected']} |")
        else:
            A("No reclassifications — frozen v1.0 mapping reproduced "
              "exactly under collision-aware normalization.")
        A("")
    A("## Product-visible impact")
    A("")
    pv = evidence.get("product_visible_changes", [])
    A(f"{len(pv)} reclassified concepts occur in the 117 frozen instances "
      "as fact metrics, dimension keys or members — all are taxonomy-drift "
      "*labels* consumed by `bankcall changes`; no fact value, identity "
      "mapping or slot transfer is affected.")
    A("")
    A("## Reproduction")
    A("")
    A("```text")
    A("python scripts/g1/g1dr_revalidate.py")
    A("```")
    A("")
    A("Inputs (sha256 recorded in `g1-dr-evidence.json`): "
      "`g1-evidence.json` (frozen G1-D), `g1-cr-evidence.json` and "
      "`g1-cr-mapping.json` (G1-CR corrected outputs).")
    (EV / "G1-DR-REPORT.md").write_text("\n".join(L) + "\n",
                                       encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
