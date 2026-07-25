# Converged Fix List — LUMI Scorecard & Design Docs (red→blue)

Applied to:
- `docs/compatibility-scorecard.md` (rewritten as measurement instrument)
- `docs/superpowers/specs/2026-07-25-lumi-a2ui-bench-product-design.md` (§3/§4/§11)
- Track plan one-liners (evidence-gated score updates)
- This review set under `docs/superpowers/reviews/2026-07-25-lumi-scorecard-*.md`

**Process:** Sequential red → blue → edits (not parallel).

| ID | Severity | Disposition | Fix |
|----|----------|-------------|-----|
| R1 | blocker | ACCEPT | Per-Di algorithms + evidence + **asserting** `scripts/scorecard_recompute.py` (exit 0) |
| R2 | blocker | ACCEPT | Baseline D1 **1** (not 2); D1≠D6b |
| R3 | blocker | ACCEPT | Baseline D2 **1** (not 2); D2=2 needs per-type lint≡render |
| R4 | blocker | ACCEPT | “Official high” only if OII=4/4; ban fail-open narrative |
| R5 | high | ACCEPT | Partner indices OII/LEI/EDI; forbid publishing `5/18` as KPI |
| R6 | high | ACCEPT | Strip gold = hygiene gain + scoring loss in product design §3 |
| R7 | high | PARTIAL | Keep LUMI catalog MVP ≥1 unique; Product MVP + B-card anti-game floors |
| I1 | high | ACCEPT | Parallel Business Scenario Scorecard B1–B9 |
| I2 | medium | ACCEPT | B-card v0 documents S5 n=1 / untagged depth; v1 retag floors |
| I3 | medium | ACCEPT | D7 algorithm: stale tokens ⇒ max 1 until Track 3 |
| D8 | medium | PARTIAL | Stay deferred; labeled commercial gap; excluded from EDI |

**Baseline indices after converge (2026-07-25):** OII **2/4** · LEI **0/4** · EDI **1/8**

**Status:** Docs ready; scorecard is authoritative for claims until next evidence-backed rescoring.
