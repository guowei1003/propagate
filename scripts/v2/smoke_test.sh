#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"
SMOKE_TIMEOUT_SEC="${SMOKE_TIMEOUT_SEC:-30}"
PROFILE_NAME="smoke-demo-$(date +%s)"

TMP_PROFILE_PAYLOAD="$(mktemp)"
cat > "$TMP_PROFILE_PAYLOAD" <<'JSON'
{
  "name": "__PROFILE_NAME__",
  "provider_type": "demo",
  "api_base_url": "",
  "api_key": "",
  "default_model": "demo-heuristic",
  "review_model": "",
  "test_model": "",
  "capability_generation_model": "",
  "report_model": "",
  "temperature": 0.2,
  "default_timeout_sec": 300,
  "max_retries": 2,
  "max_concurrency": 2,
  "enable_docker_sandbox": true,
  "enable_auto_sub_agents": true
}
JSON
python3 - <<PY
from pathlib import Path
path = Path("$TMP_PROFILE_PAYLOAD")
path.write_text(path.read_text(encoding="utf-8").replace("__PROFILE_NAME__", "$PROFILE_NAME"), encoding="utf-8")
PY

PROFILE_JSON="$(curl -fsS -X POST "${API_BASE_URL}/v2/env-profiles" -H 'Content-Type: application/json' --data @"$TMP_PROFILE_PAYLOAD")"
PROFILE_ID="$(printf '%s' "$PROFILE_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"

TASK_JSON="$(curl -fsS -X POST "${API_BASE_URL}/v2/tasks" -H 'Content-Type: application/json' --data "{\"title\":\"smoke\",\"prompt\":\"实现后端与前端工作台\",\"env_profile_id\":\"${PROFILE_ID}\",\"model_overrides\":{}}")"
TASK_ID="$(printf '%s' "$TASK_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
RUN_ID="$(printf '%s' "$TASK_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["run"]["id"])')"

TASK_DETAIL="$(curl -fsS "${API_BASE_URL}/v2/tasks/${TASK_ID}")"
TASK_DETAIL_FILE="$(mktemp)"
printf '%s' "$TASK_DETAIL" > "$TASK_DETAIL_FILE"

python3 - "$TASK_DETAIL_FILE" <<'PY' | while IFS= read -r capability_id; do
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as fh:
    task = json.load(fh)
ids = []
for subtask in task.get("subtasks", []):
    for binding in subtask.get("capability_bindings", []):
        ids.append(binding["capability_id"])
print("\n".join(ids))
PY
  [[ -z "$capability_id" ]] && continue
  APPROVAL_JSON="$(curl -fsS -X POST "${API_BASE_URL}/v2/capabilities/${capability_id}/approve" \
    -H 'Content-Type: application/json' \
    --data '{"approver":"smoke-test","comment":"auto approve for smoke"}')"
  STATUS="$(printf '%s' "$APPROVAL_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
  [[ "$STATUS" == "approved" ]] || { echo "Capability 审批失败: ${capability_id}" >&2; exit 1; }
done

curl -fsS -X POST "${API_BASE_URL}/v2/runs/${RUN_ID}/resume" >/dev/null

START_TS="$(date +%s)"
while true; do
  TASK_DETAIL="$(curl -fsS "${API_BASE_URL}/v2/tasks/${TASK_ID}")"
  STATUS="$(printf '%s' "$TASK_DETAIL" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
  if [[ "$STATUS" == "COMPLETED" || "$STATUS" == "PARTIAL_SUCCESS" ]]; then
    break
  fi
  NOW_TS="$(date +%s)"
  if (( NOW_TS - START_TS > SMOKE_TIMEOUT_SEC )); then
    echo "Smoke test 超时，task=${TASK_ID} run=${RUN_ID}" >&2
    printf '%s' "$TASK_DETAIL" | python3 -c 'import json,sys; print(json.dumps(json.load(sys.stdin).get("events", [])[-10:], ensure_ascii=False, indent=2))' >&2
    exit 1
  fi
  sleep 1
done

BUNDLE_JSON="$(curl -fsS -X POST "${API_BASE_URL}/v2/runs/${RUN_ID}/bundle/build")"
MANIFEST_PATH="$(printf '%s' "$BUNDLE_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["manifest_path"])')"
[[ -n "$MANIFEST_PATH" ]] || { echo "Bundle manifest path 为空" >&2; exit 1; }

echo "Smoke test 完成：task=${TASK_ID} run=${RUN_ID}"
