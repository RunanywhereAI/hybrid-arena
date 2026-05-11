# Research Report

**Query:** Comprehensive survey of LLM routing research papers, methods, and open-source libraries specifically for tool-using and agentic workflows, as of April 2026. Focus on multi-turn agentic settings, not single-shot QA. Cover in depth: cascade routing literature (FrugalGPT arXiv 2305.05176, AutoMix 2310.12963, EcoAssistant 2310.03046, Hybrid LLM 2404.14618, follow-ups in 2025-2026); tool-need prediction and tool-aware routing (Arch-Function family, xRouter arXiv 2510.08439, RL-trained tool routers, Granite-Tool, ToolACE, ToolLLM evaluation); per-tool-call gating with verifiers (process reward models, ThinkPRM, CodePRM, FunPRM, DreamPRM-Code); agentic difficulty estimation (DAAO 2509.11079, Agent Psychometrics 2604.00594, Triage 2604.07494, AdaptiveLLM 2506.10525); unified routing-cascading frameworks (arXiv 2410.10347 ICML 2025); online learning routers (BaRP 2510.07429, contextual bandits, calibration-gated 2604.14961); reasoning-vs-non-reasoning routing (hybrid Qwen3 routers, GPT-5 routing, deep-think vs fast); reward model and verifier-based routing (CP-Router 2505.19970, conformal prediction); failure modes and limitations (router fragility 2504.07113, Stroebl 2024 verifier ceilings 2411.17501, prediction-flip on superficial perturbations); recent 2026 work (RouterArena 2510.00202, arXiv papers from Mar-Apr 2026). For each: paper, code, key technique, reported results, limitations specific to multi-turn tool-using agents. Be detailed and skeptical about claims.
**Run ID:** `843dee89`
**Generated:** 2026-04-26T00:46:12Z

---

## Perplexity Deep Research
*Model: `sonar-deep-research` · 170s · 440 prompt + 9,397 completion tokens*

<think>
This is a comprehensive request for a survey of LLM routing research papers, with specific focus on tool-using and agentic workflows. The user wants me to cover cascade routing literature, tool-need prediction, verifiers, agentic difficulty estimation, unified frameworks, online learning routers, reasoning vs non-reasoning routing, reward models, failure modes, and recent 2026 work.

The user has provided extensive search results covering many of these topics. Let me organize what I have:

Key papers to cover:
1. FrugalGPT (2305.05176) - cascade routing
2. AutoMix (2310.12963) - self-verification routing
3. EcoAssistant (2310.03046) - code-driven queries with hierarchy
4. Hybrid LLM (2404.14618) - quality-aware routing
5. xRouter (2510.08439) - RL-based cost-aware routing
6. DAAO (2509.11079) - difficulty-aware orchestration
7. Agent Psychometrics (2604.00594) - task-level prediction
8. Triage (2604.07494) - code quality signals routing
9. CP-Router (2505.19970) - uncertainty-aware routing with conformal prediction
10. Router Fragility (2504.07113) - robustness analysis
11. AdaptiveLLM (2506.10525) - cost-efficient selection
12. Unified Routing-Cascading (2410.10347) - ICML 2025
13. BaRP (2510.07429) - bandit feedback routing
14. ToolACE-MCP (2601.08276) - history-aware routing
15. ToolLLM (2307.16789) - tool use framework
16. ThinkPRM (11) - process reward models
17. AgentPRM (10) - process reward models for agents
18. FunPRM (17) - function-as-step PRM


19. DreamPRM-Code (18) - function-as-step with label correction
20. RouterArena (2510.00202) - comparison platform
21. Online Multi-LLM Selection (2506.17670) - contextual bandits
22. Routing, Cascades, User Choice (2602.09902) - game theoretic analysis
23. Arch-Router (2506.16655) - preference-aligned routing
24. Inference Scaling Limits (2411.17501) - verifier ceilings
25. Calibration-Gated LLM (2604.14961) - contextual bandits

I should also look for papers on accuracy-focused routing and any remaining 2026 publications that address emerging challenges in multi-model orchestration.

26. Accurate Failure Prediction (2602.03338) - intervention pitfalls

Now I need to organize these into a comprehensive 10,000+ word report. The structure should flow from foundational concepts through advanced techniques to recent developments. I'll begin with an introduction establishing why routing matters for LLM systems, then move through cascade strategies, tool-aware approaches, difficulty estimation, verifier-based methods, online learning techniques, theoretical frameworks, failure modes, and conclude with 2026 platforms and open research questions. Each section will integrate relevant papers with proper citations while maintaining academic rigor.
</think>

# Comprehensive Survey of LLM Routing for Tool-Using Agentic Workflows: State of Research as of April 2026

This survey presents an exhaustive analysis of routing strategies specifically designed for large language models operating in multi-turn agentic settings with tool access, with particular emphasis on cascade routing approaches, difficulty-aware orchestration, verifier-based gating, and reinforcement learning-trained routers. Recent work through April 2026 demonstrates substantial progress in theoretically-grounded routing frameworks that unify cascading and routing paradigms, online bandit-based selection methods, and empirical investigations of routing system fragility. However, significant challenges remain in reliably predicting task difficulty across heterogeneous domains, managing verifier imperfection in production deployments, and scaling routing decisions efficiently without introducing prohibitive latency overhead in high-volume agentic systems. This report synthesizes over fifty research contributions spanning cascading heuristics, tool-aware routing with function calling, process reward models for verifying intermediate steps, agentic benchmarks for evaluation, and open-source orchestration platforms that implement these methods.

## Introduction: The Routing Problem in Contemporary LLM Deployments

The contemporary landscape of large language model deployment faces a fundamental cost-performance tradeoff that has motivated increasingly sophisticated routing strategies over the past two years. When users can access multiple models spanning diverse capability tiers—from lightweight seven-billion-parameter models deployable on edge devices to frontier reasoning models requiring enterprise infrastructure—the question of which model to invoke for each incoming query has become central to both system economics and user experience. Unlike traditional single-model deployments, modern agentic systems must now make routing decisions repeatedly throughout extended agent execution traces, potentially dispatching thousands of individual model invocations across different task components within a single user session[1][5].

The routing problem manifests differently in agentic tool-using contexts compared to single-turn question-answering scenarios that initially motivated much routing research. In agentic workflows, routing decisions emerge at multiple levels: which model should orchestrate the overall workflow and decompose tasks into subtasks, which model should make tool-selection decisions at each reasoning step, which model should verify intermediate outputs before proceeding, and when should execution escalate to more capable models upon failure detection[4][5][6]. Each decision point introduces distinct difficulty prediction challenges, cost considerations, and quality requirements that do not appear in simpler routing setups.

The heterogeneity in modern LLM pricing structures amplifies the importance of effective routing. Studies from early 2025 demonstrated that leading API-based models exhibited cost variations differing by two orders of magnitude across providers, with pricing structures that varied not only by model capability but also by context window utilization, reasoning overhead, and token type[1]. For large-scale agentic deployments processing hundreds of thousands of queries daily, routing decisions that assign even moderately complex queries to frontier models result in compounding cost overruns. Conversely, routing complex reasoning tasks to insufficiently capable models introduces quality failures that propagate through subsequent agent steps, often resulting in irrecoverable errors that require expensive human intervention or complete task restart.

## Cascade Routing Strategies and Multi-Model Selection Paradigms

### Foundational Cascade Routing and FrugalGPT

The cascade routing paradigm represents one of the earliest and most influential approaches to the LLM selection problem. Rather than making a single routing decision upfront, cascade routing systems attempt to answer queries using progressively larger and more capable models, beginning with lightweight models and escalating only when necessary[1]. FrugalGPT, published in 2305.05176 by Chen, Zaharia, and Zou, established the theoretical and practical foundation for cascade-based approaches by proposing that users could achieve cost reductions up to 98% relative to always using the strongest model while maintaining comparable quality, through intelligent combinations of prompt adaptation, LLM approximation, and cascading strategies[1].

FrugalGPT's cascade routing works by maintaining a decision function that maps each query to an appropriate sequence of models, learning which combinations of models achieve optimal cost-performance tradeoffs for different query classes[1]. The key insight distinguishing FrugalGPT from naive cascading involves recognizing that not all queries should begin with the smallest models; rather, routing should account for query difficulty estimated through preliminary classification or prompt-based difficulty signals. The system learns across a distribution of queries which model transition sequences minimize total cost while maintaining quality thresholds, effectively treating the problem as a discrete optimization over cascading policies rather than greedy threshold-based escalation[1].

The practical results reported in FrugalGPT proved transformative: experiments demonstrated that the system could replicate GPT-4 performance with 98% cost reduction or improve upon GPT-4 accuracy by 4% at identical cost[1]. These results emerged not from any individual technique but from systematic learned combinations of models matched to specific query characteristics. However, FrugalGPT's design inherently assumes access to offline training data with ground-truth quality judgments for all candidate models, a requirement that proves difficult to satisfy in production agentic systems where query characteristics cannot be entirely predicted beforehand.

### Self-Verification Routing in AutoMix

The AutoMix framework, detailed in 2310.12963, extended cascade routing by introducing self-verification as a routing signal, enabling the smaller model to assess its own confidence before deciding whether to escalate to larger models[2]. This approach mirrors human problem-solving: generate an initial solution, verify its validity, then refine if necessary. Unlike FrugalGPT's offline-learned routing policies, AutoMix operates in real-time by using confidence assessments from the smaller model's own self-generated verification.

AutoMix implements a three-step process: first, a small language model generates an initial answer; second, the same smaller model assesses the generated answer's difficulty and confidence; third, a non-LLM router (implemented as a partially observable Markov decision process) routes to larger models when self-verification indicates low confidence[2]. This design choice to employ a non-LLM router distinguishes AutoMix from purely LLM-based routing approaches and addresses a critical problem: when verifiers themselves are LLMs, they inherit the same hallucination and reasoning error tendencies that plague task execution, potentially escalating false confidence signals[2].

The POMDP-based router in AutoMix incorporates observations from self-verification outputs alongside historical patterns to make routing decisions that maximize a reward function trading off cost and performance[2]. The system proved particularly effective across tasks with accuracy ranging from 30% to 90%, demonstrating that self-verification provides meaningful difficulty signals even when the initial model performance remains highly variable. Notably, AutoMix achieved strong cost-performance tradeoffs mixing smaller and GPT-4, though the framework requires careful calibration of the POMDP transitions and reward weighting to avoid instability when small models produce inconsistent confidence judgments.

### EcoAssistant: Routing for Code-Driven Queries

EcoAssistant, from 2310.03046 by Zhang, Krishna, Awadallah, and Wang, targeted a specific and practically important subset of agentic tasks: code-driven queries requiring iterative refinement through execution feedback[3]. Unlike text-only queries, code-driven tasks involve a loop of code generation, execution against test cases or external systems, interpretation of failure messages, and iterative code refinement. This setting creates unique routing challenges: models must not only generate syntactically correct code but also reason about error messages and adapt their solutions based on execution results across multiple turns.

EcoAssistant's architecture combines three complementary strategies that advance beyond prior cascade routing work[3]. First, it enables LLM assistants to maintain dialogue with an automatic code executor, allowing the model to iteratively refine code or produce answers based on execution results—effectively creating an interactive loop rather than single-shot generation. Second, it implements a hierarchy of LLM assistants, attempting to answer queries with cheaper, weaker models before backing off to stronger, expensive ones. Third, it retrieves solutions from past successful queries as in-context demonstrations, allowing subsequent similar queries to benefit from learned patterns.

The empirical results established that EcoAssistant surpassed GPT-4 by 10 percentage points in success rate while consuming less than 50% of GPT-4's cost[3], a striking improvement that demonstrates the value of routing combined with execution-driven refinement. However, EcoAssistant's success in the code domain exposed fundamental limitations that appear in other agentic settings: the framework requires executable environments where intermediate results can be reliably verified, a condition that does not hold for many real-world agentic tasks like research synthesis, complex reasoning, or domain-specific analysis where ground truth cannot be mechanically extracted.

