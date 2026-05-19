#!/usr/bin/env python3
"""Build the agent-call routing corpus from router/logs/decisions.jsonl.

Scans the decision log for rows that look like agent (mini-swe-agent /
aider / opencode) LLM calls, then labels each by call-shape heuristics:

- ``"local"`` if the call is a short tool-result echo (returncode + output
  with no fresh user instruction) — local model can plausibly continue.
- ``"cloud"`` if the call is a long planning/synthesis message with
  significant code or new directives.

Output: ``configs/router/corpus_agent.json`` — a flat list of
``{label, text}`` entries, drop-in compatible with the existing
``configs/router/corpus.json`` schema. The ``embedding-knn`` strategy can
then optionally load this corpus alongside the human-prompt one.

Usage:
  .venv/bin/python bin/build-agent-corpus.py             # build
  .venv/bin/python bin/build-agent-corpus.py --inspect   # show sample labels
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECISIONS_LOG = ROOT / "router" / "logs" / "decisions.jsonl"
OUT_PATH = ROOT / "configs" / "router" / "corpus_agent.json"


# Agent fingerprints — start-of-prompt markers that indicate the call is
# being made by an agent harness, not a human-typed query.
AGENT_MARKERS = (
    "<pr_description>",
    "# Task Instructions",
    "You are a helpful assistant that can interact with a computer shell",
    "<returncode>",
    "<output>",
    "Edit the file",
    "I'll help you",
    "tool_calls",
)

# Mini-keyword cues for cloud-routing (new planning/synthesis):
PLAN_KEYWORDS = (
    "Now I need to",
    "Let me think",
    "submit",
    "patch.txt",
    "Step 1",
    "Plan:",
    "implement",
    "design",
    "explain",
    "fix the issue",
    "test cases",
    "Analyze",
)

# Mini-keyword cues for local-routing (consume-tool-result, simple follow-up):
TOOL_RESULT_KEYWORDS = (
    "<returncode>0</returncode>",
    "<returncode>1</returncode>",
    "ls -la",
    "cat ",
    "head ",
    "tail ",
    "grep ",
    "find ",
)


def looks_like_agent_call(prompt_preview: str, prompt_tokens_est: int) -> bool:
    if prompt_tokens_est < 100:
        return False  # too short — likely a smoke test or pre-warm probe
    return any(m in prompt_preview for m in AGENT_MARKERS)


def label_row(prompt_preview: str, prompt_tokens_est: int) -> str | None:
    """Heuristic labeller. Returns 'local', 'cloud', or None (ambiguous, skip)."""
    p = prompt_preview or ""
    n = prompt_tokens_est or 0

    has_tool_result = any(k in p for k in TOOL_RESULT_KEYWORDS) or "<returncode>" in p
    has_plan_kw = any(k in p for k in PLAN_KEYWORDS)

    # Local: short tool-result follow-up, no fresh planning keyword.
    if n < 600 and has_tool_result and not has_plan_kw:
        return "local"

    # Cloud: long task descriptions with planning/synthesis intent.
    if n > 1500 and (has_plan_kw or "<pr_description>" in p):
        return "cloud"

    # Mid-range tool consumption: lean local.
    if 100 <= n <= 800 and has_tool_result:
        return "local"

    # Long with no tool-result: probably planning.
    if n > 2000 and not has_tool_result:
        return "cloud"

    return None  # ambiguous


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", default=str(DECISIONS_LOG))
    ap.add_argument("--out", dest="out_path", default=str(OUT_PATH))
    ap.add_argument("--inspect", action="store_true",
                    help="Print 10 sample entries per label and exit (no write)")
    ap.add_argument("--max-per-label", type=int, default=80,
                    help="Cap each label class at this many entries")
    args = ap.parse_args(argv)

    in_path = Path(args.in_path)
    if not in_path.is_file():
        print(f"ERROR: input not found: {in_path}", file=sys.stderr)
        return 2

    entries: dict[str, list[dict]] = {"local": [], "cloud": []}
    seen_prompts: set[str] = set()  # dedupe by first 80 chars
    stats = Counter()

    with in_path.open() as fh:
        for line in fh:
            stats["lines"] += 1
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                stats["parse_error"] += 1
                continue

            preview = d.get("prompt_preview") or ""
            ntok = int(d.get("prompt_tokens_est") or 0)

            if not looks_like_agent_call(preview, ntok):
                stats["not_agent"] += 1
                continue
            stats["agent_calls"] += 1

            label = label_row(preview, ntok)
            if label is None:
                stats["ambiguous"] += 1
                continue
            stats[f"labeled_{label}"] += 1

            key = preview[:80]
            if key in seen_prompts:
                stats["duplicate"] += 1
                continue
            seen_prompts.add(key)

            if len(entries[label]) < args.max_per_label:
                entries[label].append({
                    "label": label,
                    "text": preview[:600],   # truncate to a reasonable embedding budget
                    "_tokens": ntok,         # debug field (not used by strategies.mjs)
                    "_ts": d.get("ts"),
                })
                stats[f"kept_{label}"] += 1

    # Output / inspect
    if args.inspect:
        for lbl in ("local", "cloud"):
            print(f"\n=== {lbl.upper()} (n={len(entries[lbl])}) ===")
            for e in entries[lbl][:10]:
                preview = (e["text"] or "").replace("\n", " ")[:120]
                print(f"  tok={e['_tokens']:>4d}: {preview}")
    else:
        # Strip debug fields before writing the actual corpus.
        out_entries = []
        for lbl in ("local", "cloud"):
            for e in entries[lbl]:
                out_entries.append({"label": e["label"], "text": e["text"]})
        out_path = Path(args.out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(out_entries, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {len(out_entries)} entries to {out_path}")

    print(f"\nstats: {dict(stats)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
