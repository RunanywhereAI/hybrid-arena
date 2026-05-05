# Research Report

**Query:** Detailed survey of hybrid local + cloud LLM routing as actually deployed in production coding agents and developer tools as of April 2026. Cover deeply: Cursor (Tab/Fusion model, Fast Apply, Composer 1/2, Composer 2 technical report, any internal classification model); GitHub Copilot Auto and the POST /models/session/intent endpoint, Next Edit Suggestions custom model, what model their auto-router uses; Sourcegraph Cody completion lifecycle; Continue.dev model roles; Cline / Roo Code / Aider model selection logic; Codeium / Windsurf Adaptive (Cascade); Tabby (TabbyML); Replit Agent v2/v3 segmented control; Zed AI; Augment Code; Sweep AI; OpenInterpreter; Anthropic Claude Code Auto Mode safety classifier; opencode plugins like marco-jardim/opencode-model-router; Goose by Block; aider-style architect/editor splits in other tools. For each: routing mechanism (rules vs ML), what signals they route on, latency, cost savings claimed or measured, postmortems and engineering blog posts, open-source code if any. Be specific about whether they ship ML routing vs hard-coded rules. Cite blog posts, eng blogs, conference talks, GitHub repos, and YouTube engineering deep-dives.
**Run ID:** `2501ab9b`
**Generated:** 2026-04-26T00:43:33Z

---

## Perplexity Deep Research
*Model: `sonar-deep-research` · 11s · 283 prompt + 691 completion tokens*

<think>
This is a very specific, technical question asking about the state of hybrid local + cloud LLM routing in production coding agents as of April 2026. The user is asking for a comprehensive survey with specific implementations across many tools.

I need to be careful here. My knowledge cutoff is April 2024, and the user is asking about the state as of April 2026. That's 2 years in the future from my training data. I should not make up or speculate about what technologies exist in April 2026.

I should clarify my knowledge cutoff and explain what I can and cannot know about April 2026. I can discuss what I know up to April 2024, but I cannot reliably know what has been deployed or what technical decisions have been made in the 2-year period from April 2024 to April 2026.

The user is asking for very specific technical details, blog posts, engineering deep-dives, YouTube videos, GitHub repos, and postmortems from April 2026, which I cannot have access to as my training data ends in April 2024.

I should:
1. Clearly state my knowledge cutoff
2. Explain that I cannot reliably answer questions about April 2026
3. Offer to help with what I do know from my training data cutoff
4. Be honest about the limitations
</think>

# Important Knowledge Cutoff Notice

I must be transparent about a critical limitation: **My training data ends in April 2024**, and you're asking me to provide a detailed survey of production systems "as of April 2026"—two years beyond my knowledge cutoff.

I cannot reliably provide:

- Blog posts, engineering deep-dives, or conference talks from 2024-2026
- Current production deployments or architectural changes made in that timeframe
- Postmortems or incident reports from 2025-2026
- Code changes or open-source releases from the last 2 years
- New tools or versions released after April 2024
- Performance measurements or cost savings claims from recent deployments

## What I Can Do Instead

I can offer:

1. **Pre-April 2024 state of the art**: A detailed survey of hybrid routing approaches as documented up to my knowledge cutoff, covering what was known about:
   - Cursor's architecture (pre-Composer 2 final release details)
   - GitHub Copilot's publicly documented routing
   - Continue.dev, Cline, Aider architectures
   - General patterns in ML-based vs rules-based routing

2. **Technical framework**: Discuss the general architecture patterns, tradeoffs, and signal types that would be relevant for such routing systems

3. **Help you research April 2026 state**: Guidance on where to find these resources (official blogs, GitHub repositories, arXiv papers, conference proceedings)

**Which approach would be most useful?** If you're looking for a comprehensive April 2026 survey, I'd recommend:
- Checking each tool's official engineering blog directly
- Reviewing recent arXiv papers on LLM routing
- Examining GitHub repositories for deployed code
- Checking conference proceedings (OSDI, SOSP, MLSys 2025-2026)

Would you like me to provide what I reliably know from pre-April 2024, or help you construct a research strategy for finding April 2026 data?

---

## Exa Deep Search  (15 sources)

### 1. Cursor: The best way to code with AI
**URL:** https://cursor.com/

Cursor: The best way to code with AI

# Built to make you extraordinarily productive, Cursor is the best way to code with AI.

## Trusted every day by teams that build world-class software

### Agents turn ideas into code

Accelerate development by handing off tasks to Cursor, while you focus on making decisions.Learn about agentic development →

### Works autonomously, runs in parallel

Agents use their own computers to build, test, and demo features end to end for you to review.

Learn about cloud agents →

cursor.com/agent

This Week

Acme Research Dashboard

Live Telemetry Pipeline

Zero-Downtime Deploys

This Month

Binary Protocol Parser

Edge Cache Invalidation

Auth Token Rotation

Acme Research Dashboard

let's build a dashboard to make our research findings interactive

Explored 12 files, 4 searches

On it. I'll build the dashboard using your theme config, wire up the research data, and add interactive charts with public access controls.

Worked for 14m 22s

Processed screen recording

Done! Here's a walkthrough of the dashboard.

Acme Labs

Summary

Built the interactive dashboard with realtime charts, data from Snowflake, and shadcn components. Deployed to staging via Vercel.

Add a follow up...

Agent

Opus 4.6

### In every tool, at every step

