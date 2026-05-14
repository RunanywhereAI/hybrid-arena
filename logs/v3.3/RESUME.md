# v3.3 sweep — resume from pause

**Paused at: 2026-05-13 17:59 PDT**

## State at pause

```
✅ Phase 1 — v3.2 strategy sweep on devstral          variants 12-16  250 rows  done
✅ Phase 2 — qwen3-coder:30b heuristic baseline       variant  17     200 rows  done
✅ Phase 3 — qwen2.5-coder:32b heuristic baseline     variant  18     200 rows  done
🔄 Phase 4 — glm-4.7-flash heuristic baseline         variant  19      83/200   PAUSED MID-FLIGHT
⏸ Phase 5 — gemma4:31b heuristic baseline             variant  20     pending
⏸ Phase 6 — classifier sub-sweep                      4 variants      pending
⏸ Phase 7 — cascade threshold sub-sweep               5 variants      pending
⏸ Phase 8 — model × strategy recovery                 8 variants      pending
```

## What's stopped + what's still running

**Stopped:**
- Master sweep (PID was 27730)
- Watcher (PID was 75930)
- Log mirror (PID was 23206)
- Active bench run (PID was 5834, variant 19)
- caffeinate processes — Mac can sleep / close lid normally now

**Still running (low-power idle):**
- `ollama serve` (the daemon) — minimal power. Models in RAM will auto-unload after ~5 min idle.

## To resume (one command)

```bash
cd /Users/sanchitmonga/development/ODLM/MONOREPOOO/CODING/hybrid-coding-eval

# 1. Verify router is up (if you closed the lid, it may have died)
curl -s http://127.0.0.1:8787/healthz | head -3
# If "Connection refused" → restart it:
( cd router && nohup ./start.sh > /tmp/router.log 2>&1 & )
sleep 3

# 2. Restart the log mirror
nohup ./bin/v3.3-mirror-logs.sh > /tmp/v3.3-mirror.log 2>&1 &
disown

# 3. Restart the master sweep — --resume on every ./bench run skips
#    completed (task_id, route) pairs. Variant 19 will resume at row 84.
nohup caffeinate -i ./bin/v3.3-full-sweep.sh > /tmp/v3.3-sweep.log 2>&1 &
disown

# 4. Restart the watcher (chains Phase 6→7→8 when master sweep finishes)
NEW_MASTER_PID=$(pgrep -f "v3.3-full-sweep.sh" | head -1)
MASTER_PID=$NEW_MASTER_PID nohup caffeinate -i ./bin/v3.3-wait-and-launch-p67.sh > /tmp/v3.3-watcher.log 2>&1 &
disown
```

## Estimated wall time remaining when resumed

| Phase | Rows remaining | Est. wall |
|---|---|---|
| 4 (variant 19) | 117 | ~7 h |
| 5 (variant 20) | 200 | ~12 h |
| 6 (classifiers) | 200 | ~10 h |
| 7 (cascade thresholds) | 250 | ~12 h |
| 8 (model × strategy) | 400 | ~20 h |
| **Total** | **~1,167 rows** | **~61 h** |

About 2.5 days continuous after resume.

## Sanity checks after resume

```bash
# Verify variant 19 resumed from row 84 (not from row 1)
sleep 60 && wc -l results/runs/19-glm47flash-all-routes/raw.jsonl
# Expect: 84+ within a minute of resume start

# Verify processes
ps -p $(pgrep -f "v3.3-full-sweep.sh") -o pid,etime,command
ps -p $(pgrep -f "v3.3-wait-and-launch-p67.sh") -o pid,etime,command
ps -p $(pgrep -f "v3.3-mirror-logs.sh") -o pid,etime,command
```

## If something fails on resume

The sweep is idempotent. Any failure mode is recoverable by re-running the same command. The data in `results/runs/*/raw.jsonl` is append-only — no row is lost.
