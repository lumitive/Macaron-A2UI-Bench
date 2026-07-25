# LUMI-A2UI-Bench Compatibility Scorecard

Living scores for product narrative. Scale: **0** none · **1** partial / MVP · **2** complete.

**Baseline date:** 2026-07-25  
**Spec:** [2026-07-25-lumi-a2ui-bench-product-design.md](./superpowers/specs/2026-07-25-lumi-a2ui-bench-product-design.md)

| ID | Dimension | Score | Notes |
|----|-----------|------:|-------|
| D1 | Official 0.9.1 wire | 2 | Dual stack; default 0.9.1 |
| D2 | Official basic catalog + Lit render | 2 | `render_v091` + locked basic `catalogId` |
| D3 | LUMI extended catalog (0.9.1 form) | 0 | Track 2 MVP → ≥1; full inventory → 2 |
| D4 | LUMI↔basic mapping; lint/render on **0.9.1** | 0 | Heritage 0.8 risk does **not** count; Track 2 lint≡render → ≥1 |
| D5 | 0.9.1 depth `gt_a2ui` gold | 0 | Track 3 subset → ≥1 |
| D6a | `--prompt-mode full` on 0.9.1 | 0 | Track 3 |
| D6b | Deep jsonschema L1 | 0 | Structural lint only today; Track 3 |
| D7 | L2/L3 hints & protocol terminology | 1 | Mixed 0.8 terms in `L2_RUBRIC_HINTS` |
| D8 | Client↔server / catalog functions | 0 | Deferred |

**Totals (sum):** 5 / 18

**Claim rules (must match spec §4):**

1. Full LUMI compatibility ↔ **D3=2 AND D4=2**
2. LUMI catalog MVP (after Track 2) ↔ **D3≥1 AND D4≥1**, evidence only from `protocol_catalog=lumi` runs
3. Product MVP (Tracks 1–3) ↔ Track 1 done + rule 2 + D5≥1 + D6a=2 + D6b=2 + D7=2

**Narrative:** Official 0.9.1 basic compatibility is high; LUMI-A2UI overall compatibility is low until Tracks 2–3 land.
