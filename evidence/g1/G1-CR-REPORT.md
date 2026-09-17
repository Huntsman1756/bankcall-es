# BankCall España — G1-CR Corrected Taxonomy Comparison

Revalidates the frozen G1-C v1.0 concept mapping (`concept-mapping.json`) with collision-aware normalization. Pure offline check over committed inputs; no source fetches. G1-C v1.0 artifacts, evidence and reports are preserved byte-for-byte; this report evaluates the corrected model.

## Defects corrected

| # | Defect in G1-C v1.0 | Consequence |
| --- | --- | --- |
| 1 | `normalize_fp` built `{canon: raw}` dicts — two raw QNames canonicalizing to one key silently shadowed each other (last-wins) | `tgPC_2` existed in two dated `_tab` namespaces per generation; one variant was never compared |
| 2 | `_norm_obj` did the same for dict keys *inside* fingerprints (linkrole keys after `role_map` translation) — distinct raw keys collapsed silently | 11 same-canon merges recorded on the `2018_01→2018_12` to-side (2 concepts, 6 with non-identical values); conflicted-role keys are adjudicated symbolically — 25 entries fail closed with `unresolved_fields` |
| 3 | `role_to_from` resolved multiple-candidate role renames by insertion-order last-wins — reproducible only in Arelle's live dict order, not from the sorted evidence JSON | 126 conflicted to-roles across both transitions |

## Gate result

| Gate | G1-C v1.0 | G1-CR corrected |
| --- | --- | --- |
| `CROSS_TAXONOMY_CONCEPT_MAPPING` | implementation defect: silent canonical-key collision (one colliding raw QName per side was shadowed by last-wins dict normalization) | **REVALIDATED_PASS** |
| `NO_SILENT_SEMANTIC_DRIFT` | implementation defect: equivalence/difference verdicts could rest on arbitrarily resolved role-map conflicts and silently merged inner-dict keys | **PASS_WITH_CORRECTED_MAPPING** |

## Per-transition results

| Pair | Metric | Frozen | Corrected |
| --- | --- | --- | --- |
| `publicos_2018_01__publicos_2018_12` | EXACT_EQUIVALENT | 20145 | 20145 |
| `publicos_2018_01__publicos_2018_12` | RENAMED_EQUIVALENT | 4 | 3 |
| `publicos_2018_01__publicos_2018_12` | STRUCTURALLY_CHANGED | 57 | 33 |
| `publicos_2018_01__publicos_2018_12` | NEW | 1 | 1 |
| `publicos_2018_01__publicos_2018_12` | REMOVED | 0 | 0 |
| `publicos_2018_01__publicos_2018_12` | NOT_COMPARABLE | 0 | 25 |
| `publicos_2018_01__publicos_2018_12` | UNKNOWN | 0 | 0 |
| `publicos_2018_01__publicos_2018_12` | role_conflicts | — | 126 |
| `publicos_2018_01__publicos_2018_12` | qname_collision_groups | — | 1 |
| `publicos_2018_01__publicos_2018_12` | coverage_ok | — | True |
| `publicos_2018_12__publicos_2023_03` | EXACT_EQUIVALENT | 20203 | 20203 |
| `publicos_2018_12__publicos_2023_03` | RENAMED_EQUIVALENT | 4 | 4 |
| `publicos_2018_12__publicos_2023_03` | STRUCTURALLY_CHANGED | 0 | 0 |
| `publicos_2018_12__publicos_2023_03` | NEW | 0 | 0 |
| `publicos_2018_12__publicos_2023_03` | REMOVED | 0 | 0 |
| `publicos_2018_12__publicos_2023_03` | NOT_COMPARABLE | 0 | 0 |
| `publicos_2018_12__publicos_2023_03` | UNKNOWN | 0 | 0 |
| `publicos_2018_12__publicos_2023_03` | role_conflicts | — | 0 |
| `publicos_2018_12__publicos_2023_03` | qname_collision_groups | — | 2 |
| `publicos_2018_12__publicos_2023_03` | coverage_ok | — | True |

## Reclassified entries vs frozen v1.0