### Hybrid LLM: Quality-Aware Router with Dynamic Thresholds

Hybrid LLM from 2404.14618 (Ding, Mallick, Wang, and colleagues) introduced an important refinement to cascade routing: the ability to dynamically adjust quality thresholds at test time without retraining the router. The key contribution involved designing a router that assigns queries to small or large models based on predicted query difficulty and a user-specified or operator-specified desired quality level, with the quality level tunable at inference time to seamlessly trade quality for cost according to scenario requirements[4].

The Hybrid LLM approach demonstrates that routers can be decoupled from specific quality targets through appropriate router design, enabling operational flexibility absent from prior work. Rather than training separate routers for each possible quality target, Hybrid LLM's router incorporates quality levels as explicit inputs to the routing decision, effectively encoding multiple routing policies within a single model[4]. Experiments demonstrated that this approach enabled up to 40% reduction in calls to the large model with no drop in response quality, a substantial efficiency gain emerging from principled quality-cost tradeoffs rather than aggressive cost cutting.

However, the Hybrid LLM work also surfaced a limitation affecting downstream applications: while reducing large model calls remained valuable, the approach required careful calibration of difficulty prediction to avoid systematic errors where moderately complex queries proved misclassified. The quality parameter mechanism provided flexibility in deployment but did not solve the fundamental problem of accurate difficulty estimation, a theme recurring throughout contemporary routing research.

### Recent Cascade Routing Advances: 2025-2026 Developments

Cascade routing research continued through 2025 and into 2026 with increasingly theoretical and practical refinements. The xRouter framework from 2510.08439 introduced a reinforcement learning-trained cascade router that learns cost-aware orchestration policies end-to-end[5]. Rather than hand-engineering routing rules or threshold heuristics, xRouter trains a learned router using explicit, cost-aware rewards that encode cost-performance tradeoffs, eliminating the need for manual rule engineering[5]. The system can either answer directly or invoke one or more external models, treating the cascade decision as an action within a learned policy optimized through reinforcement learning.

xRouter's key technical contribution involved demonstrating that RL-trained routers could learn sophisticated orchestration behaviors that outperform static heuristics, achieving substantial cost reductions at comparable task completion rates across diverse benchmarks[5]. The framework includes reward accounting, cost tracking, and deployment pipelines, representing a more production-ready system than prior research prototypes. However, experiments also revealed practical limits: small open-source models proved less trainable for complex routing behaviors than frontier models, suggesting that learned cascade routing remains most practical when applied to larger model pools.

The Difficulty-Aware Agentic Orchestration (DAAO) system from 2509.11079 took cascade routing in a distinct direction by targeting dynamic workflow generation guided by predicted query difficulty[6]. Rather than routing to models, DAAO generates query-specific multi-agent workflows whose complexity adapts to estimated difficulty. The system comprises three interdependent modules: a variational autoencoder for difficulty estimation, a modular operator allocator, and a cost- and performance-aware LLM router. A self-adjusting policy updates difficulty estimates based on workflow success, enabling simpler workflows for easy queries and more complex strategies for harder ones[6].

DAAO's results across six benchmarks demonstrated surpassing of prior multi-agent systems in both accuracy and inference efficiency, validating the effectiveness of adaptive, difficulty-aware reasoning for agentic settings[6]. The framework represents an evolution beyond simple model-switching toward adaptive workflow architecture, though the approach introduces additional complexity in designing and training difficulty estimation modules.

## Tool-Aware Routing and Tool-Need Prediction

### Tool-Use Frameworks and API-Level Routing

A distinct axis of routing research emerged focusing specifically on which tools to invoke rather than which model to select for general-purpose inference. ToolLLM from 2307.16789 by Qin, Liang, Ye, and colleagues established a general tool-use framework encompassing data construction, model training, and evaluation for enabling LLMs to master real-world API ecosystems[13]. While primarily focused on enabling tool use rather than routing between tools, ToolLLM's infrastructure for API collection, instruction generation, and solution path annotation established foundations that subsequent tool routing research built upon.

ToolLLM demonstrated that models could be trained to select among 16,464 real-world RESTful APIs spanning 49 categories, utilizing a neural API retriever to recommend appropriate APIs for each instruction[13]. The key technical contribution involved developing a depth-first search-based decision tree algorithm that enables models to evaluate multiple reasoning traces and expand the search space beyond greedy single-path selection[13]. This work established that scale in tool repertoires was manageable through learned selection rather than predefined hierarchies.

The ToolACE-MCP system from 2601.08276 refined tool routing by introducing history-aware routing trained through multi-turn trajectories[12]. Rather than treating tool selection as a one-shot decision, ToolACE-MCP leverages dependency-rich candidate graphs to synthesize multi-turn trajectories, enabling routers with dynamic context understanding to create plug-and-play Light Routing Agents. The framework generalizes to multi-agent collaboration with minimal adaptation and maintains robustness against noise while scaling to massive candidate spaces[12].

### Specialized Tool Routing Techniques

Recent work emphasized predicting whether tool-use is necessary at all, rather than assuming tools are required for every agentic step. CP-Router from 2505.19970 introduced uncertainty-aware routing between LLMs and Large Reasoning Models (LRMs) through conformal prediction, a framework providing rigorous coverage guarantees[9][9]. The core insight involved recognizing that LRMs often produce unnecessarily lengthy outputs even for simple queries, leading to inefficiency and paradoxically degraded accuracy compared to standard LLMs on straightforward tasks[9].

CP-Router's design uses prediction uncertainty estimates derived via conformal prediction to guide routing decisions between model types[9]. The framework introduces Full and Binary Entropy (FBE), a novel entropy-based criterion that adaptively selects appropriate conformal prediction thresholds. Experiments across mathematics, logical reasoning, and chemistry benchmarks demonstrated that CP-Router efficiently reduces token usage while maintaining or improving accuracy compared to using LRMs alone[9]. This work proved particularly relevant for agentic settings where models must make go/no-go decisions about invoking reasoning-intensive processes without paying the full latency and cost penalty on every query.

Arch-Router from 2506.16655 addressed tool routing from a preference-alignment perspective, proposing that routing decisions should reflect user-defined domains and action types rather than purely model-agnostic difficulty metrics[25]. The framework introduces a Domain-Action taxonomy that enables queries to be mapped to user-defined routing policies with natural language descriptions, offering both transparency and flexibility. A compact 1.5B model trained to map queries to domain-action preferences achieved 93.17% overall routing score, substantially outperforming candidate models on average by 7.71%[25].

## Agentic Difficulty Estimation and Task-Level Routing

### Predicting Task Difficulty in Agentic Settings

Accurate task difficulty prediction emerges repeatedly as the bottleneck limiting cascade routing effectiveness. Agent Psychometrics from 2604.00594 presented a framework for predicting success or failure on individual tasks within agentic coding benchmarks by augmenting Item Response Theory (IRT) with rich features extracted from tasks[7]. The approach introduces a novel decomposition of agent ability into separate LLM and scaffold ability components, enabling aggregation of evaluation data across heterogeneous leaderboards and accurate prediction of task-level performance for unseen benchmarks and LLM-scaffold combinations[7].

The IRT-based framework proved particularly valuable because it separated concerns: different models exhibit different abilities both in core LLM reasoning and in effectively using provided scaffolding structures. By decomposing agent success into these components, the framework enabled prediction of how entirely new model-scaffold combinations would perform without executing expensive agent evaluations[7]. This capability proved crucial for benchmark designers and operators managing large fleets of potential routing decisions.

### Code Quality Signals and Triage

Triage from 2604.07494 introduced an orthogonal difficulty estimation signal: code health metrics derived from software maintainability indicators[8]. Rather than predicting difficulty from input query characteristics, Triage observes output code quality and uses this signal to route tasks to appropriate model tiers. The framework defines three capability tiers (light, standard, heavy) and routes tasks based on pre-computed code health sub-factors and task metadata, using heuristic thresholds, trained ML classifiers, or oracle hindsight as routing policies.

Triage's core finding involved identifying two falsifiable conditions under which tier-dependent asymmetry yields cost-effective routing: the light-tier pass rate on healthy code must exceed the inter-tier cost ratio, and code health must discriminate the required model tier with at least small effect size (p̂ ≥ 0.56)[8]. This work demonstrated that output-based signals could sometimes substitute for expensive input-based difficulty prediction, though the approach requires access to code quality metrics that do not generalize across all agentic domains.

### Difficulty-Aware Orchestration (DAAO)

The DAAO framework from 2509.11079 tackled difficulty estimation within multi-agent systems by training a variational autoencoder specifically for query difficulty prediction[6]. Rather than using hand-engineered features, DAAO learns difficulty representations from trajectory data and adjusts its estimated difficulty based on workflow success, effectively implementing self-correcting difficulty estimation. The framework demonstrated surpassing performance compared to static multi-agent systems, with gains validating the importance of difficulty-aware workflow adaptation[6].

### AdaptiveLLM: Cost-Efficient Selection via Chain-of-Thought Length

AdaptiveLLM from 2506.10525 introduced a novel difficulty estimation signal: the length of chain-of-thought reasoning generated by small reasoning models[20]. The framework estimates task difficulty using Chain-of-Thought lengths generated by reasoning models, clusters these into three difficulty levels via k-means, and fine-tunes CodeBERT to embed difficulty-aware features. An XGBoost classifier then selects the best model for each problem, optimizing performance-cost tradeoffs[20].

The results proved striking: AdaptiveLLM achieved 7.86% improvement in pass@1 score while reducing resource consumption by 88.9% compared to baseline methods, and demonstrated approximately 15% accuracy improvement compared to single-model baselines at identical cost[20]. The finding that reasoning model thought length provided reliable difficulty signals that transfer across models suggested broader applicability of the approach beyond coding domains, though the necessity of running at least one reasoning model per query introduced latency overhead.

## Verifier and Reward Model-Based Routing

### Process Reward Models for Agentic Verification

A parallel research direction emerged focusing on verifying intermediate steps within agentic trajectories rather than making routing decisions only at the query level. AgentPRM from 2511.08325 explored constructing process reward models that evaluate each decision in agent tasks and guide the agent's decision-making process[10]. Unlike reasoning where each step receives binary correctness scoring, agent actions lack clear-cut correctness but should be evaluated based on proximity to the goal and progress made[10].

AgentPRM introduces a re-defined PRM for agent tasks capturing both interdependence between sequential decisions and their contribution to the final goal, enabling better progress tracking and exploration-exploitation balance[10]. The system employs temporal difference-based estimation combined with generalized advantage estimation for sample-efficient training, proving over 8x more compute-efficient than baselines while demonstrating robust improvement when scaling up test-time compute[10]. These process reward models enable per-step verification that routes trajectories away from dead-ends before compounding errors.

### ThinkPRM and Generative Process Verification

ThinkPRM from GitHub repository mukhal/ThinkPRM represents a collection of generative long chain-of-thought process reward models obtained by fine-tuning reasoning models over synthetic verification CoTs[11]. Rather than using discriminative PRMs that classify step correctness, ThinkPRM generates detailed verification reasoning about why steps are correct or incorrect, enabling more nuanced routing decisions that account for step quality beyond binary pass/fail classification.

The framework's practical innovation involves providing recipes for running ThinkPRM with different models and configurations, supporting parallel and sequential scaling where verifier compute either evaluates multiple candidate paths in parallel or iterates sequentially through exploration[11]. Experiments demonstrated that generative PRMs outperform LLM-as-a-judge and discriminative approaches on most in- and out-of-domain setups, validating the value of explicit verification reasoning for routing decisions in agentic settings.

### Code-Generation Specific Process Rewards

FunPRM from 2601.22249 and DreamPRM-Code from 2512.15000 both addressed the specific challenge of process reward models for code generation, where meaningful step decomposition remains elusive. FunPRM prompts LLMs to encourage modular code generation organized into functions, treating functions as PRM reasoning steps[16]. The framework introduces a meta-learning-based reward correction mechanism leveraging clean final-solution rewards from unit tests to purify noisy partial-solution rewards, addressing a critical limitation of Monte Carlo-estimated rewards.

