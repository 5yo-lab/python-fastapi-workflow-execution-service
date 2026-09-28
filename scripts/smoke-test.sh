#!/usr/bin/env bash
# Full docker-compose smoke test for the workflow execution service.
# Usage: ./scripts/smoke-test.sh
#        API_BASE_URL=http://localhost:8000 ./scripts/smoke-test.sh

set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
PGADMIN_URL="${PGADMIN_URL:-http://localhost:5050}"
VALIDATION_POLL_SECONDS="${VALIDATION_POLL_SECONDS:-40}"
PROCESSING_POLL_SECONDS="${PROCESSING_POLL_SECONDS:-60}"
POLL_INTERVAL_SECONDS="${POLL_INTERVAL_SECONDS:-2}"
SKIP_FRONTEND="${SKIP_FRONTEND:-0}"
SKIP_PGADMIN="${SKIP_PGADMIN:-0}"
SHOW_WORKER_LOGS="${SHOW_WORKER_LOGS:-0}"

failures=()

pass() { echo "[PASS] $*"; }
fail() { echo "[FAIL] $*"; failures+=("$*"); }

get_workflow() {
  curl -sf "$API_BASE_URL/workflows/$1"
}

apply_transition() {
  local workflow_id="$1"
  local version="$2"
  local action="$3"
  curl -sf -X POST "$API_BASE_URL/workflows/$workflow_id/transitions" \
    -H "Content-Type: application/json" \
    -d "{\"action\":\"$action\",\"expectedVersion\":$version}"
}

wait_for_state() {
  local workflow_id="$1"
  local label="$2"
  local max_seconds="$3"
  shift 3
  local target_states=("$@")

  local max_polls=$(( (max_seconds + POLL_INTERVAL_SECONDS - 1) / POLL_INTERVAL_SECONDS ))
  local workflow state

  for ((i = 1; i <= max_polls; i++)); do
    sleep "$POLL_INTERVAL_SECONDS"
    workflow="$(get_workflow "$workflow_id")"
    state="$(echo "$workflow" | jq -r '.state')"
    echo "  ${label} poll ${i}: state=${state} version=$(echo "$workflow" | jq -r '.version')"

    for target in "${target_states[@]}"; do
      if [[ "$state" == "$target" ]]; then
        echo "$workflow"
        return 0
      fi
    done

    if [[ "$state" == "VALIDATION_FAILED" || "$state" == "CANCELLED" || "$state" == "PROCESSING_FAILED" ]]; then
      echo "$workflow"
      return 1
    fi
  done

  echo "$workflow"
  return 1
}

echo ""
echo "=== Workflow Execution Service - Smoke Tests ==="
echo "API:      $API_BASE_URL"
echo "Frontend: $FRONTEND_URL"
echo "pgAdmin:  $PGADMIN_URL"
echo ""

if curl -sf "$API_BASE_URL/health" | jq -e '.status == "ok"' >/dev/null; then
  pass "GET /health"
else
  fail "GET /health"
fi

reference="SMOKE-$(date +%Y%m%d-%H%M%S)"
workflow="$(curl -sf -X POST "$API_BASE_URL/workflows" \
  -H "Content-Type: application/json" \
  -d "{\"reference\":\"$reference\",\"payload\":{\"customerId\":\"smoke-customer\",\"amount\":250}}")" \
  || { fail "POST /workflows"; echo "FAILED: cannot continue without a workflow."; exit 1; }

workflow_id="$(echo "$workflow" | jq -r '.id')"
pass "POST /workflows - id=$workflow_id state=$(echo "$workflow" | jq -r '.state')"

workflow="$(apply_transition "$workflow_id" "$(echo "$workflow" | jq -r '.version')" "START_VALIDATION")" \
  && pass "START_VALIDATION -> $(echo "$workflow" | jq -r '.state')" \
  || fail "START_VALIDATION"

if validated="$(wait_for_state "$workflow_id" "validation" "$VALIDATION_POLL_SECONDS" "APPROVED")"; then
  workflow="$validated"
  pass "Worker validation -> APPROVED"
else
  workflow="$validated"
  fail "Worker validation stuck at $(echo "$workflow" | jq -r '.state')"
fi

state="$(echo "$workflow" | jq -r '.state')"
if [[ "$state" == "APPROVED" ]]; then
  workflow="$(apply_transition "$workflow_id" "$(echo "$workflow" | jq -r '.version')" "START_PROCESSING")" \
    && pass "START_PROCESSING -> $(echo "$workflow" | jq -r '.state')" \
    || fail "START_PROCESSING"
fi

completed=0
for attempt in 1 2 3; do
  state="$(echo "$workflow" | jq -r '.state')"
  [[ "$state" == "PROCESSING" ]] || break

  if processed="$(wait_for_state "$workflow_id" "processing (attempt $attempt)" "$PROCESSING_POLL_SECONDS" "COMPLETED")"; then
    workflow="$processed"
    completed=1
    break
  fi

  workflow="$processed"
  state="$(echo "$workflow" | jq -r '.state')"
  if [[ "$state" == "PROCESSING_FAILED" ]]; then
    echo "  simulated processing failure, retrying START_PROCESSING..."
    workflow="$(apply_transition "$workflow_id" "$(echo "$workflow" | jq -r '.version')" "START_PROCESSING")"
    continue
  fi
  break
done

if [[ "$completed" -eq 1 ]]; then
  pass "Worker processing -> COMPLETED"
elif [[ "$(echo "$workflow" | jq -r '.state')" != "APPROVED" ]]; then
  fail "Worker processing stuck at $(echo "$workflow" | jq -r '.state')"
fi

if history="$(curl -sf "$API_BASE_URL/workflows/$workflow_id/history")"; then
  actions="$(echo "$history" | jq -r '[.[].action] | join(" -> ")')"
  pass "GET /workflows/$workflow_id/history - $(echo "$history" | jq 'length') entries: $actions"
else
  fail "GET /history"
fi

if list="$(curl -sf "$API_BASE_URL/workflows")"; then
  pass "GET /workflows - $(echo "$list" | jq 'length') workflow(s)"
else
  fail "GET /workflows"
fi

if [[ "$SKIP_FRONTEND" != "1" ]]; then
  if curl -sf -o /dev/null "$FRONTEND_URL"; then
    pass "Frontend $FRONTEND_URL"
  else
    fail "Frontend $FRONTEND_URL"
  fi
fi

if [[ "$SKIP_PGADMIN" != "1" ]]; then
  if curl -sf -o /dev/null "$PGADMIN_URL" || curl -s -o /dev/null -w "%{http_code}" "$PGADMIN_URL" | grep -Eq '200|301|302'; then
    pass "pgAdmin $PGADMIN_URL"
  else
    fail "pgAdmin $PGADMIN_URL"
  fi
fi

if [[ "$SHOW_WORKER_LOGS" == "1" ]]; then
  echo ""
  echo "=== Worker logs (last 20 lines) ==="
  docker logs workflow-node-worker 2>&1 | tail -20
fi

echo ""
echo "=== Summary ==="
if [[ "${#failures[@]}" -eq 0 ]]; then
  echo "All smoke tests PASSED"
  exit 0
fi

echo "Smoke tests FAILED (${#failures[@]} issue(s)):"
for item in "${failures[@]}"; do
  echo "  - $item"
done
exit 1
