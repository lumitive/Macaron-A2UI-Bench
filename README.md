# Macaron A2UI Bench

Standalone benchmark for evaluating A2UI JSON generation.

This repository is organized around a **JSON-first evaluation path**: the main benchmark reads model JSON outputs and computes L1/L2/L3 scores without requiring a render service. Render- and VLM-based visual checks are available as an **optional extension**, not the default workflow.

## What Is Core vs Optional

Core path:

- Generate or reuse task JSONs
- Run `evaluate_api_model.py`
- Score L1/L2/L3 from JSON outputs

Optional extension:

- Start `render/`
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
- `render/`: optional bundled renderer project.
- `vendor/a2ui_demo/`: bundled A2UI lint/schema assets required by the evaluator.
- `render/vendor/a2ui/renderers/`: bundled local renderer packages required only by `render/`.

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
3. Compute L1/L2/L3 outputs into `./results`.
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

Start the bundled renderer in another terminal:

```bash
cd render
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Sanity check:

```bash
curl -I http://127.0.0.1:5173/
```

Then enable the optional stage:

```bash
ENABLE_VISUAL_EVAL=1 bash run_benchmark.sh
```

Or run visual comparison directly:

```bash
python visual_compare_models.py \
  --results-dir ./results \
  --model-slugs openai__gpt-4o-mini \
  --render-url http://127.0.0.1:5173/ \
  --vlm-model moonshotai/kimi-k2.5 \
  --max-workers 2 \
  --output-dir ./results/visual_compare
```

## Key Environment Variables

- `TASK_SOURCE_DIR`: source task directory, default `./data/source`
- `EVAL_SPLIT_DIR`: sampled/fixed task directory, default `./data/eval_300`
- `RESULTS_DIR`: JSON evaluation outputs, default `./results`
- `MODEL_LIST`: space-separated API model list, default `openai/gpt-4o-mini`
- `ENABLE_VISUAL_EVAL`: set `1` only when you want the optional visual stage
- `VISUAL_MODEL_SLUGS`: space-separated result folder slugs for visual comparison, default `openai__gpt-4o-mini`
- `RENDER_URL`: visual renderer URL, default `http://127.0.0.1:5173/`
- `MODEL_CONCURRENCY`, `JUDGE_CONCURRENCY`, `VISUAL_CONCURRENCY`: concurrency controls

## Notes

- The intended open-source default is **JSON L1-L3 evaluation**, not render/VLM.
- The repo bundles the validator/schema subset required by the evaluator under `vendor/a2ui_demo/`.
- The repo bundles local renderer package dependencies under `render/vendor/a2ui/renderers/` so `render/` can be installed independently when needed.
- Do not commit real API keys. `.env` is ignored.
