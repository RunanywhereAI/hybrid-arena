#!/usr/bin/env python3
"""
Run 5 focused deep-research queries in parallel for the opencode hybrid-routing
architecture, saving each into opencode/research/<slug>/.

Each query uses Exa deep search (15 sources, 25k chars each) + Perplexity
sonar-deep-research (12k tokens, high context) in parallel.

Invoke:
  /Users/sanchitmonga/development/research_agent/.venv/bin/python \
    /Users/sanchitmonga/development/ODLM/MONOREPOOO/CODING/opencode/research/_run_research.py
"""
from __future__ import annotations

import sys
from pathlib import Path
import concurrent.futures
import time

# Make the research_agent module importable
sys.path.insert(0, "/Users/sanchitmonga/development/research_agent")
from research_agent import ResearchAgent  # noqa: E402

OUTPUT_ROOT = Path(
    "/Users/sanchitmonga/development/ODLM/MONOREPOOO/CODING/opencode/research"
)
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

# 5 focused queries. Each one is a self-contained, comprehensive research prompt.
QUERIES: list[tuple[str, str]] = [
    (
        "01_open_source_router_models",
        (
            "Comprehensive list of open-source LLM router and classifier model "
            "checkpoints available on HuggingFace and GitHub as of April 2026. For "
            "each model, report: HuggingFace model ID, parameter count, license, "
            "training data, claimed accuracy and cost-savings benchmarks, framework "
            "integration (transformers, vLLM, ONNX, MLX), inference latency on CPU "
            "and GPU. Include: the RouteLLM family (matrix factorization router, "
            "BERT classifier, causal LLM router, similarity-weighted ranking) with "
            "exact HF IDs; Arch-Router-1.5B and Arch-Function-1.5B/3B/7B/32B "
            "(Katanemo); NotDiamond, Martian, OpenRouter Auto if any open weights "
            "exist; llm-semantic-router checkpoints (HF org); CARROT-LLM-Routing "
            "org; hybrid reasoning think/no-think routers (e.g. AmirMohseni's "
            "router, Qwen3-style routers); NVIDIA llm-router blueprint models; "
            "PerSyn distilled routers; xRouter; Router-R1; cost-aware contrastive "
            "routers; DAAO; CARGO; BaRP. Also include any 2025-2026 distilled "
            "router models, embedding-based router checkpoints (jina, voyage, "
            "snowflake-arctic-embed for routing), and small classifiers fine-tuned "
            "specifically for code task routing. Be exhaustive. For each model "
            "include direct links to HuggingFace and GitHub."
        ),
    ),
    (
        "02_production_hybrid_coding_agents",
        (
            "Detailed survey of hybrid local + cloud LLM routing as actually "
            "deployed in production coding agents and developer tools as of April "
            "2026. Cover deeply: Cursor (Tab/Fusion model, Fast Apply, Composer "
            "1/2, Composer 2 technical report, any internal classification model); "
            "GitHub Copilot Auto and the POST /models/session/intent endpoint, "
            "Next Edit Suggestions custom model, what model their auto-router uses; "
            "Sourcegraph Cody completion lifecycle; Continue.dev model roles; "
            "Cline / Roo Code / Aider model selection logic; Codeium / Windsurf "
            "Adaptive (Cascade); Tabby (TabbyML); Replit Agent v2/v3 segmented "
            "control; Zed AI; Augment Code; Sweep AI; OpenInterpreter; Anthropic "
            "Claude Code Auto Mode safety classifier; opencode plugins like "
            "marco-jardim/opencode-model-router; Goose by Block; aider-style "
            "architect/editor splits in other tools. For each: routing mechanism "
            "(rules vs ML), what signals they route on, latency, cost savings "
            "claimed or measured, postmortems and engineering blog posts, "
            "open-source code if any. Be specific about whether they ship ML "
            "routing vs hard-coded rules. Cite blog posts, eng blogs, conference "
            "talks, GitHub repos, and YouTube engineering deep-dives."
        ),
    ),
    (
        "03_production_hybrid_general_use_cases",
        (
            "Survey of hybrid local + cloud LLM routing in non-coding production "
            "systems as of April 2026. Cover: customer support and chatbot "
            "deployments (Intercom Fin, Zendesk AI, Salesforce Agentforce, Klarna "
            "AI assistant); RAG systems with model routing (Glean, Notion AI, "
            "Coda AI, Mem); content moderation and trust-and-safety routers; "
            "semantic search applications; agent frameworks (LangChain LangGraph "
            "routers, LlamaIndex query routers, AutoGen, CrewAI, OpenAI Swarm, "
            "Microsoft Semantic Kernel); AI gateways and routers (Portkey, "
            "Helicone, Bifrost, Arch Gateway, LiteLLM Router, OptiLLM, Martian, "
            "Cloudflare AI Gateway, AWS Bedrock model evaluation, Azure AI Foundry "
            "Model Router, Vertex AI model garden router); enterprise platforms "
            "(Glean, Hebbia, Harvey, Decagon, Sierra). For each: architecture "
            "pattern, routing model used, decision signals, cost savings claimed "
            "with sources, latency budget, postmortems, case studies. Include "
            "Spotify RLUF, Discord Clyde, Notion AI architecture talks, Anthropic "
            "and OpenAI public statements about internal model routing. Be "
            "detailed — names, signals, numbers, links."
        ),
    ),
    (
        "04_agentic_and_tool_aware_routing_research",
        (
            "Comprehensive survey of LLM routing research papers, methods, and "
            "open-source libraries specifically for tool-using and agentic "
            "workflows, as of April 2026. Focus on multi-turn agentic settings, "
            "not single-shot QA. Cover in depth: cascade routing literature "
            "(FrugalGPT arXiv 2305.05176, AutoMix 2310.12963, EcoAssistant "
            "2310.03046, Hybrid LLM 2404.14618, follow-ups in 2025-2026); "
            "tool-need prediction and tool-aware routing (Arch-Function family, "
            "xRouter arXiv 2510.08439, RL-trained tool routers, Granite-Tool, "
            "ToolACE, ToolLLM evaluation); per-tool-call gating with verifiers "
            "(process reward models, ThinkPRM, CodePRM, FunPRM, DreamPRM-Code); "
            "agentic difficulty estimation (DAAO 2509.11079, Agent Psychometrics "
            "2604.00594, Triage 2604.07494, AdaptiveLLM 2506.10525); unified "
            "routing-cascading frameworks (arXiv 2410.10347 ICML 2025); online "
            "learning routers (BaRP 2510.07429, contextual bandits, calibration-"
            "gated 2604.14961); reasoning-vs-non-reasoning routing (hybrid Qwen3 "
            "routers, GPT-5 routing, deep-think vs fast); reward model and "
            "verifier-based routing (CP-Router 2505.19970, conformal prediction); "
            "failure modes and limitations (router fragility 2504.07113, Stroebl "
            "2024 verifier ceilings 2411.17501, prediction-flip on superficial "
            "perturbations); recent 2026 work (RouterArena 2510.00202, arXiv "
            "papers from Mar-Apr 2026). For each: paper, code, key technique, "
            "reported results, limitations specific to multi-turn tool-using "
            "agents. Be detailed and skeptical about claims."
        ),
    ),
    (
        "05_routing_evaluation_benchmarks_calibration",
        (
            "Comprehensive guide to LLM router evaluation as of April 2026. Cover "
            "benchmarks: RouterBench arXiv 2403.12031 with the 405k record dataset "
            "and 70/30 split methodology; RouterArena arXiv 2510.00202; RouteLLM "
            "preference-data eval methodology; RouterEval arXiv 2503.10657; "
            "LLMRouterBench; MixEval-X if relevant. Cover metrics in depth: "
            "cost-quality Pareto and convex hull methodology, AUDC area under "
            "deferral curve, Router Efficacy, CPT call-performance-threshold, "
            "APGR average performance gain over random, QNC query-normalized cost, "
            "win-rate vs single-model baseline, latency overhead, ECE expected "
            "calibration error, Brier score, reliability diagrams. Cover "
            "evaluation protocols for code-specific routers: SWE-bench Verified "
            "and Pro routing eval, LiveCodeBench routing, BigCodeBench-Hard "
            "routing, Aider Polyglot routing. Cover calibration techniques: "
            "conformal prediction (CP-Router 2505.19970), temperature scaling, "
            "Platt scaling, isotonic regression, calibration-across-layers "
            "(2511.00280). Cover online vs offline evaluation, A/B testing "
            "routers in production, dashboards and observability stacks. Include "
            "how Anthropic / OpenAI / Google evaluate internal routers if "
            "publicly disclosed; how community projects measure cost savings "
            "honestly vs how they're claimed; common pitfalls (Goodhart's law "
            "on routing metrics, benchmark contamination, judge-LLM bias, "
            "selection bias on labeled data). Cite papers, leaderboards, and "
            "production blog posts. Be detailed and rigorous."
        ),
    ),
]


