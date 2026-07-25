# LUMI-A2UI-Bench Product Evaluation & Evolution Design

**Date:** 2026-07-25  
**Status:** Approved for implementation planning  
**Repo (current filesystem / remote):** Macaron-A2UI-Bench → **rebrand target:** LUMI-A2UI-Bench  
**Related prior design:** [2026-07-24-a2ui-0.9.1-upgrade-design.md](./2026-07-24-a2ui-0.9.1-upgrade-design.md) (Phase 1 landed)

## 1. Problem

Phase 1 delivered a dual-stack A2UI bench with **default 0.9.1 + official basic catalog**. The product is still branded **Macaron**, and the Macaron-extended component set (now productized as **LUMI-A2UI**) exists only on the **0.8** path under `vendor/a2ui_demo`. Depth gold remains 0.8-shaped and is stripped on 0.9.1. The bench cannot yet answer, with a single scorecard: “How compatible are we with official 0.9.1?” vs “How compatible are we with LUMI-A2UI?”

## 2. Decisions (locked)

| Decision | Choice |
|----------|--------|
| Product name | **LUMI-A2UI-Bench** (full rebrand, not display-only) |
| LUMI-A2UI definition | Self-extended catalog ≈ current 0.8 Macaron schemas in `vendor/a2ui_demo/resources/components/schemas/`, migrated to **0.9.1 wire + flat `component`** |
| Delivery approach | **Three tracks:** Track 1 rebrand first; Tracks 2 (LUMI catalog) and 3 (bench depth) may proceed in parallel after Track 1 |
| Official basic 0.9.1 | Keep as default baseline (Phase 1); do not replace with LUMI |
| LUMI `catalogId` | **`lumi.ai:a2ui:lumi-catalog`** (locked); **never** pretend to be `a2ui.org` basic |
| Catalog CLI/env | `--protocol-catalog {basic,lumi}` / `PROTOCOL_CATALOG` (default `basic`) |
| 0.8 stack | Retain permanently for comparison; document as LUMI 0.8 heritage source |
| Track ordering | Track 1 first; Tracks **2 and 3 may run in parallel** on `basic` (LUMI-aware gold/`full` optional after Track 2) |
| v1.0 | Out of scope (Phase 2, separate design) |
| Silent 0.8→0.9.1 convert | Forbidden (unchanged) |

## 3. Phase 1 gains (what improved)

Relative to a hard-pinned 0.8-only Macaron bench:

| Area | Before | After Phase 1 |
|------|--------|----------------|
| Protocol | 0.8 only | Parallel `protocol/v0_8` + `protocol/v0_9_1`; default **0.9.1** |
| Wire | `beginRendering` / key-wrapped components / typed values | `createSurface` + `catalogId`, flat `component`, `updateDataModel` + JSON `value`; legacy shapes rejected |
| Catalog (default) | Macaron-extended lint vs Lit standard mismatch | Official **basic** (18 types) + locked `catalogId` |
| Renderer | `render/` :5173 only | + `render_v091/` Lit `v0_9` :5174 |
| Eval | Single results mix risk | `results/<protocol_version>/` + manifest field |
| Depth | 0.8 `gt_a2ui` in data | 0.9.1 path **strips** gold (dialogue-only) |
| Visual | Root 0.8 `render_check` | Stack `render_check` per protocol |

**Verdict:** Strong base for scoring **official 0.9.1 basic** generators. Not yet a complete **LUMI-A2UI** compatibility product.

## 4. Compatibility scorecard

**Living source of truth:** [`docs/compatibility-scorecard.md`](../../compatibility-scorecard.md).  
Scale: **0** none · **1** partial / MVP · **2** complete. Snapshot below is the 2026-07-25 baseline + gates.

| ID | Dimension | Baseline | Gate after Tracks 1–3 (MVP) | Later complete (2) |
|----|-----------|----------|-----------------------------|--------------------|
| D1 | Official 0.9.1 wire | 2 | 2 | 2 |
| D2 | Official basic catalog + Lit render | 2 | 2 | 2 |
| D3 | LUMI extended catalog in 0.9.1 form | 0 | **≥1** (MVP unique + selector) | 2 (full inventory) |
| D4 | LUMI↔basic mapping; lint/render consistency on **0.9.1** | 0 | **≥1** (MVP lint≡render for LUMI catalog) | 2 (full dual-catalog) |
| D5 | 0.9.1 depth `gt_a2ui` gold | 0 | **≥1** (subset) | 2 (broad coverage) |
| D6a | `--prompt-mode full` on 0.9.1 | 0 | 2 | 2 |
| D6b | Deep jsonschema L1 | 0 | 2 | 2 |
| D7 | L2/L3 hints & protocol terminology | 1 | 2 | 2 |
| D8 | Client↔server / catalog functions | 0 | 0 | optional later |

**Claim rules (fail-closed):**

1. **Full LUMI compatibility** — only when **D3=2 AND D4=2**.
2. **LUMI catalog MVP** — after Track 2, only when **D3≥1 AND D4≥1**, and only cite runs with `protocol_catalog=lumi` (never basic-default greens).
3. **Product MVP (Tracks 1–3)** — Track 1 rebrand done + rule 2 + Track 3 gates D5≥1, D6a=2, D6b=2, D7=2.
4. D4 measures **0.9.1** lint≡render for LUMI — heritage 0.8 dual-catalog risk does **not** count as D4≥1.

