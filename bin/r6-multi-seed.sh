#!/usr/bin/env bash
# Track D — Multi-seed R6 cloud baseline.
#
# Re-runs R6 × always-cloud on the same 6 SWE-bench tasks 3 times back to
# back. mini-swe-agent v2 is intrinsically stochastic (the LLM is at temp 0.2,
# small natural variance) and we can't pass an explicit seed downstream
# without a fork, so the 3 re-runs serve as the seed surrogate. Each run
# writes to a SEPARATE raw.jsonl so we can compute per-task pass-rate
# variance.

set -o pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_BASE="$ROOT/results/runs/19-r6-multi-seed"
LOG="$OUT_BASE/sweep.log"
mkdir -p "$OUT_BASE"
exec >> "$LOG" 2>&1

now() { date -u +'%Y-%m-%dT%H:%M:%SZ'; }
log() { echo "[$(now)] $*"; }
log "=========================================================="
log "R6 multi-seed start (3 re-runs of always-cloud × 6 tasks)"
log "=========================================================="

cd "$ROOT"
[ -f .env ] && { set -a; . ./.env; set +a; }

PY="$ROOT/.venv/bin/python"

for run_id in run-a run-b run-c; do
  RUN_DIR="$OUT_BASE/$run_id"
  mkdir -p "$RUN_DIR/outputs"
  log "  ----- $run_id -----"
  $PY -m hybrid_coding_eval.cli.run \
     --out "$RUN_DIR" \
     --routes R6 --categories B --tasks 6 \
     --router-strategy always-cloud \
     --resume 2>&1 | tail -50
  rc=$?
  log "    $run_id → exit $rc; rows: $(wc -l < "$RUN_DIR/raw.jsonl" 2>/dev/null || echo 0)"
done

log "=========================================================="
log "R6 multi-seed DONE"
log "  base: $OUT_BASE"
log "=========================================================="
