// Architect / Editor pipeline — shared by the CLI (architect.mjs) and the
// proxy strategy (server.mjs handles model="router/architect" by calling
// runArchitect()).
//
// runArchitect(opts) calls the proxy three ways:
//   1. PLANNER  → opts.planner (default router/always-cloud) → JSON plan
//   2. EXECUTOR → opts.executor per step (default router/heuristic, with
//                  router_hint="local"|"cloud" overriding to those controls)
//   3. SYNTHESIS → opts.synthesizer (default router/heuristic) — only if >1 step
//
// Returns { plan, stepResults, synth, totals }.

import { lastUserText } from "../strategies.mjs";
import { costFor } from "../pricing.mjs";

export const PLAN_SYSTEM = (maxSteps) => `You are a planning architect. Given a coding/technical task, decompose it into a sequence of small, independently-executable steps.

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
3. Cap at ${maxSteps} steps.
4. Make each "task" self-contained and unambiguous.
5. NEVER include any text outside the fenced JSON block. No preamble, no postamble.`;

export const SYNTH_SYSTEM = `You are a synthesiser. You receive (a) the user's original task, (b) a list of executed steps and their outputs. Produce a single coherent answer that delivers the user's task. Quote step outputs verbatim where helpful (especially code), summarise where helpful (especially explanatory prose). Keep the response tightly scoped to what the user asked for.`;

