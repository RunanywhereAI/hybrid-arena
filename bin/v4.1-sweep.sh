#!/usr/bin/env bash
# v4.1 agent-hybrid sweep orchestrator.
#
# Runs R6/R7/R8 against the v4 task subset under 4 routing strategies
# (always-cloud, always-local, heuristic, agent-heuristic) with
# qwen3-coder:30b as local. All output → results/runs/18-v4.1-qwen3coder-agent/.

set -o pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$ROOT/results/runs/18-v4.1-qwen3coder-agent"
LOG="$OUT_DIR/sweep.log"
mkdir -p "$OUT_DIR/outputs"
exec >> "$LOG" 2>&1

now() { date -u +'%Y-%m-%dT%H:%M:%SZ'; }
log() { echo "[$(now)] $*"; }
log "=========================================================="
log "v4.1 agent-hybrid sweep starting (local=qwen3-coder:30b)"
log "=========================================================="

cd "$ROOT"
[ -f .env ] && { set -a; . ./.env; set +a; }

PY="$ROOT/.venv/bin/python"
RUN="$PY -m hybrid_coding_eval.cli.run"

# Phase 1 — restart router with qwen3-coder as local
log "Phase 1 — router restart with LOCAL_MODEL=qwen3-coder:30b"
pkill -f "node server.mjs" 2>/dev/null || true
sleep 2
( cd "$ROOT/router" && LOCAL_MODEL=qwen3-coder:30b ROUTER_BANNER=1 \
  nohup ./start.sh > logs/router-v4.1.log 2>&1 & )
for i in 1 2 3 4 5 6 7 8 9 10; do
  sleep 3
  if curl -sf http://127.0.0.1:8787/healthz >/dev/null 2>&1; then
    log "  router up (poll $i)"
    break
  fi
  if [ "$i" = "10" ]; then
    log "  router failed to come up — aborting"
    exit 2
  fi
done

# Phase 2 — Smoke (R7 × always-cloud × 1)
log "Phase 2 — smoke (R7 × always-cloud × 1)"
$RUN --out "$OUT_DIR" --routes R7 --categories X --tasks 1 \
     --router-strategy always-cloud --skip-scoring 2>&1 | tail -10
SRC=$?
log "  smoke exit $SRC"

# Phase 3 — Full sweep: route × strategy × tasks
log "Phase 3 — full sweep"

run_phase() {
  local route="$1"; local cat="$2"; local cap="$3"
  for strategy in always-cloud always-local heuristic agent-heuristic; do
    log "  --- $route on $cat (cap $cap) × $strategy ---"
    $RUN --out "$OUT_DIR" \
         --routes "$route" --categories "$cat" --tasks "$cap" \
         --router-strategy "$strategy" \
         --resume 2>&1 | tail -100
    local rc=$?
    log "    $route × $strategy → exit $rc; rows: $(wc -l < "$OUT_DIR/raw.jsonl" 2>/dev/null || echo 0)"
  done
}

# Order: R7 fastest first, then R8, then R6 (slowest)
run_phase R7 X 5
run_phase R8 D 4
run_phase R6 B 6

# Phase 4 — analyze + report (merge v4 + v4.1)
log "Phase 4 — analyze + report"
REPORT="$ROOT/reports/AGENT_HYBRID_v4.1_2026-05-19.md"
"$PY" "$ROOT/bin/agent-hybrid-analyze.py" "$OUT_DIR" > "$REPORT" 2>&1 || \
  log "  analyze errored"
log "=========================================================="
log "DONE — v4.1 sweep complete"
log "  rows: $(wc -l < "$OUT_DIR/raw.jsonl" 2>/dev/null || echo 0)"
log "  report: $REPORT"
log "=========================================================="
