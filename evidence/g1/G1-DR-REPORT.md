# BankCall España — G1-DR Integration Revalidation

**Verdict: REVALIDATED_PASS_WITH_CORRECTED_MAPPING** — the nine contract gates re-adjudicated over frozen G1-D outputs plus the corrected G1-CR taxonomy mapping. No acquisition, XBRL processing or network access was re-run; G1-C v1.0 and G1-D artifacts remain the historical record, preserved byte-for-byte.

## Gate table

| Gate | Result | Basis |
| --- | --- | --- |
| `DISCOVERY_DETERMINISTIC` | **PASS** | inherited from G1-D (frozen) |
| `ENTITY_KEY_DECOMPOSED` | **PASS** | inherited from G1-D (frozen) |
| `ENTITY_MAPPING_PROVEN` | **PASS** | inherited from G1-D (frozen) |
| `ENTITY_LIFECYCLE_HANDLED` | **PASS** | inherited from G1-D (frozen) |
| `TAXONOMY_AUTO_RESOLVABLE` | **PASS** | inherited from G1-D (frozen) |
| `PROVENANCE_COMPLETE` | **PASS** | inherited from G1-D (frozen) |
| `TEN_PERIOD_CORPUS_PASS` | **PASS** | inherited from G1-D (frozen) |
| `CROSS_TAXONOMY_CONCEPT_MAPPING` | **PASS** | G1-CR corrected: REVALIDATED_PASS |
| `NO_SILENT_SEMANTIC_DRIFT` | **PASS** | G1-CR corrected: PASS_WITH_CORRECTED_MAPPING |

## What changed vs G1-D

Nothing outside taxonomy adjudication. The period matrix (117/117 XBRL, 10 periods), the temporal identity model (9,253 mappings, 8 documented transfers), the provenance audit and the G1-B falsification record are inherited from `g1-evidence.json` unchanged.

### `publicos_2018_01__publicos_2018_12` — 26 reclassified entries

| Concept | G1-C v1.0 | G1-CR |
| --- | --- | --- |
| …`{http://www.bde.es/xbrl/dict/dim}MCI` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.bde.es/xbrl/dict/dim}PLO` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`w.bde.es/xbrl/fws/publicos/circ-4-2017/*GEN*_tab}tgPC_2` | RENAMED_EQUIVALENT | EXACT_EQUIVALENT |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/dim}APL` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/dim}BAS` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/dim}CNO` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/dim}CPS` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/dim}ENC` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/dim}FRS` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/dim}MCB` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/dim}MCE` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/dim}MCF` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/dim}MCP` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/dim}MCY` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/dim}REC` | EXACT_EQUIVALENT | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/dim}RPR` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/dim}SOL` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/dim}SUB` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/dim}TYH` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/exp}BA` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/exp}BT` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/exp}MC` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/exp}PL` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/met}md103` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eba.europa.eu/xbrl/crr/dict/met}mi53` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |
| …`{http://www.eurofiling.info/xbrl/ext/model}hyp` | STRUCTURALLY_CHANGED | NOT_COMPARABLE |

### `publicos_2018_12__publicos_2023_03` — 0 reclassified entries

No reclassifications — frozen v1.0 mapping reproduced exactly under collision-aware normalization.

## Product-visible impact

20 reclassified concepts occur in the 117 frozen instances as fact metrics, dimension keys or members — all are taxonomy-drift *labels* consumed by `bankcall changes`; no fact value, identity mapping or slot transfer is affected.

## Reproduction

```text
python scripts/g1/g1dr_revalidate.py
```

Inputs (sha256 recorded in `g1-dr-evidence.json`): `g1-evidence.json` (frozen G1-D), `g1-cr-evidence.json` and `g1-cr-mapping.json` (G1-CR corrected outputs).
