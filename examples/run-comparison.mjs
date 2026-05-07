#!/usr/bin/env node
// run-comparison.mjs — for each experiment under examples/<id>/, runs the
// prompt twice:
//   (a) cloud-only   → single chat-completion to gpt-5.5 (via router/always-cloud)
//   (b) hybrid       → architect mode (planner cloud, executor router/heuristic, synth router/heuristic)
//
// Captures cost, latency, output, and routing decisions per run. Writes
// each output to <experiment>/cloud-only/run.md and <experiment>/hybrid/run.md
// plus a comparison.md and writes an aggregate examples/RESULTS.md.
//
// Usage:
//   node run-comparison.mjs                       # run every experiment
//   node run-comparison.mjs 01-wordcount-cli      # run a specific one
//   node run-comparison.mjs --skip-cloud          # only hybrid
//   node run-comparison.mjs --skip-hybrid         # only cloud
//
// Talks to the proxy on http://127.0.0.1:8787 (override with PROXY env).

import { readFile, writeFile, mkdir, readdir } from "node:fs/promises";
import { dirname, join, basename } from "node:path";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { runArchitect } from "../router/agentic/architect-core.mjs";
import { costFor, fmtUSD } from "../router/pricing.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROXY = process.env.PROXY || "http://127.0.0.1:8787";
const CLOUD_MODEL = process.env.CLOUD_MODEL || "gpt-5.5";

// ----- args ----------------------------------------------------------------
const argv = process.argv.slice(2);
let skipCloud = false, skipHybrid = false, only = null;
for (const a of argv) {
  if (a === "--skip-cloud") skipCloud = true;
  else if (a === "--skip-hybrid") skipHybrid = true;
  else only = a;
}

// ----- helpers --------------------------------------------------------------
function fmtMs(ms) {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)}s`;
  const m = Math.floor(ms / 60_000);
  const s = Math.round((ms % 60_000) / 1000);
  return `${m}m${s}s`;
}

async function readPrompt(expDir) {
  return (await readFile(join(expDir, "prompt.txt"), "utf8")).trim();
}

// ----- (a) cloud-only single shot -----------------------------------------
// Single chat-completion through the proxy with model=router/always-cloud.
// This is what a user would do today — bang the whole task at gpt-5.5.
async function runCloudOnly(prompt) {
  const t0 = Date.now();
  const res = await fetch(`${PROXY}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "router/always-cloud",
      messages: [{ role: "user", content: prompt }],
      stream: false,
      max_tokens: 8000,        // generous so the model can finish
      temperature: 0.3,
    }),
  });
  const elapsed = Date.now() - t0;
  if (!res.ok) {
    const err = await res.text().catch(() => "");
    throw new Error(`cloud-only call failed ${res.status}: ${err.slice(0, 200)}`);
  }
  const j = await res.json();
  const usage = j.usage || null;
  const echoedModel = res.headers.get("x-router-backend-model-echo") || j.model;
  const cost = costFor(echoedModel, usage);
  // Strip the [router] banner the proxy prepends so the captured output is clean.
  const content = (j.choices?.[0]?.message?.content || "").replace(/^\[router\][^\n]+\n+/, "");
  return { content, elapsed, usage, cost, echoedModel, model: j.model };
}

// ----- (b) hybrid architect-mode ------------------------------------------
async function runHybrid(prompt) {
  const events = [];
  const run = await runArchitect({
    proxy: PROXY,
    task: prompt,
    planner: "router/always-cloud",
    executor: "router/heuristic",
    synthesizer: "router/heuristic",
    maxSteps: 10,
    onProgress: (e) => events.push({ ts: Date.now(), ...e }),
  });
  return { run, events };
}

