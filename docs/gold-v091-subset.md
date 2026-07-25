# 0.9.1 depth `gt_a2ui` gold subset (Track 3 / D5)

**Status:** partial (D5=1) — representative depth turns rewritten to valid **0.9.1 basic** gold.  
**Catalog:** `https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json`  
**Loader policy:** on protocol `0.9.1`, `filter_episode_gt_a2ui` **keeps** `gt_a2ui` when messages validate; **strips** legacy 0.8-shaped gold.

## Counts

| Metric | Value |
|--------|------:|
| Retained validating turns | **18** |
| Distinct `metadata.scenario_id` | **5** (S1–S5) |
| Tasks | 5 |

## Retained turns

`turn_idx` is **0-based** index into `context.episode_turns`.

| scenario_id | task_id | file | turn_idx |
|-------------|----------|------|----------|
| S1 | `depth_esconv_0e86e8a3` | `data/eval_300/esconv_tasks.json` | 0, 1, 2, 3 |
| S2 | `depth_esconv_85cb48cb` | `data/eval_300/esconv_tasks.json` | 0, 1, 2 |
| S3 | `depth_multiwoz_00940153` | `data/eval_300/multiwoz_tasks.json` | 0, 1, 2 |
| S4 | `depth_multiwoz_014c01ee` | `data/eval_300/multiwoz_tasks.json` | 0, 1, 2, 3 |
| S5 | `depth_sgd_a76584b4` | `data/eval_300/sgd_tasks.json` | 0, 1, 2, 3 |

Each retained `gt_a2ui` is a minimal valid batch: `createSurface` (basic `catalogId`) + `updateComponents` with `Column`/`Text` and `id: "root"`.

## Non-subset depth gold

All other `episode_turns[].gt_a2ui` in `data/eval_300` remain **0.8-shaped** and are stripped on the 0.9.1 eval path.
