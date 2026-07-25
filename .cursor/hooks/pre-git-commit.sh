#!/bin/bash
# Soft-gate git commit: ask unless ALLOW_GIT_COMMIT=1
# (honor-system after sync + full /review-pr with no unresolved Critical findings).
# After allow, the agent should continue push → PR → CI → merge automatically.
set -euo pipefail

input=$(cat)
command=$(printf '%s' "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("command",""))')

if [[ ! "$command" =~ git[[:space:]]+commit ]]; then
  echo '{ "permission": "ask" }'
  exit 0
fi

if [[ "${ALLOW_GIT_COMMIT:-}" == "1" ]]; then
  echo '{ "permission": "allow" }'
  exit 0
fi

python3 - <<'PY'
import json
print(json.dumps({
  "permission": "ask",
  "user_message": "Pre-commit gate: sync + full /review-pr (tests+code+errors+comments+types+simplify) required, then ship continues automatically.",
  "agent_message": (
      "Blocked pending ship workflow. Before ALLOW_GIT_COMMIT=1: "
      "(1) git fetch and sync/rebase onto updated base/upstream; "
      "(2) run full /review-pr via parallel Task agents — pr-test-analyzer, "
      "code-reviewer, silent-failure-hunter, comment-analyzer, "
      "type-design-analyzer, code-simplifier (recommend-only) — each must return "
      "a usable report; resolve Critical findings "
      "(tests 8-10/BLOCK; other agents Critical/BLOCK/confidence>=80); "
      "(3) commit with ALLOW_GIT_COMMIT=1, then automatically push, create/update PR, "
      "watch CI, and merge when green — do not ask the user between those steps."
  ),
}))
PY
exit 0