// ----- per-experiment writeup ---------------------------------------------
async function writeCloudRun(expDir, prompt, result) {
  const outDir = join(expDir, "cloud-only");
  await mkdir(outDir, { recursive: true });
  const lines = [];
  lines.push(`# Cloud-only run — ${basename(expDir)}\n`);
  lines.push(`Run at: ${new Date().toISOString()}\n`);
  lines.push(`## Setup\n`);
  lines.push(`- model: \`${result.echoedModel}\` (single-shot via \`router/always-cloud\`)`);
  lines.push(`- elapsed: **${fmtMs(result.elapsed)}**`);
  lines.push(`- prompt tokens: ${result.usage?.prompt_tokens ?? "?"}`);
  lines.push(`- completion tokens: ${result.usage?.completion_tokens ?? "?"} (of which reasoning: ${result.usage?.completion_tokens_details?.reasoning_tokens ?? 0})`);
  lines.push(`- cost: **${fmtUSD(result.cost.usd)}** (in ${fmtUSD(result.cost.breakdown.input_uncached + result.cost.breakdown.input_cached)} + out ${fmtUSD(result.cost.breakdown.output)})\n`);
  lines.push(`## Prompt\n`);
  lines.push("```");
  lines.push(prompt);
  lines.push("```\n");
  lines.push(`## Output\n`);
  lines.push(result.content);
  lines.push("");
  await writeFile(join(outDir, "run.md"), lines.join("\n"));
  await writeFile(join(outDir, "output.txt"), result.content);
  await writeFile(join(outDir, "metrics.json"), JSON.stringify({
    model: result.echoedModel,
    elapsed_ms: result.elapsed,
    usage: result.usage,
    cost_usd: result.cost.usd,
    cost_breakdown: result.cost.breakdown,
  }, null, 2));
}

