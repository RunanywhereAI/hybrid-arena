// Authoritative per-million-token pricing for the cloud models the proxy can
// route to. Numbers fetched from https://models.dev/api.json on 2026-04-27.
// Same registry that opencode itself reads from (so opencode and the proxy
// agree on cost). All values are USD per 1,000,000 tokens.
//
// Cost = (prompt_tokens - cached_tokens) * input
//      + cached_tokens                   * cache_read
//      + completion_tokens               * output
//
// completion_tokens already includes reasoning_tokens for reasoning models —
// OpenAI's usage object exposes both, but you should NOT add them; they're
// counted inside completion_tokens. We surface reasoning_tokens separately
// only for transparency in the report.
//
// Local backends are billed at $0 (we treat the laptop electricity / hardware
// amortisation as free at the margin — the comparison is "what extra would I
// have paid the cloud provider"). This is documented in the report.

export const RATES_PER_M = {
  // OpenAI flagship reasoning family (April 2026)
  "gpt-5.5":      { input: 5.0,   output: 30.0,  cache_read: 0.5 },
  "gpt-5.5-pro":  { input: 30.0,  output: 180.0, cache_read: 3.0 },     // cache_read estimated at 10% of input (matches gpt-5/5.5 ratio)
  "gpt-5":        { input: 1.25,  output: 10.0,  cache_read: 0.125 },
  "gpt-5-mini":   { input: 0.25,  output: 2.0,   cache_read: 0.025 },
  "gpt-5-nano":   { input: 0.05,  output: 0.4,   cache_read: 0.005 },
  // Older non-reasoning OpenAI
  "gpt-4o":       { input: 2.5,   output: 10.0,  cache_read: 1.25 },
  "gpt-4o-mini":  { input: 0.15,  output: 0.6,   cache_read: 0.075 },
  "gpt-4-turbo":  { input: 10.0,  output: 30.0,  cache_read: 5.0 },
  "gpt-4":        { input: 30.0,  output: 60.0,  cache_read: 30.0 },
  "gpt-3.5-turbo":{ input: 0.5,   output: 1.5,   cache_read: 0.25 },
  // Anthropic (in case CLOUD_MODEL is ever pointed at an OpenAI-compatible
  // Anthropic gateway). 2026-04 rates.
  "claude-opus-4-7":     { input: 15.0,  output: 75.0,  cache_read: 1.5 },
  "claude-sonnet-4-6":   { input: 3.0,   output: 15.0,  cache_read: 0.3 },
  "claude-haiku-4-5":    { input: 1.0,   output: 5.0,   cache_read: 0.1 },
  // Local-served via Ollama / LM Studio / runanywhere-server / etc.
  "__local__":    { input: 0.0,   output: 0.0,   cache_read: 0.0 },
}

const FETCHED_AT = "2026-04-27T20:00:00Z"
const SOURCE = "https://models.dev/api.json"

// Normalise a model id to a key in RATES_PER_M.
//   "gpt-5.5-2026-04-23"      → "gpt-5.5"
//   "gpt-5.5-pro-2026-04-23"  → "gpt-5.5-pro"
//   "qwen3-coder:30b"         → "__local__"
//   "qwen3.6:27b-coding-mxfp8"→ "__local__"
//   anything unrecognised     → null
export function normaliseModelId(modelId) {
  if (!modelId) return null
  const s = String(modelId).toLowerCase().trim()
  // Local Ollama-style identifiers always include a colon (model:tag).
  if (s.includes(":")) return "__local__"
  // Exact match.
  if (RATES_PER_M[s]) return s
  // Strip OpenAI-style date suffix (`-YYYY-MM-DD`).
  const dated = s.replace(/-\d{4}-\d{2}-\d{2}$/, "")
  if (RATES_PER_M[dated]) return dated
  // Try progressively shorter prefixes (handle "gpt-5.5-pro-XX" variants).
  const parts = dated.split("-")
  while (parts.length > 1) {
    parts.pop()
    const candidate = parts.join("-")
    if (RATES_PER_M[candidate]) return candidate
  }
  return null
}

// Compute cost in USD given an OpenAI-shape usage object.
//
//   usage = {
//     prompt_tokens, completion_tokens, total_tokens,
//     prompt_tokens_details: { cached_tokens, ... },
//     completion_tokens_details: { reasoning_tokens, ... },
//   }
//
// Returns { usd, breakdown: { input_uncached, input_cached, output, reasoning_visible }, key, missing }
// Throws nothing; if the model isn't in the table, returns usd=0 and missing=true.
export function costFor(modelId, usage) {
  const key = normaliseModelId(modelId)
  const rates = key ? RATES_PER_M[key] : null

  const promptTokens = usage?.prompt_tokens ?? 0
  const completionTokens = usage?.completion_tokens ?? 0
  const cachedTokens = usage?.prompt_tokens_details?.cached_tokens ?? 0
  const reasoningTokens = usage?.completion_tokens_details?.reasoning_tokens ?? 0

  const uncachedPrompt = Math.max(0, promptTokens - cachedTokens)

  if (!rates) {
    return {
      usd: 0,
      breakdown: { input_uncached: 0, input_cached: 0, output: 0 },
      key: key ?? null,
      missing: true,
      tokens: { promptTokens, completionTokens, cachedTokens, reasoningTokens },
    }
  }

  const inputUncached = (uncachedPrompt / 1_000_000) * rates.input
  const inputCached   = (cachedTokens   / 1_000_000) * rates.cache_read
  const output        = (completionTokens / 1_000_000) * rates.output
  const usd = inputUncached + inputCached + output

  return {
    usd,
    breakdown: { input_uncached: inputUncached, input_cached: inputCached, output },
    key,
    missing: false,
    tokens: { promptTokens, completionTokens, cachedTokens, reasoningTokens },
  }
}

// USD formatter — shows enough precision for sub-cent costs.
export function fmtUSD(n, opts = {}) {
  const { sign = false, pad = 0 } = opts
  if (!isFinite(n)) return "$?"
  const v = Math.abs(n)
  let s
  if (v === 0)         s = "$0.0000"
  else if (v < 0.0001) s = `$${n.toFixed(6)}`
  else if (v < 0.01)   s = `$${n.toFixed(5)}`
  else if (v < 1)      s = `$${n.toFixed(4)}`
  else                 s = `$${n.toFixed(3)}`
  if (sign && n > 0) s = "+" + s
  return pad ? s.padStart(pad) : s
}

// Token formatter — comma thousands, padded.
export function fmtTok(n, pad = 0) {
  const s = (n ?? 0).toLocaleString("en-US")
  return pad ? s.padStart(pad) : s
}

export const PRICING_META = { fetched_at: FETCHED_AT, source: SOURCE }
