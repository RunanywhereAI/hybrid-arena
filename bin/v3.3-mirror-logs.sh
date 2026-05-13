#!/usr/bin/env bash
# Periodic mirror: /tmp/v3.3-*.log → logs/v3.3/ every 5 min.
# Runs as a side-process to the master sweep so log loss from /tmp wipe
# (reboot, OS cleanup) is bounded to <5 min of drift.
#
# Usage:
#   nohup ./bin/v3.3-mirror-logs.sh > /tmp/v3.3-mirror.log 2>&1 &
#
# Polls forever until killed. Idempotent — re-running just refreshes.

set -e
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$HERE"

DEST="logs/v3.3"
mkdir -p "$DEST"

mirror_one() {
  local src="$1" dst="$2"
  if [ -f "$src" ]; then
    cp -f "$src" "$dst" 2>/dev/null || true
  fi
}

while true; do
  mirror_one /tmp/v3.3-sweep.log         "$DEST/master-sweep.log"
  mirror_one /tmp/v3.3-watcher.log       "$DEST/watcher.log"
  mirror_one /tmp/v3.3-pull.log          "$DEST/initial-model-pulls.log"
  mirror_one /tmp/phase6-classifier-pulls.log "$DEST/phase6-classifier-pulls.log"
  mirror_one /tmp/phase6-qwen35-pulls.log     "$DEST/phase6-qwen35-pulls.log"
  mirror_one /tmp/gemma4-31b-pull.log    "$DEST/gemma4-31b-pull.log"

  # Phase 6+7 router-restart logs (one per classifier / threshold variant)
  for f in /tmp/router-classifier-*.log /tmp/router-cascade-t*.log /tmp/router-restore.log; do
    [ -f "$f" ] && cp -f "$f" "$DEST/$(basename $f)" 2>/dev/null || true
  done

  # Phase 8 logs (when they exist)
  mirror_one /tmp/v3.3-p67.log           "$DEST/phase-6-7.log"

  # Smoke test logs (full dir)
  if [ -d /tmp/v3.3-smoke ]; then
    rsync -aq /tmp/v3.3-smoke/ "$DEST/smoke-tests/" 2>/dev/null || cp -r /tmp/v3.3-smoke/* "$DEST/smoke-tests/" 2>/dev/null || true
  fi

  sleep 300   # 5 min
done