Cursor runs in your terminal, collaborates in Slack, and reviews PRs in GitHub.

`curl https://cursor.com/install -fsS | bash`

### Magically accurate autocomplete

Our specialized Tab model predicts your next action with striking speed and precision.Learn about Tab →

## The new way to build software.

“It was night and day from one batch to another, adoption went from single digits to over 80%. It just spread like wildfire, all the best builders were using Cursor.”

Diana Hu General Partner, Y Combinator

“My favorite enterprise AI service is Cursor. Every one of our engineers, some 40,000, are now assisted by AI and our productivity has gone up incredibly.”

Jensen Huang President & CEO, NVIDIA

“The best LLM applications have an autonomy slider: you control how much independence to give the AI. In Cursor, you can do Tab completion, Cmd+K for targeted edits, or you can let it rip with the full autonomy agentic version.”

Andrej Karpathy CEO, Eureka Labs

“Cursor quickly grew from hundreds to thousands of extremely enthusiastic Stripe employees. We spend more on R&D and software creation than any other undertaking, and there's significant economic outcomes when making that process more efficient.”

Patrick Collison Co‑Founder & CEO, Stripe

“The most useful AI tool that I currently pay for, hands down, is Cursor. It's fast, autocompletes when and where you need it to, handles brackets properly, sensible keyboard shortcuts, bring-your-own-model... everything is well put together.”

shadcn Creator of shadcn/ui

“It's definitely becoming more fun to be a programmer. We are at the 1% of what's possible, and it's in interactive experiences like Cursor where models like GPT-5 shine brightes

*… (1,286 more characters — see results.json for full text)*

---

### 2. A new Tab model · Cursor
**URL:** https://cursor.com/en/blog/tab-update
**Published:** 2025-01-13T21:08:00.000Z

A new Tab model · Cursor

Today, we are announcing`Fusion`, our next generation Cursor Tab model.

Cursor Tab predicts both edits near your cursor and suggestions for where to move next (“jumps”). The`Fusion` model produces nearly instant, much higher quality cursor jumps while improving edit quality as well. Our proximate goal with Tab is to eliminate tedium from code editing, and`Fusion` is a significant improvement in that direction, taking us further on the path to our ultimate goal of in-flow Next Action Prediction.

## The most useful copilot

Beginning in March of 2024, Tab has been powered by a custom sparse language model trained to predict edits on billions of tokens. Since then, we’ve improved nearly every aspect of Tab, making it faster, more intelligent, and more useful over the course of dozens of model updates and infrastructure improvements.

We’ve found Tab has become more useful as we’ve continued developing it, and we’re delighted our users have too. Tab has become much bigger; it now produces over a billion edited characters per day, and the request rate has grown ~100x since our original model launch. At this point, our Tab model generates more code than almost any LLM in the world.

We’ve long since realized that inserting text is a tiny part of editing code. While other copilots only insert text at your cursor location, Cursor Tab suggests both full edits around your cursor and jumps you to the next place you want to go.

By quickly suggesting accurate edits and jumps, Tab is much more useful than other copilots. Of course, Tab can do the typical copilot tasks well too — it is good at writing small functions and following inline instructions at low latency.

## Improvements since March

Our first Tab model was trained and shipped in March 2024. Compared to this original model release, Fusion accurately predicts over 25% more difficult edits per line, while also suggesting over 10x longer stretches of changes. Fusion also improves on our original model in several other ways:

| Model version | Server latency (p50) | Cursor jumps | Context length (tokens) |
| --- | --- | --- | --- |
| Original | 475ms | None | 5500 |
| Fusion | 260ms | Instant, accurate | 13000 |

`Fusion` vastly outperforms the March model on suggestion accuracy, while providing nearly instant and higher quality cursor jumps, longer context, and lower latency.

Gains in model quality come from:

Cleaner, higher quality, and higher quantity data

Longer context windows with much more editor state and file content in the prompt

Carefully training for larger edits, resulting in the Bigger Edits model

Synthetic data for instruction following

Training recipe and base model improvements

Gains in latency come from inference improvements, performance engineering, and better base models.

## Looking forward

`Fusion` is rolling out to all users with our new client release (0.45.0).

Our next suite of Tab improvements will bring much better codebase context, bette

*… (544 more characters — see results.json for full text)*

---

### 3. LLM routing instead of heuristic-based "Auto" selection? - Help - Cursor - Community Forum
**URL:** https://forum.cursor.com/t/llm-routing-instead-of-heuristic-based-auto-selection/154050
**Published:** 2026-03-08T13:12:22.000Z

LLM routing instead of heuristic-based "Auto" selection? - Help - Cursor - Community Forum

LLM routing instead of heuristic-based "Auto" selection? - Help - Cursor - Community Forum

---

### 4. Untitled
**URL:** https://arxiv.org/pdf/2603.24477

