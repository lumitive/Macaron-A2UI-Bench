#!/bin/bash
# Remind / gate git commit until sync + pr-test-analyzer policy is acknowledged.
# Bypass for this session: ALLOW_GIT_COMMIT=1
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
  "user_message": "Pre-commit policy: sync with remote, then run /pr-test-analyzer, then approve this commit.",
  "agent_message": (
      "Blocked pending commit workflow. Before allowing git commit: "
      "(1) git fetch and sync/rebase onto updated base/upstream; "
      "(2) run Task subagent_type=pr-test-analyzer on the pending diff and resolve critical (8-10) gaps; "
      "(3) re-run the commit with ALLOW_GIT_COMMIT=1 only after both steps are done."
  ),
}))
PY
exit 0
