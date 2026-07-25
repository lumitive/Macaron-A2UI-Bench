# LUMI-A2UI-Bench Depth (Track 3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deepen the 0.9.1 evaluation path: protocol-correct L2 hints, jsonschema-backed L1, working `--prompt-mode full`, and a non-empty 0.9.1 depth `gt_a2ui` gold subset.

**Architecture:** Keep the protocol facade. Replace shallow structural-only L1 with schema validation layered on current lint. Lift the `full`+`0.9.1` hard error by assembling an in-context schema from vendored 0.9.1 + active catalog. Backfill gold surgically on depth tasks without silent conversion of model output.

**Tech Stack:** Python 3, `jsonschema`, existing pytest suite, vendored `protocol/v0_9_1/spec/`, prompt files under `prompts/`.

## Global Constraints

- Protocol CLI values remain exactly `0.8` and `0.9.1`.
- No silent conversion of model-produced 0.8 JSON to 0.9.1 for scoring.
- Default catalog remains `basic` unless Track 2 selector is used.
- Spec: `docs/superpowers/specs/2026-07-25-lumi-a2ui-bench-product-design.md`.
- Client↔server / catalog functions are **out of scope** (D8 stays 0).

---

## File map

| File | Responsibility |
|------|----------------|
| `evaluate_api_model.py` | `L2_RUBRIC_HINTS`; `resolve_generation_guide` full+0.9.1 |
| `prompts/l2_judge_v091.txt`, `l3_judge_v091.txt` | Judge copy alignment |
| `protocol/v0_9_1/lint.py` (+ optional `schema_validate.py`) | Deep jsonschema L1 |
| `protocol/v0_9_1/spec/**` | Envelope + catalog schemas already vendored |
| `system_prompt_full_v091.txt` (new) or generated artifact | Full 0.9.1 prompt body |
| `data/eval_300/**` (selected depth files) | 0.9.1 `gt_a2ui` backfill subset |
| `tests/protocol/test_v0_9_1_schema.py` | Schema validation cases |
| `docs/compatibility-scorecard.md` | D5–D7 score updates |

---

### Task 1: Fix L2_RUBRIC_HINTS + judge terminology (0.9.1)

- [ ] Split/select `L2_RUBRIC_HINTS` by protocol: keep 0.8 strings for 0.8 runs; for 0.9.1 replace stale terms (today mainly `dataModelUpdate` and any other 0.8 action names in that dict) with `updateDataModel` / `createSurface` / `ChoicePicker` as appropriate.
- [ ] Prefer structure: `L2_RUBRIC_HINTS_0_8` / `L2_RUBRIC_HINTS_0_9_1` selected by protocol version.
- [ ] Spot-check `prompts/l2_judge_v091.txt` / `l3_judge_v091.txt` (already largely 0.9.1); fix only real leftovers.
- [ ] Test: unit assert 0.9.1 hints contain `updateDataModel` (or `createSurface`) and not `dataModelUpdate`.
- [ ] Commit: `fix(eval): version L2 rubric hints for 0.9.1`
- [ ] Update scorecard D7 → 2 when done.

### Task 2: Deep jsonschema L1 on 0.9.1

- [ ] Add `protocol/v0_9_1/schema_validate.py` that validates message lists against vendored server_to_client (+ catalog component constraints as available).
- [ ] Integrate into `lint.py` **after** structural checks (or replace overlapping checks carefully—keep existing diagnostic code prefixes `STRUCT_` / `REF_` / `DATA_` / `LINT_`).
- [ ] Ensure `DATA_*` codes can fire on invalid bindings/values where schema expresses them.
- [ ] Fixtures: valid basic UI passes; deliberately broken prop type fails with schema-backed code.
- [ ] Commit: `feat(protocol): jsonschema-backed L1 for 0.9.1`
- [ ] Update scorecard D6b → 2 when done.

### Task 3: Enable `--prompt-mode full` for 0.9.1

- [ ] Remove hard error in `resolve_generation_guide` for `full`+`0.9.1`.
- [ ] Build full prompt from:
  - locked catalog rules text
  - component schema context for **active** catalog
  - short wire envelope summary (createSurface / updateComponents / updateDataModel / deleteSurface)
- [ ] Persist as `system_prompt_full_v091.txt` **or** generate at runtime (prefer checked-in file if stable).
- [ ] CLI help text: full supported on both protocols.
- [ ] Test: `resolve_generation_guide("full", stack_091)` returns non-empty and mentions `catalogId`.
- [ ] Commit: `feat(eval): support prompt-mode full on 0.9.1`
- [ ] Update scorecard D6a → 2 when done.

### Task 4: 0.9.1 depth gold subset

- [ ] Select a small depth subset (e.g. **10–20** episode turns across difficulties) from `data/eval_300` that currently embed 0.8 `gt_a2ui`.
- [ ] Hand/semi-auto rewrite those `gt_a2ui` arrays to valid **0.9.1 basic** (or LUMI if Track 2 catalog=lumi for those samples—default **basic** for this task).
- [ ] Loader change: on 0.9.1, **keep** `gt_a2ui` when messages validate as 0.9.1; still strip legacy 0.8-shaped gold (detect via lint or key heuristics).
- [ ] Document subset list in `docs/gold-v091-subset.md`.
- [ ] Test: stripped count decreases; subset samples retain gold; 0.8-shaped gold still stripped.
- [ ] Commit: `feat(data): backfill 0.9.1 gt_a2ui gold subset`
- [ ] Update scorecard D5 → 1 (subset) or 2 if expanded later.

### Task 5: Acceptance + docs

- [ ] `pytest tests/protocol` green.
- [ ] Smoke: `python evaluate_api_model.py --help` shows full mode for 0.9.1; dry-run one sample with `--prompt-mode full --protocol-version 0.9.1` (mock/no API if needed).
- [ ] Refresh `docs/compatibility-scorecard.md` totals.
- [ ] PR merge when CI green.

### Out of scope (do not implement here)

- D8 client↔server interactive scoring
- Full 300-task gold rewrite in one PR
- v1.0 protocol stack
