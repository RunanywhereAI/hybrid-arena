# EXTERNAL/

Read-only reference clones of third-party projects we study but do not vendor into our codebase. Not tracked in git (see parent `.gitignore`) — treat as reference material, not build-time dependencies.

## minions/

- **Source**: https://github.com/HazyResearch/minions
- **Paper**: *Minions: Cost-efficient Collaboration Between On-device and Cloud Language Models* (arXiv 2502.15964)
- **License**: MIT
- **What it is**: Stanford Hazy Research's implementation of the Minions protocol — stateful Q&A between a local worker and cloud supervisor.
- **Why we reference it**: The `DevMinion` variant (`minions/minion_code.py`) has a 5-stage runbook → execute → review → edit → synthesize loop that informs our post-MVP R4/R5 routes. Worth reading as prior art; reusable Python classes.
- **First cloned**: ~2026-04 into opencode/EXTERNAL/, moved here during consolidation 2026-05-05.
- **How to refresh**: `cd EXTERNAL && git clone https://github.com/HazyResearch/minions.git`