**Narrative today:** Official 0.9.1 basic compatibility is high; **LUMI-A2UI overall compatibility is low**. Post-rebrand: *LUMI-A2UI-Bench = official 0.9.1 baseline + LUMI extension track (in progress).*

## 5. Track 1 — Full rebrand

### In scope

- GitHub repo display name / README / UPSTREAM / docs titles and cross-links
- User-visible copy: `Macaron A2UI Bench` → `LUMI A2UI Bench`; “Macaron-extended” → “LUMI-extended”
- Package names: `render/package.json`, `render_v091/package.json` (`a2ui-bench-render*` → `lumi-a2ui-bench-render*`)
- CI job display names; any product strings in manifests
- Forward pointer only: LUMI 0.9.1 catalog path will be `protocol/v0_9_1/spec/catalogs/lumi/` (**created in Track 2**, not this track)

### Explicitly preserved

- Upstream A2UI / Google license headers
- Git history
- Physical path `vendor/a2ui_demo` initially (document as **LUMI 0.8 heritage source**)

### Non-goals

- Inventing a fake `a2ui.org` catalogId for LUMI
- Renaming every historical design-doc filename (optional; prefer body text updates)

## 6. Track 2 — LUMI catalog on 0.9.1 (former Phase 1.5)

1. **Inventory** schemas under `vendor/a2ui_demo/resources/components/schemas/`.
2. **Classify** components:
   - **Mappable to official basic** (e.g. Label→Text, SelectionList→ChoicePicker, TickSlider→Slider, …)
   - **LUMI-unique** (e.g. Carousel, RollPicker, PasswordKeypad, Map, FilterTags, SelectionWrap/Grid, …)
3. **Author** 0.9.1-shaped LUMI catalog (flat `component`, 0.9.1 prop names) + locked LUMI `catalogId`.
4. **Wire** `protocol/v0_9_1` for `catalog=basic|lumi` via `--protocol-catalog` / `PROTOCOL_CATALOG` (default `basic`): lint, guides, `render_check`, Lit registration — **lint-pass implies render-pass**.
5. **Eval matrix:** default basic; `PROTOCOL_CATALOG=lumi` for LUMI compatibility runs.

**MVP success:** end-to-end generate → L1 → `render_check` → `render_v091` green for **≥1 LUMI-unique** component.

## 7. Track 3 — Bench depth

Priority order:

1. Version **L2_RUBRIC_HINTS** / judge terminology for 0.9.1 (cheap noise cut)
2. **Deep jsonschema L1** (envelope + component props; meaningful `DATA_*`)
3. Enable **`--prompt-mode full`** on 0.9.1 (remove hard error; inject schema)
4. **0.9.1 `gt_a2ui` gold** — start with a representative depth subset, then expand
5. Optional later: client↔server / catalog functions (does not block Track 2)

## 8. Architecture (unchanged spine + extensions)

| Unit | Role after Tracks 1–3 |
|------|------------------------|
| `protocol/v0_8/` | Heritage / comparison; LUMI 0.8 source via `vendor/a2ui_demo` |
| `protocol/v0_9_1/` | Official basic + **LUMI** catalog mode; deeper lint |
| `evaluate_api_model.py` | `--protocol-version` + catalog selector; full prompt on 0.9.1 |
| `render/` / `render_v091/` | Renamed packages; Lit registers LUMI components when catalog=lumi |
| `data/` | Shared tasks; progressive 0.9.1 gold backfill |
| Scorecard doc | Living SoT: `docs/compatibility-scorecard.md` |

Invariant: one run = one protocol version + one active catalog end-to-end.

## 9. Error handling additions

| Case | Behavior |
|------|----------|
| LUMI component on `catalog=basic` | L1 unknown-component fail |
| `catalog=basic` + LUMI `catalogId` | L1 catalog lock fail |
| `catalog=lumi` + official basic / `a2ui.org` `catalogId` | L1 catalog lock fail |
| Lint allows type Lit cannot render | **Bug** — treat as Track 2 blocker |
| `full` + missing schema assets | Hard error with path hint |

## 10. Non-goals (this product design)

- A2UI **v1.0** stack
- Auto-converting 0.8 model output to 0.9.1 for scoring
- Deleting the 0.8 codepath
- Claiming full LUMI compatibility before D3–D4 reach **2** (MVP at ≥1 is allowed as “LUMI MVP”)

## 11. Success criteria

- Public naming consistently **LUMI-A2UI-Bench** (heritage paths documented)
- Scorecard answers “official 0.9.1 vs LUMI” quantitatively
- Track 2 → **LUMI catalog MVP** when D3≥1 **AND** D4≥1 (0.9.1 lint≡render), citing only `protocol_catalog=lumi` runs
- Tracks 1–3 → **Product MVP** when claim rules §4 items 2–3 hold
- “Full LUMI compatibility” only when D3=2 **AND** D4=2

## 12. Implementation plan artifacts

| Track | Plan file |
|-------|-----------|
| 1 Rebrand | `docs/superpowers/plans/2026-07-25-lumi-a2ui-bench-rebrand.md` |
| 2 LUMI catalog | `docs/superpowers/plans/2026-07-25-lumi-catalog-0.9.1.md` |
| 3 Bench depth | `docs/superpowers/plans/2026-07-25-lumi-bench-depth.md` |
