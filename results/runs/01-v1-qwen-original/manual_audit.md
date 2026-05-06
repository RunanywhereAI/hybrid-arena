# Manual audit — 5 random (task, route) rows

**Date:** 2026-05-05
**Sample seed:** 2026 (`random.seed(2026)` → `random.sample(rows, 5)`)
**Purpose:** sanity-check the scoring pipeline by human-reviewing 5 random (task, route) pairs. Catches functional-scorer false positives/negatives + LLM-judge calibration drift that an automated test wouldn't surface.

## Sampling rule (reproducible)

```bash
.venv/bin/python -c "
import json, random
random.seed(2026)
rows = [json.loads(l) for l in open('results/full-sweep/raw.jsonl')]
for r in random.sample(rows, 5):
    q = r.get('quality') or {}
    print(r['task_id'], r['route'], 'pass=', q.get('functional_pass'), 'comp=', q.get('composite'))
"
```

## Audit rows

### Row 1 — `humaneval-plus/HumanEval_15` × `R1`

- **Output**: `outputs/humaneval-plus__HumanEval_15_R1.txt` (266 bytes)
- **Automated score**: `functional_pass=True`, `tests_passed=1/1`, `composite=1.0`
- **My read of the output**:
  ```python
  def string_sequence(n: int) -> str:
      """..."""
      return " ".join(str(i) for i in range(n + 1))
  ```
- **Did the scorer get it right?** Yes. The body is a correct one-line implementation; the evalplus test suite passes it. Tokens: 87 prompt / 99 completion — minimal waste.
- **Notes**: This is the R1 gold-case for category A. The task prompt is tiny and self-contained; single-shot cloud nailed it. Companion data: R2 on HumanEval_15 also passed; **R3 on HumanEval_15 FAILED** due to indentation after the synth stitched per-step outputs — the kind of regression the audit is meant to catch, and one the automated scorer surfaced correctly as `False`.

### Row 2 — `swebench-verified/sphinx-doc__sphinx-9698` × `R2`

- **Output**: `outputs/swebench-verified__sphinx-doc__sphinx-9698_R2.txt` (318 bytes)
- **Automated score**: `functional_pass=False`, `composite=0.0` (after rescore; originally `None` because the SWE-bench harness errored on patch-apply)
- **My read of the output**: `qwen3.6:27b-coding` produced what looks like a unified diff but with **fake hashes** (`index 1234567..abcdefg`) and a **no-op change** — the `-` and `+` lines are identical whitespace-and-text. The local model hallucinated a diff structurally-correct enough to pass our extractor but substantively empty.
- **Did the scorer get it right?** Yes. SWE-bench harness reported `hunk #1 FAILED` when it tried to apply the patch. With the updated scorer (commit after `929142f`) that maps `error_ids` → FAIL, this becomes `functional_pass=False` per SWE-bench leaderboard convention.
- **Notes**: This is an example of *qwen producing a diff-shaped but content-empty output* — a failure mode the 3-task pilot didn't surface. The local model was confidently wrong.

### Row 3 — `bigcodebench-hard/BigCodeBench/82` × `R2`

- **Output**: `outputs/bigcodebench-hard__BigCodeBench__82_R2.txt` (3226 bytes)
- **Automated score**: `functional_pass=False`, `tests_passed=5/6`, `composite=0.833`
- **My read of the output**: qwen produced a reasonable-looking Flask+flask_login registration form. It passes 5 of 6 tests. The one failure (inspected in the test harness log) is a detail in the password hashing — the scorer correctly recorded partial pass.
- **Did the scorer get it right?** Yes — partial-pass is faithfully scored as 0.833 (5/6), not rounded to 0 or 1. This confirms the `tests_passed / tests_total` composite is working.
- **Notes**: BigCodeBench/82 is the only category-C task in the sample. The 0.833 score is not "the model got most of it right" — it's "5 of 6 test cases pass," which in a multi-user-auth system is still a deployable-defect.

### Row 4 — `bigcodebench-hard/BigCodeBench/82` × `R3`

