# Comparison — 02-todo-api

| metric | cloud-only | hybrid | delta |
| --- | ---: | ---: | ---: |
| **cost** | $0.0667 | $0.1339 | **-101% saved** |
| wall time | 24.1s | 20m20s | hybrid 50.7× cloud |
| total prompt tokens | 314 | 24385 | hybrid 77.7× (decomposed → repeated context) |
| total completion tokens | 2172 | 10006 | — |

## Cloud-only output

(see `cloud-only/run.md`)

## Hybrid output

(see `hybrid/run.md`)

## How hybrid decomposed the task

10 of 11 executor steps stayed local; 1 of 11 routed to cloud (planner is always cloud).

- 🖥 step 1 _(design, hint=auto)_: **Design project structure and API behavior** — 1m40s, $0.0000
- 🖥 step 2 _(edit, hint=local)_: **Create package.json** — 23.8s, $0.0000
- 🖥 step 3 _(edit, hint=local)_: **Implement Express app setup** — 1m30s, $0.0000
- 🖥 step 4 _(edit, hint=local)_: **Implement todo validation helpers** — 1m44s, $0.0000
- 🖥 step 5 _(edit, hint=local)_: **Implement create and list endpoints** — 1m25s, $0.0000
- 🖥 step 6 _(edit, hint=local)_: **Implement read, update, and delete endpoints** — 1m48s, $0.0000
- 🖥 step 7 _(edit, hint=local)_: **Add server startup and export** — 1m59s, $0.0000
- 🖥 step 8 _(test, hint=local)_: **Write end-to-end test** — 2m35s, $0.0000
- 🖥 step 9 _(edit, hint=local)_: **Write README documentation** — 2m33s, $0.0000
- 🖥 step 10 _(answer, hint=auto)_: **Assemble final file output** — 4m4s, $0.0000