async function writeHybridRun(expDir, prompt, result) {
  const outDir = join(expDir, "hybrid");
  await mkdir(outDir, { recursive: true });
  const { run, events } = result;

  const allCalls = [run.plannerResult, ...run.stepResults, ...(run.synth ? [run.synth] : [])];
  let baselineUSD = 0;
  for (const r of allCalls) {
    const bc = costFor(CLOUD_MODEL, r.usage);
    baselineUSD += bc.usd;
  }
  const savedUSD = baselineUSD - run.totals.hybridCostUsd;
  const savedPct = baselineUSD > 0 ? (savedUSD / baselineUSD) * 100 : 0;

  const lines = [];
  lines.push(`# Hybrid run (architect mode) — ${basename(expDir)}\n`);
  lines.push(`Run at: ${new Date().toISOString()}\n`);
  lines.push(`## Setup\n`);
  lines.push(`- planner: \`router/always-cloud\` (always cloud)`);
  lines.push(`- executor: \`router/heuristic\` (per-step decision: local or cloud)`);
  lines.push(`- synthesizer: \`router/heuristic\``);
  lines.push(`- max-steps: 10\n`);
  lines.push(`## Cost & latency\n`);
  lines.push(`| metric | value |`);
  lines.push(`| --- | --- |`);
  lines.push(`| **hybrid cost (paid)** | **${fmtUSD(run.totals.hybridCostUsd)}** |`);
  lines.push(`| all-cloud baseline (\`${CLOUD_MODEL}\`) | ${fmtUSD(baselineUSD)} |`);
  lines.push(`| saved | ${fmtUSD(savedUSD)} (${savedPct.toFixed(0)}%) |`);
  lines.push(`| total wall time | **${fmtMs(run.totals.wallMs)}** |`);
  lines.push(`| model calls | ${run.totals.totalCalls} (1 planner + ${run.stepResults.length} executor + ${run.synth ? 1 : 0} synth) |`);
  lines.push(`| local / cloud calls | ${run.totals.totalLocal} / ${run.totals.totalCloud} |`);
  lines.push(`| prompt tokens | ${run.totals.promptTokens} |`);
  lines.push(`| completion tokens (incl. reasoning) | ${run.totals.completionTokens} (reasoning: ${run.totals.reasoningTokens}) |\n`);
  lines.push(`## Per-step routing\n`);
  lines.push(`| # | kind | hint | choice | backend | elapsed | in | out | cost | if-cloud |`);
  lines.push(`| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |`);
  // planner row
  const pl = run.plannerResult;
  const plBaseline = costFor(CLOUD_MODEL, pl.usage);
  lines.push(`| 0 | planner | — | ☁ cloud | \`${pl.echoedModel}\` | ${fmtMs(pl.elapsed)} | ${pl.usage?.prompt_tokens || 0} | ${pl.usage?.completion_tokens || 0} | ${fmtUSD(pl.cost.usd)} | ${fmtUSD(plBaseline.usd)} |`);
  for (const r of run.stepResults) {
    const choice = r.routerChoice === "local" ? "🖥 local" : r.routerChoice === "cloud" ? "☁ cloud" : `✗ ${r.routerChoice}`;
    const baseline = costFor(CLOUD_MODEL, r.usage);
    lines.push(`| ${r.step.index} | ${r.step.kind || "?"} | ${r.step.router_hint || "auto"} | ${choice} | \`${r.routerBackend}\` | ${fmtMs(r.elapsed)} | ${r.usage?.prompt_tokens || 0} | ${r.usage?.completion_tokens || 0} | ${fmtUSD(r.cost.usd)} | ${fmtUSD(baseline.usd)} |`);
  }
  if (run.synth) {
    const sB = costFor(CLOUD_MODEL, run.synth.usage);
    const sChoice = run.synth.routerChoice === "local" ? "🖥 local" : run.synth.routerChoice === "cloud" ? "☁ cloud" : run.synth.routerChoice;
    lines.push(`| Σ | synth | — | ${sChoice} | \`${run.synth.routerBackend}\` | ${fmtMs(run.synth.elapsed)} | ${run.synth.usage?.prompt_tokens || 0} | ${run.synth.usage?.completion_tokens || 0} | ${fmtUSD(run.synth.cost.usd)} | ${fmtUSD(sB.usd)} |`);
  }
  lines.push("");
  lines.push(`## Plan (from planner)\n`);
  for (const s of run.plan) {
    lines.push(`${s.index}. **${s.title || ""}** — _(${s.kind || "?"}, hint=${s.router_hint || "auto"})_  ${s.task ? `\n    ${s.task}` : ""}`);
  }
  lines.push(`\n## Final synthesised output\n`);
  if (run.synth) {
    lines.push((run.synth.content || "").replace(/^\[router\][^\n]+\n+/, ""));
  } else {
    lines.push("_(single-step plan, no synthesis)_");
    lines.push("");
    for (const r of run.stepResults) lines.push((r.content || "").replace(/^\[router\][^\n]+\n+/, ""));
  }
  lines.push("");
  await writeFile(join(outDir, "run.md"), lines.join("\n"));
  await writeFile(join(outDir, "output.txt"), (run.synth?.content || run.stepResults.map(r => r.content).join("\n\n---\n\n")).replace(/^\[router\][^\n]+\n+/, ""));
  await writeFile(join(outDir, "metrics.json"), JSON.stringify({
    elapsed_ms: run.totals.wallMs,
    hybrid_cost_usd: run.totals.hybridCostUsd,
    baseline_cost_usd: baselineUSD,
    saved_usd: savedUSD,
    saved_pct: savedPct,
    calls: run.totals.totalCalls,
    local_calls: run.totals.totalLocal,
    cloud_calls: run.totals.totalCloud,
    prompt_tokens: run.totals.promptTokens,
    completion_tokens: run.totals.completionTokens,
    reasoning_tokens: run.totals.reasoningTokens,
    cached_tokens: run.totals.cachedTokens,
  }, null, 2));
  await writeFile(join(outDir, "events.json"), JSON.stringify(events, null, 2));
}

