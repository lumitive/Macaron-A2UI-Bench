# LUMI-A2UI-Bench Compatibility Scorecard

Living **measurement instrument** (not a progress sticky note).  
**Baseline date:** 2026-07-25 (post red/blue converge)  
**Spec:** [2026-07-25-lumi-a2ui-bench-product-design.md](./superpowers/specs/2026-07-25-lumi-a2ui-bench-product-design.md)  
**Converge:** [2026-07-25-lumi-scorecard-converge.md](./superpowers/reviews/2026-07-25-lumi-scorecard-converge.md)

## How to read

1. **Scale** → per-Di 0/1/2  
2. **Indices** OII / LEI / EDI (partner-facing)  
3. **Claim rules** (fail-closed)  
4. **Baseline** → **Algorithms** (+ Evidence) → **B*** scenarios  

## Scale

| Score | Meaning |
|------:|---------|
| **0** | Absent / blocked / not measurable on this path |
| **1** | Partial / MVP — falsifiable evidence exists; gaps documented |
| **2** | Complete — algorithm bar met; asserting recompute exit 0 |

**Authority:** Plan checkboxes are not authority. **Evidence** justifies the published baseline. **Recompute** for any score *change* must be **asserting** (`exit 0` = green). Smoke `ls`/`echo` snippets alone never authorize a bump.

**Asserting recompute (required for rescoring):**

```bash
python3 scripts/scorecard_recompute.py          # must exit 0 vs claimed baseline
python3 scripts/scorecard_recompute.py --report-only
# Plus dimension-specific pytest named in each Di section when raising that Di
```

Extend `scripts/scorecard_recompute.py` predicates when raising a score so “green” cannot fail open.

## Partner-facing indices (never a single unweighted sum)

| Index | Points (max) | Display | Answers |
|-------|-------------:|---------|---------|
| **Official Infra (OII)** | D1 + D2 | `points/4` | Is official 0.9.1 wire + basic catalog/render benchable? |
| **LUMI Extension (LEI)** | D3 + D4 | `points/4` | Is LUMI catalog on 0.9.1 real (lint≡render)? |
| **Eval Depth (EDI)** | D5 + D6a + D6b + D7 | `points/8` | Can we evaluate generators deeply on 0.9.1? |

**D8** is tracked but **excluded from EDI** until interactive/capabilities work is in scope.

**Forbidden partner claims**

- Any single `x/18` / “N% compatible” as overall compatibility (including internal eng points)
- “Official 0.9.1 basic compatibility is high” unless **OII = 4/4**
- LUMI claims without claim rules below + `protocol_catalog=lumi` evidence
- Citing 0.8 Macaron/LUMI heritage greens as 0.9.1 LUMI compatibility

**Internal only:** “Engineering progress points” = sum(D1…D8) displayed as `points/18` — not marketing.

## Claim rules (fail-closed)

1. **Full LUMI compatibility** ↔ D3=2 ∧ D4=2 (`protocol_catalog=lumi` evidence only)
2. **LUMI catalog MVP** ↔ D3≥1 ∧ D4≥1 ∧ Track 1 naming done; `protocol_catalog=lumi` only; heritage 0.8 ≠ D4
3. **Product MVP (Tracks 1–3)** ↔ rule 2 ∧ D5≥1 ∧ D6a=2 ∧ D6b=2 ∧ D7=2 ∧ anti-game floors:
   - D5 subset in `docs/gold-v091-subset.md` with ≥15 retained 0.9.1-valid depth turns **and** ≥3 distinct `scenario_id` values (on turns or parent tasks after retag)
   - Catalog wedge alone ≠ Product MVP
4. **Official infra high** ↔ OII=4/4 only
5. **Scenario-compatible (public)** ↔ Business Scenario Scorecard **B-card v1** gates — not implied by OII/LEI/EDI

## Baseline scores (2026-07-25)

| ID | Dimension | Score | Index |
|----|-----------|------:|-------|
| D1 | Official 0.9.1 wire | **1** | OII |
| D2 | Official basic catalog + Lit render | **1** | OII |
| D3 | LUMI extended catalog (0.9.1 form) | **0** | LEI |
| D4 | LUMI↔basic mapping; lint≡render on 0.9.1 | **0** | LEI |
| D5 | 0.9.1 depth `gt_a2ui` gold | **0** | EDI |
| D6a | `--prompt-mode full` on 0.9.1 | **0** | EDI |
| D6b | Deep jsonschema L1 | **0** | EDI |
| D7 | L2/L3 hints & protocol terminology | **1** | EDI |
| D8 | Client↔server / catalog functions | **0** | deferred |

| Index | Value | Band |
|-------|------:|------|
| OII | **2 / 4** | Partial — **not** “high” |
| LEI | **0 / 4** | Absent |
| EDI | **1 / 8** | Low |
| Eng. progress (internal) | 3 / 18 | Do not publish |

**Narrative:** Official 0.9.1 **infra is partial (OII 2/4)**. **LUMI extension is absent (LEI 0/4).** **Eval depth is low (EDI 1/8).** Overall LUMI-A2UI compatibility remains low until Tracks 2–3 move the indices.

