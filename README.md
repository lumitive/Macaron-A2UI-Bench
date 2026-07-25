# LUMI A2UI Bench

Standalone benchmark for evaluating A2UI JSON generation (**LUMI-A2UI-Bench**).

This repository is organized around a **JSON-first evaluation path**: the main benchmark reads model JSON outputs and computes L1/L2/L3 scores without requiring a render service. Render- and VLM-based visual checks are available as an **optional extension**, not the default workflow.

The benchmark supports two A2UI protocol stacks in parallel:

- **v0.9.1** (default): modern flat-component messages; official **basic** catalog by default; results under `./results/0.9.1/`; optional renderer in `render_v091/` on port **5174**
- **v0.8** (legacy comparison): key-wrapped messages; results under `./results/0.8/`; optional renderer in `render/` on port **5173**

**Heritage:** the 0.8 extended component schemas live in `vendor/a2ui_demo` (**LUMI 0.8 source**). The LUMI extended catalog on 0.9.1 is selected with `--protocol-catalog lumi` (Track 2). Default eval remains official basic 0.9.1.

Select a stack with `--protocol-version` on Python CLIs or `PROTOCOL_VERSION` in `run_benchmark.sh`. To compare against the legacy stack:

```bash
PROTOCOL_VERSION=0.8 bash run_benchmark.sh
```

## What Is Core vs Optional

Core path:

- Generate or reuse task JSONs
- Run `evaluate_api_model.py`
- Score L1/L2/L3 from JSON outputs

Optional extension:

- Start `render/` or `render_v091/`
- Run `visual_eval.py` or `visual_compare_models.py`
- Add VLM-based visual scoring on top of the JSON benchmark

## Repository Layout

- `evaluate_api_model.py`: main JSON-based L1/L2/L3 evaluator for API models.
- `prepare_eval_split.py`: build a fixed-size eval split from the bundled source tasks.
- `run_benchmark.sh`: default JSON-first pipeline. Visual stage stays off unless explicitly enabled.
- `data/eval_300/`: bundled 300-task benchmark split.
- `data/source/`: bundled source task files used for resampling.
- `visual_eval.py`: optional render + screenshot + VLM-based visual scoring.
- `visual_compare_models.py`: optional cross-model visual comparison.
- `render/`: optional bundled **v0.8** renderer project (port 5173).
- `render_v091/`: optional bundled **v0.9.1** renderer project (port 5174).
- `vendor/a2ui_demo/`: LUMI 0.8 heritage lint/schema assets (and 0.8 stack).
- `render/vendor/a2ui/renderers/`: bundled local renderer packages required only by `render/`.
- `docs/compatibility-scorecard.md`: living OII / LEI / EDI compatibility scorecard.

## Python Setup

Core JSON benchmark only:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If you also want visual evaluation:

```bash
pip install -r requirements-visual.txt
```

Create local env file:

```bash
cp .env.example .env
```

Set at least:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL` if you are not using the default OpenRouter-compatible endpoint

## Default Path: JSON L1-L3

Run the default JSON evaluation pipeline:

```bash
bash run_benchmark.sh
```

By default this will:

1. Build a sampled eval set from bundled `./data/source`.
2. Run JSON-based API evaluation.
3. Compute L1/L2/L3 outputs into `./results/<protocol-version>/` (default `./results/0.9.1/`).
4. Skip render/VLM entirely unless `ENABLE_VISUAL_EVAL=1`.

If you want to use the bundled fixed split directly:

```bash
python -u evaluate_api_model.py \
  --task-dir ./data/eval_300 \
  --sources annomi esconv multiwoz sgd \
  --models openai/gpt-4o-mini \
  --judge-model openai/gpt-5.1 \
  --max-per-scenario 0 \
  --seed 42 \
  --prompt-mode minimal \
  --protocol-version 0.9.1 \
  --output-dir ./results \
  --model-concurrency 8 \
  --judge-concurrency 8
```

## Optional Path: Visual Evaluation

Only use this if you specifically want render- and VLM-based visual checks in addition to the JSON benchmark.

Install optional Python deps first:

```bash
pip install -r requirements-visual.txt
```

Start the compatible local renderer in another terminal (match `--protocol-version` / `PROTOCOL_VERSION`):

**v0.9.1 (default):**

```bash
cd render_v091
npm install
npm run dev
```

**v0.8:**

```bash
cd render
npm install
npm run dev
```

Then enable visual eval in the pipeline (see `run_benchmark.sh` / `ENABLE_VISUAL_EVAL`).

## Compatibility scorecard

Living measurement instrument: [`docs/compatibility-scorecard.md`](docs/compatibility-scorecard.md) (OII / LEI / EDI; Business Scenario B*).

## License / upstream

See `UPSTREAM.md` for vendored trees and dual-stack notes. Upstream A2UI / Google license headers are preserved.
