# Red Team Memo — LUMI Compatibility Scorecard (2026-07-25)

> **Historical review artifact.** Superseded by [converge](./2026-07-25-lumi-scorecard-converge.md) + living [`docs/compatibility-scorecard.md`](../../compatibility-scorecard.md). Do not cite as current ship status.

**Role:** Adversarial review of design docs (scorecard primary).  
**Verdict (at review time):** Scorecard **not fit for commercial use** as published (narrative checklist, not measurement).

## Critical (R1–R7)

| ID | Finding |
|----|---------|
| R1 | No scoring algorithm, evidence table, or recompute procedure |
| R2 | D1=2 overclaims complete 0.9.1 wire (shallow L1, thin fixtures) |
| R3 | D2=2 overclaims complete basic+Lit (CI build ≠ per-type lint≡render) |
| R4 | Narrative “official high” fails open despite LUMI claim gates |
| R5 | Unweighted `5/18` equal-weight sum misleads partners |
| R6 | Phase 1 “strip gold” listed as gain while D5=0 (hygiene vs scoring loss) |
| R7 | MVP thresholds gameable (≥1 LUMI type / 10–20 gold turns) without scenario floors |

## Important

- Omits 0.8-era commercial surface: S1–S5, V1–V3, difficulty ladder as scored panels
- `eval_300`: S5 n=1; depth/width lack `scenario_id` (200/300)
- D7: `L2_RUBRIC_HINTS` still `dataModelUpdate` on 0.9.1 path
- Missing 0.9.1 realities as first-class dims: incremental, MIME, capabilities (D8 deferred)

## Keep

Dual official/LUMI axes; Full LUMI = D3=2∧D4=2; `protocol_catalog=lumi` citation; heritage ≠ D4; honest zeros on D3–D6b.

Full attack detail archived in agent transcript; converge applies blue refinements.