---

## Per-dimension algorithms

### D1 — Official 0.9.1 wire

| Score | Definition |
|------:|------------|
| 0 | No selectable 0.9.1 stack, or default ≠ `0.9.1` |
| 1 | CLI/env `0.8`\|`0.9.1`; default `0.9.1`; contract tests (legacy reject; version accept); ≥4 envelope fixtures; `UPSTREAM_PIN.txt`; CI `pytest tests/protocol` green |
| 2 | D1=1 **and** fixtures cover create/update/delete **and** ≥1 incremental ≥2-turn fixture **and** (multi-surface policy tested-accept **or** documented single-surface limit with asserting test) |

**Not in D1:** component prop jsonschema (→ **D6b**).

**Evidence today (⇒ 1):** Dual stack; default 0.9.1; legacy reject; ≥4 fixtures; `protocol/v0_9_1/UPSTREAM_PIN.txt`; CI protocol job. Incomplete delete/incremental matrix; multi-surface forbidden in `render_check` without full policy doc suite ⇒ not 2.

**Recompute (asserting):**
```bash
python3 scripts/scorecard_recompute.py   # includes D1 predicates
pytest tests/protocol -q                 # required alongside when changing D1
```

### D2 — Official basic catalog + Lit render

| Score | Definition |
|------:|------------|
| 0 | Basic catalog missing or `catalogId` unlocked |
| 1 | Locked basic `catalogId`; 18 types; `render_v091` CI build green; guide mentions locked id; ≥1 create/update fixture passes lint + `render_check` |
| 2 | Per-type coverage 18/18 with lint_pass ⇒ `render_check` pass **and** ≥1 example from each family (layout / input / media / overlay) |

**Evidence today (⇒ 1):** 18 types; locked id; CI build; happy-path fixture. No per-type fixture matrix ⇒ not 2.

**Recompute (asserting):**
```bash
python3 scripts/scorecard_recompute.py
pytest tests/protocol/test_v0_9_1_lint.py tests/protocol/test_v0_9_1_render_check.py -q
```

### D3 — LUMI extended catalog (0.9.1 form)

| Score | Definition |
|------:|------------|
| 0 | No LUMI catalog asset / catalogId |
| 1 | `catalogId=lumi.ai:a2ui:lumi-catalog`; inventory doc; ≥1 `lumi_unique` authored; `map_basic` aliases for classified mappables |
| 2 | `authored / inventory.lumi_unique ≥ 95%` and catalog supersets full basic 18 |

**Evidence today (⇒ 0).**

**Recompute (asserting):** file presence alone is **not** D3≥1. All score-1 clauses must pass in `scripts/scorecard_recompute.py` (catalogId + inventory `lumi_unique` + mappable/`map_basic` + ≥1 component). Stub catalog ⇒ stay **0**.

```bash
python3 scripts/scorecard_recompute.py --report-only   # D3 must print 0 today
```

### D4 — LUMI↔basic mapping; lint≡render on 0.9.1

| Score | Definition |
|------:|------------|
| 0 | No `PROTOCOL_CATALOG=lumi` path, or only 0.8 heritage proof |
| 1 | Selector wired; MVP fixtures: lint ⇒ `render_check` ⇒ Lit ingest; basic rejects LUMI types/ids |
| 2 | 100% rate on full inventory fixtures + bidirectional catalogId lock tests |

**Evidence today (⇒ 0).**

**Recompute (asserting):**
```bash
# Absent tests ⇒ D4=0 (collection miss is not a pass)
pytest tests/protocol/test_v0_9_1_lumi_*.py -q
python3 scripts/scorecard_recompute.py
```

### D5 — 0.9.1 depth `gt_a2ui` gold

| Score | Definition |
|------:|------------|
| 0 | Strip-all, or zero retained 0.9.1-valid gold |
| 1 | ≥15 retained 0.9.1-valid depth turns **or** ≥10% depth tasks + `docs/gold-v091-subset.md` — **D5 partial only; does not imply Product MVP** |
| 2 | ≥80% depth tasks retain validating gold **and** gold used in ≥1 scored depth metric |

**Product MVP** still requires claim rule 3 floors: ≥15 retained turns **and** ≥3 `metadata.scenario_id` values (the OR path above is insufficient for Product MVP).

**Evidence today (⇒ 0):** `strip_gt_a2ui=True` on 0.9.1 path.

**Recompute (asserting):** after Track 3, extend `scorecard_recompute.py` (or dedicated loader tests) to count retained validating gold; `gold-v091-subset.md` alone ≠ D5≥1.

### D6a — `--prompt-mode full` on 0.9.1

| Score | Definition |
|------:|------------|
| 0 | `full`+`0.9.1` hard error |
| 1 | Non-empty guide with `catalogId` + active catalog types |
| 2 | Full prompt = rules + schemas + envelope; CI locks `createSurface` / `updateDataModel` / `ChoicePicker` |

**Evidence today (⇒ 0).**

**Recompute (asserting):** after Track 3 wiring, `pytest tests/protocol -k full -q` must exit 0 **and** `scorecard_recompute.py` D6a≥ target.