Composer 2 Technical Report
Cursor Research Team
1 Introduction
Composer 2 is a specialized model designed for agentic software engineering. The model
demonstrates strong long-term planning and coding intelligence while maintaining the
ability to efficiently solve problems for interactive use. The model scores strongly on
CursorBench, our benchmark of real-world software engineering (Figure 1), while also
scoring at frontier levels on public software engineering benchmarks such as SWE-bench
Multilingual [28] and Terminal-Bench [39].
The model is trained in two phases: first, continued pretraining to improve the model’s
knowledge and latent coding ability, followed by large-scale reinforcement learning to
improve end-to-end coding performance through stronger reasoning, accurate multi-step
execution, and coherence on long-horizon realistic coding problems.
A core tenet of Composer training is to emulate real-world user challenges as closely as
possible to minimize train-test mismatch. We develop infrastructure to support training
in the same Cursor harness that is used by the deployed model, with equivalent tools and
structure, and use environments that match real problems closely. To measure the ability
of the model on increasingly difficult tasks, we introduce a benchmark derived from real
software engineering problems in large codebases including our own.
Composer 2 is a frontier-level coding model and demonstrates a process for training strong
domain-specialized models. On our CursorBench evaluations the model achieves a major
improvement in accuracy compared to previous Composer models (61.3). On public benchmarks the model scores 61.7 on Terminal-Bench and 73.7 on SWE-bench Multilingual in our
harness, comparable to state-of-the-art systems.
Figure 1: Composer 2 improves greatly from previous Composer models, achieving
performance competitive with state-of-the-art models. By specializing entirely on coding
ability, Composer attains such performance while being lower cost to serve than state-ofthe-art model API pricing. See Section 5 for detailed evaluations.
1
arXiv:2603.24477v2 [cs.SE] 26 Mar 2026
2 Background and Related Work
Generating code has been a standout application of large language models [15, 9, 7, 31].
Code provides a rich source of challenging training data that has supplemented language
data in most large models [16, 30, 36, 51, 19, 10, 5, 44, 25, 71, 72, 62, 41]. Early applications of
code generation typically focused on autocomplete applications. Subsequently, instruction
tuning turned models into coding assistants [37, 73, 83, 43] capable of responding to user
requests. In the last year, software engineering agents have achieved widespread adoption,
pushing models beyond chat to autonomously navigate repositories and solve complex
engineering tasks [75, 76, 70, 49, 23].
Software engineering agents aim to autonomously act to solve a given task prompt. Given
an environment, i.e., a codebase and an isolated container for cod

*… (22,000 more characters — see results.json for full text)*

---

### 5. Composer: Building a fast frontier model with RL · Cursor
**URL:** https://cursor.com/blog/composer
**Published:** 2025-10-29T06:49:00.000Z

Composer: Building a fast frontier model with RL · Cursor

Composer is our new agent model designed for software engineering intelligence and speed. On our benchmarks, the model achieves frontier coding results with generation speed four times faster than similar models.

We achieve these results by training the model to complete real-world software engineering challenges in large codebases. During training, Composer is given access to a set of production search and editing tools and tasked with efficiently solving a diverse range of difficult problems. The final result is a large-scale model optimized for high-speed use as an agent in Cursor.

Our motivation comes from our experience developing Cursor Tab, our custom completion model. We found that often developers want the smartest model that can support interactive use, keeping them in the flow of coding. In our development process, we experimented with a prototype agent model, codenamed Cheetah, to better understand the impact of faster agent models. Composer is a smarter version of this model that keeps coding delightful by being fast enough for an interactive experience.

Composer is a mixture-of-experts (MoE) language model supporting long-context generation and understanding. It is specialized for software engineering through reinforcement learning (RL) in a diverse range of development environments. At each iteration of training, the model is given a problem description and instructed to produce the best response, be it a code edit, a plan, or an informative answer. The model has access to simple tools, like reading and editing files, and also more powerful ones like terminal commands and codebase-wide semantic search.

To measure progress, we constructed an evaluation that measures a model's usefulness to a software developer as faithfully as possible. Our benchmark, Cursor Bench, consists of real agent requests from engineers and researchers at Cursor, along with hand-curated optimal solutions to these requests. The resulting evaluation measures not just the agent’s correctness, but also its adherence to a codebase's existing abstractions and software engineering practices.

Reinforcement learning allows us to actively specialize the model for effective software engineering. Since response speed is a critical component for interactive development, we incentivize the model to make efficient choices in tool use and to maximize parallelism whenever possible. In addition, we train the model to be a helpful assistant by minimizing unnecessary responses and claims made without evidence. We also find that during RL, the model learns useful behaviors on its own like performing complex searches, fixing linter errors, and writing and executing unit tests.

Efficient training of large MoE models requires significant investment into building infrastructure and systems research. We built custom training infrastructure leveraging PyTorch and Ray to power asynchronous reinforcement learning at scale.

*… (2,294 more characters — see results.json for full text)*

---

### 6. Evolving GitHub Copilot’s next edit suggestions through custom model training - The GitHub Blog
**URL:** https://github.blog/ai-and-ml/github-copilot/evolving-github-copilots-next-edit-suggestions-through-custom-model-training/
**Published:** 2025-11-20T18:02:21.000Z

Evolving GitHub Copilot’s next edit suggestions through custom model training - The GitHub Blog

&

November 20, 2025 | Updated November 25, 2025

| 9 minutes

- Share:

Editing code often involves a series of small but necessary changes ranging from refactors to fixes to cleanup and edge-case handling. In February, we launched next edit suggestions (NES), a custom Copilot model that predicts the next logical edit based on the code you’ve already written. Since launch, we’ve shipped several major model updates, including the newest release earlier this month.

In this post, we’ll look at how we built the original model, how we’ve improved it over time, what’s new, and what we’re building next.

## Why edit suggestions are challenging

Predicting the next edit is a harder problem than predicting the next token. NES has to understand what you’re doing, why you’re doing it, and what you’ll likely do next. That means:

