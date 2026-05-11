# Comparison — 03-url-shortener

| metric | cloud-only | hybrid | delta |
| --- | ---: | ---: | ---: |
| **cost** | $0.1259 | $0.1629 | **-29% saved** |
| wall time | 57.5s | 18m4s | hybrid 18.9× cloud |
| total prompt tokens | 465 | 22617 | hybrid 48.6× (decomposed → repeated context) |
| total completion tokens | 4120 | 10814 | — |

## Cloud-only output

(see `cloud-only/run.md`)

## Hybrid output

(see `hybrid/run.md`)

## How hybrid decomposed the task

9 of 10 executor steps stayed local; 1 of 10 routed to cloud (planner is always cloud).

- 🖥 step 1 _(edit, hint=local)_: **Create project metadata** — 1m15s, $0.0000
- 🖥 step 2 _(edit, hint=local)_: **Implement URL store module** — 42.5s, $0.0000
- 🖥 step 3 _(edit, hint=local)_: **Implement rate limiter module** — 1m31s, $0.0000
- 🖥 step 4 _(edit, hint=local)_: **Implement Express server** — 1m60s, $0.0000
- 🖥 step 5 _(edit, hint=local)_: **Add happy-path integration test** — 1m13s, $0.0000
- 🖥 step 6 _(edit, hint=local)_: **Write README sections** — 2m6s, $0.0000
- 🖥 step 7 _(test, hint=local)_: **Run tests and fix failures** — 3m9s, $0.0000
- 🖥 step 8 _(review, hint=auto)_: **Review requirement coverage** — 2m36s, $0.0000
- 🖥 step 9 _(answer, hint=auto)_: **Assemble final file output** — 2m32s, $0.0000
