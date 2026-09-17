"""G1-CR corrected classifier: collision-aware normalization and
three-valued comparison.  Guards the defects found in frozen G1-C v1.0:
silent QName/dict-key shadowing and order-dependent role_map conflicts.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent
                     / "scripts" / "g1"))
import taxonomy_classify_cr as cr  # noqa: E402

NS = "http://t/ns"
ROLE = "http://t/role"


def _fp(local, **kw):
    base = {"type": "{http://www.xbrl.org/2003/instance}monetaryItemType",
            "substitutionGroup": "{http://www.xbrl.org/2003/instance}item",
            "abstract": False, "nillable": True, "periodType": "instant",
            "balance": None, "labels": [], "references": [],
            "presentation": {}, "calculation": {}, "dimensions": {},
            "qname": f"{{{NS}}}{local}", "namespace": NS,
            "localname": local, "entry_points": ["ep.xsd"]}
    base.update(kw)
    return base


def test_no_collision_matches_frozen_shape():
    fp = {"{%s}a" % NS: _fp("a"), "{%s}b" % NS: _fp("b")}
    m, meta = cr.classify_concepts_cr(fp, dict(fp))
    assert cr.summarize(m)["EXACT_EQUIVALENT"] == 2
    assert meta["qname_collisions"] == {"from": {}, "to": {}}


def test_qname_collision_identical_variants_is_exact_not_silent():
    """tgPC_2 regression: two dated-namespace raws of one canon key with
    identical structure must be adjudicated once, with both raws kept."""
    a, b = "{%s/a_2018}x" % NS, "{%s/b_2018}x" % NS
    stamp = cr.GEN_STAMP_RE
    # force collision via declared canonicalization on the dated segment
    a = a.replace("/a_2018", "/circ-4-2017/2018-01-01")
    b = b.replace("/b_2018", "/circ-4-2017/2018-12-01")
    fa = _fp("x", qname=a, namespace=a[1:].split("}")[0],
             entry_points=["e1.xsd", "e2.xsd"])
    fb = _fp("x", qname=b, namespace=b[1:].split("}")[0],
             entry_points=["e1.xsd"])
    m, meta = cr.classify_concepts_cr({a: fa}, {a: fa, b: fb})
    (e,) = m.values()
    assert e["classification"] == "EXACT_EQUIVALENT"      # identity pair A↔A
    assert sorted(e["to_qnames"]) == sorted([a, b])
    assert meta["qname_collisions"]["to"]               # collision recorded
    assert stamp is not None


def test_qname_collision_differing_variants_fail_closed():
    a = "{%s/circ-4-2017/2018-01-01}x" % NS
    b = "{%s/circ-4-2017/2018-12-01}x" % NS
    fa = _fp("x", qname=a, namespace=a[1:].split("}")[0])
    fb = _fp("x", qname=b, namespace=b[1:].split("}")[0],
             balance="debit")
    m, _ = cr.classify_concepts_cr({a: fa}, {a: fa, b: fb})
    (e,) = m.values()
    assert e["classification"] == "NOT_COMPARABLE"
    assert e["evidence"] == "ambiguous_canonical_collision"


def test_inner_dict_collision_identical_values_merge_safely():
    """Two raw dict keys canonicalizing to one key with identical values
    must merge without data loss or a false unresolved."""
    dim_from = {"dimensionedBy": {"%s/r1" % ROLE: ["{d}x"]}}
    dim_to = {"dimensionedBy": {"%s/2018-01/r1" % ROLE: ["{d}x"],
                                "%s/2018-12/r1" % ROLE: ["{d}x"]}}
    # both to-keys canonicalize to the same GEN_STAMP key? force via map
    role_c = {"%s/2018-12/r1" % ROLE: ("%s/r1" % ROLE,)}
    ns_map = {"%s/2018-01/r1" % ROLE: "%s/r1" % ROLE}
    f = {"{%s}c" % NS: _fp("c", dimensions=dim_from)}
    t = {"{%s}c" % NS: _fp("c", dimensions=dim_to)}
    m, meta = cr.classify_concepts_cr(f, t, ns_map=ns_map,
                                      role_candidates=role_c)
    (e,) = m.values()
    assert e["classification"] == "EXACT_EQUIVALENT"


def test_inner_dict_collision_differing_values_unresolved():
    dim_from = {"dimensionedBy": {"%s/r1" % ROLE: ["{d}x"]}}
    dim_to = {"dimensionedBy": {"%s/2018-01/r1" % ROLE: ["{d}x"],
                                "%s/2018-12/r1" % ROLE: ["{d}y"]}}
    role_c = {"%s/2018-12/r1" % ROLE: ("%s/r1" % ROLE,)}
    ns_map = {"%s/2018-01/r1" % ROLE: "%s/r1" % ROLE}
    f = {"{%s}c" % NS: _fp("c", dimensions=dim_from)}
    t = {"{%s}c" % NS: _fp("c", dimensions=dim_to)}
    m, _ = cr.classify_concepts_cr(f, t, ns_map=ns_map,
                                   role_candidates=role_c)
    (e,) = m.values()
    assert e["classification"] == "NOT_COMPARABLE"
    assert e["unresolved_fields"] == ["dimensions"]


def test_conflicted_role_makes_equivalence_unprovable():
    """REC regression: a to-side linkrole with two distinct from-candidates
    cannot prove equality under every resolution -> NOT_COMPARABLE."""
    dim_from = {"dimensionedBy": {"%s/A" % ROLE: ["{d}x"]}}
    dim_to = {"dimensionedBy": {"%s/T" % ROLE: ["{d}x"]}}
    role_c = {"%s/T" % ROLE: ("%s/A" % ROLE, "%s/B" % ROLE)}
    f = {"{%s}c" % NS: _fp("c", dimensions=dim_from)}
    t = {"{%s}c" % NS: _fp("c", dimensions=dim_to)}
    m, _ = cr.classify_concepts_cr(f, t, role_candidates=role_c)
    (e,) = m.values()
    assert e["classification"] == "NOT_COMPARABLE"
    assert e["unresolved_fields"] == ["dimensions"]


def test_conflicted_role_proven_different_is_struct_changed():
    dim_from = {"dimensionedBy": {"%s/A" % ROLE: ["{d}x"],
                                  "%s/B" % ROLE: ["{d}y"]}}
    dim_to = {"dimensionedBy": {"%s/T" % ROLE: ["{d}x"],
                                "%s/U" % ROLE: ["{d}z"]}}
    role_c = {"%s/T" % ROLE: ("%s/A" % ROLE, "%s/Q" % ROLE),
              "%s/U" % ROLE: ("%s/B" % ROLE, "%s/W" % ROLE)}
    f = {"{%s}c" % NS: _fp("c", dimensions=dim_from)}
    t = {"{%s}c" % NS: _fp("c", dimensions=dim_to)}
    m, _ = cr.classify_concepts_cr(f, t, role_candidates=role_c)
    (e,) = m.values()
    # under every assignment T->A/Q, U->B/W the dicts differ
    assert e["classification"] == "STRUCTURALLY_CHANGED"
    assert e["changed_fields"] == ["dimensions"]


def test_rename_candidate_uniqueness_and_consumed_target():
    f = {"{%s}old" % NS: _fp("old", balance="debit")}
    t = {"{%s}n1" % NS: _fp("n1", balance="debit"),
         "{%s}n2" % NS: _fp("n2", balance="debit")}
    m, _ = cr.classify_concepts_cr(f, t)
    assert m["{%s}old" % NS]["classification"] == "NOT_COMPARABLE"
    assert m["{%s}old" % NS]["evidence"] == "ambiguous_structural_match"