- The model must respond quickly to keep up with your flow.
- It has to know when not to suggest anything (too many suggestions can break your focus).
- It must infer intent from local context alone without your explicit prompts.
- It must integrate deeply with VS Code so suggestions appear exactly where you expect them.

Frontier models didn’t meet our quality and latency expectations. The smaller ones were fast but produced low-quality suggestions, while the larger ones were accurate but too slow for an in-editor experience. To get both speed and quality, we needed to train a custom model.

NES isn’t a general-purpose chat model. It’s a low-latency, task-specific model that runs alongside the editor and responds in real time. It’s the result of aligning model training, prompting, and UX around a single goal: seamless editing inside the IDE. That required tight coordination between model training, prompt design, UX design, and the VS Code team—the model only works because the system was co-designed end-to-end.

This “AI-native” approach where every part of the experience evolves together is very different from training a general-purpose model for any task or prompt. It’s how we believe AI features should be built: end to end, with the developer experience at the center.

## How we trained

The hard part wasn’t the architecture; it was the data. We needed a model that could predict the next edit a developer might make, but no existing dataset captured real-time editing behavior.

Our first attempt used internal pull request data. It seemed reasonable: pull requests contain diffs, and diffs look like edits. But internal testing revealed limitations. The model behaved overly cautiously—reluctant to touch unfinished code, hesitant to suggest changes to the line a user was typing, and often chose to do nothing. In practice, it performed worse than a vanilla LLM.

That failure made the requirement clear: we needed data that reflected how developers actually edit code in the editor, not how code looks after review.

Pull request data wasn’t

*… (10,393 more characters — see results.json for full text)*

---

### 7. About Copilot auto model selection - GitHub Docs
**URL:** https://docs.github.com/copilot/concepts/auto-model-selection

# About Copilot auto model selection

Automatically select models for Copilot Chat, Copilot cloud agent, and third-party agents.

## Overview

Experience less rate limiting and reduce the mental load of choosing a model by letting Copilot auto model selection choose the best available model on your behalf.

Copilot auto model selection intelligently chooses models based on real time system health and model performance. You benefit from:

- Reduced rate limiting
- Lower latency and errors
- Discounted multipliers for paid plans (Copilot Chat only)

Auto model selection won't include these models:

- Models excluded by administrator policies. See Configuring access to AI models in GitHub Copilot.
- Models with premium request multipliers greater than one. See Supported AI models in GitHub Copilot.
- Models not available in your plan. See Supported AI models in GitHub Copilot.

> [!NOTE] Soon Copilot auto model selection will choose the best model for you based on your task.

## Auto model selection in Copilot Chat

Auto model selection is generally available in the following IDEs:

- VS Code
- JetBrains IDEs

Auto model selection is in public preview for the following IDEs:

- Visual Studio
- Eclipse
- Xcode

When you select Auto in Copilot Chat in IDEs, Auto model selection chooses from the supported models, subject to your policies and subscription type. Models may change over time. See Supported AI models in GitHub Copilot.

> [!TIP] To see which model was used for each response, hover over the response in Copilot Chat in IDEs.

You can change the model Copilot uses to generate responses to chat prompts. You may find that different models perform better, or provide more useful responses, depending on the type of questions you ask. Options include premium models with advanced capabilities. See Changing the AI model for GitHub Copilot Chat.

### Multiplier discounts

If you are on a paid Copilot plan and use auto model selection, models qualify for a 10% multiplier discount. See Requests in GitHub Copilot.

### Enabling access during public preview

During the public preview, if you're using a Copilot Business or Copilot Enterprise plan, the organization or enterprise that provides your plan must have the Editor preview features policy enabled. See Managing policies and features for GitHub Copilot in your organization or Managing policies and features for GitHub Copilot in your enterprise.

## Auto model selection in GitHub Copilot CLI

When you select Auto from the list of available models in GitHub Copilot CLI, Auto model selection chooses from the supported models, subject to your policies and subscription type. Models may change over time. See Supported AI models in GitHub Copilot.

When using Auto, the model used for each response displays in the terminal.

You can change the model Copilot uses to generate responses to chat prompts. You may find that different models perform better, or provide more useful responses, depending on the type of q

*… (1,292 more characters — see results.json for full text)*

---

### 8. The lifecycle of a code AI completion | Sourcegraph
**URL:** https://sourcegraph.com/blog/the-lifecycle-of-a-code-ai-completion
**Published:** 2023-10-31T00:00:00.000Z

The lifecycle of a code AI completion | Sourcegraph

BLOG The lifecycle of a code AI completion

# The lifecycle of a code AI completion

Demystifying code AI: Learn how Cody analyzes context, retrieves references, prompts models, and refines completions behind the scenes.

Generative AI, whether for code, text, images, or other use cases, appears as a magic black box to many users. Users typically navigate to a website, install an app, or set up an extension and start seeing the results of the AI tool. But, have you ever wondered what goes into this magic black box or how it really works?

In this post, we want to demystify what goes into a code AI completion for Cody, our code AI assistant that knows your entire codebase. Leveraging a Large Language Model (LLM) to generate a code AI response is fairly trivial, but doing so in a production-grade application that serves many different use cases, coding languages, workflows, and other variables while achieving a high-level of completion acceptance and developer happiness is a whole other thing. We'll cover the importance of the underlying LLM but also expand the implementation to a fully featured AI engineering system that features various pre and post processing steps, discuss the role of context and how to retrieve it, and more as we explore the lifecycle of a code AI completion. Let's dive in!