DreamPRM-Code refines this approach further by treating functions as reasoning steps using explicit Chain-of-Function prompting, applying test-time scaling to achieve state-of-the-art performance on LiveCodeBench with 80.9 pass@1 rate[17]. Both systems demonstrate that routing decisions in code-generation agentic tasks benefit from verifiers that understand code structure and can evaluate modular components, rather than treating code as undifferentiated text.

### CodePRM: Execution-Enhanced Process Rewards

CodePRM from 2025 integration (aclanthology reference) introduces execution feedback as auxiliary information for constructing robust process reward models. Rather than relying solely on code correctness predictions, CodePRM leverages code execution results to distinguish between high-quality and low-quality thought steps[37]. The framework develops a Generate-Verify-Refine pipeline where CodePRM serves as a process verifier to dynamically identify and correct errors in agent reasoning.

## Unified Routing and Cascading Frameworks

### Cascade Routing: Theoretically Optimal Unified Framework

A significant theoretical contribution emerged from the ICML 2025 poster presentation on "A Unified Approach to Routing and Cascading for LLMs" (arXiv 2410.10347), which for the first time derived optimal strategies for both routing and cascading while proving optimality conditions[33][34]. The authors identified three key limitations in prior approaches: lack of formal proofs of optimality, failure to identify conditions under which strategies prove effective, and inability to combine both paradigms for further improvements[33].

The unified framework introduces "cascade routing," a paradigm integrating routing and cascading into theoretically optimal strategy[33]. Rather than always running models in fixed sequence or sticking to a single model, cascade routing iteratively picks the best model and can therefore skip models, reorder them, or run only as few as needed. Through mathematical analysis, the work identifies good quality estimators as the critical factor for success of model selection paradigms[33]. Experiments demonstrate that cascade routing consistently outperforms individual approaches by large margins, improving performance by up to 8% on RouterBench and 14% on SWE-Bench[34].

The theoretical foundation provided by this work represents a major advancement: rather than treating routing and cascading as distinct paradigms, the unified framework demonstrates that both emerge as special cases of a more general problem where sequential decisions about model selection can be optimized jointly[33]. This theoretical unification provides principled guidance for when routing alone suffices, when cascading proves necessary, and how to combine both approaches optimally.

## Online Learning and Adaptive Routing

### Bandit-Feedback Routing with Preferences

BaRP from 2510.07429 addresses a critical practical limitation of prior routing work: most routers train offline with labels for all candidate models, an assumption that breaks in deployment where only the outcome of the chosen model is observed[22][22]. BaRP implements Bandit-feedback Routing with Preferences, training under the same partial-feedback restriction as deployment while supporting preference-tunable inference where operators can adjust performance-cost tradeoffs at test time without retraining[22].

Framed as a contextual bandit problem over prompt features and user preference vectors, BaRP simulates online feedback settings during training and adapts routing decisions to each new prompt[22][22]. The approach avoids the offline-to-online distribution shift that plagued earlier routers by matching training conditions to deployment conditions. Comprehensive experiments demonstrate that BaRP consistently outperforms strong offline routers by at least 12.46% and the largest LLM by at least 2.45%, while generalizing robustly to unseen tasks[22].

### Contextual Bandits for Sequential LLM Selection

Online Multi-LLM Selection via Contextual Bandits from 2506.17670 extends bandit-based routing to multi-turn query refinement settings where the prompt dynamically changes in response to previous model outputs[42]. The key challenge involves unstructured context evolution: the prompt changes through a black-box process that cannot be simulated, modeled, or learned. The paper proposes the first contextual bandit framework for sequential LLM selection under unstructured prompt dynamics, formalizing myopic regret and developing a LinUCB-based algorithm achieving sublinear regret without relying on future context prediction[42].

The framework introduces budget-aware and positionally-aware extensions accommodating variable query costs and user preferences for early high-quality responses[42]. Experiments on diverse benchmarks demonstrate that contextual bandit methods outperform existing LLM routing strategies in both accuracy and cost-efficiency, validating the power of online learning for real-time adaptive LLM selection in agentic workflows.

### Calibration-Gated LLM Pseudo-Observations

Calibration-Gated LLM Pseudo-Observations from 2604.14961 introduces a novel online learning technique for contextual bandits where LLM predictions augment human feedback during cold-start phases[21]. The approach augments Disjoint LinUCB with LLM pseudo-observations where after each round, a language model predicts counterfactual rewards for unplayed arms. These predictions are injected as weighted pseudo-observations where the injection weight tracks the LLM's prediction accuracy via exponential moving average[21].

Evaluation on contextual bandit environments demonstrates 19% regret reduction on MIND relative to pure LinUCB when equipped with task-specific prompts[21]. However, the work also reveals that prompt design dominates over calibration gating parameters, suggesting that online learning effectiveness remains fundamentally bounded by the quality of LLM-based counterfactual reward estimation.

## Router Evaluation, Fragility, and Limitations

### Router Robustness and Fragility Analysis

How Robust Are Router-LLMs from 2504.07113 represents one of the first systematic investigations of LLM router fragility and failure modes[19]. The paper proposes DSC (Diverse, Simple, Categorized), an evaluation framework categorizing router performance across coding, translation, mathematics, human instructions, general knowledge, and LLM jailbreaking. Critically, the evaluation integrates privacy and safety assessments to reveal hidden risks[19].

The experimental results proved concerning: preference-based routers often make suboptimal, category-driven decisions. For instance, a BERT-based router directed all coding and mathematics queries to the most powerful LLM even when simpler models would suffice, while routing jailbreaking attempts to weaker models thereby elevating safety risks[19]. This systematic analysis demonstrates that routing systems, despite improving efficiency, can exhibit systematic biases where certain query types trigger unnecessary model escalation while simultaneously routing adversarial queries to less robust models.

### Verifier Ceiling Effects and Inference Scaling Limits

A critical limitation of verifier-based routing emerged from Inference Scaling Limits by Stroebl, Kapoor, and Narayanan from 2411.17501[18]. The paper demonstrates that indefinite accuracy improvement through resampling can only be realized if the verifier is perfect. When verifiers prove imperfect (as nearly always in reasoning or coding domains with incomplete test coverage), a nonzero probability of false positives exists: incorrect solutions passing the verifier. Resampling cannot decrease this probability, imposing a hard upper bound to resampling-based inference scaling even with infinite compute budgets[18].

The correlation between single-sample accuracy and false positive rate proves very strong on HumanEval and MBPP, establishing that no amount of inference scaling of weaker models enables matching the single-sample accuracy of stronger models[18]. Furthermore, when false positives carry negative utility compared to abstaining, the inference scaling curve bends downward further, with optimal sample counts potentially less than 10 under realistic assumptions[18]. These findings establish fundamental limits on what cascade routing with imperfect verifiers can achieve, suggesting that ultimate accuracy requires either stronger base models or better verifiers rather than simply more resampling.

### Failure Prevention vs. Failure Prediction

Accurate Failure Prediction in Agents Does Not Imply Effective Failure Prevention from 2602.03338 reveals a subtle but critical problem: LLM critics achieving high offline accuracy (AUROC 0.94) can nevertheless cause severe performance degradation during deployment[40]. The paper identifies a disruption-recovery tradeoff where interventions may recover failing trajectories but simultaneously disrupt trajectories that would have succeeded without intervention[40].

The finding proves particularly relevant for agentic routing: a router that perfectly predicts which trajectories fail might still degrade overall system performance if its interventions disrupt more successful trajectories than they save. The paper proposes a pre-deployment test using small pilots of 50 tasks to estimate whether intervention is likely to help or harm[40]. Across benchmarks, the test correctly identified when interventions degraded performance on high-success tasks (0 to -26 percentage points) while yielding modest improvement on high-failure benchmarks. This work establishes that routing system design must account for intervention disruption effects, not merely prediction accuracy.

### RouterArena: Comprehensive Router Evaluation Platform

RouterArena from 2510.00202 addresses the lack of standardized router evaluation by introducing an open platform enabling comprehensive comparison of LLM routers[23]. The platform provides a principally-constructed dataset with broad knowledge domain coverage, distinguishable difficulty levels for each domain, extensive evaluation metrics, and automated framework for leaderboard updates[23]. The resulting initial leaderboard with detailed metrics comparison represents the first standardized framework for systematic router evaluation.

The existence of RouterArena signals both progress and continued fragmentation in router research: the need for a comprehensive comparison platform indicates that individual router papers had not established sufficiently standardized evaluation to enable direct comparison. RouterArena's construction with domain-specific difficulty levels and extensive metrics addresses earlier limitations where routers were evaluated only on generic benchmarks potentially misrepresenting domain-specific routing difficulty.

## Tool-Calling and Function-Calling in Agentic Routing

### Core Tool-Calling Challenges and Limitations

The Berkeley Function Calling Leaderboard (BFCL) and related research revealed systematic degradation in tool-calling accuracy as tool count increases, a phenomenon directly relevant to routing in multi-tool agentic settings[58][60]. More tools mean more options to confuse, more documentation to parse, and more chances to select the wrong one. One consistent finding across function-calling research: accuracy drops as the number of available tools increases[60].

ToolPRM introduced an inference scaling framework that scores internal steps of function calls, discovering an "unrecoverability" characteristic in structured function calling[60]. Once models start generating malformed function calls, recovery becomes extremely difficult because the constraint structure of function specifications prevents mid-generation course correction. This characteristic means that routing errors in tool selection compound more severely than equivalent errors in general text generation tasks, requiring either more reliable routing decisions or fallback mechanisms that abandon malformed tool calls and retry with alternative models.

### Tool Specification and Routing Decision Making

The importance of clear tool specifications emerges repeatedly in function-calling research[56][60]. When tools lack clear best practices or documented failure modes, LLMs struggle with selection and execution. The proposed solution, ToolObserver, iteratively refines tool documentation by observing execution feedback from actual tool-calling trajectories[60]. This approach treats tool descriptions themselves as routing-relevant artifacts that can be improved through deployment experience.

Nested API call sequences present a distinct challenge where outputs of one call feed as inputs to subsequent calls[60]. GPT-4o, the best-performing model in NESTFUL benchmark evaluation, achieved only 28% full sequence match accuracy, with 60% win-rate indicating success on individual calls but failure at composition[60]. This finding suggests that routing in agentic tool-using settings must account for tool-interaction complexity: simple tool-by-tool routing decisions might route each individual call to appropriate models, but fail to ensure compatibility and correct sequencing.

## Multi-Agent Coordination and Orchestration Failures

### Systematic Failure Modes in Multi-Agent LLM Systems

Recent research from UC Berkeley on multi-agent system failures (2025-2026) identified that such systems fail between 41% and 86.7% of the time on standard benchmarks[50]. These failures cluster into three categories: Specification and System Design issues (41.8%), Inter-Agent Misalignment (36.9%), and Task Verification and Termination failures (21.3%)[50]. Within agentic routing contexts, inter-agent misalignment emerges as particularly challenging because routing decisions influence communication patterns between agents.

Context loss during agent handoffs represents a major failure source within the Inter-Agent Misalignment category[50]. When routing causes task transitions between agents, context preservation becomes critical but frequently fails. The MAST taxonomy establishing these failure categories provides a framework for evaluating router designs: routers should be assessed not only on model selection quality but also on their effects on inter-agent communication and context preservation[50].

Task Verification and Termination failures account for 21.3% of multi-agent failures, with premature termination (6.2%), incomplete verification (8.2%), and incorrect verification (9.1%) as key components[50]. This finding emphasizes that routers enabling multi-agent orchestration must coordinate verification decisions: different agents might reach inconsistent conclusions about task completion, requiring meta-verification that aggregates across agent outputs.

### Retrieval-Prediction Imbalance in Agent Evaluation