async function writeComparison(expDir, cloud, hybrid) {
  const lines = [];
  const id = basename(expDir);
  lines.push(`# Comparison — ${id}\n`);
  lines.push(`| metric | cloud-only | hybrid | delta |`);
  lines.push(`| --- | ---: | ---: | ---: |`);

  const cloudCost = cloud?.cost?.usd ?? null;
  const hybridCost = hybrid?.run?.totals?.hybridCostUsd ?? null;
  const cloudMs = cloud?.elapsed ?? null;
  const hybridMs = hybrid?.run?.totals?.wallMs ?? null;
  const cloudIn = cloud?.usage?.prompt_tokens ?? null;
  const cloudOut = cloud?.usage?.completion_tokens ?? null;
  const hybridIn = hybrid?.run?.totals?.promptTokens ?? null;
  const hybridOut = hybrid?.run?.totals?.completionTokens ?? null;

  if (cloudCost !== null && hybridCost !== null) {
    const savedPct = cloudCost > 0 ? ((cloudCost - hybridCost) / cloudCost) * 100 : 0;
    lines.push(`| **cost** | ${fmtUSD(cloudCost)} | ${fmtUSD(hybridCost)} | **${savedPct.toFixed(0)}% saved** |`);
  }
  if (cloudMs !== null && hybridMs !== null) {
    const ratio = (hybridMs / cloudMs).toFixed(1);
    lines.push(`| wall time | ${fmtMs(cloudMs)} | ${fmtMs(hybridMs)} | hybrid ${ratio}× cloud |`);
  }
  if (cloudIn !== null && hybridIn !== null) {
    lines.push(`| total prompt tokens | ${cloudIn} | ${hybridIn} | hybrid ${(hybridIn / cloudIn).toFixed(1)}× (decomposed → repeated context) |`);
  }
  if (cloudOut !== null && hybridOut !== null) {
    lines.push(`| total completion tokens | ${cloudOut} | ${hybridOut} | — |`);
  }
  lines.push("");
  lines.push(`## Cloud-only output\n`);
  lines.push("(see `cloud-only/run.md`)");
  lines.push("");
  lines.push(`## Hybrid output\n`);
  lines.push("(see `hybrid/run.md`)");
  lines.push("");
  lines.push(`## How hybrid decomposed the task\n`);
  if (hybrid) {
    lines.push(`${hybrid.run.totals.totalLocal} of ${hybrid.run.totals.totalCalls - 1} executor steps stayed local; ${hybrid.run.totals.totalCloud} of ${hybrid.run.totals.totalCalls - 1} routed to cloud (planner is always cloud).`);
    lines.push("");
    for (const r of hybrid.run.stepResults) {
      const c = r.routerChoice === "local" ? "🖥" : "☁";
      lines.push(`- ${c} step ${r.step.index} _(${r.step.kind || "?"}, hint=${r.step.router_hint || "auto"})_: **${r.step.title || ""}** — ${fmtMs(r.elapsed)}, ${fmtUSD(r.cost?.usd || 0)}`);
    }
  }
  lines.push("");
  await writeFile(join(expDir, "comparison.md"), lines.join("\n"));
}

// ----- main -----------------------------------------------------------------
async function main() {
  // Discover experiments.
  const all = (await readdir(__dirname, { withFileTypes: true }))
    .filter((e) => e.isDirectory() && /^\d{2}-/.test(e.name))
    .map((e) => e.name)
    .sort();
  const targets = only ? all.filter((n) => n === only || n.startsWith(only)) : all;
  if (!targets.length) {
    console.error(`no experiments matched "${only ?? "(all)"}"; available: ${all.join(", ")}`);
    process.exit(2);
  }

  const aggregate = [];
  for (const id of targets) {
    const expDir = join(__dirname, id);
    const prompt = await readPrompt(expDir);
    console.log(`\n========== ${id} ==========`);
    console.log(`prompt: ${prompt.slice(0, 80).replace(/\n/g, " ")}…`);

    let cloud = null, hybrid = null;

    if (!skipCloud) {
      console.log(`\n→ cloud-only single-shot (router/always-cloud)…`);
      try {
        cloud = await runCloudOnly(prompt);
        console.log(`  done. ${fmtMs(cloud.elapsed)}, cost=${fmtUSD(cloud.cost.usd)}, tokens=${cloud.usage?.prompt_tokens || 0}/${cloud.usage?.completion_tokens || 0}`);
        await writeCloudRun(expDir, prompt, cloud);
      } catch (err) {
        console.error(`  cloud-only failed: ${err.message}`);
      }
    }

    if (!skipHybrid) {
      console.log(`\n→ hybrid architect mode…`);
      try {
        hybrid = await runHybrid(prompt);
        console.log(`  done. ${fmtMs(hybrid.run.totals.wallMs)}, hybrid cost=${fmtUSD(hybrid.run.totals.hybridCostUsd)}, ${hybrid.run.totals.totalLocal} local / ${hybrid.run.totals.totalCloud} cloud`);
        await writeHybridRun(expDir, prompt, hybrid);
      } catch (err) {
        console.error(`  hybrid failed: ${err.message}`);
      }
    }

    if (cloud || hybrid) {
      await writeComparison(expDir, cloud, hybrid);
      console.log(`✓ wrote ${expDir}/comparison.md`);
    }

    aggregate.push({ id, cloud, hybrid });
  }

  // Final aggregate.
  await writeAggregate(aggregate);
  console.log(`\n✓ wrote ${join(__dirname, "RESULTS.md")}`);
}