## Code completions 101

In its minimal form, a code autocomplete request takes the current code inside the editor and asks an LLM to complete it. You can do this with ChatGPT too! Consider the following example:

`// sort.jsfunction bubbleSort(array) { |}`

From this limited file we already have a lot of information to work with:

- The cursor is inside the function body so the user is most likely going to continue writing code at this position
- We know that the file is called`sort.js`
- The code before the cursor (which we refer to as prefix) has strong hints about what code we want to write
- The code after the cursor (postfix) is empty and consists only of a closing bracket.

We can easily convert this into a prompt for ChatGPT and have it generate the implementation for us: https://chat.openai.com/share/27aeb581-2d68-4ac8-94eb-3c64af91f0c6

Congratulations, you just wrote a code completion AI!

In fact, this is pretty much how we started out with Cody autocomplete back in March! All you need to make this into a full-blown VS Code extension, is to implement this API interface:

```
/**
 - Provides inline completion items for the given position and document.
 - If inline completions are enabled, this method will be called whenever the user stopped typing.
 - It will also be called when the user explicitly triggers inline completions or explicitly asks for the next or previous inline completion.
 - In that case, all available inline completions should be returned.
 - `context.triggerKind` can be used to distinguish between these scenarios.
 *
 - @param document The document inline completions are requ

*… (22,000 more characters — see results.json for full text)*

---

### 9. Configuring Models, Rules, and Tools | Continue Docs
**URL:** https://docs.continue.dev/guides/configuring-models-rules-tools

Configuring Models, Rules, and Tools | Continue Docs

ChecksCLIIDE Extensions

# Configuring Models, Rules, and Tools

Copy page

Learn how to work with Continue's configuration system. Understand how to use hub models, rules, and tools, create local configurations, and organize your setup for maximum reusability.

## What Are Models, Rules, and Tools?

Continue configs are built from three main types of configuration:

### Models

Language models that power different capabilities like chat, autocomplete, and agent mode

### Rules

Guidelines and instructions that shape how the AI behaves and responds

### Tools

MCP tools that provide additional capabilities like database access, web search, or custom functions

There are two places where you can define these configurations:

### Local

Custom configurations you create and manage in your workspace or globally

### Hub

Pre-built models, rules, and tools from the Continue community that you can import and use immediately

## Local

Local configurations let you create custom models, rules, and tools that automatically apply to multiple configs, reducing duplication and ensuring consistency across your setup.

### Global

Applied to all configs across all workspaces. Ideal for personal preferences, universal coding standards, or tools you use everywhere.

### Workspace

Applied automatically to all configs when working in a specific project.

Perfect for project-specific setups like TypeScript rules for web apps or the Playwright MCP tool.

## Hub

Continue hub uses a slug in the format of`owner/item-name` to resolve blocks.

For example, to use the Claude 4 Sonnet model, you'd reference it as`anthropic/claude-4-sonnet`.

Import from Mission Control using the`uses` syntax alongside your custom configurations:

```yaml
name: Team Config
version: 1.0.0
schema: v1

models:
  - uses: anthropic/claude-4-sonnet
    with:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }} # Use a hub secret

```

### Organization

Organize your local configurations using these directories:

### Models

`.continue/models`

### Rules

`.continue/rules`

### Tools

`.continue/mcpServers`

## Working with Secrets

Models, and many MCP servers, require a secret for things like API keys.

On Mission Control, you can configure secrets when adding a model or MCP server.

This will use mustache notation to pass the secret, eg`${{ secrets.SECRET_NAME }}`

When configuring a local model or MCP server, you can use the same mustache notation for secrets which are resolved from these sources in order:

### Workspace

`.env` file at your project root, or in` /.continue/.env`

### Global

`.env` file in`~/.continue/.env`

See Managing Local Secrets and Environment Variables for full details on secret resolution and IDE vs CLI differences.

When to use`secrets.` vs`inputs.`

For most use cases, use`${{ secrets.SECRET_NAME }}` directly in your configuration. This is the recommended approach for both personal and organizational workf

*… (2,122 more characters — see results.json for full text)*

---

### 10. Chat Role | Continue Docs
**URL:** https://docs.continue.dev/customize/model-roles/chat

Chat Role | Continue Docs

ChecksCLIIDE Extensions

# Chat Role

Copy page

Chat model role

A "chat model" is an LLM that is trained to respond in a conversational format. Because they should be able to answer general questions and generate complex code, the best chat models are typically large, often 405B+ parameters.

In Continue, these models are used for normal Chat. The selected chat model will also be used for Edit and Apply if no`edit` or`apply` models are specified, respectively.

## Recommended Chat models

| Model role | Best open models | Best closed models | Notes |
| --- | --- | --- | --- |
| Chat Edit | Closed and open models have similar performance |

## Best overall experience

For the best overall Chat experience, you will want to use a 400B+ parameter model or one of the frontier models.

### Claude Opus 4.6 and Claude Sonnet 4 from Anthropic

Our current top recommendations are Claude Opus 4.6 and Claude Sonnet 4 from Anthropic.

HubYAML

View the Claude Opus 4.6 model block or Claude Sonnet 4 model block on the hub.

### Gemma from Google DeepMind

If you prefer to use an open-weight model, then the Gemma family of Models from Google DeepMind is a good choice. You will need to decide if you use it through a SaaS model provider, e.g. Together, or self-host it, e.g. Ollama.

HubYAML

OllamaTogether

Add the Ollama Gemma 3 27B block from the hub

### GPT-5.1 from OpenAI

If you prefer to use a model from OpenAI, then we recommend GPT-5.1.

HubYAML

Add the OpenAI GPT-5.1 block from the hub

### Grok-4 from xAI

If you prefer to use a model from xAI, then we recommend Grok-4.

HubYAML

Add the xAI Grok-4.1 block from the hub

### Gemini 3.1 Pro from Google

If you prefer to use a model from Google, then we recommend Gemini 3.1 Pro.

HubYAML

Add the Gemini 3.1 Pro block from the hub

## Local, Offline Experience

For the best local, offline Chat experience, you will want to use a model that is large but fast enough on your machine.

### Llama 3.1 8B

If your local machine can run an 8B parameter model, then we recommend running Llama 3.1 8B on your machine (e.g. using Ollama or LM Studio).

HubYAML

Ollama

Add the Ollama Llama 3.1 8b block from the hub

### DeepSeek Coder 2 16B

If your local machine can run a 16B parameter model, then we recommend running DeepSeek Coder 2 16B (e.g. using Ollama or LM Studio).

YAML

OllamaLM StudioMsty

```yaml
name: My Config
version: 0.0.1
schema: v1