The CryptoBench benchmark revealed a critical failure mode in contemporary LLM agents: retrieval-prediction imbalance where agents excel at data retrieval but demonstrate near-complete failure in predictive analysis[39]. Many leading models proved proficient at retrieving relevant information yet lacked deeper analytical capabilities to synthesize information into forecasts[39]. This imbalance suggests that multi-tier routing strategies must differ between retrieval-focused and reasoning-focused subtasks within agentic workflows.

## Cost-Performance Tradeoffs and Economics of Routing

### Theoretical Analysis of Routing and User Preference Alignment

Routing, Cascades, and User Choice from 2602.09902 provides game-theoretic analysis of routing in contexts where user preferences and provider costs misalign[65]. The paper solves a Stackelberg game where users maximize utility minus delay while providers minimize service costs, fully characterizing user best response and simplifying provider optimization[65].

The analysis reveals that optimal routing policies typically involve static strategies with no cascading that depend on expected utility to the user[65]. Furthermore, a misalignment gap emerges between provider-optimal and user-preferred routes when model rankings by utility and cost differ[65]. Most concerning, providers face incentives to artificially throttle latency to minimize costs when user churn probability is low, thereby depressing user utility while maximizing provider margins[65]. These findings establish that router design exists within an economic system where incentives matter: purely technically optimal routing might prove economically unstable in production systems.

### Cost Reduction Through Pool-Based Routing

Token-Budget-Aware Pool Routing from 2604.09613 addresses cost reduction through infrastructure-level routing: dispatching requests to differentiated vLLM pools optimized for short versus long sequences[45]. By learning per-category bytes-per-token ratios online through exponential moving average, the system routes high-volume short requests to a high-throughput pool while directing longer sequences to a capacity-optimized pool[45]. On production traces, token-budget routing reduced GPU instances by 17-39%, translating to \$1.2-2.0M annual savings at 1,000 req/s scale[45].

This infrastructure-level routing represents a distinct tier from model-selection routing but proves complementary: after deciding which model to invoke, infrastructure routers determine how to efficiently execute that model. The results demonstrate significant savings from specializing infrastructure to specific workload characteristics, suggesting that comprehensive agentic routing systems benefit from multi-level routing decisions at model, tool, and infrastructure tiers.

## Open-Source Frameworks and Implementation Platforms

### RouteLLM and Production Router Implementations

RouteLLM represents one of the most widely adopted open-source router implementations, providing drop-in replacement for OpenAI's client or OpenAI-compatible server to route simpler queries to cheaper models[43]. The framework reduces costs by up to 85% while maintaining 95% GPT-4 performance on widely-used benchmarks like MT Bench[43]. RouteLLM's ease of integration into existing systems and proven cost-performance characteristics have made it influential in production deployments.

The framework enables clients to specify router and cost threshold for each request in standard format, supporting multiple trained routers out of the box[43]. This accessibility has established RouteLLM as a de facto standard for practitioners implementing basic cost-based routing, though the system's relatively simple classification approach (typically linear or matrix factorization routers) may not capture complex agentic difficulty patterns.

### Semantic Router: Vector-Space Decision Making

Semantic Router provides a superfast decision-making layer for LLMs and agents using semantic vector space rather than waiting for slow LLM generations to make tool-use decisions[47]. The framework uses vector embeddings to make routing decisions instantaneously, avoiding the 50-200ms latency overhead of classifier-based routing when applied per-request. For agents making thousands of tool-calling decisions, vector-space routing could substantially reduce total execution time.

### LangGraph and Multi-Agent Orchestration

LangGraph from LangChain provides explicit state machine representation for multi-agent workflows with integrated routing capabilities[49]. The framework simplifies implementation of hierarchical routing scenarios through acyclic graph structures, enabling developers to specify routing decisions at graph nodes and ensure deterministic behavior. LangGraph's integration into the LangChain ecosystem has established it as a primary platform for practitioners implementing agentic workflows with custom routing logic.

### CrewAI and Role-Based Multi-Agent Coordination

CrewAI implements multi-agent collaboration by defining specialized roles, tasks, and skills with human-in-the-loop patterns[49]. The framework targets developer ergonomics and enterprise readiness for team-of-agents metaphors. CrewAI's role-based architecture naturally aligns with routing strategies that route tasks to specialized agents by role rather than dynamically selecting among generic models.

## Recent 2026 Developments and Emerging Directions

### Preference-Aligned Routing with Arch-Router

Arch-Router from early 2026 represents progress in incorporating human preferences into routing rather than purely technical metrics[25]. The framework introduces Domain-Action taxonomy enabling queries to map to user-defined routing policies with natural language descriptions. By encoding preferences explicitly in policy descriptions, the system achieves transparency and flexibility reflecting how LLMs are evaluated and integrated in real-world scenarios[25]. The reported 93.17% routing score substantially outperforms candidate models, suggesting that preference-aligned framing improves routing reliability.

### Reasoning-Time Compute Scaling and Deep Think

Recent advances in reasoning-focused models (Gemini 3 Deep Think, released February 2026) introduced selective routing between standard and reasoning-intensive models based on task characteristics[28]. The practical architecture uses Deep Think selectively by routing simple queries to standard Gemini 3 Pro for fast, cheap responses and escalating to Deep Think only for queries requiring multi-step reasoning[28]. This represents an emerging routing pattern where routing decisions select not merely between models but between inference-time compute budgets and reasoning strategies.

### Dynamic Verification and Reward-Based Routing

Recent work on verifier-based routing incorporates dynamic difficulty estimation that updates rewards based on trajectory success, enabling self-correcting routing decisions[6]. These systems learn from deployment experience, adjusting routing policies as they observe which model assignments prove effective for specific task categories.

## Conclusion: Integration, Open Problems, and Future Directions

The contemporary landscape of LLM routing for agentic tool-using workflows has evolved from simple cascade heuristics toward theoretically-grounded frameworks, online learning systems, and empirically-validated router implementations. The survey has documented progression across multiple research axes: from FrugalGPT's foundational cascade routing through AutoMix's self-verification to recent unified framework contributions; from basic difficulty estimation toward Bayesian and VAE-based approaches; from offline router training to online bandit-based selection; and from generic routing toward tool-aware and domain-aware specialization.

Despite this progress, fundamental challenges persist that define the frontier of routing research as of April 2026. Verifier imperfection and false positive ceiling effects establish hard limits on cascade routing effectiveness, limits that only stronger base models can overcome[18]. Router fragility and systematic biases in category-driven routing decisions reveal that efficiency improvements sometimes come with hidden costs in robustness and fairness[19]. The disruption-recovery tradeoff in routing interventions suggests that prediction accuracy alone cannot guide practical deployment decisions[40]. Multi-agent coordination failures concentrated in context loss and inter-agent misalignment indicate that router impact extends beyond individual model selection to system-level communication patterns[50].

The most promising research directions heading into 2026 and beyond involve: (1) theoretical characterization of verifier accuracy requirements for cascade routing to achieve practical cost reductions; (2) robust difficulty estimation that generalizes across domains and resists adversarial query constructions; (3) routing systems that account for downstream task structure rather than treating difficulty as static query property; (4) integration of router decisions with agent communication protocols to minimize context loss; (5) online learning routers that detect and adapt to distribution shift in query difficulty; and (6) benchmark standardization through platforms like RouterArena enabling direct comparison of routing approaches.

Production deployment of agentic routing systems must grapple with tension between technical optimality and economic incentives, between efficiency and robustness, and between latency-minimizing router decisions and reliability-maximizing verification. As agentic systems scale toward large-scale deployments managing thousands of concurrent tool-using workflows, router design becomes increasingly critical to overall system performance. The research documented in this survey provides substantial foundation for such systems, though the evolution from research prototypes to production-grade routers at scale remains an ongoing engineering challenge extending beyond the scope of current research literature.

### Citations

1. https://arxiv.org/abs/2305.05176
2. https://arxiv.org/pdf/2310.12963.pdf
3. https://arxiv.org/abs/2310.03046
4. https://arxiv.org/abs/2404.14618
5. https://arxiv.org/abs/2510.08439
6. https://arxiv.org/abs/2509.11079
7. https://arxiv.org/abs/2604.00594
8. https://arxiv.org/abs/2604.07494
9. https://arxiv.org/abs/2505.19970
10. https://arxiv.org/abs/2511.08325
11. https://github.com/mukhal/thinkprm
12. https://arxiv.org/abs/2601.08276
13. https://arxiv.org/abs/2307.16789
14. https://www.granquartz.com/stone-fabrication/router-bits-profiling-tools-specialty-tools
15. https://www.youtube.com/watch?v=cixmqTsi2A4
16. https://arxiv.org/abs/2601.22249
17. https://arxiv.org/abs/2512.15000
18. https://arxiv.org/abs/2411.17501
19. https://arxiv.org/abs/2504.07113
20. https://arxiv.org/abs/2506.10525
21. https://arxiv.org/abs/2604.14961
22. https://arxiv.org/abs/2510.07429
23. https://arxiv.org/abs/2510.00202
24. https://www.patronus.ai/ai-agent-development/ai-agent-routing
25. https://arxiv.org/html/2506.16655v1
26. https://help.mypurecloud.com/articles/predictive-routing-overview/
27. https://artificialanalysis.ai/models/comparisons/gpt-5-5-non-reasoning-vs-qwen3-5-27b-non-reasoning
28. https://www.digitalapplied.com/blog/gemini-3-deep-think-reasoning-benchmarks-guide
29. https://github.com/gis-ops/routingpy
30. https://reference.langchain.com/python/langchain-litellm/embeddings/litellm_router
31. https://arxiv.org/pdf/2604.15728.pdf
32. https://www.augmentcode.com/guides/ai-model-routing-guide
33. https://icml.cc/virtual/2025/poster/46183
34. https://arxiv.org/pdf/2410.10347.pdf
35. https://arxiv.org/abs/2402.19446
36. https://arxiv.org/abs/2308.02066
37. https://aclanthology.org/2025.findings-acl.428.pdf
38. https://arxiv.org/html/2512.00164v1
39. https://arxiv.org/html/2512.00417v4
40. https://arxiv.org/abs/2602.03338
41. https://arxiv.org/html/2510.14242v1
42. https://arxiv.org/abs/2506.17670
43. https://github.com/lm-sys/routellm
44. https://arxiv.org/pdf/2505.12601.pdf
45. https://arxiv.org/abs/2604.09613
46. https://docs.langchain.com/oss/python/langchain/multi-agent/router-knowledge-base
47. https://github.com/aurelio-labs/semantic-router
48. https://swift.ethz.ch
49. https://www.langflow.org/blog/the-complete-guide-to-choosing-an-ai-agent-framework-in-2025
50. https://futureagi.substack.com/p/why-do-multi-agent-llm-systems-fail
51. https://simmering.dev/blog/agent-benchmarks/
52. https://www.emergentmind.com/topics/retrieval-prediction-imbalance
53. https://arxiv.org/abs/2507.04410
54. https://arxiv.org/html/2410.20445v5
55. https://aimultiple.com/agentic-llm
56. https://www.promptingguide.ai/agents/function-calling
57. https://arxiv.org/html/2510.06732v1
58. https://gorilla.cs.berkeley.edu/leaderboard.html
59. https://arxiv.org/html/2412.13719v1
60. https://dev.to/terzioglub/why-llm-agents-break-when-you-give-them-tools-and-what-to-do-about-it-f5
61. https://developers.liveperson.com/conversation-builder-generative-ai-routing-ai-agents-route-consumers-conversationally.html
62. https://www.confident-ai.com/blog/llm-evaluation-metrics-everything-you-need-for-llm-evaluation
63. https://www.youtube.com/watch?v=K6Adzg5OREw
64. https://docs.langchain.com/langsmith/trajectory-evals
65. https://arxiv.org/html/2602.09902v1
66. https://www.hud.ai/resources/verifier-reward-design-rl-environments
67. https://developer.nvidia.com/blog/how-to-train-scientific-agents-with-reinforcement-learning/

---

## Exa Deep Search  (15 sources)

### 1. [2305.05176v1] FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance
**URL:** https://arxiv.org/abs/2305.05176v1
**Published:** 2023-05-09T19:34:22.000Z

[2305.05176v1] FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance

# Computer Science > Machine Learning

arXiv:2305.05176v1 (cs)

[Submitted on 9 May 2023]

# Title:FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance

Authors: Lingjiao Chen, Matei Zaharia, James Zou

> Abstract:There is a rapidly growing number of large language models (LLMs) that users can query for a fee. We review the cost associated with querying popular LLM APIs, e.g. GPT-4, ChatGPT, J1-Jumbo, and find that these models have heterogeneous pricing structures, with fees that can differ by two orders of magnitude. In particular, using LLMs on large collections of queries and text can be expensive. Motivated by this, we outline and discuss three types of strategies that users can exploit to reduce the inference cost associated with using LLMs: 1) prompt adaptation, 2) LLM approximation, and 3) LLM cascade. As an example, we propose FrugalGPT, a simple yet flexible instantiation of LLM cascade which learns which combinations of LLMs to use for different queries in order to reduce cost and improve accuracy. Our experiments show that FrugalGPT can match the performance of the best individual LLM (e.g. GPT-4) with up to 98% cost reduction or improve the accuracy over GPT-4 by 4% with the same cost. The ideas and findings presented here lay a foundation for using LLMs sustainably and efficiently.

arXiv-issued DOI via DataCite

| Subjects: | Machine Learning (cs.LG); Artificial Intelligence (cs.AI); Computation and Language (cs.CL); Software Engineering (cs.SE) |
| --- | --- |
| Cite as: | arXiv:2305.05176 [cs.LG] |
| (or arXiv:2305.05176v1 [cs.LG] for this version) |

## Submission history

From: Lingjiao Chen [view email] [v1] Tue, 9 May 2023 05:11:02 UTC (1,717 KB)

Full-text links:

## Access Paper:

- View PDF
- TeX Source

Current browse context:

cs.LG

< prev| next >

Change to browse by:

### References & Citations

- Google Scholar
- Semantic Scholar

### 2 blog links

(what is this?)

export BibTeX citation

### Bookmark

Bibliographic Tools

# Bibliographic and Citation Tools

Bibliographic Explorer Toggle

Bibliographic Explorer (What is the Explorer?)

Connected Papers Toggle

Connected Papers (What is Connected Papers?)

Litmaps Toggle

Litmaps (What is Litmaps?)

scite.ai Toggle

scite Smart Citations (What are Smart Citations?)

Code, Data, Media

# Code, Data and Media Associated with this Article

alphaXiv Toggle

alphaXiv (What is alphaXiv?)

Links to Code Toggle

CatalyzeX Code Finder for Papers (What is CatalyzeX?)

DagsHub Toggle

DagsHub (What is DagsHub?)

GotitPub Toggle

Gotit.pub (What is GotitPub?)

Huggingface Toggle

Hugging Face (What is Huggingface?)

Links to Code Toggle

Papers with Code (What is Papers with Code?)

ScienceCast Toggle

ScienceCast (What is ScienceCast?)

Demos

# Demos

Replicate Toggle

Replicate (What is Replicate?)

Spaces Toggle

Hugging Face Spaces (W

*… (886 more characters — see results.json for full text)*

---

### 2. EcoAssistant: Using LLM Assistant More Affordably and Accurately - arXiv.gg
**URL:** https://arxiv.gg/abs/2310.03046

EcoAssistant: Using LLM Assistant More Affordably and Accurately - arXiv.gg

# EcoAssistant: Using LLM Assistant More Affordably and Accurately

Jieyu Zhang, Ranjay Krishna, Ahmed H. Awadallah, Chi Wang

Today, users ask Large language models (LLMs) as assistants to answer queries that require external knowledge; they ask about the weather in a specific city, about stock prices, and even about where specific locations are within their neighborhood. These queries require the LLM to produce code that invokes external APIs to answer the user's question, yet LLMs rarely produce correct code on the first try, requiring iterative code refinement upon execution results. In addition, using LLM assistants to support high query volumes can be expensive. In this work, we contribute a framework, EcoAssistant, that enables LLMs to answer code-driven queries more affordably and accurately. EcoAssistant contains three components. First, it allows the LLM assistants to converse with an automatic code executor to iteratively refine code or to produce answers based on the execution results. Second, we use a hierarchy of LLM assistants, which attempts to answer the query with weaker, cheaper LLMs before backing off to stronger, expensive ones. Third, we retrieve solutions from past successful queries as in-context demonstrations to help subsequent queries. Empirically, we show that EcoAssistant offers distinct advantages for affordability and accuracy, surpassing GPT-4 by 10 points of success rate with less than 50% of GPT-4's cost.

PDF on arXiv.org Regenerate Embedding Auto-embed arxiv.org

embedding-generator

Original on arxiv.org PDF (external)

## Citation Graph

Reset Fullscreen

This paper

Reference

Citing

Uncached

## References

## Cited By

- 2509.01920 Dynamic Speculative Agent Planning(Sep 2025) 1 cites
- 2508.03923 CoAct-1: Computer-using Agents with Coding as Actions(Aug 2025) 3 cites
- 2507.21035 GenoMAS: A Multi-Agent Framework for Scientific Discovery via Code-Driven Gene Expression Analysis(Jul 2025) 1 cites
- 2507.02076 Reasoning on a Budget: A Survey of Adaptive and Controllable Test-Time Compute in LLMs(Jul 2025) 2 cites
- 2506.19676 A Survey of LLM-Driven AI Agent Communication: Protocols, Security Risks, and Defense Countermeasures(Jun 2025) 6 cites
- 2505.00212 Which Agent Causes Task Failures and When? On Automated Failure Attribution of LLM Multi-Agent Systems(May 2025) 9 cites
- 2504.08148 Orchestrating Agents and Data for Enterprise: A Blueprint Architecture for Compound AI(Apr 2025) 2 cites
- 2502.18036 Harnessing Multiple Large Language Models: A Survey on LLM Ensemble(Feb 2025) 9 cites
- 2501.10688 Neural Algorithmic Reasoning for Hypergraphs with Looped Transformers(Jan 2025) 11 cites
- 2501.05452 ReFocus: Visual Editing as a Chain of Thought for Structured Image Understanding(Jan 2025) 17 cites
- 2501.01818 Rerouting LLM Routers(Jan 2025) 4 cites
- 2412.12170 PickLLM: Context-Aware RL-Assisted Large Language Model Routing(Dec 20

*… (2,675 more characters — see results.json for full text)*

---

### 3. AutoMix: Automatically Mixing Language Models - arXiv.gg
**URL:** https://arxiv.gg/abs/2310.12963

AutoMix: Automatically Mixing Language Models - arXiv.gg

# AutoMix: Automatically Mixing Language Models

Large language models (LLMs) are now available from cloud API providers in various sizes and configurations. While this diversity offers a broad spectrum of choices, effectively leveraging the options to optimize computational cost and performance remains challenging. In this work, we present Automix, an approach that strategically routes queries to larger LMs, based on the approximate correctness of outputs from a smaller LM. Central to Automix are two key technical contributions. First, it has a few-shot self-verification mechanism, which estimates the reliability of its own outputs without requiring extensive training. Second, given that self-verification can be noisy, it employs a POMDP based router that can effectively select an appropriately sized model, based on answer confidence. Experiments across five language models and five challenging datasets show that Automix consistently surpasses strong baselines, reducing computational cost by over 50% for comparable performance.

PDF on arXiv.org Regenerate Embedding Auto-embed arxiv.org

embedding-generator

Original on arxiv.org PDF (external)

## Citation Graph

Reset Fullscreen

This paper

Reference

Citing

Uncached

## References

- 2405.02134 Optimising Calls to Large Language Models with Uncertainty-Based Two-Tier Selection(May 2024) 9 cites
- 2311.08516 LLMs cannot find reasoning errors, but can correct them given the error location(Nov 2023) 85 cites
- 2310.06825 Mistral 7B(Oct 2023) 3645 cites
- 2310.03714 DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines(Oct 2023) 179 cites
- 2310.01798 Large Language Models Cannot Self-Correct Reasoning Yet(Oct 2023) 358 cites
- 2309.11495 Chain-of-Verification Reduces Hallucination in Large Language Models(Sep 2023) 260 cites
- 2308.07758 Forward-Backward Reasoning in Large Language Models for Mathematical Verification(Aug 2023) 28 cites
- 2308.03188 Automatically Correcting Large Language Models: Surveying the landscape of diverse self-correction strategies(Aug 2023) 213 cites
- 2307.01928 Robots That Ask For Help: Uncertainty Alignment for Large Language Model Planners(Jul 2023) 109 cites
- 2305.18654 Faith and Fate: Limits of Transformers on Compositionality(May 2023) 187 cites
- 2305.14196 ZeroSCROLLS: A Zero-Shot Benchmark for Long Text Understanding(May 2023) 76 cites
- 2305.12744 Fact-Checking Complex Claims with Program-Guided Reasoning(May 2023) 22 cites
- 2305.10403 PaLM 2 Technical Report(May 2023) 1751 cites
- 2305.03047 Principle-Driven Self-Alignment of Language Models from Scratch with Minimal Human Supervision(May 2023) 231 cites
- 2304.05302 RRHF: Rank Responses to Align Language Models with Human Feedback without tears(Apr 2023) 405 cites
- 2303.17651 Self-Refine: Iterative Refinement with Self-Feedback(Mar 2023) 823 cites
- 2303.11366 Reflexion: Language Agents with Verbal Reinforcement Learnin

*… (8,273 more characters — see results.json for full text)*

---

### 4. Untitled
**URL:** https://arxiv.org/pdf/2310.12963

AutoMix: Automatically Mixing Language Models
Pranjal Aggarwal♢∗ Aman Madaan♣ ∗ Ankit Anand ‡ Srividya Pranavi Potharaju †
Swaroop Mishra‡ Pei Zhou△ Aditya Gupta Dheeraj Rajagopal† Karthik Kappaganthu†
Yiming Yang♠ Shyam Upadhyay† Manaal Faruqui† Mausam♢
♠ Carnegie Mellon University ♣ xAI † Google ‡ Google DeepMind
♢ IIT Delhi △ University of Southern California
automix-models@googlegroups.com
Abstract
Large language models (LLMs) are now available from cloud API providers in
various sizes and configurations. While this diversity offers a broad spectrum
of choices, effectively leveraging the options to optimize computational cost and
performance remains challenging. In this work, we present AutoMix, an approach
that strategically routes queries to larger LMs, based on the approximate correctness of outputs from a smaller LM. Central to AutoMix are two key technical
contributions. First, it has a few-shot self-verification mechanism, which estimates
the reliability of its own outputs without requiring extensive training. Second,
given that self-verification can be noisy, it employs a POMDP based router that
can effectively select an appropriately sized model, based on answer confidence.
Experiments across five language models and five challenging datasets show that
AutoMix consistently surpasses strong baselines, reducing computational cost by
over 50% for comparable performance. 1
1 Introduction
The landscape of Large Language Models (LLMs) is rapidly evolving, with a wide array of models
now available in various sizes, capabilities, and computational requirements [Touvron et al., 2023,
OpenAI, 2023, Jiang et al., 2023a]. While larger models generally exhibit superior performance,
their substantial computational costs render them unaffordable for many simpler tasks. Moreover,
the vast array of available options makes it challenging for end-users to determine the optimal
model configuration for their specific needs. This challenge is further compounded by the intrinsic
complexity and variability of real-world tasks, ranging from simple (e.g., binary classification on
separable data) to complex (e.g., code generation) and potentially unsolvable tasks (e.g., certain
forms of multi-step reasoning). To address these issues and ensure that end-users can obtain the best
performance within their budget constraints, the development of model-switching techniques has
become increasingly important. These techniques involve dispatching queries to models of disparate
sizes and capabilities, allowing for a more efficient allocation of computational resources [Liu et al.,
2020, Zhou et al., 2020, Madaan and Yang, 2022, Geng et al., 2021, Schuster et al., 2022].
Contemporary model-switching strategies often rely on separate routing models trained for a fixed
set of tasks [Chen et al., 2023, Ding et al., 2024]. Moreover, modern LLMs are frequently accessible
only through black-box APIs, restricting direct model optimization due to the unavailability of
fine-tunin

*… (22,000 more characters — see results.json for full text)*

---

### 5. FrugalGPT: Cost-Effective LLM Optimization
**URL:** https://www.emergentmind.com/papers/2305.05176

0 }" @focus="focused = true" @click="focused = true; clicked = true; handleQueryChange()" @click.away="clicked = false" @keydown="focused = true" @keydown.escape="setQuery(''); focused = false; clicked = false" @input.debounce.100ms="handleQueryChange();" @input="if ($event.target.value === '') { setQuery('') }" @keyup="if ($event.target.value === '') { setQuery('') }" @keydown.enter.prevent="if (!$event.shiftKey) { $refs.search_form.submit() } else { handleShiftEnter($event) }" maxlength="2000">2305.05176

0">Papers

0">Topics

0">Authors

0">

Recent

Search

2000 character limit reached

# FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance

Published 9 May 2023 in cs.LG, cs.AI, cs.CL, and cs.SE | (2305.05176v1)

Abstract: There is a rapidly growing number of LLMs that users can query for a fee. We review the cost associated with querying popular LLM APIs, e.g. GPT-4, ChatGPT, J1-Jumbo, and find that these models have heterogeneous pricing structures, with fees that can differ by two orders of magnitude. In particular, using LLMs on large collections of queries and text can be expensive. Motivated by this, we outline and discuss three types of strategies that users can exploit to reduce the inference cost associated with using LLMs: 1) prompt adaptation, 2) LLM approximation, and 3) LLM cascade. As an example, we propose FrugalGPT, a simple yet flexible instantiation of LLM cascade which learns which combinations of LLMs to use for different queries in order to reduce cost and improve accuracy. Our experiments show that FrugalGPT can match the performance of the best individual LLM (e.g. GPT-4) with up to 98% cost reduction or improve the accuracy over GPT-4 by 4% with the same cost. The ideas and findings presented here lay a foundation for using LLMs sustainably and efficiently.