| Canon key | Frozen | Corrected | Detail |
| --- | --- | --- | --- |
| `publicos_2018_01__publicos_2018_12` …{http://www.bde.es/xbrl/dict/dim}MCI | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …{http://www.bde.es/xbrl/dict/dim}PLO | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …brl/fws/publicos/circ-4-2017/*GEN*_tab}tgPC_2 | RENAMED_EQUIVALENT | EXACT_EQUIVALENT | reclassified |
| `publicos_2018_01__publicos_2018_12` …ttp://www.eba.europa.eu/xbrl/crr/dict/dim}APL | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …ttp://www.eba.europa.eu/xbrl/crr/dict/dim}BAS | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …ttp://www.eba.europa.eu/xbrl/crr/dict/dim}CNO | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …ttp://www.eba.europa.eu/xbrl/crr/dict/dim}CPS | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …ttp://www.eba.europa.eu/xbrl/crr/dict/dim}ENC | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …ttp://www.eba.europa.eu/xbrl/crr/dict/dim}FRS | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …ttp://www.eba.europa.eu/xbrl/crr/dict/dim}MCB | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …ttp://www.eba.europa.eu/xbrl/crr/dict/dim}MCE | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …ttp://www.eba.europa.eu/xbrl/crr/dict/dim}MCF | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …ttp://www.eba.europa.eu/xbrl/crr/dict/dim}MCP | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …ttp://www.eba.europa.eu/xbrl/crr/dict/dim}MCY | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …ttp://www.eba.europa.eu/xbrl/crr/dict/dim}REC | EXACT_EQUIVALENT | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …ttp://www.eba.europa.eu/xbrl/crr/dict/dim}RPR | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …ttp://www.eba.europa.eu/xbrl/crr/dict/dim}SOL | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …ttp://www.eba.europa.eu/xbrl/crr/dict/dim}SUB | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …ttp://www.eba.europa.eu/xbrl/crr/dict/dim}TYH | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …http://www.eba.europa.eu/xbrl/crr/dict/exp}BA | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …http://www.eba.europa.eu/xbrl/crr/dict/exp}BT | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …http://www.eba.europa.eu/xbrl/crr/dict/exp}MC | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …http://www.eba.europa.eu/xbrl/crr/dict/exp}PL | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …p://www.eba.europa.eu/xbrl/crr/dict/met}md103 | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …tp://www.eba.europa.eu/xbrl/crr/dict/met}mi53 | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |
| `publicos_2018_01__publicos_2018_12` …http://www.eurofiling.info/xbrl/ext/model}hyp | STRUCTURALLY_CHANGED | NOT_COMPARABLE | unresolved=['dimensions'] |

## Product-visible impact

Changed/surfaced concepts traced into the 117 frozen XBRL instances (via `facts.parquet`): **20** occur in actual reported facts (as metrics, dimension keys or members); the rest exist only in taxonomy structure.

| QName | fact metric | dims key | member |
| --- | --- | --- | --- |
| `{http://www.bde.es/xbrl/dict/dim}MCI` | False | True | False |
| `{http://www.bde.es/xbrl/dict/dim}PLO` | False | True | False |
| `{http://www.eba.europa.eu/xbrl/crr/dict/dim}APL` | False | True | False |
| `{http://www.eba.europa.eu/xbrl/crr/dict/dim}BAS` | False | True | False |
| `{http://www.eba.europa.eu/xbrl/crr/dict/dim}CNO` | False | True | False |
| `{http://www.eba.europa.eu/xbrl/crr/dict/dim}CPS` | False | True | False |
| `{http://www.eba.europa.eu/xbrl/crr/dict/dim}ENC` | False | True | False |
| `{http://www.eba.europa.eu/xbrl/crr/dict/dim}FRS` | False | True | False |
| `{http://www.eba.europa.eu/xbrl/crr/dict/dim}MCB` | False | True | False |
| `{http://www.eba.europa.eu/xbrl/crr/dict/dim}MCE` | False | True | False |
| `{http://www.eba.europa.eu/xbrl/crr/dict/dim}MCF` | False | True | False |
| `{http://www.eba.europa.eu/xbrl/crr/dict/dim}MCP` | False | True | False |
| `{http://www.eba.europa.eu/xbrl/crr/dict/dim}MCY` | False | True | False |
| `{http://www.eba.europa.eu/xbrl/crr/dict/dim}REC` | False | True | False |
| `{http://www.eba.europa.eu/xbrl/crr/dict/dim}RPR` | False | True | False |
| `{http://www.eba.europa.eu/xbrl/crr/dict/dim}SOL` | False | True | False |
| `{http://www.eba.europa.eu/xbrl/crr/dict/dim}SUB` | False | True | False |
| `{http://www.eba.europa.eu/xbrl/crr/dict/dim}TYH` | False | True | False |
| `{http://www.eba.europa.eu/xbrl/crr/dict/met}md103` | True | False | False |
| `{http://www.eba.europa.eu/xbrl/crr/dict/met}mi53` | True | False | False |

`ingest` prefers `g1-cr-mapping.json` when present, so `changes` drift flags reflect the corrected verdicts: the concepts above now surface as `NOT_COMPARABLE` (or drop out, for `tgPC_2`'s upgraded equivalence) instead of the v1.0 labels.

## Reproduction

```text
python scripts/g1/taxonomy_g1cr.py
```

Inputs: `dts-fingerprints.json` (sha256 `8a95ff97c0330ec8…`), committed versioning XMLs in document order. Frozen mapping sha256 `8c71c2cec239006d…` verified read-only.