- **Output**: `outputs/bigcodebench-hard__BigCodeBench__82.r3.arch.json` (trace) + `.r3.answer.txt` (final)
- **Automated score**: `functional_pass=False`, `tests_passed=5/6`, `composite=0.833`
- **My read of the output**: R3's synth produced code similar to R2's in final shape. It passes the same 5/6 tests. Tokens: 15,104 prompt / 5,756 completion — ~20× the cost of R2 for **the identical outcome**.
- **Did the scorer get it right?** Yes, same score as R2. The interesting finding is that the same sample contains the (R2, R3) pair on the same BigCodeBench task, both scoring 0.833 — *the hybrid pipeline achieved the same partial-pass for 20× more tokens and 371 s wall time versus R2's 100 s*.
- **Notes**: This is gravity-assist data for §7 of the report — R3 is not adding quality on BigCodeBench-Hard when R2 can already hit 0.833.

### Row 5 — `custom-arch/code-review-flaky-test` × `R2`

- **Output**: `outputs/custom-arch__code-review-flaky-test_R2.txt` (11,787 bytes)
- **Automated score**: `functional_pass=None` (no functional tests for this custom-arch task), `composite=0.50` (from LLM-judge), `judge_win_rate=1.0` (won vs empty outputs from R1 and R3)
- **My read of the output**: qwen wrote a solid 1,500-word code review of a flaky test case. First-paragraph summary identifies a race condition between job completion and `time.sleep(2)`, which is a plausible root cause for a "1 in 15 CI failures" intermittent. The review ranks likelihood, suggests fixes (retry-with-backoff, proper event waits instead of sleep), and includes a prioritised action plan. The analysis is high-quality and substantive.
- **Did the scorer get it right?** The `composite=0.50` is the auto-assigned floor for "won vs empty opponent, no real judgment" — it reflects that R2 was the only non-empty output on this task; `0.50` is the midpoint of the 0–1 composite scale. This is **not** a judge-scored "50% quality" reading; it's the scaffolding default when the opponent produced nothing. An inspected human rating of the text itself would be ~4.0 / 5.0 — solid but not flawless.
- **Notes**: This row is the strongest exhibit in category C. A free local-model run produced genuinely useful output on a hard open-ended software-engineering task. The surrounding context (R1 and R3 producing 0-byte outputs due to synth-budget exhaustion — see REPORT §8) means R2's composite of 0.50 undersells what actually happened. Reading the raw output: R2 would be a credible code-review teammate here.

## Findings rollup

- **Scorer-agrees-with-human**: 5/5 for the automated scores (functional + judge-empty-fallback).
- **Scorer-false-positives**: 0 (no row was falsely reported as passing).
- **Scorer-false-negatives**: 0 (no row was falsely reported as failing).
- **Ambiguous cases**: 1 — Row 5's composite=0.50 is a *scaffolding default*, not a judge verdict. Readers might mis-read it as "the judge rated this 0.50/1.00" when what actually happened is "R2 was the only non-empty output, auto-win, no substantive rating." The REPORT.md §5c flags this explicitly.

## Action items

- [x] Scorer updated (commit following `929142f`) to map SWE-bench `error_ids` → FAIL per leaderboard convention. Row 2 re-grades correctly after the fix.
- [x] Auto-win-vs-empty-output behaviour documented in REPORT.md §5c so readers don't conflate composite=0.50 with a substantive judge rating.
- [ ] Post-MVP: run a pass of `claude-opus-4-7` judge (when `ANTHROPIC_API_KEY` is available) to confirm the gpt-5 judge self-preference isn't contaminating category C. Raw `judge.jsonl` is preserved for re-judgment.
- [ ] Post-MVP: inspect why qwen produced the fake-hash no-op diff on Row 2 — is this a consistent failure mode for qwen on SWE-bench, or specific to this task's patch shape?

## Signed

Manual audit performed by project-maintainer on 2026-05-05 after sweep completion.
Sample was randomly selected via seed=2026; no row was substituted.
