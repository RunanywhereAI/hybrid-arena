#!/usr/bin/env node
// Architect/Editor — per-subtask hybrid routing demo.
//
//   ┌──────────────┐       ┌──────────────────────────────────┐
//   │ user task    │──────▶│ Phase 1 : PLANNER (router/cloud) │
//   └──────────────┘       │  emits a structured JSON plan    │
//                          └──────────────────────────────────┘
//                                          │
//                                          ▼  for each step:
//                          ┌──────────────────────────────────┐
//                          │ Phase 2 : EXECUTOR               │
//                          │ each step → router/heuristic     │
//                          │  → individual local-or-cloud     │
//                          │  decision per step               │
//                          └──────────────────────────────────┘
//                                          │
//                                          ▼
//                          ┌──────────────────────────────────┐
//                          │ Phase 3 : SYNTHESIS (optional)   │
//                          │ folds per-step outputs into one  │
//                          │ coherent report (router/heuristic)│
//                          └──────────────────────────────────┘
//
// Usage:
//   node architect.mjs "your task"
//   node architect.mjs --dry-run "your task"           # plan only, no execution
//   node architect.mjs --planner router/always-cloud "your task"
//   node architect.mjs --executor router/cascade "your task"
//   node architect.mjs --max-steps 8 "your task"

import { writeFile, mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { costFor, fmtUSD } from "../pricing.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));

// Cloud model used for the all-cloud baseline. Read from env so the CLI
// always compares against whatever the proxy is actually configured to
// route to.
const BASELINE_CLOUD_MODEL = process.env.CLOUD_MODEL || "gpt-5.5";

// ----- args ----------------------------------------------------------------
const argv = process.argv.slice(2);
const opts = {
  proxy: process.env.PROXY || "http://127.0.0.1:8787",
  planner: "router/always-cloud",
  executor: "router/heuristic",
  synthesizer: "router/heuristic",
  maxSteps: 12,
  dryRun: false,
  out: null,
  task: "",
};
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === "--dry-run") opts.dryRun = true;
  else if (a === "--planner") opts.planner = argv[++i];
  else if (a === "--executor") opts.executor = argv[++i];
  else if (a === "--synthesizer") opts.synthesizer = argv[++i];
  else if (a === "--max-steps") opts.maxSteps = Number(argv[++i]);
  else if (a === "--proxy") opts.proxy = argv[++i];
  else if (a === "--out") opts.out = argv[++i];
  else if (a === "--help" || a === "-h") { printUsage(); process.exit(0); }
  else opts.task += (opts.task ? " " : "") + a;
}
if (!opts.task) { printUsage(); process.exit(1); }

function printUsage() {
  console.log(`architect.mjs — per-subtask hybrid routing demo

Usage:
  node architect.mjs [options] "<your task>"

Options:
  --planner    <model>    model id for the planning phase    (default: router/always-cloud)
  --executor   <model>    model id for each executor step    (default: router/heuristic)
  --synthesizer <model>   model id for final aggregation     (default: router/heuristic)
  --max-steps  <n>        cap on number of steps             (default: 12)
  --dry-run               make the plan but skip execution
  --proxy      <url>      proxy base url                     (default: http://127.0.0.1:8787)
  --out        <path>     write the markdown report here     (default: examples/<ts>-<slug>.md)
`);
}

// ----- helpers -------------------------------------------------------------

function nowSlug(task) {
  const ts = new Date().toISOString().replace(/[-:T]/g, "").slice(0, 15);
  const slug = task
    .toLowerCase()
    .replace(/[^a-z0-9 ]+/g, "")
    .trim()
    .split(/\s+/)
    .slice(0, 6)
    .join("-");
  return `${ts}-${slug || "task"}`;
}

