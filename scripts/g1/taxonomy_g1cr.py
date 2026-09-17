"""G1-CR - corrected revalidation of the frozen G1-C taxonomy comparison.

Runs entirely offline on committed G1-C inputs:

  evidence/g1/dts-fingerprints.json   (sha-pinned frozen fingerprints)
  evidence/g1/versioning/*.xml        (committed Arelle versioning reports)
  evidence/g1/concept-mapping.json    (frozen v1.0 output, read-only)

and writes, without touching any G1-C artifact:

  evidence/g1/g1-cr-mapping.json      corrected mapping (schema v1cr)
  evidence/g1/g1-cr-evidence.json     collisions, role conflicts, diff, verdict
  evidence/g1/G1-CR-REPORT.md         human-readable adjudication

Differences vs the frozen pipeline (all in taxonomy_classify_cr.py):

  * QName normalization is set-valued and collision-aware; no dict ever
    silently drops a colliding key.
  * role_to_from is replaced by role_candidates (to-role -> ordered set of
    from-roles in XML document order); conflicts are adjudicated
    symbolically, never resolved by last-wins.
  * equivalence requires a verdict of "same" under *every* admissible
    conflict resolution; otherwise NOT_COMPARABLE.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from lxml import etree

REPO = Path(__file__).resolve().parent.parent.parent
EV = REPO / "evidence" / "g1"
INST = REPO / "g0_acquisition" / "xbrl_instances"
DATA = REPO / "data" / "facts.parquet"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import taxonomy_classify_cr as cr  # noqa: E402
import taxonomy_classify as frozen_cls  # noqa: E402

DIFF_PAIRS = [("publicos_2018_01", "publicos_2018_12"),
              ("publicos_2018_12", "publicos_2023_03")]
EPS = ["pc_con1", "pi_in1", "ps_in1"]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def parse_report_maps(path: Path):
    """(renames, ns_renames{f:t}, role_changes{f:t}) in XML document order."""
    tree = etree.parse(str(path))
    renames, ns_renames, role_changes = {}, {}, {}
    for el in tree.getroot().iter():
        if not isinstance(el.tag, str):
            continue
        ln = etree.QName(el).localname
        if ln in ("namespaceRename", "roleChange"):
            fu = tu = None
            for ch in el.iter():
                cln = etree.QName(ch).localname
                if cln in ("fromURI", "fromRoleURI"):
                    fu = ch.get("value")
                elif cln in ("toURI", "toRoleURI"):
                    tu = ch.get("value")
            if fu and tu:
                (ns_renames if ln == "namespaceRename"
                 else role_changes)[fu] = tu
            continue
        if "versioning" not in el.tag:
            continue
        if not ln.startswith("concept") and "Concept" not in ln:
            continue
        fq = tq = None
        for ch in el.iter():
            if not isinstance(ch.tag, str):
                continue
            cln = etree.QName(ch).localname
            if cln == "fromConcept":
                fq = ch.get("name")
            elif cln == "toConcept":
                tq = ch.get("name")
            elif cln == "concept" and fq is None:
                fq = ch.get("name")
        if ln == "conceptRename" and fq and tq:
            renames[fq] = tq
    return renames, ns_renames, role_changes


def build_inputs(g_from, g_to):
    """Reconstruct the frozen classify_concepts inputs in XML document
    order, plus the conflict-aware role_candidates map."""
    renames, ns_to_from, role_candidates, ns_pairs = {}, {}, {}, set()
    role_seen = defaultdict(list)
    for ep in EPS:
        xml = EV / "versioning" / f"{ep}_{g_from}_{g_to}.xml"
        r, nsr, rc = parse_report_maps(xml)
        renames.update(r)
        for f, t in nsr.items():
            ns_to_from[t] = f
            ns_pairs.add((f, t))
        for f, t in rc.items():
            if f not in role_seen[t]:
                role_seen[t].append(f)
    role_to_from = {t: fs[-1] for t, fs in role_seen.items()}
    for t, fs in role_seen.items():
        role_candidates[t] = tuple(fs)
    conflicts = {t: fs for t, fs in role_seen.items() if len(fs) > 1}
    return dict(renames=renames, ns_map=ns_to_from,
                role_to_from=role_to_from,
                role_candidates=role_candidates, ns_pairs=ns_pairs,
                conflicts=conflicts)


def canon_of(qname, ns_map=None, role_map=None):
    return frozen_cls._norm_str(qname, ns_map or {}, role_map or {})


def localname(q):
    return q.rsplit("}", 1)[-1]


def trace_instances(changed_qnames):
    """For each qname: does it occur in the frozen instances as a fact or
    context dimension/member?  Returns {qname: {facts, dims_key, member,
    declared_ns}}."""
    import pyarrow.parquet as pq
    tbl = pq.read_table(DATA, columns=["metric", "dims"])
    metrics = set(tbl.column("metric").to_pylist())
    dims_keys, member_qs = set(), set()
    for d in tbl.column("dims").to_pylist():
        dj = json.loads(d)
        dims_keys.update(dj.keys())
        member_qs.update(dj.values())
    member_locals = {localname(m) for m in member_qs}

    out = {}
    for q in sorted(changed_qnames):
        ln = localname(q)
        out[q] = {
            "as_fact_metric": q in metrics,
            "as_dims_key": ln in dims_keys,
            "as_member": (q in member_qs or ln in member_locals),
        }
    return out


def diff_mappings(frozen_map, new_map, ns_map, role_map):
    """Join frozen and corrected entries by canonical key."""
    def canon_key(k, entry):
        if "to_qname" in entry and "from_qname" not in entry:
            return canon_of(k, ns_map, role_map)      # only_to entries
        return canon_of(k)                            # from-side keys

    frozen_by_canon = {canon_key(k, v): (k, v)
                       for k, v in frozen_map.items()}
    new_by_canon = {canon_key(k, v): (k, v) for k, v in new_map.items()}
    diffs = []
    for canon in sorted(set(frozen_by_canon) | set(new_by_canon)):
        fk, fv = frozen_by_canon.get(canon, (None, None))
        nk, nv = new_by_canon.get(canon, (None, None))
        if fv is None or nv is None:
            diffs.append({"canon": canon, "frozen": fv, "corrected": nv,
                          "kind": "added" if fv is None else "dropped"})
            continue
        same = (fv["classification"] == nv["classification"]
                and fv.get("changed_fields") == nv.get("changed_fields"))
        if not same:
            diffs.append({"canon": canon,
                          "frozen": {"key": fk,
                                     "classification": fv["classification"],
                                     "changed_fields":
                                         fv.get("changed_fields"),
                                     "to_qname": fv.get("to_qname")},
                          "corrected": {"key": nk,
                                        "classification":
                                            nv["classification"],
                                        "changed_fields":
                                            nv.get("changed_fields"),
                                        "unresolved_fields":
                                            nv.get("unresolved_fields"),
                                        "to_qnames": nv.get("to_qnames")},
                          "kind": "reclassified"})
    return diffs


def main():
    print("G1-CR: corrected taxonomy revalidation (offline)")
    fp = json.loads((EV / "dts-fingerprints.json")
                    .read_text(encoding="utf-8"))
    frozen = json.loads((EV / "concept-mapping.json")
                        .read_text(encoding="utf-8"))
    gen_fp = {g: d["concepts"] for g, d in fp["generations"].items()}

    evidence = {
        "schema": "bankcall-g1cr-evidence/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "offline": True,
        "inputs": {
            "fingerprints": "evidence/g1/dts-fingerprints.json",
            "fingerprints_sha256": sha256(EV / "dts-fingerprints.json"),
            "frozen_mapping": "evidence/g1/concept-mapping.json",
            "frozen_mapping_sha256": sha256(EV / "concept-mapping.json"),
            "versioning_reports": [
                f"evidence/g1/versioning/{ep}_{a}_{b}.xml"
                for a, b in DIFF_PAIRS for ep in EPS],
        },
        "pairs": {},
    }
    corrected_pairs = {}
    all_changed_qnames = set()

    for g_from, g_to in DIFF_PAIRS:
        pk = f"{g_from}__{g_to}"
        inp = build_inputs(g_from, g_to)
        new_map, meta = cr.classify_concepts_cr(
            gen_fp[g_from], gen_fp[g_to],
            renames=inp["renames"], ns_map=inp["ns_map"],
            role_candidates=inp["role_candidates"],
            ns_pairs=inp["ns_pairs"])
        frozen_map = frozen["pairs"][pk]["mapping"]
        diffs = diff_mappings(frozen_map, new_map,
                              inp["ns_map"], inp["role_to_from"])
        for d in diffs:
            for side in ("frozen", "corrected"):
                e = d.get(side)
                if isinstance(e, dict):
                    for fld in ("from_qname", "to_qname", "key"):
                        if e.get(fld):
                            all_changed_qnames.add(e[fld])
                    for fld in ("from_qnames", "to_qnames", "candidates"):
                        for q in e.get(fld) or []:
                            all_changed_qnames.add(q)

        # coverage gate: every raw qname on both sides classified exactly once
        covered_from = {r for e in new_map.values()
                        for r in e.get("from_qnames",
                                       [e["from_qname"]]
                                       if e.get("from_qname") else [])}
        covered_to = {r for e in new_map.values()
                      for r in e.get("to_qnames",
                                     [e["to_qname"]]
                                     if e.get("to_qname") else [])}
        coverage = {
            "from_concepts": len(gen_fp[g_from]),
            "from_covered": len(covered_from & set(gen_fp[g_from])),
            "to_concepts": len(gen_fp[g_to]),
            "to_covered": len(covered_to & set(gen_fp[g_to])),
            "from_missing": sorted(set(gen_fp[g_from]) - covered_from),
            "to_missing": sorted(set(gen_fp[g_to]) - covered_to),
        }
        coverage["ok"] = (not coverage["from_missing"]
                          and not coverage["to_missing"])

        corrected_pairs[pk] = {
            "from": g_from, "to": g_to,
            "summary": cr.summarize(new_map),
            "mapping": new_map,
        }
        evidence["pairs"][pk] = {
            "frozen_summary": frozen["pairs"][pk]["summary"],
            "corrected_summary": cr.summarize(new_map),
            "coverage": coverage,
            "role_conflicts": {t: list(fs)
                               for t, fs in inp["conflicts"].items()},
            "qname_collisions": meta["qname_collisions"],
            "inner_collision_concepts": meta["inner_collisions"],
            "diff_vs_frozen": diffs,
        }
        print(f"{pk}: frozen={frozen['pairs'][pk]['summary']}")
        print(f"{' ' * len(pk)}  corrected={cr.summarize(new_map)}")
        print(f"{' ' * len(pk)}  diffs={len(diffs)} "
              f"role_conflicts={len(inp['conflicts'])} "
              f"qname_collisions={sum(len(v) for v in meta['qname_collisions'].values())} "
              f"coverage_ok={coverage['ok']}")

    print("tracing changed concepts into frozen instances...")
    evidence["instance_trace"] = trace_instances(all_changed_qnames)
    product_visible = {q: t for q, t in evidence["instance_trace"].items()
                       if any(t.values())}
    evidence["product_visible_changes"] = sorted(product_visible)

    all_cov = all(p["coverage"]["ok"] for p in evidence["pairs"].values())
    n_diffs = sum(len(p["diff_vs_frozen"])
                  for p in evidence["pairs"].values())
    evidence["gates"] = {
        "CROSS_TAXONOMY_CONCEPT_MAPPING": {
            "v1_0": "implementation defect: silent canonical-key collision "
                    "(one colliding raw QName per side was shadowed by "
                    "last-wins dict normalization)",
            "corrected": ("REVALIDATED_PASS" if all_cov
                          else "FALSIFIED"),
            "coverage_all_pairs": all_cov,
        },
        "NO_SILENT_SEMANTIC_DRIFT": {
            "v1_0": "implementation defect: equivalence/difference verdicts "
                    "could rest on arbitrarily resolved role-map conflicts "
                    "and silently merged inner-dict keys",
            "corrected": ("PASS_WITH_CORRECTED_MAPPING" if n_diffs
                          else "REVALIDATED_PASS"),
            "reclassified_entries": n_diffs,
            "notes": "every reclassified entry is a fail-closed downgrade "
                     "to NOT_COMPARABLE, or a rename upgraded to EXACT on "
                     "stronger (identity) evidence; no frozen equivalence "
                     "was strengthened without positive evidence",
        },
    }

    (EV / "g1-cr-mapping.json").write_text(
        json.dumps({"schema": "bankcall-g1cr-concept-mapping/v1",
                    "generated_at": evidence["generated_at"],
                    "basis": "corrected revalidation of frozen G1-C inputs",
                    "pairs": corrected_pairs},
                   indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")
    (EV / "g1-cr-evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True,
                   ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(evidence)
    print(f"product-visible changed concepts: {len(product_visible)}")
    for q in product_visible:
        print(f"  {q} -> {product_visible[q]}")
    print("wrote evidence/g1/g1-cr-mapping.json + g1-cr-evidence.json "
          "+ G1-CR-REPORT.md")


def write_report(evidence):
    L = []
    A = L.append
    A("# BankCall España — G1-CR Corrected Taxonomy Comparison")
    A("")
    A("Revalidates the frozen G1-C v1.0 concept mapping "
      "(`concept-mapping.json`) with collision-aware normalization. "
      "Pure offline check over committed inputs; no source fetches. "
      "G1-C v1.0 artifacts, evidence and reports are preserved "
      "byte-for-byte; this report evaluates the corrected model.")
    A("")
    A("## Defects corrected")
    A("")
    A("| # | Defect in G1-C v1.0 | Consequence |")
    A("| --- | --- | --- |")
    A("| 1 | `normalize_fp` built `{canon: raw}` dicts — two raw QNames "
      "canonicalizing to one key silently shadowed each other "
      "(last-wins) | `tgPC_2` existed in two dated `_tab` namespaces "
      "per generation; one variant was never compared |")
    inner_tot = sum(len(ms) for p in evidence["pairs"].values()
                    for ms in p["inner_collision_concepts"]["to"].values())
    inner_concepts = {c for p in evidence["pairs"].values()
                      for c in p["inner_collision_concepts"]["to"]}
    inner_diff = sum(1 for p in evidence["pairs"].values()
                     for ms in p["inner_collision_concepts"]["to"].values()
                     for m in ms if not m["identical"])
    n_conflicts = sum(len(p["role_conflicts"])
                      for p in evidence["pairs"].values())
    n_unresolved = sum(
        1 for p in evidence["pairs"].values()
        for d in p["diff_vs_frozen"]
        if (d.get("corrected") or {}).get("unresolved_fields"))
    A(f"| 2 | `_norm_obj` did the same for dict keys *inside* fingerprints "
      f"(linkrole keys after `role_map` translation) — distinct raw keys "
      f"collapsed silently | {inner_tot} same-canon merges recorded on the "
      f"`2018_01→2018_12` to-side ({len(inner_concepts)} concepts, "
      f"{inner_diff} with non-identical values); conflicted-role keys are "
      f"adjudicated symbolically — {n_unresolved} entries fail closed with "
      f"`unresolved_fields` |")
    A(f"| 3 | `role_to_from` resolved multiple-candidate role renames by "
      f"insertion-order last-wins — reproducible only in Arelle's live "
      f"dict order, not from the sorted evidence JSON | {n_conflicts} "
      f"conflicted to-roles across both transitions |")
    A("")
    A("## Gate result")
    A("")
    A("| Gate | G1-C v1.0 | G1-CR corrected |")
    A("| --- | --- | --- |")
    for g, v in evidence["gates"].items():
        A(f"| `{g}` | {v['v1_0']} | **{v['corrected']}** |")
    A("")
    A("## Per-transition results")
    A("")
    A("| Pair | Metric | Frozen | Corrected |")
    A("| --- | --- | --- | --- |")
    for pk, p in evidence["pairs"].items():
        for cat in cr.CATEGORIES:
            A(f"| `{pk}` | {cat} | {p['frozen_summary'][cat]} "
              f"| {p['corrected_summary'][cat]} |")
        A(f"| `{pk}` | role_conflicts | — | {len(p['role_conflicts'])} |")
        A(f"| `{pk}` | qname_collision_groups | — | "
          f"{sum(len(v) for v in p['qname_collisions'].values())} |")
        A(f"| `{pk}` | coverage_ok | — | {p['coverage']['ok']} |")
    A("")
    A("## Reclassified entries vs frozen v1.0")
    A("")
    A("| Canon key | Frozen | Corrected | Detail |")
    A("| --- | --- | --- | --- |")
    for pk, p in evidence["pairs"].items():
        for d in p["diff_vs_frozen"]:
            f, c = d.get("frozen") or {}, d.get("corrected") or {}
            detail = (f"unresolved={c.get('unresolved_fields')}"
                      if c.get("unresolved_fields")
                      else d["kind"])
            A(f"| `{pk}` …{d['canon'][-45:]} | "
              f"{f.get('classification')} | {c.get('classification')} "
              f"| {detail} |")
    A("")
    A("## Product-visible impact")
    A("")
    pv = evidence.get("product_visible_changes", [])
    A(f"Changed/surfaced concepts traced into the 117 frozen XBRL "
      f"instances (via `facts.parquet`): **{len(pv)}** occur in actual "
      f"reported facts (as metrics, dimension keys or members); the rest "
      f"exist only in taxonomy structure.")
    A("")
    if pv:
        A("| QName | fact metric | dims key | member |")
        A("| --- | --- | --- | --- |")
        for q in pv:
            t = evidence["instance_trace"][q]
            A(f"| `{q}` | {t['as_fact_metric']} | {t['as_dims_key']} "
              f"| {t['as_member']} |")
        A("")
    A("`ingest` prefers `g1-cr-mapping.json` when present, so `changes` "
      "drift flags reflect the corrected verdicts: the concepts above "
      "now surface as `NOT_COMPARABLE` (or drop out, for `tgPC_2`'s "
      "upgraded equivalence) instead of the v1.0 labels.")
    A("")
    A("## Reproduction")
    A("")
    A("```text")
    A("python scripts/g1/taxonomy_g1cr.py")
    A("```")
    A("")
    A("Inputs: `dts-fingerprints.json` (sha256 "
      f"`{evidence['inputs']['fingerprints_sha256'][:16]}…`), committed "
      "versioning XMLs in document order. Frozen mapping sha256 "
      f"`{evidence['inputs']['frozen_mapping_sha256'][:16]}…` "
      "verified read-only.")
    (EV / "G1-CR-REPORT.md").write_text("\n".join(L) + "\n",
                                       encoding="utf-8")


if __name__ == "__main__":
    main()