def run_one(slug: str, query: str) -> tuple[str, bool, str]:
    out_dir = OUTPUT_ROOT / slug
    print(f"[{slug}] starting…", flush=True)
    t0 = time.monotonic()
    try:
        agent = ResearchAgent()
        agent.research(
            query,
            save=True,
            output_dir=out_dir,
            exa_num_results=15,
            exa_max_characters=25_000,
            perplexity_tokens=12_000,
        )
        elapsed = time.monotonic() - t0
        print(f"[{slug}] DONE in {elapsed:.0f}s", flush=True)
        return (slug, True, f"{elapsed:.0f}s")
    except Exception as exc:
        elapsed = time.monotonic() - t0
        msg = f"{type(exc).__name__}: {exc}"
        print(f"[{slug}] FAILED after {elapsed:.0f}s — {msg}", flush=True)
        return (slug, False, msg)


def main() -> int:
    print(f"Output root: {OUTPUT_ROOT}")
    print(f"Running {len(QUERIES)} queries in parallel…\n")
    t_overall = time.monotonic()

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(QUERIES)) as pool:
        futures = {pool.submit(run_one, slug, q): slug for slug, q in QUERIES}
        results = []
        for fut in concurrent.futures.as_completed(futures):
            results.append(fut.result())

    elapsed = time.monotonic() - t_overall
    print("\n" + "=" * 60)
    print(f"ALL DONE in {elapsed:.0f}s\n")
    successes = sum(1 for _, ok, _ in results if ok)
    failures = len(results) - successes
    print(f"Success: {successes}  Failed: {failures}")
    for slug, ok, info in results:
        status = "OK " if ok else "FAIL"
        print(f"  [{status}] {slug}  ({info})")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
