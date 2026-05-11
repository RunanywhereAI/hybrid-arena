# Judge-robustness audit (T-14)

Triple-judge × 2-order replay of the custom_arch pairings that the MVP report's Category C finding was load-bearing on.

Total verdicts: **30**.

| task | pair | unanimous? | majority | order-swap flips |
|---|---|:-:|---|---:|
| `custom-arch/auth-multitenant-design` | R1_vs_R3 | ✅ | **tie** (6/6) | 0/3 judges |
| `custom-arch/cache-invalidation-tradeoffs` | R1_vs_R3 | ✅ | **tie** (6/6) | 0/3 judges |
| `custom-arch/code-review-flaky-test` | R1_vs_R3 | ❌ | **tie** (5/6) | 1/3 judges |
| `custom-arch/migration-planning-zero-downtime` | R1_vs_R3 | ❌ | **tie** (5/6) | 1/3 judges |
| `custom-arch/production-debug-reasoning` | R1_vs_R3 | ❌ | **tie** (5/6) | 1/3 judges |

---

Interpretation: any task with order-swap flips is *contested* and its winner should be marked with a footnote in the article.
