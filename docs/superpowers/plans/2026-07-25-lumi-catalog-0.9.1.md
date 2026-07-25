# LUMI Catalog on A2UI 0.9.1 (Track 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a 0.9.1-shaped **LUMI** extended catalog (from Macaron `vendor/a2ui_demo` schemas) selectable alongside official basic, with lint/guides/`render_check`/Lit aligned so lint-pass implies render-pass.

**Architecture:** Extend `protocol/v0_9_1` with an active-catalog switch (`basic` | `lumi`). Author LUMI catalog JSON under `protocol/v0_9_1/spec/catalogs/lumi/`. Register LUMI-unique Lit components in `render_v091` (or map to basic widgets where equivalent). Default remains `basic`.

**Tech Stack:** Python protocol stack, JSON Schema catalogs, Lit/`@a2ui/web_core` v0_9, pytest, Vite harness.

## Global Constraints

- Default catalog: **basic** with locked URI `https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json`.
- LUMI `catalogId`: **`lumi.ai:a2ui:lumi-catalog`** (locked for this plan; change only via spec amend).
- Wire version: **0.9.1** (accept `v0.9` / `v0.9.1` messages as today).
- No silent 0.8→0.9.1 conversion.
- Spec: `docs/superpowers/specs/2026-07-25-lumi-a2ui-bench-product-design.md`.
- Depends on Track 1 brand naming (can land after or with soft brand strings).

---

## File map

| File / dir | Responsibility |
|------------|----------------|
| `docs/lumi-catalog-inventory.md` | Component inventory + basic mapping table |
| `protocol/v0_9_1/spec/catalogs/lumi/catalog.json` | LUMI catalog document |
| `protocol/v0_9_1/catalog.py` (new) | Resolve active catalog id + component type set |
| `protocol/v0_9_1/lint.py` | Validate against active catalog types |
| `protocol/v0_9_1/guides.py` | Generation guide for `lumi` |
| `protocol/v0_9_1/render_check.py` | Renderability for LUMI types |
| `protocol/types.py` / facade | Plumb `catalog` / `PROTOCOL_CATALOG` |
| `evaluate_api_model.py` | CLI `--protocol-catalog {basic,lumi}` |
| `render_v091/src/**` | Register/map LUMI components |
| `tests/protocol/test_v0_9_1_lumi_*.py` | Fixtures: unique component E2E lint + render_check |

---

### Task 1: Inventory Macaron → LUMI mapping

- [ ] List all `*_schema.json` under `vendor/a2ui_demo/resources/components/schemas/` (exclude envelope helpers).
- [ ] Write `docs/lumi-catalog-inventory.md` with columns: `0.8_name`, `class` (`map_basic` \| `lumi_unique` \| `skip`), `0.9.1_name`, `notes`.
- [ ] Minimum classifications:
  - map_basic examples: Label→Text, SelectionList→ChoicePicker, TickSlider→Slider, MarkdownView→Text (or keep unique if Markdown required).
  - lumi_unique examples: Carousel, RollPicker, PasswordKeypad, Map, FilterTags, SelectionWrap, SelectionGrid, OrderedSelectionList, PhotoInput, Rating, BottomBar.
- [ ] Commit: `docs(lumi): inventory Macaron schemas for 0.9.1 catalog mapping`

### Task 2: Author LUMI catalog.json (MVP subset)

- [ ] Create `protocol/v0_9_1/spec/catalogs/lumi/catalog.json` with:
  - `catalogId`: `lumi.ai:a2ui:lumi-catalog`
  - All official **basic** types (copy/alias from basic catalog for supersets)
  - **≥1 lumi_unique** type fully defined for MVP (recommend `Carousel` or `SelectionWrap`—pick one and document)
- [ ] Keep props in 0.9.1 style (flat component; native literals / `{path}`).
- [ ] Commit: `feat(lumi): add 0.9.1 LUMI catalog MVP JSON`

### Task 3: Protocol catalog switch

- [ ] Add `protocol/v0_9_1/catalog.py` with `BASIC_CATALOG_ID`, `LUMI_CATALOG_ID`, `get_catalog(name) -> CatalogInfo`.
- [ ] Extend facade / `ProtocolStack` (or parallel factory args) so stack knows `catalog_name` and exposes matching `catalog_id` + component allow-list + guide context.
- [ ] CLI: `--protocol-catalog {basic,lumi}` default `basic`; env `PROTOCOL_CATALOG`.
- [ ] Reject unknown catalog name with clear error.
- [ ] Tests: facade accepts both; basic stack catalog_id unchanged.
- [ ] Commit: `feat(protocol): add basic|lumi catalog selector on 0.9.1`

### Task 4: Lint + render_check + guides for LUMI

- [ ] `lint.py`: when catalog=lumi, allow LUMI types; require `createSurface.catalogId == LUMI_CATALOG_ID` (or accept both if createSurface uses LUMI id only—**lock: must match active catalog**).
- [ ] `render_check.py`: rules for MVP unique component; no 0.8-only assumptions.
- [ ] `guides.py`: LUMI generation guide listing basic + MVP unique types.
- [ ] Fixtures under `protocol/v0_9_1/fixtures/lumi/`: valid carousel (or chosen) UI; wrong catalogId; unknown type on basic.
- [ ] Commit: `feat(lumi): lint/render_check/guides for LUMI catalog MVP`

### Task 5: Lit / render_v091 registration

- [ ] Register MVP LUMI-unique component in `render_v091` (custom element or map to composition of basic widgets **only if** visually acceptable—prefer real registration).
- [ ] Ensure harness `processTurn` accepts messages with LUMI `catalogId`.
- [ ] Manual: `npm run build` in `render_v091`.
- [ ] Optional smoke HTML fixture loaded via query param.
- [ ] Commit: `feat(render_v091): register LUMI MVP component`

### Task 6: Eval wiring + scorecard update

- [ ] Thread `--protocol-catalog` through `evaluate_api_model.py` / `run_benchmark.sh`.
- [ ] Results manifest includes `protocol_catalog`.
- [ ] Update `docs/compatibility-scorecard.md`: set **D3≥1 AND D4≥1** only after MVP lint≡render on 0.9.1 LUMI catalog (not heritage D4).
- [ ] Commit: `feat(eval): wire PROTOCOL_CATALOG=lumi and update scorecard`

### Task 7: MVP acceptance

- [ ] Automated: pytest LUMI fixtures green.
- [ ] Manual or scripted: one message with LUMI-unique component passes lint → render_check → `render_v091` build ingest.
- [ ] PR merge when CI green.