models:
  - name: DeepSeek Coder 2 16B
    provider: ollama
    model: deepseek-coder-v2:16b

```

## Other experiences

There are many more models and providers you can use with Chat beyond those mentioned above. Read more here

Intro to Roles Autocomplete Role

---

### 11. Models | Continue Docs
**URL:** https://docs.continue.dev/customize/models

Models | Continue Docs

ChecksCLIIDE Extensions

# Models

Copy page

Models form the foundation of the entire agent experience, offering different specialized capabilities:

- Chat: Power conversational interactions about code and provide detailed guidance
- Edit: Handle complex code transformations and refactoring tasks
- Apply: Execute targeted code modifications with high accuracy
- Autocomplete: Provide real-time suggestions as developers type
- Embedding: Transform code into vector representations for semantic search
- Reranker: Improve search relevance by ordering results based on semantic meaning

When creating an agent, you can choose the model for a new task in Mission Control or workflow.

If no model is specified, Continue automatically uses the default agent with our recommended model.

## Recommended Models

### Best Models by Role

zerank-1

zerank-1-small

| Model role | Best open models | Best closed models | Notes |
| --- | --- | --- | --- |
| Agent Plan | Closed models are slightly better than open models |
| Chat Edit | Closed and open models have similar performance |
| Autocomplete | Closed models are slightly better than open models |
| Apply | Closed models are better than open models |
| Embed | Closed models are slightly better than open models |
| Rerank | Open models are beginning to emerge for this model role |

Explore models in The Hub.

## Learn More About Models

Continue supports many model providers, including Anthropic, OpenAI, Gemini, Ollama, Amazon Bedrock, Azure, xAI, and more. Models can have various roles like`chat`,`edit`,`apply`,`autocomplete`,`embed`, and`rerank`.

Read more about model roles, model capabilities and view models in the YAML Reference.

### Example Model Setup Instructions

# Frontier Models

Claude Sonnet 4.6 from Anthropic

1. Get your API key from Anthropic
2. Add Claude Sonnet 4.6 to a config on Continue Mission Control
3. Add`ANTHROPIC_API_KEY` as a User Secret on Continue Mission Control here
4. Click`Reload config` in the config selector in the Continue IDE extension

Qwen Coder 3 480B from Qwen

1. Get your API key from OpenRouter
2. Add Qwen Coder 3 480B a config on Continue Mission Control
3. Add`OPENROUTER_API_KEY` as a User Secret on Continue Mission Control here
4. Click`Reload config` in the config selector in the Continue IDE extension

1. Get your API key from OpenAI
2. Add GPT-5 a config on Continue Mission Control
3. Add`OPENAI_API_KEY` as a User Secret on Continue Mission Control here
4. Click`Reload config` in the config selector in the Continue IDE extension

Kimi K2 from Moonshot AI

1. Get your API key from OpenRouter
2. Add Kimi K2 a config on Continue Mission Control
3. Add`OPENROUTER_API_KEY` as a User Secret on Continue Mission Control here
4. Click`Reload config` in the config selector in the Continue IDE extension

Gemini 3.1 Pro from Google

1. Get your API key from Google AI Studio
2. Add Gemini 3.1 Pro a config on Continue Mission Control
3. Add`GEMINI_API_

*… (2,310 more characters — see results.json for full text)*

---

### 12. aidrivencoder/Roo-Cline
**URL:** https://github.com/aidrivencoder/Roo-Cline
**Published:** 2024-12-18T23:07:27.000Z

# Repository: aidrivencoder/Roo-Cline

Autonomous coding agent right in your IDE, capable of creating/editing files, executing commands, using the browser, and more with your permission every step of the way.

