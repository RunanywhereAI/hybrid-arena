#!/usr/bin/env bash
# v3.3 Phase 6 + 7 launcher — runs after the master sweep (Phase 1-5) finishes.
#
# Phase 6: Classifier sub-sweep. Holds devstral/gpt-5.5/R3/llm-classifier
# strategy constant, varies the classifier model. Tests whether scaling
# the classifier model fixes llm-classifier's SWE-bench collapse.
#
# Phase 7: Cascade threshold sub-sweep. Holds devstral/gpt-5.5/R3/cascade
# strategy constant, varies the cascade threshold (5, 10, 15, 20, 25).
# Tests whether the heuristic-vs-LLM-tiebreak cutoff is well-tuned.
#
# Both phases require restarting the router with different env vars per
# variant — restart cost is ~5s, well-amortized over 50-task sweeps.
#
# Usage:
#   nohup caffeinate -i ./bin/v3.3-phase-6-7.sh > /tmp/v3.3-p67.log 2>&1 &
#
# Or to chain after the master sweep automatically:
#   ./bin/v3.3-wait-and-launch-p67.sh

set -e
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$HERE"

log() { echo "=== [$(date +%Y-%m-%d_%H:%M:%S)] $* ==="; }

restart_router() {
  local label="$1"
  shift
  pkill -f "node.*router/server.mjs" 2>/dev/null || true
  pkill -f "router/start.sh" 2>/dev/null || true
  sleep 3
  log "router restart for $label"
  ( cd router && env "$@" nohup ./start.sh > "/tmp/router-${label//[\/:]/-}.log" 2>&1 & )
  sleep 5
  if ! curl -s --max-time 3 http://127.0.0.1:8787/healthz | grep -q '"ok": *true'; then
    log "ERROR: router did not restart for $label"
    return 1
  fi
  log "router up: $label"
}

# Save original router env so we can restore at end
ORIG_ROUTER_MODEL="${ROUTER_MODEL:-qwen3:0.6b}"
ORIG_CASCADE="${ROUTER_CASCADE_THRESHOLD:-15}"

# ============================================================================
# PHASE 6 — classifier sub-sweep
# ============================================================================

log "=== Phase 6 — classifier sub-sweep ==="

# Four classifier candidates focused on the newer Qwen3.5 family + one
# code-specialized variant. The qwen3:0.6b baseline is reused from v3.2
# Phase 1 variant 14 (50 rows already in results/runs/14-r3-strategy-
# llm-classifier/) — no need to re-run it.
#
# Why this lineup:
#   - Qwen3.5 is the newest Qwen general-purpose family available with
#     small variants on Ollama (Qwen3-Coder has only 30B+; Qwen3.6 has
#     only 27B+; both unsuitable for the classifier role).
#   - Three Qwen3.5 sizes (0.8b/2b/4b) span the classifier-scale spectrum
#     and let us measure "does scaling the classifier fix llm-classifier's
#     SWE-bench collapse?"
#   - qwen2.5-coder:1.5b is the code-specialized control — does a model
#     trained on code route code tasks better than a generalist?
CLASSIFIERS=(
  "qwen3.5:0.8b"         # Qwen3.5 small — direct competitor to qwen3:0.6b baseline
  "qwen3.5:2b"           # Qwen3.5 mid
  "qwen3.5:4b"           # Qwen3.5 big
  "qwen2.5-coder:1.5b"   # code-specialized small (1.5B params, code-trained)
)

for C in "${CLASSIFIERS[@]}"; do
  SLUG="${C//[:\/]/-}"
  OUTDIR="results/runs/p6-classifier-${SLUG}"
  log "Phase 6 — classifier=${C} → ${OUTDIR}"

  # Skip if already done
  if [ -f "$OUTDIR/raw.jsonl" ] && [ "$(wc -l < "$OUTDIR/raw.jsonl" | tr -d ' ')" -ge 50 ]; then
    log "  SKIP — already has 50+ rows"
    continue
  fi

  restart_router "classifier-${SLUG}" ROUTER_MODEL="$C" ROUTER_CASCADE_THRESHOLD="15"

  ./bench run --config configs/variants/14-r3-strategy-llm-classifier.yaml \
    --set out_dir="$OUTDIR" \
    --resume || log "WARN: Phase 6 ${C} failed; continuing"

  log "Phase 6 — classifier=${C} done"
done

# ============================================================================
# PHASE 7 — cascade threshold sub-sweep
# ============================================================================

log "=== Phase 7 — cascade threshold sub-sweep ==="

THRESHOLDS=(5 10 15 20 25)

for T in "${THRESHOLDS[@]}"; do
  OUTDIR="results/runs/p7-cascade-threshold-${T}"
  log "Phase 7 — threshold=${T} → ${OUTDIR}"

  if [ -f "$OUTDIR/raw.jsonl" ] && [ "$(wc -l < "$OUTDIR/raw.jsonl" | tr -d ' ')" -ge 50 ]; then
    log "  SKIP — already has 50+ rows"
    continue
  fi

  restart_router "cascade-t${T}" ROUTER_MODEL="qwen3:0.6b" ROUTER_CASCADE_THRESHOLD="$T"

  ./bench run --config configs/variants/16-r3-strategy-cascade.yaml \
    --set out_dir="$OUTDIR" \
    --resume || log "WARN: Phase 7 threshold=${T} failed; continuing"

  log "Phase 7 — threshold=${T} done"
done

# ============================================================================
# Restore original router state
# ============================================================================

log "Restoring original router state (ROUTER_MODEL=${ORIG_ROUTER_MODEL}, CASCADE=${ORIG_CASCADE})"
restart_router "restore" ROUTER_MODEL="$ORIG_ROUTER_MODEL" ROUTER_CASCADE_THRESHOLD="$ORIG_CASCADE"

# ============================================================================
# Re-analyze + refresh article
# ============================================================================

log "Re-analyze + refresh article"
for D in results/runs/p6-classifier-*/ results/runs/p7-cascade-threshold-*/; do
  [ -d "$D" ] || continue
  ./bench analyze "$D" || true
  ./bench rejudge "$D" || true
done

./bin/v3.3-refresh-article.sh --commit || true
git push origin main 2>&1 | tail -3 || true

log "Phase 6 + 7 complete."