export function executorSystem(originalTask, prevResults) {
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

export function parsePlanFromText(text) {
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

export async function callProxy({ proxy, model, system, user, maxTokens = 1500, temperature = 0.4 }) {
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
  // Cost. Local backend is keyed at __local__ (=$0); cloud uses the echoed
  // model id so OpenAI's dated variants (gpt-5.5-2026-04-23) resolve via
  // pricing.mjs's prefix matcher.
  const costKey = routerChoice === "local" ? "__local__" : echoedModel;
  const cost = costFor(costKey, usage);
  return {
    content,
    elapsed,
    routerStrategy: res.headers.get("x-router-strategy") || "?",
    routerChoice,
    routerBackend,
    echoedModel,
    usage,
    cost,
  };
}

// Compute the all-cloud baseline: what would this run have cost if every
// single call (planner + every executor step + synth) had gone to the
// configured cloud model? Uses the actual per-call usage we observed (since
// that's what we have to work with), priced at the cloud model's rates.
//
// Caveat: not perfect — the local model may produce different completion
// token counts than the cloud model would have. We make this assumption
// explicit in the report. As an upper-bound check it's still useful: if the
// local-completion-tokens approximation is biased (likely toward shorter
// because local models can be terser), our baseline UNDER-estimates cloud
// cost, so reported savings are conservative.
export function computeBaseline(run, cloudModelId) {
  let baseline = 0;
  const items = [];
  const collect = (label, callResult) => {
    if (!callResult || !callResult.usage) return;
    const c = costFor(cloudModelId, callResult.usage);
    baseline += c.usd;
    items.push({ label, usd: c.usd, key: c.key, tokens: c.tokens });
  };
  collect("planner", run.plannerResult);
  for (const r of run.stepResults || []) {
    collect(`step ${r.step.index} (${r.step.kind || "?"})`, r);
  }
  if (run.synth) collect("synth", run.synth);
  return { baseline, items, cloudModelId };
}

export function stripBanner(text) {
  return (text || "").replace(/^\[router\][^\n]+\n+/, "");
}

// runArchitect — the main pipeline.
//   opts.proxy        — proxy URL (default http://127.0.0.1:8787)
//   opts.task         — the user task
//   opts.planner      — model id (default router/always-cloud)
//   opts.executor     — model id per step (default router/heuristic)
//   opts.synthesizer  — model id for synthesis (default router/heuristic)
//   opts.maxSteps     — cap (default 12)
//   opts.dryRun       — if true, plan only, no execution
//   opts.onProgress   — optional callback(event) for live updates
//                       events: {type:"plan-start"|"plan-done"|"step-start"|"step-done"|"synth-start"|"synth-done", ...}
//
// Throws on planner failure; per-step errors are recorded and execution continues.
export async function runArchitect(opts) {
  const o = {
    proxy: "http://127.0.0.1:8787",
    planner: "router/always-cloud",
    executor: "router/heuristic",
    synthesizer: "router/heuristic",
    maxSteps: 12,
    dryRun: false,
    onProgress: () => {},
    ...opts,
  };
  if (!o.task) throw new Error("runArchitect: opts.task is required");

  const startedAt = Date.now();
  o.onProgress({ type: "plan-start", planner: o.planner });

  const plannerResult = await callProxy({
    proxy: o.proxy,
    model: o.planner,
    system: PLAN_SYSTEM(o.maxSteps),
    user: o.task,
    maxTokens: 4000,
    temperature: 0.3,
  });
  let plan;
  try {
    plan = parsePlanFromText(plannerResult.content);
  } catch (err) {
    throw new Error(`planner returned unparseable plan: ${err.message}`);
  }
  if (!Array.isArray(plan) || plan.length === 0) throw new Error("plan is empty");
  if (plan.length > o.maxSteps) plan = plan.slice(0, o.maxSteps);
  o.onProgress({ type: "plan-done", plan, plannerResult });

  const stepResults = [];
  let totalLocal = 0,
    totalCloud = 0;
  if (!o.dryRun) {
    for (const step of plan) {
      // Resolve router for this step.
      let stepModel = o.executor;
      if (step.router_hint === "local") stepModel = "router/always-local";
      else if (step.router_hint === "cloud") stepModel = "router/always-cloud";

      const stepUserMsg = `Step ${step.index} — ${step.title || ""}\n\n${step.task}`;
      o.onProgress({ type: "step-start", step, model: stepModel });
      let er;
      try {
        er = await callProxy({
          proxy: o.proxy,
          model: stepModel,
          system: executorSystem(o.task, stepResults),
          user: stepUserMsg,
          maxTokens: 1500,
          temperature: 0.3,
        });
      } catch (err) {
        er = {
          content: `(executor error: ${err.message})`,
          elapsed: 0,
          routerStrategy: stepModel.replace(/^router\//, ""),
          routerChoice: "error",
          routerBackend: "?",
          error: err.message,
        };
      }
      if (er.routerChoice === "local") totalLocal++;
      if (er.routerChoice === "cloud") totalCloud++;
      const r = { step, ...er };
      stepResults.push(r);
      o.onProgress({ type: "step-done", step, result: r });
    }
  }

  let synth = null;
  if (!o.dryRun && stepResults.length > 1) {
    o.onProgress({ type: "synth-start", synthesizer: o.synthesizer });
    const stepsBlob = stepResults
      .map(
        (r) =>
          `### Step ${r.step.index}: ${r.step.title || ""}\n(${r.routerChoice}/${r.routerBackend})\n\n${stripBanner(r.content)}`,
      )
      .join("\n\n");
    synth = await callProxy({
      proxy: o.proxy,
      model: o.synthesizer,
      system: SYNTH_SYSTEM,
      user: `ORIGINAL TASK:\n${o.task}\n\nEXECUTED STEPS:\n\n${stepsBlob}\n\nProduce the final answer.`,
      maxTokens: 2500,
      temperature: 0.3,
    });
    if (synth.routerChoice === "local") totalLocal++;
    if (synth.routerChoice === "cloud") totalCloud++;
    o.onProgress({ type: "synth-done", synth });
  }

  const wallMs = Date.now() - startedAt;
  // Aggregate hybrid cost across every model call we made.
  let hybridCost = 0;
  let totalPromptTokens = 0;
  let totalCompletionTokens = 0;
  let totalCachedTokens = 0;
  let totalReasoningTokens = 0;
  const accumulate = (r) => {
    if (!r) return;
    if (r.cost) hybridCost += (r.cost.usd || 0);
    if (r.usage) {
      totalPromptTokens     += r.usage.prompt_tokens || 0;
      totalCompletionTokens += r.usage.completion_tokens || 0;
      totalCachedTokens     += r.usage.prompt_tokens_details?.cached_tokens || 0;
      totalReasoningTokens  += r.usage.completion_tokens_details?.reasoning_tokens || 0;
    }
  };
  accumulate(plannerResult);
  for (const r of stepResults) accumulate(r);
  if (synth) accumulate(synth);

  return {
    task: o.task,
    plan,
    plannerResult,
    stepResults,
    synth,
    totals: {
      totalLocal,
      totalCloud,
      totalCalls: 1 + stepResults.length + (synth ? 1 : 0),
      wallMs,
      hybridCostUsd: hybridCost,
      promptTokens: totalPromptTokens,
      completionTokens: totalCompletionTokens,
      cachedTokens: totalCachedTokens,
      reasoningTokens: totalReasoningTokens,
    },
  };
}

// Helper: extract the "user task" from an OpenAI-style chat-completion body.
// Used by the proxy when model="router/architect" — the architect needs ONE
// task string, not a multi-message conversation.
export function userTaskFromMessages(messages) {
  return lastUserText(messages || []);
}

// Compose a single human-readable answer from an architect run, suitable for
// returning as the assistant message body when called via the proxy.
export function answerFromRun(run) {
  const L = [];
  L.push(`# Architect mode\n`);
  L.push(`**Task:** ${run.task}\n`);
  L.push(`**Plan (${run.plan.length} steps):**\n`);
  for (const s of run.plan) {
    L.push(`  ${s.index}. _(${s.kind || "?"}, hint=${s.router_hint || "auto"})_  ${s.title || ""}`);
  }
  L.push("");
  L.push("**Per-step routing decisions:**\n");
  L.push("| # | kind | choice | backend | elapsed |");
  L.push("| --- | --- | --- | --- | --- |");
  for (const r of run.stepResults) {
    const choice =
      r.routerChoice === "local" ? "🖥 local" : r.routerChoice === "cloud" ? "☁ cloud" : `✗ ${r.routerChoice}`;
    L.push(
      `| ${r.step.index} | ${r.step.kind || "?"} | ${choice} | ${r.routerBackend} | ${(r.elapsed / 1000).toFixed(1)}s |`,
    );
  }
  L.push("");
  L.push(`**Totals:** ${run.totals.totalCalls} model calls • ${run.totals.totalLocal} local / ${run.totals.totalCloud} cloud • ${(run.totals.wallMs / 1000).toFixed(1)}s wall\n`);
  L.push("---\n");
  if (run.synth) {
    L.push("## Final answer\n");
    L.push(stripBanner(run.synth.content));
  } else if (run.stepResults.length === 1) {
    L.push("## Step output\n");
    L.push(stripBanner(run.stepResults[0].content));
  } else {
    L.push("## Per-step outputs\n");
    for (const r of run.stepResults) {
      L.push(`### Step ${r.step.index}: ${r.step.title || ""}\n`);
      L.push(stripBanner(r.content));
      L.push("");
    }
  }
  return L.join("\n");
}