function fmtMs(ms) {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function parsePlanFromText(text) {
  // Try to extract a JSON array. Accept either bare JSON or fenced.
  const fenced = /```(?:json|JSON)?\s*\n([\s\S]*?)\n```/g;
  let candidate = null;
  let m;
  while ((m = fenced.exec(text)) !== null) {
    const t = m[1].trim();
    if (t.startsWith("[")) candidate = t;
  }
  if (!candidate) {
    const idx = text.indexOf("[");
    const last = text.lastIndexOf("]");
    if (idx !== -1 && last > idx) candidate = text.slice(idx, last + 1);
  }
  if (!candidate) throw new Error("planner did not emit a JSON array");
  return JSON.parse(candidate);
}

async function callProxy({ proxy, model, system, user, maxTokens = 1500, temperature = 0.4 }) {
  const t0 = Date.now();
  const messages = [];
  if (system) messages.push({ role: "system", content: system });
  messages.push({ role: "user", content: user });
  const res = await fetch(`${proxy}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model, messages, stream: false, max_tokens: maxTokens, temperature }),
  });
  const elapsed = Date.now() - t0;
  if (!res.ok) {
    const errText = await res.text().catch(() => "");
    throw new Error(`proxy returned ${res.status}: ${errText.slice(0, 240)}`);
  }
  const j = await res.json();
  const content = j.choices?.[0]?.message?.content || "";
  const usage = j.usage || null;
  const routerChoice = res.headers.get("x-router-choice") || "?";
  const routerBackend = res.headers.get("x-router-backend") || "?";
  const echoedModel = res.headers.get("x-router-backend-model-echo") || j.model || routerBackend;
  // Hybrid cost = what we ACTUALLY paid: $0 for local calls, real OpenAI rates for cloud.
  const costKey = routerChoice === "local" ? "__local__" : echoedModel;
  const cost = costFor(costKey, usage);
  // Baseline cost = what we WOULD have paid if this call had gone cloud.
  // Used per-call so the totals can show a real "what hybrid saved you" number.
  const baselineCost = costFor(BASELINE_CLOUD_MODEL, usage);
  return {
    content,
    elapsed,
    routerStrategy: res.headers.get("x-router-strategy") || "?",
    routerChoice,
    routerBackend,
    echoedModel,
    usage,
    cost,
    baselineCost,
  };
}

// ----- planner system prompt ----------------------------------------------

const PLAN_SYSTEM = `You are a planning architect. Given a coding/technical task, decompose it into a sequence of small, independently-executable steps.

Output format — A SINGLE JSON ARRAY in a fenced \`\`\`json block. No prose before or after. Each element of the array MUST have these fields:

{
  "index": 1,
  "title": "short imperative title (≤ 60 chars)",
  "task": "detailed instruction for the executor — be self-contained, since the executor sees only this string and the user's original ask, not the rest of the plan",
  "kind": "edit | explain | test | search | design | refactor | review | summarise | answer",
  "rationale": "one short sentence on why this step exists",
  "depends_on": [<list of earlier step indices that must complete first, or []>],
  "expected_output": "code | prose | json | shell-output | none",
  "router_hint": "auto | local | cloud"
}

Rules:
1. Maximise STEP-LEVEL DECOMPOSITION. Each step should be doable in <5 minutes by a junior dev (router_hint:"local") OR is genuinely architectural and needs a flagship model (router_hint:"cloud"). Default to "auto" and let the router decide.
2. Order steps so dependencies are respected.
3. Cap at ${opts.maxSteps} steps.
4. Make each "task" self-contained and unambiguous.
5. NEVER include any text outside the fenced JSON block. No preamble, no postamble.`;

// ----- executor system prompt ----------------------------------------------

function executorSystem(originalTask, prevResults) {
  const ctx = prevResults
    .map(
      (r) =>
        `Step ${r.step.index} (${r.step.title}) → ${r.routerChoice.toUpperCase()} [${r.routerBackend}]:\n${(r.content || "").slice(0, 800)}`,
    )
    .join("\n\n---\n\n");
  return `You are an executor working on one step of a multi-step plan. Stay focused on the SINGLE step you are given. Be concise and direct — produce exactly the artifact the step asks for, nothing more.

ORIGINAL TASK FROM USER:
${originalTask}

${ctx ? `PRIOR STEP OUTPUTS (so you have context, do not re-do them):\n${ctx}\n\n` : ""}Now execute the step you receive. Output the artifact directly. Do not narrate the meta-process.`;
}

// ----- synthesizer system prompt ------------------------------------------

const SYNTH_SYSTEM = `You are a synthesiser. You receive (a) the user's original task, (b) a list of executed steps and their outputs. Produce a single coherent answer that delivers the user's task. Quote step outputs verbatim where helpful (especially code), summarise where helpful (especially explanatory prose). Keep the response tightly scoped to what the user asked for.`;

// ----- main flow -----------------------------------------------------------

async function main() {
  const startedAt = new Date();
  const slug = nowSlug(opts.task);
  const outPath = opts.out || join(__dirname, "examples", `${slug}.md`);
  await mkdir(dirname(outPath), { recursive: true });

  console.log(`\n📋 architect.mjs`);
  console.log(`   task        : ${opts.task}`);
  console.log(`   planner     : ${opts.planner}`);
  console.log(`   executor    : ${opts.executor}`);
  console.log(`   synthesizer : ${opts.synthesizer}`);
  console.log(`   max-steps   : ${opts.maxSteps}`);
  console.log(`   dry-run     : ${opts.dryRun}`);
  console.log(`   report      : ${outPath}\n`);

  // -- Phase 1: plan --
  console.log("Phase 1 ▸ planning…");
  const plannerResult = await callProxy({
    proxy: opts.proxy,
    model: opts.planner,
    system: PLAN_SYSTEM,
    user: opts.task,
    maxTokens: 4000,
    temperature: 0.3,
  });
  console.log(
    `   planner → ${plannerResult.routerChoice.toUpperCase().padEnd(5)} (${plannerResult.routerBackend.padEnd(28)}) ${fmtMs(plannerResult.elapsed).padStart(7)}  cost=${fmtUSD(plannerResult.cost.usd)}  in=${plannerResult.usage?.prompt_tokens ?? 0}  out=${plannerResult.usage?.completion_tokens ?? 0}`,
  );

  let plan;
  try {
    plan = parsePlanFromText(plannerResult.content);
  } catch (err) {
    console.error(`\n❌ planner returned unparsable plan: ${err.message}`);
    console.error(`first 600 chars of planner response:\n${plannerResult.content.slice(0, 600)}`);
    process.exit(2);
  }
  if (!Array.isArray(plan) || plan.length === 0) {
    console.error(`❌ plan is empty`);
    process.exit(2);
  }
  console.log(`   plan        : ${plan.length} steps`);
  for (const s of plan)
    console.log(
      `     [${s.index}] (${s.kind || "?"}, hint=${s.router_hint || "auto"}) ${(s.title || s.task || "").slice(0, 80)}`,
    );

  // -- Phase 2: execute --
  const stepResults = [];
  let totalLocal = 0, totalCloud = 0;
  if (!opts.dryRun) {
    console.log("\nPhase 2 ▸ executing…");
    for (const step of plan) {
      // Resolve router for this step.
      let stepModel = opts.executor;
      if (step.router_hint === "local") stepModel = "router/always-local";
      else if (step.router_hint === "cloud") stepModel = "router/always-cloud";

      const stepUserMsg = `Step ${step.index} — ${step.title || ""}\n\n${step.task}`;
      const t0 = Date.now();
      let er;
      try {
        er = await callProxy({
          proxy: opts.proxy,
          model: stepModel,
          system: executorSystem(opts.task, stepResults),
          user: stepUserMsg,
          maxTokens: 1500,
          temperature: 0.3,
        });
      } catch (err) {
        er = {
          content: `(executor error: ${err.message})`,
          elapsed: Date.now() - t0,
          routerStrategy: stepModel.replace(/^router\//, ""),
          routerChoice: "error",
          routerBackend: "?",
          error: err.message,
        };
      }
      const tag =
        er.routerChoice === "local"
          ? "🖥 local"
          : er.routerChoice === "cloud"
          ? "☁ cloud"
          : "✗ err";
      const costStr = er.cost ? fmtUSD(er.cost.usd) : "$?";
      const inTok = er.usage?.prompt_tokens ?? 0;
      const outTok = er.usage?.completion_tokens ?? 0;
      console.log(
        `   step ${String(step.index).padStart(2)} (${(step.kind || "?").padEnd(9)}) → ${tag.padEnd(8)} ${fmtMs(er.elapsed).padStart(7)}  cost=${costStr.padStart(9)}  in=${String(inTok).padStart(5)}  out=${String(outTok).padStart(5)}  hint=${step.router_hint || "auto"}`,
      );
      if (er.routerChoice === "local") totalLocal++;
      if (er.routerChoice === "cloud") totalCloud++;
      stepResults.push({ step, ...er, content: er.content });
    }
  } else {
    console.log("\nPhase 2 ▸ skipped (dry-run)");
  }

  // -- Phase 3: synthesise --
  let synthResult = null;
  if (!opts.dryRun && stepResults.length > 1) {
    console.log("\nPhase 3 ▸ synthesising…");
    const stepsBlob = stepResults
      .map(
        (r) =>
          `### Step ${r.step.index}: ${r.step.title || ""}\n(${r.routerChoice}/${r.routerBackend})\n\n${r.content}`,
      )
      .join("\n\n");
    synthResult = await callProxy({
      proxy: opts.proxy,
      model: opts.synthesizer,
      system: SYNTH_SYSTEM,
      user: `ORIGINAL TASK:\n${opts.task}\n\nEXECUTED STEPS:\n\n${stepsBlob}\n\nProduce the final answer.`,
      maxTokens: 16000,
      temperature: 0.3,
    });
    const sCost = synthResult.cost ? fmtUSD(synthResult.cost.usd) : "$?";
    const sIn = synthResult.usage?.prompt_tokens ?? 0;
    const sOut = synthResult.usage?.completion_tokens ?? 0;
    console.log(
      `   synth → ${synthResult.routerChoice.toUpperCase().padEnd(5)} (${synthResult.routerBackend.padEnd(28)}) ${fmtMs(synthResult.elapsed).padStart(7)}  cost=${sCost}  in=${sIn}  out=${sOut}`,
    );
    if (synthResult.routerChoice === "local") totalLocal++;
    if (synthResult.routerChoice === "cloud") totalCloud++;
  }

  // -- Cost roll-up --
  // Hybrid cost  = what we actually paid (local=$0, cloud=real rates).
  // Baseline     = what we WOULD have paid if every call had gone to the
  //                configured cloud model (priced using each call's actual
  //                token counts). Comparing to the same model the proxy
  //                falls back to keeps the comparison apples-to-apples.
  const allCalls = [
    plannerResult,
    ...stepResults,
    ...(synthResult ? [synthResult] : []),
  ];
  let hybridUSD = 0, baselineUSD = 0;
  let promptToks = 0, completionToks = 0, cachedToks = 0, reasoningToks = 0;
  for (const r of allCalls) {
    if (!r) continue;
    if (r.cost)         hybridUSD   += r.cost.usd          || 0;
    if (r.baselineCost) baselineUSD += r.baselineCost.usd  || 0;
    if (r.usage) {
      promptToks     += r.usage.prompt_tokens     || 0;
      completionToks += r.usage.completion_tokens || 0;
      cachedToks     += r.usage.prompt_tokens_details?.cached_tokens         || 0;
      reasoningToks  += r.usage.completion_tokens_details?.reasoning_tokens  || 0;
    }
  }
  const savedUSD = baselineUSD - hybridUSD;
  const savedPct = baselineUSD > 0 ? (savedUSD / baselineUSD) * 100 : 0;

  // -- Report --
  const finishedAt = new Date();
  const totalElapsed =
    (finishedAt - startedAt) / 1000;
  const totalCalls = 1 + stepResults.length + (synthResult ? 1 : 0);

  console.log("");
  console.log(`✓ done  ${stepResults.length} executor steps  •  ${totalLocal} local / ${totalCloud} cloud  •  ${totalElapsed.toFixed(1)}s wall  •  ${totalCalls} model calls`);
  console.log("");
  console.log(`╭─ cost summary ────────────────────────────────────────────╮`);
  console.log(`│  hybrid (actual paid)        : ${fmtUSD(hybridUSD).padStart(10)}                  │`);
  console.log(`│  all-cloud baseline (${BASELINE_CLOUD_MODEL.padEnd(8)})  : ${fmtUSD(baselineUSD).padStart(10)}                  │`);
  console.log(`│  saved                       : ${fmtUSD(savedUSD).padStart(10)}  (${savedPct.toFixed(0).padStart(3)}% off)        │`);
  console.log(`├───────────────────────────────────────────────────────────┤`);
  console.log(`│  prompt tokens     : ${String(promptToks).padStart(8)}  (${String(cachedToks).padStart(6)} cached)         │`);
  console.log(`│  completion tokens : ${String(completionToks).padStart(8)}  (${String(reasoningToks).padStart(6)} reasoning)      │`);
  console.log(`╰───────────────────────────────────────────────────────────╯`);

  const report = renderReport({
    task: opts.task,
    opts,
    startedAt,
    finishedAt,
    plannerResult,
    plan,
    stepResults,
    synthResult,
    totals: {
      totalLocal, totalCloud, totalCalls, totalElapsed,
      hybridUSD, baselineUSD, savedUSD, savedPct,
      promptToks, completionToks, cachedToks, reasoningToks,
    },
  });
  await writeFile(outPath, report);
  console.log(`\n  report → ${outPath}`);
}

function renderReport(d) {
  const L = [];
  L.push(`# Architect run — ${d.startedAt.toISOString()}`);
  L.push("");
  L.push(`**Task:** ${d.task}`);
  L.push("");
  L.push("**Options:**");
  L.push("");
  L.push("```");
  L.push(`proxy        : ${d.opts.proxy}`);
  L.push(`planner      : ${d.opts.planner}`);
  L.push(`executor     : ${d.opts.executor}`);
  L.push(`synthesizer  : ${d.opts.synthesizer}`);
  L.push(`max-steps    : ${d.opts.maxSteps}`);
  L.push(`dry-run      : ${d.opts.dryRun}`);
  L.push("```");
  L.push("");
  // -- Headline cost block (most-readable at top of report). --
  L.push("## Cost summary");
  L.push("");
  L.push(`| metric | value |`);
  L.push(`| --- | --- |`);
  L.push(`| **hybrid total (actual paid)** | **${fmtUSD(d.totals.hybridUSD)}** |`);
  L.push(`| all-cloud baseline (\`${BASELINE_CLOUD_MODEL}\`) | ${fmtUSD(d.totals.baselineUSD)} |`);
  L.push(`| saved | ${fmtUSD(d.totals.savedUSD)} (${d.totals.savedPct.toFixed(0)}%) |`);
  L.push(`| total prompt tokens (incl. cached) | ${d.totals.promptToks.toLocaleString()} |`);
  L.push(`| of which cached | ${d.totals.cachedToks.toLocaleString()} |`);
  L.push(`| total completion tokens (incl. reasoning) | ${d.totals.completionToks.toLocaleString()} |`);
  L.push(`| of which reasoning | ${d.totals.reasoningToks.toLocaleString()} |`);
  L.push(`| model calls | ${d.totals.totalCalls} (1 planner + ${d.stepResults.length} executor + ${d.synthResult ? 1 : 0} synth) |`);
  L.push(`| local / cloud calls | ${d.totals.totalLocal} / ${d.totals.totalCloud} |`);
  L.push(`| wall time | ${d.totals.totalElapsed.toFixed(1)} s |`);
  L.push("");
  L.push(`> Pricing: gpt-5.5 = \\$5/M input, \\$30/M output, \\$0.50/M cached input (models.dev, 2026-04-27). Local backend billed at \\$0 (laptop hardware/electricity treated as free at the margin). Baseline assumes the same prompt and completion token counts at cloud rates — a simplification (a cloud model may be more or less verbose than the local one), so this is the apples-to-apples upper bound for what going all-cloud would have cost on the same workload.`);
  L.push("");

  L.push("## Phase 1 — plan");
  L.push("");
  L.push(`Planner: \`${d.plannerResult.routerStrategy}\` → **${d.plannerResult.routerChoice.toUpperCase()}** (${d.plannerResult.routerBackend}) in ${fmtMs(d.plannerResult.elapsed)} — cost ${fmtUSD(d.plannerResult.cost.usd)} (in: ${d.plannerResult.usage?.prompt_tokens ?? 0} tok, out: ${d.plannerResult.usage?.completion_tokens ?? 0} tok)`);
  L.push("");
  L.push(`The planner produced **${d.plan.length} steps**:`);
  L.push("");
  L.push(`| # | kind | hint | title |`);
  L.push(`| --- | --- | --- | --- |`);
  for (const s of d.plan) {
    const t = (s.title || s.task || "").replace(/\|/g, "/").slice(0, 100);
    L.push(`| ${s.index} | ${s.kind || "?"} | ${s.router_hint || "auto"} | ${t} |`);
  }
  L.push("");

  L.push("## Phase 2 — executor decisions per step");
  L.push("");
  if (d.stepResults.length === 0) {
    L.push("_skipped (dry-run)_");
  } else {
    L.push(`| # | hint | choice | backend | elapsed | in | out | cost (paid) | cost (if cloud) |`);
    L.push(`| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |`);
    for (const r of d.stepResults) {
      const choiceCell =
        r.routerChoice === "local"
          ? "🖥 local"
          : r.routerChoice === "cloud"
          ? "☁ cloud"
          : `✗ ${r.routerChoice}`;
      const inTok = r.usage?.prompt_tokens ?? 0;
      const outTok = r.usage?.completion_tokens ?? 0;
      const paid = r.cost ? fmtUSD(r.cost.usd) : "?";
      const ifCloud = r.baselineCost ? fmtUSD(r.baselineCost.usd) : "?";
      L.push(
        `| ${r.step.index} | ${r.step.router_hint || "auto"} | ${choiceCell} | \`${r.routerBackend}\` | ${fmtMs(r.elapsed)} | ${inTok} | ${outTok} | ${paid} | ${ifCloud} |`,
      );
    }
  }
  L.push("");

  L.push("## Phase 3 — final synthesised answer");
  L.push("");
  if (d.synthResult) {
    const sCost = d.synthResult.cost ? fmtUSD(d.synthResult.cost.usd) : "$?";
    const sIfCloud = d.synthResult.baselineCost ? fmtUSD(d.synthResult.baselineCost.usd) : "$?";
    const sIn = d.synthResult.usage?.prompt_tokens ?? 0;
    const sOut = d.synthResult.usage?.completion_tokens ?? 0;
    L.push(`_(synthesiser: \`${d.synthResult.routerStrategy}\` → **${d.synthResult.routerChoice.toUpperCase()}** in ${fmtMs(d.synthResult.elapsed)} — paid ${sCost}, would-be ${sIfCloud} all-cloud; ${sIn} in / ${sOut} out)_`);
    L.push("");
    L.push("```text");
    L.push(stripBanner(d.synthResult.content).slice(0, 6000));
    L.push("```");
  } else {
    L.push("_skipped (single-step plan or dry-run)_");
  }
  L.push("");

  L.push("## Per-step output detail");
  L.push("");
  for (const r of d.stepResults) {
    L.push(`### Step ${r.step.index} — ${r.step.title || ""}`);
    L.push("");
    L.push(`*kind:* ${r.step.kind || "?"} • *hint:* ${r.step.router_hint || "auto"} • *route:* ${r.routerChoice} (${r.routerBackend}) • *elapsed:* ${fmtMs(r.elapsed)}`);
    L.push("");
    L.push(`> ${(r.step.task || "").replace(/\n/g, " ").slice(0, 220)}`);
    L.push("");
    L.push("```text");
    L.push(stripBanner(r.content).slice(0, 4000));
    L.push("```");
    L.push("");
  }

  // (Totals are at the top under "Cost summary".)
  return L.join("\n");
}

function stripBanner(text) {
  return (text || "").replace(/^\[router\][^\n]+\n+/, "");
}

main().catch((err) => {
  console.error("FATAL:", err.message);
  process.exit(1);
});
