"""G1-CR - collision-aware revalidation of the frozen G1-C classification.

G1-C v1.0 (``taxonomy_classify.py``) normalized fingerprints into plain dicts:
``out[nq] = ...`` silently kept only the last raw QName when two concepts
canonicalized to the same key, and ``_norm_obj`` did the same for dict keys
inside fingerprints (linkrole keys after ``role_map`` translation).  The
frozen run also resolved ``role_map`` conflicts by insertion-order
last-wins -- reproducible only if the consumer replays Arelle's live dict
order (XML document order), not the sorted evidence JSON.

This module re-runs the same transitions on the same frozen inputs with:

* set-valued normalization: every string maps to a *set* of canonical
  candidates (singleton unless the string is a conflicted to-side linkrole),
* collision-aware dicts: a normalized dict is a list of (keyset, value)
  pairs; entries never overwrite each other,
* three-valued comparison: ``same`` / ``different`` / ``unresolved``.
  Equivalence is claimed only when it holds under *every* admissible
  conflict resolution; a proven difference under every resolution is a real
  difference; anything else fails closed as NOT_COMPARABLE,
* full enumeration of every collision in the evidence artifact.

Categories are the seven frozen ones (G1-CONTRACT v1.0); the machinery that
decides them is what changed.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict

CATEGORIES = (
    "EXACT_EQUIVALENT", "RENAMED_EQUIVALENT", "STRUCTURALLY_CHANGED",
    "NEW", "REMOVED", "NOT_COMPARABLE", "UNKNOWN",
)

STRUCTURAL_FIELDS = (
    "type", "substitutionGroup", "abstract", "nillable", "periodType",
    "balance", "labels", "references", "presentation", "calculation",
    "dimensions",
)

GEN_STAMP_RE = re.compile(r"(circ-4-2017/)\d{4}-\d{2}-01")
GEN_STAMP_TOKEN = "*GEN*"

IDENTITY_FIELDS = ("qname", "namespace", "localname", "entry_points")


# --------------------------------------------------------------------------
# Set-valued normalization
# --------------------------------------------------------------------------

def _norm_scalar(s, ns_map, role_candidates):
    """-> frozenset of canonical candidates for a raw string.

    ``role_candidates``: to-role -> tuple of admissible from-roles (XML
    document order).  A conflicted to-role yields >1 candidate; anything
    else yields a singleton, identical to the frozen ``_norm_str``.
    """
    if s in ns_map:
        bases = (ns_map[s],)
    elif s in role_candidates:
        bases = role_candidates[s]
    else:
        bases = (s,)
    out = set()
    for b in bases:
        t = b
        for to_uri, from_uri in ns_map.items():
            needle = "{%s}" % to_uri
            if needle in t:
                t = t.replace(needle, "{%s}" % from_uri)
        out.add(GEN_STAMP_RE.sub(r"\1" + GEN_STAMP_TOKEN, t))
    return frozenset(out)


def _norm_obj(o, ns_map, role_candidates, merges):
    """Collision-aware normalization.

    Returns a tree where leaves are frozensets of candidate strings and
    dicts are lists of (keyset, value) pairs in original order.  ``merges``
    collects one record per dict position whose distinct raw keys collide:
    {path, canon_keys, raws, identical} (identical = all values equal).
    """
    if isinstance(o, str):
        return _norm_scalar(o, ns_map, role_candidates)
    if isinstance(o, list):
        return [_norm_obj(x, ns_map, role_candidates, merges) for x in o]
    if isinstance(o, dict):
        index = {}
        order = []
        for k, v in o.items():
            nv = _norm_obj(v, ns_map, role_candidates, merges)
            ks = _norm_scalar(k, ns_map, role_candidates)
            gkey = next(iter(ks)) if len(ks) == 1 else ks
            if gkey in index:
                index[gkey].append((k, nv))
            else:
                index[gkey] = [(k, nv)]
                order.append(gkey)
        entries = []
        for gkey in order:
            items = index[gkey]
            if len(items) > 1 and isinstance(gkey, str):
                vals = {json.dumps(v, sort_keys=True, default=str)
                        for _, v in items}
                merges.append({"canon": gkey,
                               "raws": [r for r, _ in items],
                               "identical": len(vals) == 1})
                if len(vals) == 1:          # identical -> safe to merge
                    items = items[:1]
            keyset = (frozenset([gkey]) if isinstance(gkey, str)
                      else gkey)
            for raw, nv in items:
                entries.append((keyset, nv, raw))
        return ("DICT", entries)
    return o


def _prune_empty(o):
    if isinstance(o, tuple) and o[0] == "DICT":
        out = []
        for ks, v, raw in o[1]:
            pv = _prune_empty(v)
            if pv not in ({}, [], None, ("DICT", [])):
                out.append((ks, pv, raw))
        return ("DICT", out)
    if isinstance(o, list):
        return [_prune_empty(x) for x in o]
    return o


def normalize_fp_cr(fp, ns_map=None, role_candidates=None):
    """-> (canon -> [(raw_qname, nfp, merges)], collisions, inner).

    ``collisions``: every top-level QName canon group with >1 raw.
    ``inner``: canon -> inner-dict-key collision records (both identical
    and differing-value merges), for the evidence artifact.
    """
    ns_map = ns_map or {}
    role_candidates = role_candidates or {}
    out = defaultdict(list)
    inner = {}
    for q, c in fp.items():
        merges = []
        nc = _prune_empty(_norm_obj(c, ns_map, role_candidates, merges))
        canon = next(iter(_norm_scalar(q, ns_map, role_candidates)))
        out[canon].append((q, nc, merges))
        if merges:
            inner.setdefault(canon, []).extend(merges)
    collisions = {k: [r for r, _, _ in v] for k, v in out.items()
                  if len(v) > 1}
    return dict(out), collisions, inner


# --------------------------------------------------------------------------
# Three-valued comparison
# --------------------------------------------------------------------------

def _cmp(a, b):
    """'same' | 'different' | 'unresolved' for two normalized values."""
    if isinstance(a, frozenset) and isinstance(b, frozenset):
        if a == b:
            return "same"
        return "unresolved" if a & b else "different"
    if isinstance(a, frozenset) or isinstance(b, frozenset):
        return "different"
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return "different"
        res = "same"
        for x, y in zip(a, b):
            r = _cmp(x, y)
            if r == "different":
                return "different"
            res = res if r == "same" else "unresolved"
        return res
    if isinstance(a, tuple) and isinstance(b, tuple):
        return _cmp_dict(a[1], b[1])
    if isinstance(a, tuple) or isinstance(b, tuple):
        return "different"
    return "same" if a == b else "different"


def _cmp_dict(ea, eb):
    """Compare two (keyset, value, raw) entry lists.

    'same'      equal under every admissible conflict resolution
    'different' provably different under every resolution
    'unresolved' otherwise
    """
    def _has_amb(entries):
        seen = set()
        for ks, _, _ in entries:
            if len(ks) > 1 or ks in seen:
                return True
            seen.add(ks)
        return False

    amb = _has_amb(ea) or _has_amb(eb)
    if len(ea) != len(eb):
        return "unresolved" if amb else "different"
    if not amb:
        ka = sorted(next(iter(ks)) for ks, _, _ in ea)
        kb = sorted(next(iter(ks)) for ks, _, _ in eb)
        if ka != kb:
            return "different"
        va = {next(iter(ks)): v for ks, v, _ in ea}
        res = "same"
        for ks, v, _ in eb:
            r = _cmp(va[next(iter(ks))], v)
            if r == "different":
                return "different"
            res = res if r == "same" else "unresolved"
        return res
    # ambiguous keys: per-entry viability analysis
    keys_a = {k for ks, _, _ in ea for k in ks}
    res = "same"
    covered = set()
    for ks, v, _ in eb:
        matched, has_unres = [], False
        for ks2, v2, _ in ea:
            for k in ks & ks2:
                r = _cmp(v2, v)
                if r == "same":
                    matched.append(k)
                elif r == "unresolved":
                    has_unres = True
        viable = [k for k in ks if k in keys_a]
        if not viable:
            return "different"          # lands outside under every assign.
        if not matched and not has_unres:
            return "different"          # unequal under every assignment
        if len(ks) > 1 or len(set(matched)) != 1 or has_unres:
            res = "unresolved"
        covered.update(matched)
    if covered != {k for ks, _, _ in ea for k in ks}:
        return "different" if not amb else "unresolved"
    return "unresolved" if amb else res


def _field_verdicts(a_fp, b_fp):
    """-> (diffs, unresolved): STRUCTURAL_FIELDS verdicts."""
    diffs, unresolved = [], []
    for f in STRUCTURAL_FIELDS:
        av = _field_get(a_fp, f)
        bv = _field_get(b_fp, f)
        r = _cmp(av, bv)
        if r == "different":
            diffs.append(f)
        elif r == "unresolved":
            unresolved.append(f)
    return diffs, unresolved


def _field_get(nfp, field):
    """Extract field value from a normalized DICT fingerprint."""
    if isinstance(nfp, tuple) and nfp[0] == "DICT":
        for ks, v, _ in nfp[1]:
            if ks == frozenset([field]):
                return v
        return None
    return None


# --------------------------------------------------------------------------
# Concept-level adjudication
# --------------------------------------------------------------------------

def _variants(items):
    """Distinct normalized fingerprints (modulo identity fields) in a canon
    group -> [(rep_nfp, merges, [raws])]."""
    groups = defaultdict(list)
    for raw, nfp, merges in items:
        key = json.dumps(_strip_identity(nfp), sort_keys=True, default=str)
        groups[key].append((raw, nfp, merges))
    return [(v[0][1], v[0][2], [r for r, _, _ in v])
            for v in groups.values()]


def _strip_identity(o):
    if isinstance(o, tuple) and o[0] == "DICT":
        return ("DICT", [(ks, _strip_identity(v)) for ks, v, _ in o[1]
                         if not (len(ks) == 1
                                 and next(iter(ks)) in IDENTITY_FIELDS)])
    if isinstance(o, list):
        return [_strip_identity(x) for x in o]
    return o


def _adjudicate_shared(canon, from_items, to_items, ns_pairs):
    """Classify one canon key present on both sides."""
    fvars = _variants(from_items)
    tvars = _variants(to_items)
    f_raws = [r for r, _, _ in from_items]
    t_raws = [r for r, _, _ in to_items]
    f_merges = [m for _, _, ms in from_items for m in ms]
    t_merges = [m for _, _, ms in to_items for m in ms]
    inner_amb = [m for m in f_merges + t_merges if not m["identical"]]

    if len(fvars) > 1 or len(tvars) > 1:
        return {"classification": "NOT_COMPARABLE",
                "from_qnames": f_raws, "to_qnames": t_raws,
                "from_qname": f_raws[0], "to_qname": t_raws[0],
                "evidence": "ambiguous_canonical_collision",
                "collision": {"canon": canon,
                              "from_variants": len(fvars),
                              "to_variants": len(tvars)}}

    (bf, mf, _), (bt, mt, _) = fvars[0], tvars[0]
    diffs, unresolved = _field_verdicts(bf, bt)
    base = {"from_qnames": f_raws, "to_qnames": t_raws,
            "from_qname": f_raws[0], "to_qname": t_raws[0]}
    if len(f_raws) > 1 or len(t_raws) > 1:
        base["collision"] = {"canon": canon, "identical_variants": True}
    if inner_amb:
        base["inner_collisions"] = inner_amb

    same_raw = set(f_raws) & set(t_raws)
    if diffs:
        return dict(base, classification="STRUCTURALLY_CHANGED",
                    changed_fields=diffs,
                    unresolved_fields=unresolved or None,
                    evidence="fingerprint_diff")
    if unresolved:
        return dict(base, classification="NOT_COMPARABLE",
                    unresolved_fields=unresolved,
                    evidence="ambiguous_inner_collision")
    if same_raw:
        return dict(base, classification="EXACT_EQUIVALENT")
    return dict(base, classification="RENAMED_EQUIVALENT",
                evidence=_rename_evidence(f_raws[0], t_raws[0], ns_pairs))


def _rename_evidence(fq, tq, ns_pairs):
    fns = fq[1:].split("}")[0] if fq.startswith("{") else ""
    tns = tq[1:].split("}")[0] if tq.startswith("{") else ""
    if (fns, tns) in ns_pairs:
        return "arelle_namespace_rename"
    if fns != tns:
        return "declared_generation_stamp_normalization"
    return "identical_structural_fingerprint_modulo_qname"


def _structural_key(nfp):
    return json.dumps(_strip_identity(nfp), sort_keys=True, default=str)


def classify_concepts_cr(from_fp, to_fp, renames=None, ns_map=None,
                         role_candidates=None, ns_pairs=None):
    """Collision-aware classification.  Returns (mapping, meta).

    meta: {"collisions": ..., "inner_collisions": ..., "ambiguous": [...]}
    """
    renames = dict(renames or {})
    ns_map = ns_map or {}
    role_candidates = role_candidates or {}
    ns_pairs = ns_pairs or set()

    n_from, col_from, inner_from = normalize_fp_cr(from_fp)
    n_to, col_to, inner_to = normalize_fp_cr(to_fp, ns_map,
                                           role_candidates)
    out = {}
    meta = {"qname_collisions": {"from": col_from, "to": col_to},
            "inner_collisions": {"from": inner_from, "to": inner_to}}

    from_q, to_q = set(n_from), set(n_to)
    shared, only_from, only_to = (from_q & to_q, from_q - to_q,
                                  to_q - from_q)

    for q in sorted(shared):
        entry = _adjudicate_shared(q, n_from[q], n_to[q], ns_pairs)
        out[_entry_key(q, n_from[q])] = entry

    def _rep(items):
        v = _variants(items)
        return v[0][0] if len(v) == 1 else None

    key_to_new = defaultdict(list)
    for q in sorted(only_to):
        r = _rep(n_to[q])
        if r is not None:
            key_to_new[_structural_key(r)].append(q)
    key_to_old = defaultdict(list)
    for q in sorted(only_from):
        r = _rep(n_from[q])
        if r is not None:
            key_to_old[_structural_key(r)].append(q)

    renamed = set()
    for q in sorted(only_from):
        items = n_from[q]
        fq = items[0][0]
        f_raws = [r for r, _, _ in items]
        rep = _rep(items)
        if rep is None:
            out[fq] = {"classification": "NOT_COMPARABLE",
                       "from_qnames": f_raws, "from_qname": fq,
                       "evidence": "ambiguous_canonical_collision"}
            continue
        cand = key_to_new.get(_structural_key(rep), [])
        if cand:
            if len(cand) == 1 and cand[0] not in renamed:
                t = cand[0]
                t_raws = [r for r, _, _ in n_to[t]]
                ev = _rename_evidence(fq, t_raws[0], ns_pairs)
                if renames.get(fq) in t_raws:
                    ev += "+arelle_versioning_rename"
                out[fq] = {"classification": "RENAMED_EQUIVALENT",
                           "from_qnames": f_raws, "to_qnames": t_raws,
                           "from_qname": fq, "to_qname": t_raws[0],
                           "evidence": ev}
                renamed.add(t)
            else:
                out[fq] = {"classification": "NOT_COMPARABLE",
                           "from_qnames": f_raws, "from_qname": fq,
                           "candidates": sorted(
                               r for c in cand for r, _, _ in n_to[c]),
                           "evidence": "ambiguous_structural_match"}
        elif fq in renames:
            t = renames[fq]
            tn = next(iter(_norm_scalar(t, ns_map, role_candidates)))
            if tn in only_to and tn not in renamed:
                out[fq] = {"classification": "RENAMED_EQUIVALENT",
                           "from_qnames": f_raws, "from_qname": fq,
                           "to_qname": t,
                           "evidence": "arelle_versioning_rename"}
                renamed.add(tn)
            else:
                out[fq] = {"classification": "NOT_COMPARABLE",
                           "from_qnames": f_raws, "from_qname": fq,
                           "evidence": "rename_target_absent_or_consumed"}
        else:
            out[fq] = {"classification": "REMOVED", "from_qnames": f_raws,
                       "from_qname": fq}

    for q in sorted(only_to):
        if q in renamed:
            continue
        items = n_to[q]
        tq = items[0][0]
        t_raws = [r for r, _, _ in items]
        rep = _rep(items)
        if rep is None:
            out[tq] = {"classification": "NOT_COMPARABLE",
                       "to_qnames": t_raws, "to_qname": tq,
                       "evidence": "ambiguous_canonical_collision"}
            continue
        cand = key_to_old.get(_structural_key(rep), [])
        if cand:
            out[tq] = {"classification": "NOT_COMPARABLE",
                       "to_qnames": t_raws, "to_qname": tq,
                       "candidates": sorted(
                           r for c in cand for r, _, _ in n_from[c]),
                       "evidence": "unmatched_structural_candidate"}
        else:
            out[tq] = {"classification": "NEW", "to_qnames": t_raws,
                       "to_qname": tq}

    return out, meta


def _entry_key(canon, items):
    """Mapping key: the raw QName that also exists on the other side when
    known (identity pairing wins), else the first raw in document order."""
    return items[0][0]


def summarize(mapping):
    counts = {c: 0 for c in CATEGORIES}
    for v in mapping.values():
        counts[v["classification"]] += 1
    return counts