- Stars: 46
- Forks: 15
- Watchers: 46
- Open issues: 0
- Primary language: TypeScript
- Languages: TypeScript (98.3%), CSS (1.0%), JavaScript (0.6%), Nix, HTML, MDX
- License: Apache License 2.0 (Apache-2.0)
- Default branch: main
- Homepage: https://marketplace.visualstudio.com/items?itemName=RooVeterinaryInc.roo-cline
- Created: 2024-12-18T23:07:27Z
- Last push: 2025-02-11T00:02:50Z
- Contributors: 50 (top: saoudrizwan, mrubens, samhvw8, github-actions[bot], cte, daniel-lxs, a8trejo, ColemanRoo, stea9499, pugazhendhi-m)

---

 
 Join the Roo Code Community 
 Connect with developers, contribute ideas, and stay ahead with the latest AI-powered coding tools. 

 
 

 
 
 

 
 Roo Code (prev. Roo Cline) 

 
 
 
 

**Roo Code** is an AI-powered **autonomous coding agent** that lives in your editor. It can:

- Communicate in natural language
- Read and write files directly in your workspace
- Run terminal commands
- Automate browser actions
- Integrate with any OpenAI-compatible or custom API/model
- Adapt its “personality” and capabilities through **Custom Modes**

Whether you’re seeking a flexible coding partner, a system architect, or specialized roles like a QA engineer or product manager, Roo Code can help you build software more efficiently.

Check out the [CHANGELOG](CHANGELOG.md) for detailed updates and fixes.

---

## New in 3.3: Code Actions, More Powerful Modes, and a new Discord! 🚀

This release brings significant improvements to how you interact with Roo Code:

### Code Actions

Roo Code now integrates directly with VS Code's native code actions system, providing quick fixes and refactoring options right in your editor. Look for the lightbulb 💡 to access Roo Code's capabilities without switching context.

### Enhanced Mode Capabilities

- **Markdown Editing**: Addressing one of the most requested features, Ask and Architect modes can now create and edit markdown files!
- **Custom File Restrictions**: In general, custom modes can now be restricted to specific file patterns (for example, a technical writer who can only edit markdown files 👋). There's no UI for this yet, but who needs that when you can just ask Roo to set it up for you?
- **Self-Initiated Mode Switching**: Modes can intelligently request to switch between each other based on the task at hand. For instance, Code mode might request to switch to Test Engineer mode once it's ready to write tests.

### Join Our Discord!

We've launched a new Discord community! Join us at [https://roocode.com/discord](https://roocode.com/discord) to:

- Share your custom modes
- Get help and support
- Connect with other Roo Code users
- Stay updated on the latest features

## New in 3.2: Introducing Custom Modes, plus rebranding from Roo Cline → Roo Code! 🚀

### Introducing Roo Code

Our b

*… (11,377 more characters — see results.json for full text)*

---

### 13. Windsurf - Cascade
**URL:** https://docs.codeium.com/plugins/cascade/cascade-overview

> ## Documentation Index
> 
> Fetch the complete documentation index at: https://docs.windsurf.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Cascade Overview

> Cascade brings agentic AI coding to JetBrains with Write/Chat modes, voice input, tool access, turbo mode, and real-time collaboration.

Windsurf's Cascade brings the best of agentic coding to the JetBrains suite.

To open Cascade, press `Cmd/Ctrl+L` or click the Cascade icon.

# Model selection

Select your desired model from the selection menu below the Cascade conversation input box. Click below too see the full breakdown of the available models and their availability across different plans and pricing.

## Models

Model availability in Windsurf.

# Write/Chat Modes

Cascade comes in two modes: Write and Chat.

Write mode allows Cascade to create and make modifications to your codebase, while Chat mode is optimized for questions around your codebase or general coding principles.

# Queued Messages

While you are waiting for Cascade to finish its current task, you can queue up new messages to execute in order once the task is complete.

To add a message to the queue, simply type in your message while Cascade is working and press `Enter`.

- Send immediately: Press Enter again on an empty text box to send it right away.
- Delete: Remove any message from the queue before it's sent

# Access to Tools

Cascade has a variety of tools at its disposal, such as Search, Analyze, Web Search, and the terminal.

It can detect which packages and tools that you're using, which ones need to be installed, and even install them for you. Just ask Cascade how to run your project and press Accept.

Cascade can make up to 25 tool calls per prompt. If the trajectory stops, simply type in `continue` and Cascade will resume from where it left off. Each `continue` will count as a new prompt.

# Voice input

Use Voice input to use your voice to interact with Cascade. In its current form it can transcribe your speech to text.

# Revert to previous steps

You have the ability to revert changes that Cascade has made if you want to. Simply hover your mouse over the original prompt and click on the revert arrow on the right, or revert directly from the table of contents. This will revert all code changes back to the state of your codebase at the desired step.

Reverts are currently irreversible, so be careful!

# Auto-Execution Modes

Cascade supports three levels of command auto-execution in JetBrains: Off, Auto, and Turbo. You can select your preferred level via the Windsurf Settings panel.

| Level | Description |
| --- | --- |
| Off | Never auto-execute terminal commands, except those in your allow list. |
| Auto | Model decides whether to auto-execute commands based on safety assessment. Available with premium models only. |
| Turbo | Always auto-execute terminal commands and browser controls, except those in your deny list. |

For Teams and Enterprise users, administr

*… (1,207 more characters — see results.json for full text)*

---

### 14. JetBrains Changelogs | Windsurf
**URL:** https://codeium.com/changelog/jetbrains

JetBrains Changelogs | Windsurf

# JetBrains Changelog

View Docs Follow us on

2.12.21

April 9, 2026