async function writeAggregate(rows) {
  const lines = [];
  lines.push(`# Hybrid vs cloud-only comparison — aggregate\n`);
  lines.push(`Run at: ${new Date().toISOString()}\n`);
  lines.push(`Local model: \`${process.env.LOCAL_MODEL || "qwen3.6:27b-coding-mxfp8"}\` (M4 Max via Ollama, native API with \`think:false\`).\n`);
  lines.push(`Cloud model: \`${CLOUD_MODEL}\` (\$5/M input, \$30/M output, \$0.50/M cached input — models.dev 2026-04-27).\n`);
  lines.push(`## Headline\n`);
  lines.push(`| experiment | cloud cost | hybrid cost | saved | cloud time | hybrid time | local/cloud calls |`);
  lines.push(`| --- | ---: | ---: | ---: | ---: | ---: | --- |`);
  for (const { id, cloud, hybrid } of rows) {
    const cc = cloud?.cost?.usd;
    const hc = hybrid?.run?.totals?.hybridCostUsd;
    const ct = cloud?.elapsed;
    const ht = hybrid?.run?.totals?.wallMs;
    const saved = cc != null && hc != null ? `${(((cc - hc) / cc) * 100).toFixed(0)}%` : "—";
    const calls = hybrid ? `${hybrid.run.totals.totalLocal}/${hybrid.run.totals.totalCloud}` : "—";
    lines.push(`| **${id}** | ${cc != null ? fmtUSD(cc) : "—"} | ${hc != null ? fmtUSD(hc) : "—"} | ${saved} | ${ct != null ? fmtMs(ct) : "—"} | ${ht != null ? fmtMs(ht) : "—"} | ${calls} |`);
  }
  lines.push("");
  lines.push(`## Per-experiment summary\n`);
  for (const { id, cloud, hybrid } of rows) {
    lines.push(`### ${id}`);
    lines.push("");
    if (cloud) lines.push(`- **cloud-only**: ${fmtUSD(cloud.cost.usd)}, ${fmtMs(cloud.elapsed)}, ${cloud.usage?.completion_tokens || 0} completion tokens`);
    if (hybrid) {
      lines.push(`- **hybrid**: ${fmtUSD(hybrid.run.totals.hybridCostUsd)}, ${fmtMs(hybrid.run.totals.wallMs)}, ${hybrid.run.totals.totalCalls} calls (${hybrid.run.totals.totalLocal} local / ${hybrid.run.totals.totalCloud} cloud)`);
    }
    lines.push(`- artefacts: \`${id}/cloud-only/run.md\`, \`${id}/hybrid/run.md\`, \`${id}/comparison.md\``);
    lines.push("");
  }
  await writeFile(join(__dirname, "RESULTS.md"), lines.join("\n"));
}

main().catch((err) => { console.error("FATAL:", err.stack || err.message); process.exit(1); });