1. Lingjiao Chen
2. Matei Zaharia
3. James Zou

1. LongLLMLingua: Accelerating and Enhancing LLMs in Long Context Scenarios via Prompt Compression(2023)
2. Large Language Model Cascades with Mixture of Thoughts Representations for Cost-efficient Reasoning(2023)
3. EcoRank: Budget-Constrained Text Re-ranking Using Large Language Models(2024)
4. SMART: Automatically Scaling Down Language Models with Accuracy Guarantees for Reduced Processing Fees(2024)
5. MetaLLM: A High-performant and Cost-efficient Dynamic Framework for Wrapping LLMs(2024)

View on Semantic Scholar

### Summary

- The paper demonstrates a novel framework that uses prompt adaptation, LLM approximation, and cascade strategies to reduce inference costs by up to 98%.
- It empirically validates that FrugalGPT can maintain GPT-4-level accuracy or achieve a 4% improvement at equivalent expenditure.
- The approach provides a viable, sustainable path for high-volume LLM deployment, balancing performance with financial and environmental benefits.

## FrugalGPT: Enhancing Cost-Effectiveness and Performance in LLM Utilization

### Introduction

The proliferation of LLMs has

*… (5,547 more characters — see results.json for full text)*

---

### 6. [2510.08439] xRouter: Training Cost-Aware LLMs Orchestration System via Reinforcement Learning
**URL:** https://arxiv.org/abs/2510.08439
**Published:** 2025-10-09T14:28:44.000Z

[2510.08439] xRouter: Training Cost-Aware LLMs Orchestration System via Reinforcement Learning

# Computer Science > Machine Learning

arXiv:2510.08439 (cs)

[Submitted on 9 Oct 2025]

# Title:xRouter: Training Cost-Aware LLMs Orchestration System via Reinforcement Learning

View PDF HTML (experimental)

> Abstract:Modern LLM deployments confront a widening cost-performance spectrum: premium models deliver strong reasoning but are expensive, while lightweight models are economical yet brittle on complex tasks. Static escalation rules and keyword heuristics under-utilize this spectrum and fail to adapt across task types. We present xRouter, a tool-calling-based routing system in which a learned router can either answer directly or invoke one or more external models. The router is trained end-to-end with reinforcement learning using an explicit, cost-aware reward that encodes cost-performance trade-offs, eliminating the need for hand-engineered routing rules. Our implementation encompasses the full reinforcement learning framework, including reward and cost accounting, as well as the deployment and evaluation pipelines. Across diverse benchmarks, xRouter achieves strong cost-performance trade-offs (e.g., substantial cost reductions at comparable task completion rates), and provides empirical insights into what reliably helps learned routing and what does not, ranging from model trainability to the difficulty of eliciting sophisticated orchestration behaviors in small open models. We hope these findings and our open implementation will serve as a practical substrate for advancing learned, cost-aware LLM orchestration.

arXiv-issued DOI via DataCite

| Comments: |
| --- |
| Subjects: | Machine Learning (cs.LG); Artificial Intelligence (cs.AI); Computation and Language (cs.CL) |
| Cite as: | arXiv:2510.08439 [cs.LG] |
| (or arXiv:2510.08439v1 [cs.LG] for this version) |

## Submission history

From: Cheng Qian [view email] [v1] Thu, 9 Oct 2025 16:52:01 UTC (9,913 KB)

Full-text links:

## Access Paper:

Current browse context:

cs.LG

< prev| next >

Change to browse by:

### References & Citations

- Google Scholar
- Semantic Scholar

export BibTeX citation

### Bookmark

Bibliographic Tools

# Bibliographic and Citation Tools

Bibliographic Explorer Toggle

Bibliographic Explorer (What is the Explorer?)

Connected Papers Toggle

Connected Papers (What is Connected Papers?)

Litmaps Toggle

Litmaps (What is Litmaps?)

scite.ai Toggle

scite Smart Citations (What are Smart Citations?)

Code, Data, Media

# Code, Data and Media Associated with this Article

alphaXiv Toggle

alphaXiv (What is alphaXiv?)

Links to Code Toggle

CatalyzeX Code Finder for Papers (What is CatalyzeX?)

DagsHub Toggle

DagsHub (What is DagsHub?)

GotitPub Toggle

Gotit.pub (What is GotitPub?)

Huggingface Toggle

Hugging Face (What is Huggingface?)

Links to Code Toggle

Papers with Code (What is Papers with Code?)

ScienceCast Toggle

ScienceCast (What is ScienceCast?)

Demos

*… (984 more characters — see results.json for full text)*

---

### 7. [2504.01400v1] ToolACE-R: Tool Learning with Adaptive Self-Refinement
**URL:** https://arxiv.org/abs/2504.01400v1

[2504.01400v1] ToolACE-R: Tool Learning with Adaptive Self-Refinement

# Computer Science > Computation and Language

arXiv:2504.01400v1 (cs)

[Submitted on 2 Apr 2025 (this version), latest version 10 Jan 2026 (v3)]

# Title:ToolACE-R: Tool Learning with Adaptive Self-Refinement

View PDF HTML (experimental)

> Abstract:Tool learning, which allows Large Language Models (LLMs) to leverage external tools for solving complex user tasks, has emerged as a promising avenue for extending model capabilities. However, current approaches primarily focus on data synthesis for fine-tuning LLMs to invoke tools effectively, largely ignoring how to fully stimulate the potential of the model. In this paper, we propose ToolACE-R, a novel method that introduces adaptive self-refinement for tool invocations. Our approach features a model-aware iterative training procedure that progressively incorporates more training samples based on the model's evolving capabilities. Additionally, it allows LLMs to iteratively refine their tool calls, optimizing performance without requiring external feedback. To further enhance computational efficiency, we integrate an adaptive mechanism when scaling the inference time, enabling the model to autonomously determine when to stop the refinement process. We conduct extensive experiments across several benchmark datasets, showing that ToolACE-R achieves competitive performance compared to advanced API-based models, even without any refinement. Furthermore, its performance can be further improved efficiently through adaptive self-refinement. Our results demonstrate the effectiveness of the proposed method, which is compatible with base models of various sizes, offering a promising direction for more efficient tool learning.

arXiv-issued DOI via DataCite

| Subjects: | Computation and Language (cs.CL); Artificial Intelligence (cs.AI); Machine Learning (cs.LG) |
| --- | --- |
| Cite as: | arXiv:2504.01400 [cs.CL] |
| (or arXiv:2504.01400v1 [cs.CL] for this version) |

## Submission history

From: Xingshan Zeng [view email] [v1] Wed, 2 Apr 2025 06:38:56 UTC (378 KB) [v2] Thu, 14 Aug 2025 03:37:54 UTC (300 KB) [v3] Sat, 10 Jan 2026 10:48:00 UTC (409 KB)

Full-text links:

## Access Paper:

### Current browse context:

cs.CL

< prev| next >

Change to browse by:

### References & Citations

- Google Scholar
- Semantic Scholar

export BibTeX citation

### Bookmark

Bibliographic Tools

# Bibliographic and Citation Tools

Bibliographic Explorer Toggle

Bibliographic Explorer (What is the Explorer?)

Connected Papers Toggle

Connected Papers (What is Connected Papers?)

Litmaps Toggle

Litmaps (What is Litmaps?)

scite.ai Toggle

scite Smart Citations (What are Smart Citations?)

Code, Data, Media

# Code, Data and Media Associated with this Article

alphaXiv Toggle

alphaXiv (What is alphaXiv?)

Links to Code Toggle

CatalyzeX Code Finder for Papers (What is CatalyzeX?)

DagsHub Toggle

DagsHub (What is DagsHub?)

GotitPub Toggle

Gotit.pub

*… (1,059 more characters — see results.json for full text)*

---

### 8. ToolACE: Winning the Points of LLM Function Calling - arXiv.gg
**URL:** https://arxiv.gg/abs/2409.00920

ToolACE: Winning the Points of LLM Function Calling - arXiv.gg

# ToolACE: Winning the Points of LLM Function Calling

Function calling significantly extends the application boundary of large language models, where high-quality and diverse training data is critical for unlocking this capability. However, real function-calling data is quite challenging to collect and annotate, while synthetic data generated by existing pipelines tends to lack coverage and accuracy. In this paper, we present ToolACE, an automatic agentic pipeline designed to generate accurate, complex, and diverse tool-learning data. ToolACE leverages a novel self-evolution synthesis process to curate a comprehensive API pool of 26,507 diverse APIs. Dialogs are further generated through the interplay among multiple agents, guided by a formalized thinking process. To ensure data accuracy, we implement a dual-layer verification system combining rule-based and model-based checks. We demonstrate that models trained on our synthesized data, even with only 8B parameters, achieve state-of-the-art performance on the Berkeley Function-Calling Leaderboard, rivaling the latest GPT-4 models. Our model and a subset of the data are publicly available at https://huggingface.co/Team-ACE.

PDF on arXiv.org Regenerate Embedding Auto-embed arxiv.org

embedding-generator

Original on arxiv.org PDF (external)

## Citation Graph

Reset Fullscreen

This paper

Reference

Citing

Uncached

## References

