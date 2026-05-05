# Manual audit — 5 random (task, route) rows

**Status:** skeleton (sweep in progress, 36/90 rows at time of writing)

Purpose: sanity-check the scoring pipeline by human-reviewing 5 random (task, route) pairs. Catches functional-scorer false positives/negatives + LLM-judge calibration drift that an automated test wouldn't see.

## Sampling rule

After the sweep completes:

```bash
cd hybrid-coding-eval
# Random sample, seeded for reproducibility
.venv/bin/python -c "
import json, random
random.seed(2026)
rows = [json.loads(l) for l in open('results/full-sweep/raw.jsonl')]
sample = random.sample(rows, 5)
for r in sample: print(r['task_id'], r['route'], r['quality'].get('functional_pass'))
"
```

## Audit template (fill in per row)

### Row 1 — `<task_id>` × `<route>`

- **Output file**: `outputs/<...>.txt`
- **Automated score**: functional_pass=?, tests_passed=?/?, composite=?
- **My read of the output**: (quote the first 10 lines of the model's response here)
- **Did the scorer get it right?**: yes / no / partial
- **If no, what's wrong**:
  - Scorer bug (e.g. wrong test harness, wrong regex)
  - Extraction bug (e.g. failed to parse a diff)
  - Model output genuinely ambiguous
- **Notes**:

### Row 2 — `<task_id>` × `<route>`
(same template)

### Row 3 — `<task_id>` × `<route>`
(same template)

### Row 4 — `<task_id>` × `<route>`
(same template)

### Row 5 — `<task_id>` × `<route>`
(same template)

## Findings rollup

After filling in all 5:

- **Scorer-agrees-with-human**: N/5
- **Scorer-false-positives** (scorer says PASS, human says FAIL): N
- **Scorer-false-negatives** (scorer says FAIL, human says PASS): N
- **Ambiguous cases**: N

## Action items (if any scorer bugs surface)

- [ ] ...
- [ ] ...

## Signed

_(your name + date after you audit)_

---

## Why this template exists unfilled

The sweep is still running (36/90 rows at `2026-05-05T22:34Z`). The random sample depends on the final row count; sampling now would over-represent Category A. Fill in after the sweep finishes:

```bash
ps -p 6569 -o etime,stat  # check it's done
wc -l results/full-sweep/raw.jsonl  # confirm ~90 rows
```

Then re-run the sampling script above and audit each row in this file.
