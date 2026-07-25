#!/bin/bash
# Gate git commit until sync + pr-test-analyzer policy is done.
# After that, the agent should continue push → PR → CI → merge automatically.
# Bypass: ALLOW_GIT_COMMIT=1
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
  "user_message": "Pre-commit gate: sync + /pr-test-analyzer required, then full ship (push/PR/CI/merge) continues automatically.",
  "agent_message": (
      "Blocked pending ship workflow. Before ALLOW_GIT_COMMIT=1: "
      "(1) git fetch and sync/rebase onto updated base/upstream; "
      "(2) run Task subagent_type=pr-test-analyzer and resolve critical (8-10) gaps; "
      "(3) commit with ALLOW_GIT_COMMIT=1, then automatically push, create/update PR, "
      "watch CI, and merge when green — do not ask the user between those steps."
  ),
}))
PY
exit 0
