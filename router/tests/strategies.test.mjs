#!/usr/bin/env node
/**
 * Unit tests for the routing strategies in router/strategies.mjs that are
 * NOT the agent-aware heuristic (which has its own file,
 * agent-heuristic.test.mjs). Covers the deterministic strategies and the
 * offline-safe fallback paths of the model-backed ones.
 *
 * Uses Node's built-in test runner (node:test) — no extra deps, no running
 * proxy, no Ollama. The two model-backed strategies (llm-classifier,
 * embedding-knn) are exercised only on their network-failure fallback path:
 * we point ctx.localBase at a closed port so fetch refuses fast and the
 * strategy returns its documented `local` fallback. This keeps CI offline
 * and deterministic.
 *
 * Run via:
 *     node --test router/tests/strategies.test.mjs
 * or  npm test --prefix router   (globs tests/*.test.mjs)
 */

import { test } from "node:test";
import assert from "node:assert/strict";

import {
  alwaysLocal,
  alwaysCloud,
  rules,
  cascade,
  llmClassifier,
  embeddingKnn,
  STRATEGIES,
  lastUserText,
  approxTokens,
  countCodeBlocks,
} from "../strategies.mjs";

// A localBase that will refuse connections immediately (port 1 is
// privileged + unbound), so model-backed strategies hit their catch path
// without a slow timeout.
const DEAD_LOCAL_BASE = "http://127.0.0.1:1/v1";

const msg = (role, content) => ({ role, content });
const userReq = (text) => ({ messages: [msg("user", text)] });

// phase-aware reads its strategy via the registry (it's not a named export).
const phaseAware = STRATEGIES["phase-aware"].fn;

// -- helpers ----------------------------------------------------------------

test("approxTokens / countCodeBlocks / lastUserText behave", () => {
  assert.equal(approxTokens(""), 0);
  assert.equal(approxTokens("abcd"), 1); // 4 chars/token
  assert.equal(countCodeBlocks("```\nx\n```"), 1);
  assert.equal(countCodeBlocks("no fences here"), 0);
  assert.equal(
    lastUserText([msg("user", "first"), msg("assistant", "a"), msg("user", "last")]),
    "last",
  );
});

// -- always-local / always-cloud (controls) --------------------------------

test("always-local always returns local with full confidence", async () => {
  const r = await alwaysLocal(userReq("design a distributed system"));
  assert.equal(r.choice, "local");
  assert.equal(r.confidence, 1);
});

test("always-cloud always returns cloud with full confidence", async () => {
  const r = await alwaysCloud(userReq("rename a variable"));
  assert.equal(r.choice, "cloud");
  assert.equal(r.confidence, 1);
});

// -- rules ------------------------------------------------------------------

test("rules: cloud keyword routes cloud", async () => {
  const r = await rules(userReq("Please design the architecture for this service"));
  assert.equal(r.choice, "cloud");
  assert.match(r.reason, /kw\[cloud\]/);
});

test("rules: local keyword routes local", async () => {
  const r = await rules(userReq("just fix the typo in this comment"));
  assert.equal(r.choice, "local");
  assert.match(r.reason, /kw\[local\]/);
});

test("rules: a >4000-token paste forces cloud even with no keywords", async () => {
  const big = "x ".repeat(9000); // ~4500 tokens, no keywords
  const r = await rules(userReq(big));
  assert.equal(r.choice, "cloud");
  assert.match(r.reason, /tokens>/);
});

test("rules: >=3 code blocks forces cloud", async () => {
  const threeBlocks = "```\na\n```\n```\nb\n```\n```\nc\n```";
  const r = await rules(userReq(threeBlocks));
  assert.equal(r.choice, "cloud");
  assert.match(r.reason, /code-blocks>=3/);
});

test("rules: a plain short prompt defaults to local", async () => {
  const r = await rules(userReq("write a function that adds two numbers"));
  assert.equal(r.choice, "local");
  assert.match(r.reason, /default-local/);
});

// -- phase-aware ------------------------------------------------------------

test("phase-aware: aider architect role -> cloud", async () => {
  const req = {
    messages: [
      msg(
        "system",
        "You are an expert software engineer acting as the architect. Plan the change.",
      ),
      msg("user", "add a feature"),
    ],
  };
  const r = await phaseAware(req);
  assert.equal(r.choice, "cloud");
  assert.equal(r.meta.phase, "architect");
});

test("phase-aware: aider editor role -> local", async () => {
  const req = {
    messages: [
      msg(
        "system",
        "You are an expert software engineer acting as the editor. Apply the edits.",
      ),
      msg("user", "apply the diff"),
    ],
  };
  const r = await phaseAware(req);
  assert.equal(r.choice, "local");
  assert.equal(r.meta.phase, "editor");
});

test("phase-aware: non-aider request falls through to legacy heuristic", async () => {
  const req = { messages: [msg("user", "rename a variable")] };
  const r = await phaseAware(req);
  assert.equal(r.meta.phase, "fallback");
  // local-keyword "rename" should keep this on local
  assert.equal(r.choice, "local");
});

// -- llm-classifier: offline fallback ---------------------------------------

test("llm-classifier: network failure falls back to local (no hang)", async () => {
  const ctx = { localBase: DEAD_LOCAL_BASE, routerModel: "qwen3:0.6b" };
  const r = await llmClassifier(userReq("explain why this race condition occurs"), ctx);
  assert.equal(r.choice, "local");
  assert.match(r.reason, /llm-classifier: error/);
  assert.ok(r.confidence <= 0.5);
});

// -- embedding-knn: offline fallback ----------------------------------------

test("embedding-knn: corpus load failure falls back to local", async () => {
  const ctx = {
    localBase: DEAD_LOCAL_BASE,
    corpus: { path: "/nonexistent/corpus.json", _loaded: false },
    log: () => {},
  };
  const r = await embeddingKnn(userReq("optimize this data pipeline"), ctx);
  assert.equal(r.choice, "local");
  assert.match(r.reason, /empty corpus|fallback local/);
});

// -- cascade: trust-heuristic path (no model call) --------------------------

test("cascade: clear-cut prompt trusts the heuristic without a tie-break", async () => {
  // A short tool-result echo scores far below threshold => distance > 15 =>
  // cascade trusts the heuristic and never calls the (dead) classifier.
  const req = {
    messages: [
      msg("system", "You are a helpful assistant that can interact with a computer shell."),
      msg("assistant", "running"),
      { role: "tool", content: "<returncode>0</returncode>\nok" },
    ],
  };
  const ctx = { localBase: DEAD_LOCAL_BASE, cascadeThreshold: 15 };
  const r = await cascade(req, ctx);
  assert.equal(r.choice, "local");
  assert.match(r.reason, /trust-heuristic/);
});

// -- registry integrity -----------------------------------------------------

test("registry exposes all 8 strategies with a fn + description", () => {
  const names = [
    "always-local",
    "always-cloud",
    "rules",
    "heuristic",
    "llm-classifier",
    "embedding-knn",
    "cascade",
    "phase-aware",
  ];
  for (const n of names) {
    assert.ok(STRATEGIES[n], `missing strategy: ${n}`);
    assert.equal(typeof STRATEGIES[n].fn, "function");
    assert.equal(typeof STRATEGIES[n].description, "string");
  }
  assert.equal(Object.keys(STRATEGIES).length, 8);
});