- 2407.03502 AgentInstruct: Toward Generative Teaching with Agentic Flows(Jul 2024) 31 cites
- 2407.00121 Granite-Function Calling Model: Introducing Function Calling Abilities via Multi-task Learning of Granular Tasks(Jul 2024) 11 cites
- 2406.18518 APIGen: Automated Pipeline for Generating Verifiable and Diverse Function-Calling Datasets(Jun 2024) 39 cites
- 2405.17935 Tool Learning with Large Language Models: A Survey(May 2024) 54 cites
- 2404.11891 Large Language Models Can Solve Real-World Planning Rigorously with Formal Verification Tools(Apr 2024) 22 cites
- 2402.15491 API-BLEND: A Comprehensive Corpora for Training and Benchmarking API LLMs(Feb 2024) 12 cites
- 2402.10891 Instruction Diversity Drives Generalization To Unseen Tasks(Feb 2024) 9 cites
- 2401.17167 Planning, Creation, Usage: Benchmarking LLMs for Comprehensive Tool Utilization in Real-World Complex Scenarios(Jan 2024) 14 cites
- 2401.15328 Equipping Language Models with Tool Use Capability for Tabular Data Analysis in Finance(Jan 2024) 1 cites
- 2401.12224 LLM4EDA: Emerging Progress in Large Language Models for Electronic Design Automation(Jan 2024) 13 cites
- 2401.02524 Comprehensive Exploration of Synthetic Data Generation: A Survey(Jan 2024) 18 cites
- 2401.00741 ToolEyes: Fine-Grained Evaluation for Tool Learning Capabilities of Large Language Models in Real-world Scenarios(Jan 2024) 34 cites
- 2311.15653 MoDS: Model-oriented Data Selection for Instruction Tuning(Nov 2023) 73 cites
- 2310.03731 MathCoder: Seamless Code Integration

*… (5,967 more characters — see results.json for full text)*

---

### 9. xRouter: Training Cost-Aware LLMs Orchestration System via Reinforcement Learning
**URL:** https://arxiv.org/html/2510.08439v1
**Published:** 2025-10-09T00:00:00.000Z

xRouter: Training Cost-Aware LLMs Orchestration System via Reinforcement Learning

# xRouter: Training Cost-Aware LLMs Orchestration System via Reinforcement Learning

Cheng Qian1,2∗, Zuxin Liu1∗♢, Shirley Kokane1†♢, Akshara Prabhakar1†, Jielin Qiu1†, Haolin Chen1, Zhiwei Liu1, Heng Ji2, Weiran Yao1, Shelby Heinecke1, Silvio Savarese1, Caiming Xiong1, Huan Wang1 1Salesforce AI Research 2University of Illinois Urbana-Champaign ∗Co-first authors †Core contributors ♢Work done while at Salesforce AI Research

(October 9, 2025)

Abstract. Modern LLM deployments confront a widening cost–performance spectrum: premium models deliver strong reasoning but are expensive, while lightweight models are economical yet brittle on complex tasks. Static escalation rules and keyword heuristics under-utilize this spectrum and fail to adapt across task types. We present xRouter, a tool-calling–based routing system in which a learned router can either answer directly or invoke one or more external models. The router is trained end-to-end with reinforcement learning using an explicit, cost-aware reward that encodes cost–performance trade-offs, eliminating the need for hand-engineered routing rules. Our implementation encompasses the full reinforcement learning framework, including reward and cost accounting, as well as the deployment and evaluation pipelines. Across diverse benchmarks, xRouter achieves strong cost–performance trade-offs (e.g., substantial cost reductions at comparable task completion rates) and provides empirical insights into what reliably helps learned routing and what does not, ranging from model trainability to the difficulty of eliciting sophisticated orchestration behaviors in small open models. We hope these findings and our open implementation will serve as a practical substrate for advancing learned, cost-aware LLM orchestration. Code https://github.com/SalesforceAIResearch/xRouter

## 1 Introduction

The proliferation of large language models (LLMs) has turned single-model inference into a multi-model selection problem [11, 43, 53, 7, 49, 10, 26]. In practice, queries arrive with unpredictable difficulty and domain variation; no single model optimally spans this space given the steep gradient in capability [40], latency, and price [3]. Naïve strategies, such as “using expensive/bigger models for hard queries, the cheaper ones for easy queries” [48, 37, 41], are brittle; and hand-crafted routing trees [11] rarely transfer across domains, providers or evolving APIs. The result is a persistent gap between what deployments pay for and what they need on a per-request basis.

We approach routing as decision-making under uncertainty with explicit economic constraints. Our system, xRouter, trains a tool-calling router that can either respond directly or delegate to external models (and, when beneficial, coordinate multiple calls). Rather than encoding escalation logic by hand, we formulate routing as a reinforcement-learning problem with a cost-aware

*… (22,000 more characters — see results.json for full text)*

---

### 10. mukhal/ThinkPRM
**URL:** https://github.com/mukhal/thinkprm
**Published:** 2025-04-22T06:05:30.000Z

# Repository: mukhal/ThinkPRM

[TMLR] Process Reward Models That Think

- Stars: 83
- Forks: 6
- Watchers: 83
- Open issues: 1
- Primary language: Python
- Languages: Python (97.4%), ANTLR (1.7%), Shell (0.9%), Makefile
- Default branch: main
- Homepage: https://arxiv.org/abs/2504.16828
- Created: 2025-04-22T06:05:30Z
- Last push: 2025-11-29T01:27:14Z
- Contributors: 1 (top: mukhal)

---

# Process Reward Models That Think 🧠

 
 
 
 
 
 
 
 
 
 
 
 
 
 

 
 
 🎉 News •
 📖 Introduction 
 📄 Data Collection 

 
 
 ✨ Getting Started •
 🎈 Citation 
 
 

 

# 🎉News

