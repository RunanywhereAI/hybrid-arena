- Should cloud approval be one-time, per-provider, per-session, or per-privacy-tier?
- Should opencode own router training, or export telemetry to external eval/gateway systems?
- Should the native router wrap a virtual `LanguageModelV3` or select concrete models before assistant messages are created?
## 13. Recommendation
Build this in two tracks:
1. **Immediate track:** Use existing custom provider support to run local Ollama and an external gateway. This validates model quality, tool compatibility, and cost savings quickly.
2. **Native track:** Add a `Routing.Service` that decides before each assistant turn, records route decisions/outcomes, enforces privacy gates, and escalates on verification failure.
The first native router should be deliberately simple:
```text
privacy rules
  + task/risk heuristics
  + model capability filter
  + budget cap
  + local-first for high-confidence low-risk tasks
  + cloud for high-risk/high-complexity tasks when allowed
  + ask when privacy blocks cloud and local is unlikely to succeed
```
Then use opencode's own session outcomes to train a sub-1B classifier. The long-term win is not "always use local." The win is using frontier cloud models only when they are likely to change the outcome.
## 14. Source Links
Repository files inspected:
- `packages/opencode/src/session/prompt.ts`
- `packages/opencode/src/session/llm.ts`
- `packages/opencode/src/provider/provider.ts`
- `packages/opencode/src/config/config.ts`
- `packages/opencode/src/config/provider.ts`
- `packages/opencode/src/tool/registry.ts`
- `packages/opencode/src/session/session.sql.ts`
- `packages/opencode/src/server/routes/instance/session.ts`
Research sources used:
- Qwen3.6-35B-A3B: https://huggingface.co/Qwen/Qwen3.6-35B-A3B
- Qwen3-Coder 30B Ollama: https://ollama.com/library/qwen3-coder:30b
- Qwen2.5-Coder 32B: https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct
- Ollama docs: https://docs.ollama.com
- LiteLLM routing/fallbacks: https://docs.litellm.ai
- RouteLLM: https://github.com/lm-sys/RouteLLM and https://arxiv.org/abs/2406.18665
- FrugalGPT: https://arxiv.org/abs/2305.05176
- ModernBERT: https://huggingface.co/answerdotai/ModernBERT-base
- Sentence Transformers MiniLM: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- E5 small: https://huggingface.co/intfloat/e5-small-v2
- Qwen3-0.6B: https://huggingface.co/Qwen/Qwen3-0.6B
- Qwen2.5-Coder-0.5B: https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B-Instruct