#!/usr/bin/env node
// End-to-end router test harness.
// Runs every prompt in test/prompts.json through every router strategy
// against the running proxy, capturing the routing decision (from
// X-Router-* response headers + the banner in the response body) and a
// short response sample.
// Writes a markdown report to test/RESULTS.md.

import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROXY = process.env.PROXY || "http://127.0.0.1:8787";
const TIMEOUT_MS = Number(process.env.PROMPT_TIMEOUT_MS || 60000);

// Strategies to test. Order matters for the table.
const STRATEGIES = [
  "always-local",
  "always-cloud",
  "rules",
  "heuristic",
  "llm-classifier",
  "embedding-knn",
  "cascade",
];

async function checkHealth() {
  try {
    const r = await fetch(`${PROXY}/healthz`, { signal: AbortSignal.timeout(5000) });
    if (!r.ok) throw new Error(`status ${r.status}`);
    return await r.json();
  } catch (err) {
    throw new Error(`proxy not reachable at ${PROXY}: ${err.message}`);
  }
}

async function runOne(strategy, prompt) {
  const t0 = Date.now();
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);

  try {
    const res = await fetch(`${PROXY}/v1/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: `router/${strategy}`,
        messages: [{ role: "user", content: prompt }],
        stream: false,
        max_tokens: 800,
        temperature: 0.2,
      }),
      signal: ctrl.signal,
    });
    clearTimeout(timer);

    const choice = res.headers.get("x-router-choice") || "?";
    const backend = res.headers.get("x-router-backend") || "?";
    const status = res.status;
    let bodyText = "";
    try {
      const j = await res.json();
      bodyText = j?.choices?.[0]?.message?.content || JSON.stringify(j).slice(0, 400);
    } catch {
      bodyText = await res.text().catch(() => "");
    }
    const elapsed = Date.now() - t0;

    // Extract router banner if present.
    let bannerLine = null;
    const m = /^\[router\][^\n]+/.exec(bodyText || "");
    if (m) bannerLine = m[0];
    const responseExcerpt = (bodyText || "")
      .replace(/^\[router\][^\n]+\n+/, "")
      .replace(/\s+/g, " ")
      .slice(0, 240);

    return {
      ok: status >= 200 && status < 300,
      status,
      choice,
      backend,
      elapsed,
      banner: bannerLine,
      excerpt: responseExcerpt,
    };
  } catch (err) {
    clearTimeout(timer);
    return { ok: false, status: 0, choice: "?", backend: "?", elapsed: Date.now() - t0, error: err.message };
  }
}

function fmtMs(ms) {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

async function main() {
  console.log(`Pinging proxy at ${PROXY} …`);
  const health = await checkHealth();
  console.log(`Proxy OK. local=${health.local.reachable ? "✓" : "✗"} cloud=${health.cloud.reachable ? "✓" : "✗"} (key ${health.cloud.key_present ? "present" : "missing"})\n`);

  const promptsRaw = await readFile(join(__dirname, "prompts.json"), "utf8");
  const prompts = JSON.parse(promptsRaw);

  // Results: prompts × strategies.
  const matrix = {};
  for (const p of prompts) matrix[p.tag] = {};

  let i = 0;
  for (const p of prompts) {
    i++;
    console.log(`[${i}/${prompts.length}] ${p.tag}`);
    for (const s of STRATEGIES) {
      process.stdout.write(`    ${s.padEnd(16)} … `);
      const r = await runOne(s, p.prompt);
      matrix[p.tag][s] = r;
      const tag = r.ok ? `${r.choice.padEnd(5)} (${r.backend}) ${fmtMs(r.elapsed)}` : `FAIL ${r.status} ${r.error || ""}`;
      console.log(tag);
    }
  }

  // Build markdown report.
  const lines = [];
  lines.push(`# Router test results`);
  lines.push("");
  lines.push(`Run at ${new Date().toISOString()}`);
  lines.push("");
  lines.push(`Proxy: ${PROXY}  `);
  lines.push(`Local backend: ${health.local.base} model=${health.local.model} reachable=${health.local.reachable}  `);
  lines.push(`Cloud backend: ${health.cloud.base} model=${health.cloud.model} reachable=${health.cloud.reachable} key_present=${health.cloud.key_present}  `);
  if (health.cloud.sample_models)
    lines.push(`Cloud sample models: ${health.cloud.sample_models.join(", ")}  `);
  lines.push("");

  lines.push(`## Decision matrix (which backend each strategy chose)`);
  lines.push("");
  lines.push(`| prompt | ${STRATEGIES.join(" | ")} |`);
  lines.push(`| --- | ${STRATEGIES.map(() => "---").join(" | ")} |`);
  for (const p of prompts) {
    const row = STRATEGIES.map((s) => {
      const r = matrix[p.tag][s];
      if (!r || !r.ok) return "✗";
      return r.choice === "cloud" ? "☁ cloud" : "🖥 local";
    });
    lines.push(`| **${p.tag}** | ${row.join(" | ")} |`);
  }
  lines.push("");

  lines.push(`## Latency per strategy (median ms)`);
  lines.push("");
  for (const s of STRATEGIES) {
    const ms = prompts
      .map((p) => matrix[p.tag][s])
      .filter((r) => r && r.ok)
      .map((r) => r.elapsed)
      .sort((a, b) => a - b);
    if (ms.length === 0) {
      lines.push(`- **${s}**: no successful runs`);
      continue;
    }
    const med = ms[Math.floor(ms.length / 2)];
    const min = ms[0];
    const max = ms[ms.length - 1];
    lines.push(`- **${s}**: median ${fmtMs(med)}, min ${fmtMs(min)}, max ${fmtMs(max)}, n=${ms.length}`);
  }
  lines.push("");

  lines.push(`## Per-prompt detail`);
  lines.push("");
  for (const p of prompts) {
    lines.push(`### ${p.tag}`);
    lines.push("");
    lines.push(`> ${p.prompt.replace(/\n/g, " ").slice(0, 200)}${p.prompt.length > 200 ? "…" : ""}`);
    lines.push("");
    lines.push(`| strategy | choice | backend | elapsed | banner / error |`);
    lines.push(`| --- | --- | --- | --- | --- |`);
    for (const s of STRATEGIES) {
      const r = matrix[p.tag][s];
      const choice = r?.choice || "?";
      const backend = r?.backend || "?";
      const elapsed = r ? fmtMs(r.elapsed) : "—";
      const note = r?.banner || r?.error || "";
      lines.push(`| ${s} | ${choice} | ${backend} | ${elapsed} | ${(note || "").replace(/\|/g, "/").slice(0, 220)} |`);
    }
    lines.push("");
    // Sample response from heuristic for quick eyeball:
    const hr = matrix[p.tag]["heuristic"];
    if (hr?.excerpt) {
      lines.push(`<details><summary>heuristic-routed response excerpt</summary>`);
      lines.push("");
      lines.push("```");
      lines.push(hr.excerpt);
      lines.push("```");
      lines.push("");
      lines.push(`</details>`);
      lines.push("");
    }
  }

  const outFile = join(__dirname, "RESULTS.md");
  await writeFile(outFile, lines.join("\n"));
  console.log(`\nWrote ${outFile}`);

  // Also write raw JSON for further analysis.
  const jsonFile = join(__dirname, "RESULTS.json");
  await writeFile(jsonFile, JSON.stringify({ proxy: PROXY, health, matrix }, null, 2));
  console.log(`Wrote ${jsonFile}`);
}

main().catch((err) => {
  console.error("FATAL:", err.message);
  process.exit(1);
});