- **[2025-07-3]** Gave a talk at Tsinghua university on ThinkPRM. Slides are [here](https://docs.google.com/presentation/d/1O7HIoQLFn6ACJgAwD-e_O8c643fQUSRqbjJjO4S4s2I/edit?usp=sharing).
- **[2025-07-2]** We have released code for running test-time scaling experiments with ThinkPRM!.
- **[2025-04-23]** Our [paper](https://arxiv.org/abs/2504.16828) is released on arxiv.
- **[2025-04-24]** Our synthetic verification CoTs used to train ThinkPRM on are now on [huggingface](https://huggingface.co/datasets/launch/thinkprm-1K-verification-cots).
- **[2025-04-25]** Our trained PRMs are released in two sizes: [1.5B](https://huggingface.co/launch/ThinkPRM-1.5B) and [14B](https://huggingface.co/launch/ThinkPRM-14B) finetuned from R1-Distill-Qwen models.
- **[2025-05-16]** To provide a balanced performance between 1.5B and 14B, we have upload [ThinkPRM-7B](https://huggingface.co/launch/ThinkPRM-7B), based on Deepseek-R1-Distill-Qwen-7B and finetuned on our data.

# 📖Introduction

We introduce ThinkPRM, a collection of generative long CoT process reward models. Our verifiers are obtained by finetuning reasoning models over 1K synthetic verification CoTs---filtered based on only on 8K process labels from PRM800K. The resulting verifiers outperform LLM-as-a-judge, discriminative PRMs, on most in- and out-of-domain setups. ThinkPRM enables scaling up verifier compute either in parallel or sequentially by thinking longer.

 
 
 

# 📑 Data Collection

ThinkPRM was trained on synthetic verification CoTs. This dataset contains 1,000 high-quality synthetic verification chains-of-thought (CoTs) designed for training generative Process Reward Models (PRMs), as used in the paper ["Process Reward Models that Think"](https://arxiv.org/abs/2504.16828). The goal was to create a data-efficient alternative to traditional PRM training which often requires extensive human annotation or expensive rollouts.

Each instance consists of a math problem, a corresponding multi-step solution prefix (sourced from PRM800K [Lightman et al., 2023]), and a detailed verification CoT generated by the [QwQ-32B-Preview](https://huggingface.co/Qwen/QwQ-32B-Preview). The verification CoT critiques each step of the solution prefix and provides a step-level correctness judgment (`\boxed{correct}` or `\boxed{incorrect}`).

To ensure high-quality synthetic CoTs, only chains where all step-level judgments matched the ground-truth human annotations

*… (6,802 more characters — see results.json for full text)*

---

### 11. [2512.15000] DreamPRM-Code: Function-as-Step Process Reward Model with Label Correction for LLM Coding
**URL:** https://arxiv.org/abs/2512.15000
**Published:** 2025-12-17T07:39:04.000Z

[2512.15000] DreamPRM-Code: Function-as-Step Process Reward Model with Label Correction for LLM Coding

# Computer Science > Machine Learning

arXiv:2512.15000 (cs)

[Submitted on 17 Dec 2025]

# Title:DreamPRM-Code: Function-as-Step Process Reward Model with Label Correction for LLM Coding

Authors: Ruiyi Zhang, Peijia Qin, Qi Cao, Pengtao Xie

View PDF HTML (experimental)

> Abstract:Process Reward Models (PRMs) have become essential for improving Large Language Models (LLMs) via test-time scaling, yet their effectiveness in coding remains limited due to the lack of meaningful step decompositions in code and the noise of Monte-Carlo-generated partial labels. We propose DreamPRM-Code, a coding-focused PRM that treats functions as reasoning steps using a Chain-of-Function prompting strategy to induce modular code generation, enabling PRM training and application analogous to mathematical reasoning tasks. To address label noise, DreamPRM-Code introduces a meta-learning-based correction mechanism that leverages clean final-solution unit-test labels and performs bi-level optimization to refine intermediate labels. Applying on test-time scaling, DreamPRM-Code achieved state-of-the-art performance on LiveCodeBench with 80.9 pass@1 rate, surpassing OpenAI o4-mini.

arXiv-issued DOI via DataCite

| Subjects: | Machine Learning (cs.LG); Artificial Intelligence (cs.AI); Computation and Language (cs.CL) |
| --- | --- |
| Cite as: | arXiv:2512.15000 [cs.LG] |
| (or arXiv:2512.15000v1 [cs.LG] for this version) |

## Submission history

From: Ruiyi Zhang [view email] [v1] Wed, 17 Dec 2025 01:11:35 UTC (158 KB)

Full-text links:

## Access Paper:

Current browse context:

cs.LG

< prev| next >

Change to browse by:

### References & Citations

- Google Scholar
- Semantic Scholar

export BibTeX citation

### Bookmark

Bibliographic Tools

# Bibliographic and Citation Tools

Bibliographic Explorer Toggle

Bibliographic Explorer (What is the Explorer?)

Connected Papers Toggle

Connected Papers (What is Connected Papers?)

Litmaps Toggle

Litmaps (What is Litmaps?)

scite.ai Toggle

scite Smart Citations (What are Smart Citations?)

Code, Data, Media

# Code, Data and Media Associated with this Article

alphaXiv Toggle

alphaXiv (What is alphaXiv?)

Links to Code Toggle

CatalyzeX Code Finder for Papers (What is CatalyzeX?)

DagsHub Toggle

DagsHub (What is DagsHub?)

GotitPub Toggle

Gotit.pub (What is GotitPub?)

Huggingface Toggle

Hugging Face (What is Huggingface?)

Links to Code Toggle

Papers with Code (What is Papers with Code?)

ScienceCast Toggle

ScienceCast (What is ScienceCast?)

Demos

# Demos

Replicate Toggle

Replicate (What is Replicate?)

Spaces Toggle

Hugging Face Spaces (What is Spaces?)

Spaces Toggle

TXYZ.AI (What is TXYZ.AI?)

Related Papers

# Recommenders and Search Tools

Link to Influence Flower

Influence Flower (What are Influence Flowers?)

Core recommender toggle

CORE Recommender (What is CORE?)

IArxiv recommender toggle

IArxi

*… (612 more characters — see results.json for full text)*

---

### 12. [2504.16828] Process Reward Models That Think
**URL:** https://arxiv.org/abs/2504.16828
**Published:** 2025-04-23T05:07:07.000Z

[2504.16828] Process Reward Models That Think

# Computer Science > Machine Learning

arXiv:2504.16828 (cs)

[Submitted on 23 Apr 2025 (v1), last revised 8 Dec 2025 (this version, v5)]

# Title:Process Reward Models That Think

View PDF HTML (experimental)

> Abstract:Step-by-step verifiers -- also known as process reward models (PRMs) -- are a key ingredient for test-time scaling. PRMs require step-level supervision, making them expensive to train. This work aims to build data-efficient PRMs as verbalized step-wise reward models that verify every step in the solution by generating a verification chain-of-thought (CoT). We propose ThinkPRM, a long CoT verifier fine-tuned on orders of magnitude fewer process labels than those required by discriminative PRMs. Our approach capitalizes on the inherent reasoning abilities of long CoT models, and outperforms LLM-as-a-Judge and discriminative verifiers -- using only 1% of the process labels in PRM800K -- across several challenging benchmarks. Specifically, ThinkPRM beats the baselines on ProcessBench, MATH-500, and AIME '24 under best-of-N selection and reward-guided search. In an out-of-domain evaluation on a subset of GPQA-Diamond and LiveCodeBench, our PRM surpasses discriminative verifiers trained on the full PRM800K by 8% and 4.5%, respectively. Lastly, under the same token budget, ThinkPRM scales up verification compute more effectively compared to LLM-as-a-Judge, outperforming it by 7.2% on a subset of ProcessBench. Our work highlights the value of generative, long CoT PRMs that can scale test-time compute for verification while requiring minimal supervision for training. Our code, data, and models are released at this https URL.

arXiv-issued DOI via DataCite

| Comments: |
| --- |
| Subjects: | Machine Learning (cs.LG); Artificial Intelligence (cs.AI); Computation and Language (cs.CL) |
| Cite as: | arXiv:2504.16828 [cs.LG] |
| (or arXiv:2504.16828v5 [cs.LG] for this version) |

## Submission history

From: Muhammad Khalifa [view email] [v1] Wed, 23 Apr 2025 15:44:54 UTC (251 KB) [v2] Sun, 18 May 2025 01:23:04 UTC (240 KB) [v3] Tue, 24 Jun 2025 03:05:02 UTC (236 KB) [v4] Thu, 25 Sep 2025 04:09:09 UTC (256 KB) [v5] Mon, 8 Dec 2025 06:50:53 UTC (276 KB)

Full-text links:

## Access Paper:

### Current browse context:

cs.LG

< prev| next >

Change to browse by:

### References & Citations

- Google Scholar
- Semantic Scholar

export BibTeX citation

### Bookmark

Bibliographic Tools

# Bibliographic and Citation Tools

Bibliographic Explorer Toggle

Bibliographic Explorer (What is the Explorer?)

Connected Papers Toggle

Connected Papers (What is Connected Papers?)

Litmaps Toggle

Litmaps (What is Litmaps?)

scite.ai Toggle

scite Smart Citations (What are Smart Citations?)

Code, Data, Media

# Code, Data and Media Associated with this Article

alphaXiv Toggle

alphaXiv (What is alphaXiv?)

Links to Code Toggle

CatalyzeX Code Finder for Papers (What is CatalyzeX?)

DagsHub Toggle

DagsHub (Wha

*… (1,166 more characters — see results.json for full text)*

---

### 13. llmrouter/models/hybrid_llm/README.md at main · ulab-uiuc/LLMRouter
**URL:** https://github.com/ulab-uiuc/LLMRouter/blob/main/llmrouter/models/hybrid_llm/README.md

# File: ulab-uiuc/LLMRouter/llmrouter/models/hybrid_llm/README.md

- Repository: ulab-uiuc/LLMRouter | LLMRouter: An Open-Source Library for LLM Routing | 2K stars | Python
- Branch: main

```md
# Hybrid LLM Router

## Overview

The **Hybrid LLM Router** intelligently balances between a small (cheap) and large (expensive) model by learning to predict when the small model's quality will be sufficient. It uses MLP regression to estimate the quality gap and makes routing decisions based on cost-quality trade-offs.

## Paper Reference

Based on the **Hybrid LLM** approach:

- **[Hybrid LLM: Cost-Efficient and Quality-Aware Query Routing](https://arxiv.org/abs/2404.14618)**
  - Ding, Y., et al. (2024). arXiv:2404.14618.
  - Proposes MLP-based quality gap prediction for cost-aware routing.

- **Key Idea**: Route to small model when quality gap is small, large model otherwise.

## How It Works

### Architecture

```
Query → Longformer Embedding → MLP Regressor → Quality Gap Score → Routing Decision
 ↓
 (Compare to threshold)
 ↓
 Small Model (score ≥ threshold)
 Large Model (score < threshold)
```

### Routing Modes

The router supports three decision strategies:

#### 1. Deterministic Mode
- Label: `y = 1` if `q(Small) ≥ q(Large)`, else `y = 0`
- Decision: Route to small if `score ≥ 0.5`

#### 2. Probabilistic Mode
- Label: `y = sigmoid((q(Small) - q(Large)) / tau)`
- Soft labels based on quality gap
- More nuanced than hard binary

#### 3. Transformed Mode
- Find optimal threshold `t*` that maximizes label separation
- Label: `y = 1` if `q(Small) ≥ q(Large) - t*`
- Automatically balanced classes

## Configuration Parameters

### Router Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `router_mode` | str | `"deterministic"` | Mode: `"deterministic"`, `"probabilistic"`, or `"transformed"` |
| `router_tau` | float | `0.1` | Temperature for probabilistic mode |
| `router_threshold` | float | `0.5` | Decision threshold |

### MLP Hyperparameters (`hparam`)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `hidden_layer_sizes` | list[int] | `[128, 64]` | MLP architecture |
| `activation` | str | `"relu"` | Activation function |
| `solver` | str | `"adam"` | Optimizer |
| `max_iter` | int | `300` | Training iterations |

## CLI Usage

The Hybrid LLM Router can be used via the `llmrouter` command-line interface:

### Training

```bash
# Train the Hybrid LLM router
llmrouter train --router hybrid_llm --config configs/model_config_train/hybrid_llm.yaml

# Train with quiet mode
llmrouter train --router hybrid_llm --config configs/model_config_train/hybrid_llm.yaml --quiet
```

### Inference

```bash
# Route a single query
llmrouter infer --router hybrid_llm --config configs/model_config_test/hybrid_llm.yaml \
    --query "What is photosynthesis?"

# Route queries from a file
llmrouter infer --router hybrid_llm --config configs/model_config_test/hybrid_llm.yaml \

*… (2,800 more characters — see results.json for full text)*

---

### 14. Difficulty-Aware Agent Orchestration in LLM-Powered Workflows
**URL:** https://arxiv.org/html/2509.11079v1

Difficulty-Aware Agent Orchestration in LLM-Powered Workflows

# Difficulty-Aware Agent Orchestration in LLM-Powered Workflows

Jinwei Su, Yinghui Xia, Qizhen Lan, Xinyuan Song Yang Jingsong, Lewei He,Tianyu Shi

###### Abstract

Large Language Model (LLM)-based agentic systems have shown strong capabilities across various tasks. However, existing multi-agent frameworks often rely on static or task-level workflows, which either over-process simple queries or underperform on complex ones, while also neglecting the efficiency-performance trade-offs across heterogeneous LLMs. To address these limitations, we propose Difficulty-Aware Agentic Orchestration (DAAO), a dynamic framework that adapts workflow depth, operator selection, and LLM assignment based on the difficulty of each input query. DAAO comprises three interdependent modules: a variational autoencoder (VAE) for difficulty estimation, a modular operator allocator, and a cost- and performance-aware LLM router. By leveraging heterogeneous LLMs and dynamically tailoring workflows, DAAO enables fine-grained, query-specific reasoning strategies. DAAO outperforms prior multi-agent systems in both accuracy and inference efficiency across six benchmarks. We will release our code and implementation details upon publication.

Figure 1: The overall framework of our proposed DAAO.

## Introduction

Large Language Model (LLM)-based agents (Richards and et al. 2023; Nakajima 2023; Reworkd 2023) have exhibited remarkable capabilities across a wide spectrum of tasks, including question answering (Zhu et al. 2024), data analysis (Hong et al. 2024; Li et al. 2024), decision-making (Song et al. 2023), code generation (Shinn, Labash, and Gopinath 2023) and web navigation (Deng et al. 2024). Building upon the success of single agents, recent advancements reveal that organizing multiple LLM-based agents into structured agentic workflows can significantly enhance task performance. In such workflows, agents can interact either cooperatively (Zhuge et al. 2024) or competitively (Zhao et al. 2023) depending on the task context. These multi-agent systems can overcome the cognitive and functional limitations of individual models (Du et al. 2023; Liang et al. 2023; Wang et al. 2023b; Jiang, Ren, and Lin 2023; Wu et al. 2023; Zhang et al. 2024a), thereby exhibiting collective intelligence similar to human collaboration in a society of agents.

In recent years, the research community has focused on automating multi-agent system design. For instance, DsPy (Khattab et al. 2023) and EvoPrompting (Guo et al. 2023) automate prompt optimization, GPTSwarm (Zhuge et al. 2024) optimizing inter-agent communication, and EvoAgent (Yuan et al. 2024) self-evolving agent profiling. However, these systems are often constrained by limited search spaces and rigid representation paradigms, resulting in marginal performance gains and limited adaptability to diverse task requirements. Subsequently, ADAS (Hu, Lu, and Clune 2024) and AFlow (Zh

*… (21,879 more characters — see results.json for full text)*

---

### 15. [2604.00594v1] Agent psychometrics: Task-level performance prediction in agentic coding benchmarks
**URL:** https://arxiv.org/abs/2604.00594v1
**Published:** 2026-04-01T20:07:29.000Z

[2604.00594v1] Agent psychometrics: Task-level performance prediction in agentic coding benchmarks

# Computer Science > Artificial Intelligence

arXiv:2604.00594v1 (cs)

[Submitted on 1 Apr 2026]

# Title:Agent psychometrics: Task-level performance prediction in agentic coding benchmarks

View PDF HTML (experimental)

> Abstract:As the focus in LLM-based coding shifts from static single-step code generation to multi-step agentic interaction with tools and environments, understanding which tasks will challenge agents and why becomes increasingly difficult. This is compounded by current practice: agent performance is typically measured by aggregate pass rates on benchmarks, but single-number metrics obscure the diversity of tasks within a benchmark. We present a framework for predicting success or failure on individual tasks tailored to the agentic coding regime. Our approach augments Item Response Theory (IRT) with rich features extracted from tasks, including issue statements, repository contexts, solutions, and test cases, and introduces a novel decomposition of agent ability into LLM and scaffold ability components. This parameterization enables us to aggregate evaluation data across heterogeneous leaderboards and accurately predict task-level performance for unseen benchmarks, as well as unseen LLM-scaffold combinations. Our methods have practical utility for benchmark designers, who can better calibrate the difficulty of their new tasks without running computationally expensive agent evaluations.

arXiv-issued DOI via DataCite

| Subjects: | Artificial Intelligence (cs.AI) |
| --- | --- |
| Cite as: | arXiv:2604.00594 [cs.AI] |
| (or arXiv:2604.00594v1 [cs.AI] for this version) |

## Submission history

From: Daria Kryvosheieva [view email] [v1] Wed, 1 Apr 2026 07:59:59 UTC (1,032 KB)

Full-text links:

## Access Paper:

Current browse context:

cs.AI

< prev| next >

Change to browse by:

### References & Citations

- Google Scholar
- Semantic Scholar

export BibTeX citation

### Bookmark

Bibliographic Tools

# Bibliographic and Citation Tools

Bibliographic Explorer Toggle

Bibliographic Explorer (What is the Explorer?)

Connected Papers Toggle

Connected Papers (What is Connected Papers?)

Litmaps Toggle

Litmaps (What is Litmaps?)

scite.ai Toggle

scite Smart Citations (What are Smart Citations?)

Code, Data, Media

# Code, Data and Media Associated with this Article

alphaXiv Toggle

alphaXiv (What is alphaXiv?)

Links to Code Toggle

CatalyzeX Code Finder for Papers (What is CatalyzeX?)

DagsHub Toggle

DagsHub (What is DagsHub?)

GotitPub Toggle

Gotit.pub (What is GotitPub?)

Huggingface Toggle

Hugging Face (What is Huggingface?)

ScienceCast Toggle

ScienceCast (What is ScienceCast?)

Demos

# Demos

Replicate Toggle

Replicate (What is Replicate?)

Spaces Toggle

Hugging Face Spaces (What is Spaces?)

Spaces Toggle

TXYZ.AI (What is TXYZ.AI?)

Related Papers

# Recommenders and Search Tools

Link to Influence Flower

Influence F

*… (675 more characters — see results.json for full text)*

---
