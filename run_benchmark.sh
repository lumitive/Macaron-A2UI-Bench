#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TASK_SOURCE_DIR="${TASK_SOURCE_DIR:-$SCRIPT_DIR/data/source}"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/.env}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

PROTOCOL_VERSION="${PROTOCOL_VERSION:-0.9.1}"
EVAL_SPLIT_DIR="${EVAL_SPLIT_DIR:-$SCRIPT_DIR/data/eval_300}"
RESULTS_DIR="${RESULTS_DIR:-$SCRIPT_DIR/results}"
VISUAL_COMPARE_DIR="${VISUAL_COMPARE_DIR:-$RESULTS_DIR/$PROTOCOL_VERSION/visual_compare_kimi25}"

JUDGE_MODEL="${JUDGE_MODEL:-openai/gpt-5.1}"
VLM_MODEL="${VLM_MODEL:-moonshotai/kimi-k2.5}"
if [[ -z "${RENDER_URL:-}" ]]; then
  if [[ "$PROTOCOL_VERSION" == "0.9.1" ]]; then
    RENDER_URL="http://127.0.0.1:5174/"
  else
    RENDER_URL="http://127.0.0.1:5173/"
  fi
fi
PROMPT_MODE="${PROMPT_MODE:-minimal}"
MODEL_CONCURRENCY="${MODEL_CONCURRENCY:-32}"
JUDGE_CONCURRENCY="${JUDGE_CONCURRENCY:-32}"
VISUAL_CONCURRENCY="${VISUAL_CONCURRENCY:-4}"
ENABLE_VISUAL_EVAL="${ENABLE_VISUAL_EVAL:-0}"
SEED="${SEED:-42}"
MODEL_LIST="${MODEL_LIST:-openai/gpt-4o-mini}"
VISUAL_MODEL_SLUGS="${VISUAL_MODEL_SLUGS:-openai__gpt-4o-mini}"

read -r -a MODELS <<< "$MODEL_LIST"
read -r -a VISUAL_SLUGS <<< "$VISUAL_MODEL_SLUGS"

python "$SCRIPT_DIR/prepare_eval_split.py" \
  --input-dir "$TASK_SOURCE_DIR" \
  --output-dir "$EVAL_SPLIT_DIR" \
  --per-difficulty 100 \
  --seed "$SEED"

python -u "$SCRIPT_DIR/evaluate_api_model.py" \
  --task-dir "$EVAL_SPLIT_DIR" \
  --sources annomi esconv multiwoz sgd \
  --models "${MODELS[@]}" \
  --judge-model "$JUDGE_MODEL" \
  --max-per-scenario 0 \
  --seed "$SEED" \
  --prompt-mode "$PROMPT_MODE" \
  --protocol-version "$PROTOCOL_VERSION" \
  --output-dir "$RESULTS_DIR" \
  --model-concurrency "$MODEL_CONCURRENCY" \
  --judge-concurrency "$JUDGE_CONCURRENCY"

if [[ "$ENABLE_VISUAL_EVAL" == "1" ]]; then
  python "$SCRIPT_DIR/visual_compare_models.py" \
    --results-dir "$RESULTS_DIR" \
    --protocol-version "$PROTOCOL_VERSION" \
    --model-slugs "${VISUAL_SLUGS[@]}" \
    --render-url "$RENDER_URL" \
    --vlm-model "$VLM_MODEL" \
    --max-workers "$VISUAL_CONCURRENCY" \
    --output-dir "$VISUAL_COMPARE_DIR"
else
  echo "Completed JSON-only L1/L2/L3 evaluation. Skipping optional visual eval (set ENABLE_VISUAL_EVAL=1 to enable)."
fi
