# Comparison — 01-wordcount-cli

| metric | cloud-only | hybrid | delta |
| --- | ---: | ---: | ---: |
| **cost** | $0.0593 | $0.1903 | **-221% saved** |
| wall time | 26.5s | 15m13s | hybrid 34.5× cloud |
| total prompt tokens | 205 | 22847 | hybrid 111.4× (decomposed → repeated context) |
| total completion tokens | 1942 | 13030 | — |

## Cloud-only output

(see `cloud-only/run.md`)

## Hybrid output

(see `hybrid/run.md`)

## How hybrid decomposed the task

8 of 10 executor steps stayed local; 2 of 10 routed to cloud (planner is always cloud).

- 🖥 step 1 _(design, hint=auto)_: **Design CLI counting behavior** — 1m46s, $0.0000
- ☁ step 2 _(edit, hint=auto)_: **Implement wordcount.js** — 12.5s, $0.0276
- 🖥 step 3 _(edit, hint=auto)_: **Write normal-file test** — 1m20s, $0.0000
- 🖥 step 4 _(edit, hint=auto)_: **Write empty-file test** — 2m14s, $0.0000
- 🖥 step 5 _(edit, hint=auto)_: **Write missing-file test** — 1m28s, $0.0000
- 🖥 step 6 _(edit, hint=auto)_: **Add README.md** — 36.8s, $0.0000
- 🖥 step 7 _(test, hint=local)_: **Run the test suite** — 2m20s, $0.0000
- 🖥 step 8 _(review, hint=auto)_: **Review final file contents** — 2m12s, $0.0000
- 🖥 step 9 _(answer, hint=auto)_: **Format single deliverable** — 2m9s, $0.0000