### D6b — Deep jsonschema L1

| Score | Definition |
|------:|------------|
| 0 | Structural-only; deliberate bad props silent |
| 1 | Envelope schema on; bad-prop catch rate ≥50% |
| 2 | Component props vs catalog; `DATA_*` on binding/value faults; catch rate ≥95% |

**Evidence today (⇒ 0):** structural lint; prop type faults often silent.

**Recompute (asserting):** Track 3 must add `tests/protocol/test_v0_9_1_schema.py` **and** a bad-prop fixture set with measured catch rate; document the probe command in that PR. Thresholds are not subjective once the probe exists.

### D7 — L2/L3 hints & terminology

| Score | Definition |
|------:|------------|
| 0 | 0.9.1 path uses 0.8-only judge prompts/hints |
| 1 | Versioned judge prompts exist, but stale 0.8 tokens remain in hints (`stale>0`) |
| 2 | Protocol-selected hints `stale=0`; unit forbids `dataModelUpdate` on 0.9.1 |

**Evidence today (⇒ 1):** `l2_judge_v091.txt` exists; `L2_RUBRIC_HINTS` still uses `dataModelUpdate`.

**Recompute (asserting):**
```bash
python3 scripts/scorecard_recompute.py   # D7=1 while dataModelUpdate remains in evaluate_api_model.py
# Pass rule for D7=2: zero hits of dataModelUpdate in 0.9.1-selected hint paths + unit test
```

### D8 — Client↔server / catalog functions (deferred)

| Score | Definition |
|------:|------------|
| 0 | Capabilities unused in eval (today) |
| 1 | Client capability advertisement validated |
| 2 | Interactive client→server scoring with pass rates |

**Not in Tracks 1–3.** Known commercial gap for Prompt-First agent products; do not imply “0.9.1 eval complete” in sales stories that need interactivity while D8=0.

---

## Phase 1 gold strip — hygiene vs scoring

| Lens | Statement |
|------|-----------|
| **Hygiene gain** | Default 0.9.1 path does not score 0.8-shaped `gt_a2ui` as if it were 0.9.1 gold |
| **Scoring loss** | Depth-comparative metrics unavailable until D5≥1; **D5=0 expresses that loss** |

---

## Business Scenario Scorecard (B*) — parallel, phased

Infrastructure indices do **not** answer “emotion → transaction on 0.9.1.” B* is parallel; not folded into D*.

### Sample reality (`data/eval_300`, 2026-07-25)

Counts use raw `metadata.scenario_id` tags (not loader inference fallbacks).

| Fact | Value |
|------|------:|
| Tasks | 300 (atomic/depth/width = 100 each) |
| Atomic `metadata.scenario_id` | S1≈36, S2≈14 (**low-confidence**), S3≈43, S4≈6, **S5≈1** (**anecdotal**) |
| Depth+width with `metadata.scenario_id` | **0 / 200** |
| Depth `gt_a2ui` on 0.9.1 default | stripped |

**B* recompute (v0):** count tagged tasks per scenario; band by n. **B-card v1** public claims require the floors below — no asserting script yet; until one exists, public scenario claims remain forbidden (claim rule 5).

### B dimensions

| ID | Dimension | B-card v0 (measure now) | B-card v1 (public claims) |
|----|-----------|-------------------------|---------------------------|
| **B1** | S1 Emotion | Atomic S1 L1/L2/L3; report n | n≥30 tagged incl. depth/width share |
| **B2** | S2 Commitment | Atomic S2; report n | n≥10 across difficulties |
| **B3** | S3 Slot filling | Atomic S3; report n | n≥30; depth accumulation when D5≥1 |
| **B4** | S4 Candidate compare | Atomic S4; **low-confidence** if n&lt;15 | n≥15 tagged |
| **B5** | S5 Transaction | n≈1 → **anecdotal only** | **n≥20** before “supported” |
| **B6** | Difficulty coverage | Atomic vs depth vs width L1; depth gold “stripped” until D5≥1 | Depth/width need `scenario_id` + D5 policy |
| **B7** | Visual V1–V3 | Optional; omit ⇒ “not run” | Means with stack `render_check` when enabled |
| **B8** | Catalog matrix | Report under `basic`; `lumi` = N/A until Track 2 | Dual-report; basic ≠ LUMI |
| **B9** | Prompt-First readiness | Label runs **“minimal-guide only”** while D6a&lt;2 | Uncaveated B* only if D6a=2 |

**Bands (v0):** `anecdotal` (n&lt;5) · `low-confidence` (n&lt;15) · `measurable` (n≥15).

**B-card v0:** define + measure existing atomic tags; **no public “scenario-compatible” claim.**  
**B-card v1:** retag depth/width; meet floors; then public scenario claims under B8×B9.

### B* claim rules

1. Public “scenario-compatible on 0.9.1” requires **B-card v1** floors for claimed scenarios  
2. B5 “supported” requires n≥20 — v0 must not imply support from n=1  
3. LUMI scenario claims require B8=`lumi` columns  
