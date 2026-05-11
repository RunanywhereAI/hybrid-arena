# BigCodeBench-Hard adapter

A thin, reproducible wrapper around the public
[`bigcode/bigcodebench-hard`](https://huggingface.co/datasets/bigcode/bigcodebench-hard)
dataset. This adapter is **Category-C** of our eval plan:
library-intensive programming — the model must use real third-party
Python APIs (numpy, pandas, flask, matplotlib, cv2, ...) to solve each
task. Functional scoring via the task's own pytest / unittest code.

## What is BigCodeBench-Hard?

BigCodeBench is a benchmark from BigCode for evaluating code generation
on *realistic* library-calling tasks (as opposed to pure algorithmic
puzzles like HumanEval). The "Hard" subset is a curated 148-task slice
that even frontier models struggle with — state-of-the-art pass@1 sits
well below the full-set numbers, so small quality deltas remain
legible. See the paper: *BigCodeBench: Benchmarking Code Generation
with Diverse Function Calls and Complex Instructions*,
[arXiv:2406.15877](https://arxiv.org/abs/2406.15877).

Each row has:

| column | meaning |
| --- | --- |
| `task_id` | upstream id, e.g. `BigCodeBench/214` |
| `complete_prompt` | stub + full docstring (complete-style input) |
| `instruct_prompt` | natural-language instruction (instruct-style input) |
| `canonical_solution` | reference body |
| `code_prompt` | minimal signature-only stub |
| `test` | pytest / unittest harness |
| `entry_point` | function name the test calls |
| `doc_struct` | structured parse of the docstring (JSON string) |
| `libs` | list of Python libraries the solution is expected to use (JSON string) |

## Our sample

We pin 5 tasks, sampled deterministically with `random.Random(42)` from
the `v0.1.4` split (148 rows). Re-running `load_tasks(n=5, seed=42)`
will always return the same ids, in the same order:

| # | our id | upstream task_id | libs required |
| -: | --- | --- | --- |
| 1 | `bigcodebench-hard/BigCodeBench/214` | `BigCodeBench/214` | numpy, matplotlib, random, cv2 |
| 2 | `bigcodebench-hard/BigCodeBench/82`  | `BigCodeBench/82`  | flask_login, flask_wtf, wtforms, werkzeug, flask |
| 3 | `bigcodebench-hard/BigCodeBench/530` | `BigCodeBench/530` | pandas, collections, matplotlib, numpy, seaborn |
| 4 | `bigcodebench-hard/BigCodeBench/501` | `BigCodeBench/501` | pandas, xlwt, os |
| 5 | `bigcodebench-hard/BigCodeBench/458` | `BigCodeBench/458` | pandas, re, json |

### Union of non-stdlib dependencies

The scorer sandbox (`lib/sandbox.py`) needs to `pip install` at least
the following third-party packages to run these 5 tasks:

```
cv2            # distributed as opencv-python
flask
flask_login
flask_wtf
matplotlib
numpy
pandas
seaborn
werkzeug
wtforms
xlwt
```

Stdlib-only names in the task `libs` lists — `collections`, `json`,
`os`, `random`, `re` — need no install.

> Note: `cv2` installs under the PyPI name **`opencv-python`** (or
> `opencv-python-headless` for server images without X11). The scorer
> task (T3.1) should translate `"cv2" → "opencv-python-headless"` in
> its requirements resolver.

## Usage

```python
from benchmark.bigcodebench_hard import load_tasks

tasks = load_tasks(n=5, seed=42)
for t in tasks:
    print(t.id, t.entry_point, t.libs)
```

On first call the adapter reads `tasks.jsonl` next to this README — no
network needed. If the pinned file is missing or has fewer than `n`
rows, the adapter falls back to `datasets.load_dataset(
"bigcode/bigcodebench-hard", split="v0.1.4")` and samples with
`random.Random(seed)`.

To refresh the pinned set (maintainer task):

```bash
python -m benchmark.bigcodebench_hard.adapter --n 5 --seed 42 --write
```

## Contamination note

BigCodeBench is publicly hosted on Hugging Face and has been available
since mid-2024, so it is in the training corpus of every cloud model
released after that date. Treat the absolute pass@1 numbers with the
usual caveats — **what we care about is the *gap* between routing
strategies on the same task set**, not the absolute score. If you need
a contamination-free tier, that's LiveCodeBench-latest (covered in a
separate adapter under the plan).

We also do not shuffle or alter upstream prompts; the `instruct_prompt`
and `complete_prompt` fields are passed through verbatim so our numbers
are directly comparable to the BigCodeBench leaderboard.

## License

The upstream dataset is released under **Apache 2.0**
(see the [dataset card](https://huggingface.co/datasets/bigcode/bigcodebench)).
The prompts, canonical solutions and test harnesses cached in
`tasks.jsonl` retain that license. Our adapter code (`adapter.py`,
`__init__.py`) is MIT, same as the rest of this repo.

## Files

- `adapter.py` — `Task` dataclass + `load_tasks(...)` + maintainer CLI.
- `tasks.jsonl` — 5 frozen tasks, one JSON object per line.
- `__init__.py` — re-exports.
- `README.md` — this file.
