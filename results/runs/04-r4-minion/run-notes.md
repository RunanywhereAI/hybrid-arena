# Run 04 — r4-minion

**Date:** 2026-05-06
**Purpose:** test whether a different hybrid pattern (Stanford Minion-style Q&A) beats R3's plan-execute-synth on SWE-bench.

## What's new

A fourth route, **R4**, implemented in `runners/r4_minion.py`. Wraps the Stanford Hazy Research Minion library (`EXTERNAL/minions/minions/minion.py`, MIT-licensed).

- **Cloud supervisor** (`gpt-5.5`) asks targeted questions.
- **Local worker** (`devstral:24b` for this run) reads context and answers.
- **Multi-round Q&A**, up to 3 rounds, ending with the supervisor emitting a final answer.

The key architectural difference from R3: the cloud **never re-sees full repository context**. Context lives on the local worker; cloud just asks what it needs. R3 replays the full plan + all prior step outputs on every cloud call.

## Scope

- Category B only (10 SWE-bench Verified tasks × R4 = 10 rows).
- A and C not tested — Minion's Q&A design aims at long-context reasoning, which is what B needs.

## Headline findings

**R4 = 4/10 pass rate — beats R1 (3/10), every R2 and R3 variant.**

R4 uniquely solved:
- `sphinx-doc/sphinx-7889` (no other route passes)
- `sphinx-doc/sphinx-9698` (no other route passes)

R4 also passed `django-11163` and `django-11179` (which R1 and some R3 variants also pass).

### Cost + wall

| route | cost/task | wall/task | passes |
|---|---:|---:|---:|
| R1 | $0.126 | 67 s | 3/10 |
| R3-devstral | $0.144 | 194 s | 3/10 |
| **R4 Minion** | **$0.083** | 155 s | **4/10** |

**R4 is the first route that's both cheaper AND more accurate than R1 cloud-only in our entire 180-row dataset.**

Token mechanism: R4 median ~11 K prompt + ~7 K completion. ~65% cloud, ~35% local. Much less prompt bloat than R3 (~20 K prompt for R3) because cloud doesn't see full context repeatedly.

## Caveats

1. **10 tasks × 1 sample.** Could be 2/10 on a different seed; could be 6/10. A 30-task sweep is the next step.
2. **R4 tested only on category B.** Unknown on A (probably wins — same "less bloat" advantage applies) and C (probably a tie — Minion Q&A is well-matched to open-ended reasoning).
3. **Minion library has a flaky JSON extractor.** ~10% of rounds produce a diff-in-JSON blob that crashes the library's regex-based parser. Patched in `runners/r4_minion.py` via a `_resilient_extract_json` monkey-patch + a `json.loads` wrapper. Orchestrator-retry covers residual flakes. Some rows in `progress.log` show retries; the deduplicated raw.jsonl keeps the latest.
4. **Only 10 SWE-bench tasks.** Not a full SWE-bench sweep. Probably the single most important follow-up experiment.

## Files

| file | notes |
|---|---|
| `raw.jsonl` | 10 rows, deduplicated. Each row has `"route": "R4"`. |
| `outputs/*_R4.txt` | Final diffs produced by Minion. |
| `minion_logs/` | Stanford library's own per-task conversation logs. |
| `env-manifest.json` | Captures `router_proxy.local_model: devstral:24b`. |

## What this run does NOT answer

- R4 on A and C (we restricted to B for the MVP stretch goal).
- R4 behaviour under a longer sweep (significance).
- Whether R5 (Aider-style architect/editor review loop) would be better or worse — not tested.
