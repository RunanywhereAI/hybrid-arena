#!/usr/bin/env python3
"""Generate the v4 agent-hybrid morning report.

Reads ``results/runs/17-v4-agent-overnight/raw.jsonl`` and produces a
markdown summary on stdout. Designed to be run from
``bin/overnight-sweep.sh`` and piped into
``reports/AGENT_HYBRID_2026-05-19.md``.

The report layout (per the plan):
  - Headline table (3 rows per agent × 3 strategies = 9 rows for R6/R7,
    plus R8 if it ran)
  - Per-task breakdown
  - Cost-per-correct
  - Cloud-fraction histogram per heuristic strategy
  - Sanity check vs published SWE-bench Verified leaderboard
  - Auto-extracted "surprising findings"
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

# Use the in-repo pricing module to re-derive cost.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from hybrid_coding_eval.core.pricing import compute_cost  # type: ignore  # noqa: E402

# Map "scenario label" → cloud model id key the pricing table uses for
# the cloud-token cost. Local tokens always price at $0 (model="__local__").
SCENARIOS: dict[str, str] = {
    "openai-gpt5.5": "gpt-5.5",
    "openai-gpt5": "gpt-5",
    "openai-gpt5-mini": "gpt-5-mini",
    "anthropic-claude-opus-4.7": "claude-opus-4-7",
    "anthropic-claude-sonnet-4.6": "claude-sonnet-4-6",
    "anthropic-claude-haiku-4.5": "claude-haiku-4-5",
}


def _load_rows(jsonl_path: Path) -> list[dict]:
    rows = []
    if not jsonl_path.exists():
        return rows
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _cost(row: dict, scenario_label: str) -> float:
    """Re-derive cloud-side cost for ``row`` under the given pricing scenario.

    Local tokens always cost $0 by construction in this harness.
    """
    tokens = row.get("tokens") or {}
    model_id = SCENARIOS.get(scenario_label)
    if not model_id:
        return 0.0
    # Build an OpenAI-shape usage dict from row tokens.
    usage = {
        "prompt_tokens": tokens.get("cloud_prompt", 0),
        "completion_tokens": tokens.get("cloud_completion", 0),
        "prompt_tokens_details": {"cached_tokens": tokens.get("cached", 0)},
    }
    try:
        return float(compute_cost(model_id, usage).get("usd") or 0.0)
    except Exception:
        return 0.0


def _passed(row: dict) -> bool | None:
    """Determine pass/fail with judge-score fallback.

    For functional shapes, ``functional_pass`` is authoritative. For
    prose-judged shapes (D3 refactor / D4 review), the judge returns
    ``composite`` ∈ [0,1] but no ``functional_pass``; use composite ≥ 0.5
    as the "pass" proxy (consistent with reports/ARTICLE.md §2).
    Rows where neither metric is present return ``None`` (not measured).
    """
    q = row.get("quality") or {}
    fp = q.get("functional_pass")
    if fp is not None:
        return bool(fp)
    comp = q.get("composite")
    if comp is not None:
        return float(comp) >= 0.5
    return None


def _composite(row: dict) -> float:
    q = row.get("quality") or {}
    c = q.get("composite")
    if c is None:
        fp = q.get("functional_pass")
        if fp is True:
            return 1.0
        if fp is False:
            return 0.0
        return 0.0
    return float(c)


def _cloud_fraction(row: dict) -> float | None:
    tokens = row.get("tokens") or {}
    cloud = tokens.get("cloud_prompt", 0) + tokens.get("cloud_completion", 0)
    local = tokens.get("local_prompt", 0) + tokens.get("local_completion", 0)
    total = cloud + local
    if total <= 0:
        return None
    return cloud / total


def _agent_name(route: str) -> str:
    return {
        "R6": "mini-swe-agent (SWE-bench)",
        "R7": "aider (Exercism Python)",
        "R8": "opencode (real-dev D1+D5)",
    }.get(route, route)


def _group(rows: list[dict]) -> dict[tuple[str, str], list[dict]]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        route = r.get("route") or "?"
        strat = r.get("router_strategy") or "?"
        groups[(route, strat)].append(r)
    return dict(groups)


def main(out_dir: Path) -> int:
    raw = out_dir / "raw.jsonl"
    rows = _load_rows(raw)
    if not rows:
        print("# AGENT_HYBRID — no rows landed yet\n")
        print(f"raw.jsonl: {raw} (empty or missing)")
        return 1

    primary_scenario = "openai-gpt5.5"

    # only the v4 agent routes
    agent_rows = [r for r in rows if r.get("route") in ("R6", "R7", "R8")]
    if not agent_rows:
        print("# AGENT_HYBRID — no R6/R7/R8 rows found\n")
        return 1

    groups = _group(agent_rows)

    # ---------------------------------------------------------------- header
    out: list[str] = []
    out.append("# Agent-Hybrid Routing — Overnight Results")
    out.append("")
    out.append(f"**Generated:** auto · **Run dir:** `{out_dir}`")
    out.append(f"**Rows total:** {len(agent_rows)} · **Pricing scenario (primary):** `{primary_scenario}`")
    out.append("")
    out.append(
        "This report compares three real coding agents (mini-swe-agent, aider, "
        "opencode) under three routing strategies (always-cloud, always-local, "
        "heuristic). All LLM calls flow through this repo's router proxy on "
        "`:8787`; the strategy decides per call which backend handles it."
    )
    out.append("")
    out.append("---")
    out.append("")

    # ----------------------------------------------------------- headline §1
    out.append("## §1 Headline — resolution × cost × cloud-fraction")
    out.append("")
    out.append(
        "| Agent | Strategy | N | Resolved | Cloud-Frac (med) | Σ cloud tok | Σ local tok | "
        f"Σ $ {primary_scenario} | $/correct | Wall med (s) |"
    )
    out.append(
        "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |"
    )

    headline_data: dict[tuple[str, str], dict] = {}
    for (route, strat), rs in sorted(groups.items()):
        n = len(rs)
        resolved = sum(1 for r in rs if _passed(r) is True)
        cloud_fracs = [cf for cf in (_cloud_fraction(r) for r in rs) if cf is not None]
        med_cf = statistics.median(cloud_fracs) if cloud_fracs else 0.0
        cloud_tok = sum((r.get("tokens") or {}).get("cloud_prompt", 0)
                        + (r.get("tokens") or {}).get("cloud_completion", 0)
                        for r in rs)
        local_tok = sum((r.get("tokens") or {}).get("local_prompt", 0)
                        + (r.get("tokens") or {}).get("local_completion", 0)
                        for r in rs)
        total_cost = sum(_cost(r, primary_scenario) for r in rs)
        per_correct = (total_cost / resolved) if resolved > 0 else float("inf")
        walls = [(r.get("latency") or {}).get("wall_ms") for r in rs]
        walls_s = [w / 1000.0 for w in walls if isinstance(w, (int, float))]
        med_wall = statistics.median(walls_s) if walls_s else 0.0

        headline_data[(route, strat)] = {
            "n": n, "resolved": resolved, "cf": med_cf, "cloud_tok": cloud_tok,
            "local_tok": local_tok, "cost": total_cost, "per_correct": per_correct,
            "wall": med_wall,
        }
        per_correct_str = "—" if resolved == 0 else f"${per_correct:.4f}"
        out.append(
            f"| {_agent_name(route)} | {strat} | {n} | {resolved}/{n} | "
            f"{med_cf*100:.0f}% | {cloud_tok:,} | {local_tok:,} | "
            f"${total_cost:.3f} | {per_correct_str} | {med_wall:.0f} |"
        )

    out.append("")

    # --------------------------------- §2 per-agent which-tasks-where breakdown
    out.append("## §2 Which tasks each strategy resolved")
    out.append("")
    for route in ("R6", "R7", "R8"):
        # Find all task_ids for this agent
        tasks_for_route: set[str] = set()
        for r in agent_rows:
            if r.get("route") == route:
                tasks_for_route.add(r.get("task_id") or "?")
        if not tasks_for_route:
            continue
        out.append(f"### {_agent_name(route)}")
        out.append("")
        out.append("| task | always-cloud | always-local | heuristic |")
        out.append("| --- | :-: | :-: | :-: |")
        for tid in sorted(tasks_for_route):
            cells = []
            for strat in ("always-cloud", "always-local", "heuristic"):
                matching = [
                    r for r in agent_rows
                    if r.get("route") == route
                    and r.get("task_id") == tid
                    and r.get("router_strategy") == strat
                ]
                if not matching:
                    cells.append("—")
                    continue
                r = matching[0]
                p = _passed(r)
                q = r.get("quality") or {}
                comp = q.get("composite")
                fp = q.get("functional_pass")
                if r.get("error"):
                    cells.append("err")
                elif fp is True:
                    cells.append("✅")
                elif fp is False:
                    cells.append("❌")
                elif comp is not None:
                    cells.append(f"{float(comp):.2f}")
                else:
                    cells.append("ran" if r.get("finished_at") else "?")
            out.append(f"| `{tid}` | {cells[0]} | {cells[1]} | {cells[2]} |")
        out.append("")

    # ------------------------------------- §3 cost-per-correct ASCII bar chart
    out.append("## §3 Cost per correctly resolved task (primary scenario)")
    out.append("")
    out.append("```")
    finite_costs = [
        d["per_correct"]
        for d in headline_data.values()
        if d["per_correct"] != float("inf")
    ]
    max_c = max(finite_costs) if finite_costs else 1.0
    for (route, strat), d in sorted(headline_data.items()):
        if d["per_correct"] == float("inf"):
            bar = "(no correct)"
        else:
            width = int(50 * d["per_correct"] / max_c) if max_c > 0 else 0
            bar = "█" * width + f"  ${d['per_correct']:.4f}"
        out.append(f"{route} {strat:14s} | {bar}")
    out.append("```")
    out.append("")

    # ----------------------------------------- §4 cloud-fraction heuristic-only
    out.append("## §4 Cloud-fraction under `heuristic` (per agent)")
    out.append("")
    out.append("Distribution of per-task cloud-fraction when the router was free to choose.")
    out.append("")
    for route in ("R6", "R7", "R8"):
        relevant = [
            r for r in agent_rows
            if r.get("route") == route and r.get("router_strategy") == "heuristic"
        ]
        if not relevant:
            continue
        cfs = sorted([cf for cf in (_cloud_fraction(r) for r in relevant) if cf is not None])
        if not cfs:
            continue
        med = statistics.median(cfs)
        mn = min(cfs); mx = max(cfs)
        out.append(f"- **{_agent_name(route)}**: n={len(cfs)}, min={mn*100:.0f}%, med={med*100:.0f}%, max={mx*100:.0f}%")
    out.append("")

    # --------------------------------- §5 pricing-scenario sensitivity (heuristic)
    out.append("## §5 Heuristic-strategy total cost under 6 pricing scenarios")
    out.append("")
    out.append("| Agent | " + " | ".join(SCENARIOS.keys()) + " |")
    out.append("| --- | " + " | ".join(["---:"] * len(SCENARIOS)) + " |")
    for route in ("R6", "R7", "R8"):
        relevant = [
            r for r in agent_rows
            if r.get("route") == route and r.get("router_strategy") == "heuristic"
        ]
        if not relevant:
            continue
        cells = [f"${sum(_cost(r, sc) for r in relevant):.3f}" for sc in SCENARIOS.keys()]
        out.append(f"| {_agent_name(route)} | " + " | ".join(cells) + " |")
    out.append("")

    # ---------------------------------------- §6 auto-extracted findings
    out.append("## §6 Auto-extracted findings")
    out.append("")
    findings: list[str] = []

    # heuristic vs always-cloud cost savings per agent
    for route in ("R6", "R7", "R8"):
        ac = headline_data.get((route, "always-cloud"))
        hu = headline_data.get((route, "heuristic"))
        if not ac or not hu:
            continue
        if ac["cost"] > 0:
            savings = 100.0 * (1 - hu["cost"] / ac["cost"])
            findings.append(
                f"- **{_agent_name(route)}** heuristic vs always-cloud: "
                f"cost {savings:+.1f}% (heuristic ${hu['cost']:.3f} vs "
                f"always-cloud ${ac['cost']:.3f}), "
                f"resolution {hu['resolved']}/{hu['n']} vs {ac['resolved']}/{ac['n']}"
            )

    # routing-tax: resolution-rate drop heuristic vs always-cloud
    for route in ("R6", "R7", "R8"):
        ac = headline_data.get((route, "always-cloud"))
        hu = headline_data.get((route, "heuristic"))
        if not ac or not hu:
            continue
        if ac["n"] > 0 and hu["n"] > 0:
            ac_rate = ac["resolved"] / ac["n"]
            hu_rate = hu["resolved"] / hu["n"]
            delta = (hu_rate - ac_rate) * 100
            findings.append(
                f"- **{_agent_name(route)}** routing-tax: heuristic resolution "
                f"{hu_rate*100:.0f}% vs always-cloud {ac_rate*100:.0f}% "
                f"(Δ {delta:+.0f}pp)"
            )

    # tasks resolved by local but not cloud (local advantage)
    for route in ("R6", "R7", "R8"):
        ac_pass: set[str] = set()
        al_pass: set[str] = set()
        for r in agent_rows:
            if r.get("route") != route:
                continue
            if r.get("router_strategy") == "always-cloud" and _passed(r) is True:
                ac_pass.add(r.get("task_id") or "")
            if r.get("router_strategy") == "always-local" and _passed(r) is True:
                al_pass.add(r.get("task_id") or "")
        local_only = al_pass - ac_pass
        if local_only:
            findings.append(
                f"- **{_agent_name(route)}** local-advantage tasks (local resolved, cloud did not): "
                + ", ".join(sorted(local_only))
            )

    # errors
    err_count = sum(1 for r in agent_rows if r.get("error"))
    if err_count > 0:
        findings.append(
            f"- **infrastructure errors:** {err_count}/{len(agent_rows)} rows have `error` set "
            "— investigate `outputs/*/stderr.log` for the failing runs."
        )

    if not findings:
        findings = ["- (no notable findings extracted — likely small sample)"]
    out.extend(findings)
    out.append("")

    # ---------------------------------------------------- §7 leaderboard parity
    out.append("## §7 Sanity check vs published SWE-bench Verified leaderboard")
    out.append("")
    r6_ac = headline_data.get(("R6", "always-cloud"))
    if r6_ac and r6_ac["n"] > 0:
        rate = 100.0 * r6_ac["resolved"] / r6_ac["n"]
        out.append(
            f"- R6 (mini-swe-agent + gpt-5.5, always-cloud): "
            f"**{r6_ac['resolved']}/{r6_ac['n']} = {rate:.0f}%**"
        )
        out.append(
            "- Published mini-SWE-agent leaderboard range (frontier models, easy tier): ~40-75%"
        )
        if rate < 30:
            out.append(
                "  ⚠ Our number is below the published range — likely a wiring issue. "
                "Check `decisions.jsonl` for actual model used and "
                "`outputs/*/stderr.log` for agent errors."
            )
        else:
            out.append("  ✅ In the expected range — agent wiring looks correct.")
    else:
        out.append("  (R6 × always-cloud rows not present yet)")
    out.append("")

    # ---------------------------------------------------- §8 next steps
    out.append("## §8 Next steps")
    out.append("")
    out.append(
        "- **Calibrate `router/heuristic`** on agent-shaped prompts. The 24 cloud-keyword / "
        "12 local-keyword lists were tuned for human-typed prompts; tool-result echoes look "
        "different. Add agent-call examples to `configs/router/corpus.json` and re-run "
        "`embedding-knn` strategy as a comparison."
    )
    out.append(
        "- **Add Claude Opus 4.7 and Sonnet 4.6** as cloud backends to test whether the "
        "routing benefit generalises beyond OpenAI."
    )
    out.append(
        "- **Run more SWE-bench seeds** for variance estimates (3 seeds × 6 tasks × 3 "
        "configs = 54 R6 runs; another overnight)."
    )
    out.append(
        "- **Phase 1**: build an opencode plugin using `chat.params` + `tool.execute.before` "
        "hooks so routing sees the agent's state (tool results, phase) instead of "
        "raw prompt only."
    )
    out.append("")

    print("\n".join(out))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: agent-hybrid-analyze.py <out_dir>", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1])))