# Adaptive Fix

We fixed a bug with the adaptive model router which prevented switching models after the first request.

All users who encountered the bug have had quota reset and overage restored.

## Feedback

- Enjoying Cascade? Please take a moment to rate our plugin on the JetBrains Marketplace.
- Join our #cascade-on-jetbrains channel on Discord.
- Report issues at windsurf.com/support.

2.12.20

April 6, 2026

# Introducing Adaptive

We've made several model packaging changes, with more info here.

## Adaptive Model Router

A new Adaptive model option is now available in the model picker. Adaptive intelligently selects the best model for each task, helping you make your quota last longer by avoiding overuse of premium models.

- Availability: Now available to all self-serve users on Pro, Max, and Teams plans.
- Dynamic model selection - Automatically chooses the right underlying model for your task while drawing down quota at a fixed per-token rate.
- Extra usage promo - Beyond your quota, extra usage is offered at 0.50 USD per 1M input tokens, 2.00 USD per 1M output tokens, and 0.10 USD per 1M cache read tokens for the next 2 weeks.

## Updated Model Picker with Pricing Context

The model picker now shows token pricing information directly, so you can see the exact rate extra usage is billed at.

- Token pricing display - Per-model input, output, and cache read token rates visible in the picker.
- Prompt cache timer - A new prompt cache timer is integrated into the context window indicator to help you track caching status.
- Token counts in response cards - Response cards after messages now include token counts so you can understand exactly how each message cost was calculated.

# Bug Fixes & Improvements

## Improvements

- Now compatible with IntelliJ Platform 2026.1

## Bug Fixes

- Fixed a crash caused by the Cascade bar

## Feedback

- Enjoying Cascade? Please take a moment to rate our plugin on the JetBrains Marketplace.
- Join our #cascade-on-jetbrains channel on Discord.
- Report issues at windsurf.com/support.

2.12.19

March 27, 2026

# Bug Fixes & Improvements

## Improvements

- Improved tab completion responsiveness

## Feedback

- Enjoying Cascade? Please take a moment to rate our plugin on the JetBrains Marketplace.
- Join our #cascade-on-jetbrains channel on Discord.
- Report issues at windsurf.com/support.

2.12.15

March 12, 2026

# Bug Fixes & Improvements

## Bug Fixes

- Fix crash on Apple M5

## Improvements

- Improved system stability and compatibility

## Feedback

- Enjoying Cascade? Please take a moment to rate our plugin on the JetBrains Marketplace.
- Join our #cascade-on-jetbrains channel on Discord.
- Report issues at windsurf.com/support.

2.12.14

March 11, 2026

# Product Improvements & New Models

## GPT-5.4

GPT-5.4 is now available in Windsurf with limited-time promotional pricing for self serve user

*… (22,000 more characters — see results.json for full text)*

---

### 15. Adaptive - Windsurf Docs
**URL:** https://docs.windsurf.com/windsurf/adaptive

> ## Documentation Index
> 
> Fetch the complete documentation index at: https://docs.windsurf.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Adaptive

> Adaptive is Cognition's intelligent model router that automatically selects the best AI model for each task.

Adaptive is an intelligent model router that automatically selects the best AI model for each task. Instead of manually choosing between dozens of models, Adaptive analyzes your prompt and routes it to the model that will deliver the best result.

## How it works

When you select Adaptive in the model picker, Windsurf evaluates each request and dynamically chooses the right underlying model. Simple tasks get routed to fast, efficient models. Complex tasks get routed to more capable ones.

This means you get the right level of intelligence for every prompt without overspending on premium models for routine work. Adaptive helps your usage allowance last longer by avoiding unnecessary use of expensive models.

### Selecting Adaptive

To use Adaptive, open the model picker below the Cascade input box and select Adaptive at the top of the list. Once selected, Adaptive will be used for all subsequent messages in the conversation.

You can switch away from Adaptive to a specific model at any time.

Adaptive is the best default for most users.

## Pricing

Adaptive pricing depends on your billing plan.

## Self-serve

Adaptive draws down your quota at a fixed per-token rate, regardless of which underlying model is selected for a given request.

Currently, the Adaptive model consumes quota and overage at an introductory promotional rate (through April 27, 2026).

| Token type | Cost per 1M tokens |
| --- | --- |
| Input tokens | $0.50 |
| Output tokens | $2.00 |
| Cache read tokens | $0.10 |

These rates also apply to extra usage beyond your included quota.

Because Adaptive routes simpler tasks to lighter models, it typically consumes fewer tokens overall than manually selecting a frontier model for every request. This makes it the most cost-effective option for most users.

## Enterprise (Cognition Platform - ACUs)

For customers on the Cognition platform, Adaptive usage is metered in ACUs (Agent Compute Units). ACU consumption scales with the tokens used and the model selected by the router for each request.

## Enterprise (Legacy Credits)

For Windsurf enterprise customers on credit-based billing, Adaptive uses variable-token credit pricing. Each request consumes credits based on the actual tokens used and the model that Adaptive selects for that request according to your credit rate.

This means cheaper models cost fewer credits per request, and Adaptive's routing naturally favors cost-efficient choices — so your credit pool lasts longer compared to always selecting a premium model.

## Tips for getting the most out of Adaptive

- Be specific with your prompts. Clear, focused instructions help Adaptive route to the right model and reduce unnecessary

*… (455 more characters — see results.json for full text)*

---
