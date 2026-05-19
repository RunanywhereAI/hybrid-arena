#!/usr/bin/env bash
# v4 agent-hybrid overnight sweep orchestrator.
#
# Runs three real coding agents (R6 mini-swe-agent on SWE-bench Verified,
# R7 aider on Exercism Python, R8 opencode on real_dev D1+D5) under
# three routing strategies (always-cloud, always-local, heuristic).
# All output lands in results/runs/17-v4-agent-overnight/raw.jsonl.
#
# Resume-safe: re-running picks up where it left off. The resume check
# matches on (task_id, route, router_strategy).

set -o pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$ROOT/results/runs/17-v4-agent-overnight"
LOG="$OUT_DIR/sweep.log"
mkdir -p "$OUT_DIR" "$OUT_DIR/outputs"
# Redirect all output to the log file AND keep on stdout via a background
# tee. The original `exec > >(tee ...)` form is finicky inside detached
# bash; this is the boring-and-reliable equivalent.
exec >> "$LOG" 2>&1

now() { date -u +'%Y-%m-%dT%H:%M:%SZ'; }
log() { echo "[$(now)] $*"; }
log "=========================================================="
log "v4 agent-hybrid overnight sweep starting"
log "root: $ROOT"
log "out:  $OUT_DIR"
log "=========================================================="

cd "$ROOT"
if [ -f .env ]; then set -a; . ./.env; set +a; fi

PY="$ROOT/.venv/bin/python"
RUN="$PY -m hybrid_coding_eval.cli.run"

# Each invocation: --out shared, --resume on, --skip-scoring? no.
# Generated env-manifest will be reused across invocations.

# ---------------------------------------------------------------------------
# Phase 1 — runtime readiness
# ---------------------------------------------------------------------------
log "Phase 1 — runtime readiness"

# Make sure ollama is serving the local model the router will need.
ollama list 2>&1 | head -20 || true
for model in devstral:24b qwen3:0.6b nomic-embed-text; do
  if ollama list 2>/dev/null | awk 'NR>1 {print $1}' | grep -Fxq "$model" 2>/dev/null; then
    log "  ollama: $model present"
  else
    log "  ollama: pulling $model"
    ollama pull "$model" 2>&1 | tail -3 || log "  pull failed: $model"
  fi
done

log "  docker: pruning unused images/volumes…"
docker system prune -f 2>&1 | tail -2 || true
df -h / | tail -1 | awk '{print "  disk free: " $4}'

# ---------------------------------------------------------------------------
# Phase 2 — router proxy (reuse if already running)
# ---------------------------------------------------------------------------
log "Phase 2 — router proxy"

if curl -sf http://127.0.0.1:8787/healthz >/dev/null 2>&1; then
  log "  router already up — reusing"
else
  log "  router not up — starting via nohup"
  ( cd "$ROOT/router" && \
    LOCAL_MODEL=devstral:24b ROUTER_BANNER=1 \
    nohup ./start.sh > "$ROOT/router/logs/router-overnight.log" 2>&1 & )
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
fi

# ---------------------------------------------------------------------------
# Phase 3 — smoke (1 R7 task × always-cloud; aider is the fastest agent)
# ---------------------------------------------------------------------------
log "Phase 3 — smoke test"

$RUN --out "$OUT_DIR" \
     --routes R7 --categories X --tasks 1 \
     --router-strategy always-cloud \
     --skip-scoring 2>&1 | tail -30
SMOKE_RC=$?
if [ "$SMOKE_RC" -gt 2 ]; then
  log "  smoke ABORTED with exit $SMOKE_RC"
  exit 3
fi
log "  smoke completed (exit $SMOKE_RC); raw rows now: $(wc -l < "$OUT_DIR/raw.jsonl" 2>/dev/null || echo 0)"

# ---------------------------------------------------------------------------
# Phase 4 — full sweep
# 3 routes × 3 strategies = 9 invocations. Each invocation is one
# (route, category) pair. The matrix:
#   R7 (aider on Exercism)   × {always-cloud, always-local, heuristic}
#   R8 (opencode on D1+D5)   × {always-cloud, always-local, heuristic}
#   R6 (mini-swe-agent on SWE) × {always-cloud, always-local, heuristic}
# Order: R7 first (fastest), R8 second (medium), R6 last (slowest, SWE-bench
# Docker images). If R6 doesn't finish in budget, we still have R7+R8 data.
# ---------------------------------------------------------------------------
log "Phase 4 — full sweep"

run_phase() {
  local route="$1"; local category="$2"; local cap="$3"
  for strategy in always-cloud always-local heuristic; do
    log "  --- $route on $category (cap $cap) × $strategy ---"
    $RUN --out "$OUT_DIR" \
         --routes "$route" --categories "$category" --tasks "$cap" \
         --router-strategy "$strategy" \
         --resume 2>&1 | tail -200
    local rc=$?
    log "    $route × $strategy → exit $rc; raw rows: $(wc -l < "$OUT_DIR/raw.jsonl" 2>/dev/null || echo 0)"
    if [ "$rc" -gt 2 ]; then
      log "    fatal exit — continuing to next phase"
    fi
  done
}

# R7 first — Aider on 5 Exercism Python tasks. Each ~3-8min, total ~1-2h.
run_phase R7 X 5

# R8 second — opencode on first 4 real_dev tasks (whatever load_tasks returns).
# We expect D1 tasks to come first in load order; if not, the analysis groups
# by task_id regardless.
run_phase R8 D 4

# R6 last — mini-swe-agent on 6 SWE-bench Verified tasks. ~10-25min each.
# This is the biggest time consumer; ordering it last means if we run out of
# budget we still have R7+R8 results.
run_phase R6 B 6

# ---------------------------------------------------------------------------
# Phase 5 — analyze + report
# ---------------------------------------------------------------------------
log "Phase 5 — analyze + report"

REPORT="$ROOT/reports/AGENT_HYBRID_2026-05-19.md"
"$PY" "$ROOT/bin/agent-hybrid-analyze.py" "$OUT_DIR" > "$REPORT" 2>&1 || \
  log "  analyze script errored (report may be partial)"

log "=========================================================="
log "DONE — overnight sweep complete"
log "  raw rows:  $(wc -l < "$OUT_DIR/raw.jsonl" 2>/dev/null || echo 0)"
log "  report:    $REPORT"
log "  full log:  $LOG"
log "=========================================================="
