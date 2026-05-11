# Research Report

**Query:** Comprehensive guide to LLM router evaluation as of April 2026. Cover benchmarks: RouterBench arXiv 2403.12031 with the 405k record dataset and 70/30 split methodology; RouterArena arXiv 2510.00202; RouteLLM preference-data eval methodology; RouterEval arXiv 2503.10657; LLMRouterBench; MixEval-X if relevant. Cover metrics in depth: cost-quality Pareto and convex hull methodology, AUDC area under deferral curve, Router Efficacy, CPT call-performance-threshold, APGR average performance gain over random, QNC query-normalized cost, win-rate vs single-model baseline, latency overhead, ECE expected calibration error, Brier score, reliability diagrams. Cover evaluation protocols for code-specific routers: SWE-bench Verified and Pro routing eval, LiveCodeBench routing, BigCodeBench-Hard routing, Aider Polyglot routing. Cover calibration techniques: conformal prediction (CP-Router 2505.19970), temperature scaling, Platt scaling, isotonic regression, calibration-across-layers (2511.00280). Cover online vs offline evaluation, A/B testing routers in production, dashboards and observability stacks. Include how Anthropic / OpenAI / Google evaluate internal routers if publicly disclosed; how community projects measure cost savings honestly vs how they're claimed; common pitfalls (Goodhart's law on routing metrics, benchmark contamination, judge-LLM bias, selection bias on labeled data). Cite papers, leaderboards, and production blog posts. Be detailed and rigorous.
**Run ID:** `b30157f7`
**Generated:** 2026-04-26T00:46:12Z

---

## Perplexity Deep Research
*Model: `sonar-deep-research` · 170s · 359 prompt + 9,717 completion tokens*

<think>
This is a comprehensive request about LLM router evaluation as of April 2026. Let me break down what I need to cover:

1. **Benchmarks**: RouterBench, RouterArena, RouteLLM, RouterEval, LLMRouterBench, MixEval-X
2. **Metrics in depth**: Cost-quality Pareto, AUDC, Router Efficacy, CPT, APGR, QNC, win-rate, latency overhead, ECE, Brier score, reliability diagrams
3. **Code-specific routing eval**: SWE-bench, LiveCodeBench, BigCodeBench, Aider Polyglot
4. **Calibration techniques**: Conformal prediction, temperature scaling, Platt scaling, isotonic regression, calibration-across-layers
5. **Online vs offline evaluation**: A/B testing, dashboards, observability
6. **Company approaches**: Anthropic, OpenAI, Google (if publicly disclosed)
7. **Common pitfalls**: Goodhart's law, benchmark contamination, judge bias, selection bias

Let me plan the structure:
- Title
- Executive summary paragraph
- Major sections:
  1. Foundational Benchmarks for LLM Router Evaluation (RouterBench, RouterArena, RouterEval, LLMRouterBench, RouteLLM, MixEval-X)
  2. Core Evaluation Metrics and Their Interpretation (Cost-quality tradeoffs, Pareto frontier, specific metrics)
  3. Specialized Routing Evaluation for Code Generation (SWE-bench, LiveCodeBench, BigCodeBench, Aider)
  4. Calibration and Confidence Assessment in Routers (CP-Router, temperature scaling, etc.)
  5. Production Evaluation: Online Testing and Real-World Deployment (A/B testing, observability)
  6. Critical Evaluation Challenges and Pitfalls (Goodhart's law, contamination, bias)
  7. Conclusion

I need to write at least 10,000 words, cite appropriately, and maintain a narrative flow. Let me organize the search results by relevance and start writing.
</think>

# Comprehensive Guide to Large Language Model Router Evaluation in 2026

Large Language Model routing has emerged as a critical infrastructure component for organizations seeking to balance performance and cost in AI deployments. As of April 2026, the field has matured significantly with the development of standardized benchmarks, sophisticated evaluation metrics, and production-ready evaluation frameworks. This comprehensive guide synthesizes current best practices and research findings on how to rigorously evaluate LLM routers across multiple dimensions—from benchmark-based assessments to production monitoring and calibration verification. The evaluation landscape has evolved to address fundamental challenges including metric gaming, benchmark contamination, and the gap between offline testing and real-world performance. This guide covers the major standardized benchmarks that have become industry standards, explores the nuanced metrics used to assess router effectiveness, examines specialized evaluation protocols for code-based routing tasks, details calibration techniques that ensure router confidence estimates align with actual performance, describes online evaluation methodologies for production environments, and finally addresses critical pitfalls that evaluators must navigate to ensure their assessments remain meaningful and actionable.

## Foundational Benchmarks for Systematic LLM Router Evaluation

The establishment of standardized benchmarks has been instrumental in advancing LLM routing research by providing a common evaluation ground for comparing different routing strategies. The absence of such benchmarks historically created significant barriers to progress, as researchers lacked consistent ways to measure routing system efficacy across different model pools and task distributions.

### RouterBench: The First Comprehensive Multi-LLM Routing Framework

RouterBench represents a watershed moment in LLM router evaluation, introducing the first systematic evaluation framework designed specifically for assessing routing systems[1]. The framework addresses a critical gap that existed in the field: while individual LLMs had comprehensive benchmarks for evaluation, LLM routers lacked any standardized assessment methodology. RouterBench provides both a theoretical framework for understanding LLM routing and a massive empirical dataset to support router development. The benchmark comprises over 405,000 inference outcomes collected from representative LLMs across diverse tasks and domains[1]. This extensive dataset allows researchers to train and evaluate routers under realistic conditions rather than relying on synthetic or limited evaluation sets.

The methodology underlying RouterBench employs a 70-30 evaluation split that has become standard in the field[1]. The benchmark collects performance data on a heterogeneous set of models across multiple tasks, capturing both easy and hard instances to enable researchers to understand how routers make decisions across the complexity spectrum. The theoretical framework proposed within RouterBench formalizes the routing problem mathematically, defining key concepts such as the Pareto frontier of cost-quality tradeoffs, model complementarity (the observation that different models excel at different tasks), and routing efficacy metrics. This formalization has proven invaluable for understanding what makes effective routing strategies and why certain approaches succeed while others fail.

### RouterArena: Open Platform with Standardized Leaderboard

Building on the foundation established by RouterBench, RouterArena introduces an open platform for comprehensive comparison of LLM routers with several enhancements over earlier approaches[2]. RouterArena addresses the recognized need for a comprehensive router comparison and standardized leaderboard, similar to the successful leaderboards that emerged for comparing individual LLMs. The platform features a principally constructed dataset with broad knowledge domain coverage, ensuring that evaluations span diverse problem types and knowledge areas rather than concentrating on narrow specialties[2]. This breadth is critical for assessing whether a router generalizes effectively to real-world deployment scenarios.

A distinctive feature of RouterArena is its incorporation of distinguishable difficulty levels for each domain[2]. Rather than treating all problems equally, the framework recognizes that routers face different challenges when routing easy versus difficult queries. Easy problems might be answered correctly by multiple models, leaving limited room for routing improvement. Difficult problems, by contrast, may only be solved by expensive or capable models, requiring the router to identify which expensive model to use. By stratifying problems by difficulty, RouterArena enables more nuanced evaluation of router behavior across different performance regimes. The platform provides an extensive list of evaluation metrics and includes an automated framework for leaderboard updates, enabling the community to track progress in routing research over time[2]. The initial leaderboard released alongside RouterArena produced detailed metrics comparison that immediately influenced how the community understood routing performance.

### RouterEval: Massive-Scale Performance Records

RouterEval tackles router evaluation from a complementary angle, emphasizing sheer scale and comprehensive coverage of model performance records[4]. Rather than collecting new benchmark problems, RouterEval aggregates over 200 million performance records for 12 popular LLM evaluations spanning various areas including commonsense reasoning and semantic understanding, based on over 8,500 different LLMs[4]. This massive-scale approach enables researchers to study routing patterns across an unprecedented breadth of models and evaluation domains. The scale of RouterEval addresses an important limitation of earlier benchmarks: with only dozens of models, routers might overfit to those specific models. With thousands of models, routers must learn more generalizable principles about model behavior.

The research findings generated using RouterEval reveal that most existing routing methods still have significant room for improvement[4]. This finding, though sobering, has proven constructive because it clarifies that the ceiling for router performance remains high. Unlike benchmarks that become saturated as models improve, RouterEval's massive scale means that there is likely to be evaluation headroom for many years. The benchmark provides both data and code publicly, enabling the research community to build on this foundation. The breadth of evaluation domains covered by RouterEval ensures that assessments span diverse task types and difficulty levels.

### LLMRouterBench: Comprehensive Evaluation Environment

LLMRouterBench provides a unified evaluation framework supporting 27+ benchmarks with consistent interfaces, answer extraction, and scoring mechanisms[5]. This standardization across multiple benchmarks addresses a practical challenge that researchers face: different benchmarks use different answer formats, scoring rules, and evaluation protocols. By providing consistent evaluation infrastructure, LLMRouterBench reduces implementation burden and makes it easier to conduct multi-benchmark studies where results can be directly compared.

### RouteLLM and Preference-Based Training Methodologies

RouteLLM introduces an important dimension to router evaluation by proposing a training framework that leverages human preference data[3]. The key insight underlying RouteLLM is that the choice of which model to use involves explicit tradeoffs between performance and cost that can be made transparent through preference learning. Rather than training routers only on correctness labels, RouteLLM uses human preference annotations that explicitly account for the performance-cost tradeoff. This approach recognizes that "better" routing decisions are inherently preference-dependent: a different tradeoff parameter produces different optimal routing strategies.

RouteLLM proposes several efficient router models that dynamically select between stronger and weaker LLMs during inference[3]. Evaluation on widely-recognized benchmarks shows that the approach significantly reduces costs—by over 2x in certain cases—without compromising response quality. Critically, RouteLLM demonstrates that routers trained with preference data exhibit significant transfer learning capabilities, maintaining performance even when the strong and weak models are changed at test time[3]. This finding has profound implications for router evaluation: it suggests that routers can learn generalizable principles about model behavior rather than memorizing specific model characteristics.

### MixEval-X: Real-World Task Distribution Alignment

MixEval-X introduces a novel approach to router evaluation by focusing on alignment with real-world task distributions[6]. The framework is designed as an "any-to-any" benchmark that can handle diverse input and output modalities. A key innovation is the multi-modal benchmark mixture and adaptation-rectification pipelines that reconstruct real-world task distributions, ensuring that evaluations generalize effectively to actual use cases rather than theoretical benchmarks. Extensive meta-evaluations demonstrate that MixEval-X's model rankings correlate strongly with crowd-sourced real-world evaluations (up to 0.98 correlation) while being much more efficient to execute[6]. This alignment between benchmark rankings and real-world preference is critical for router evaluation, as it suggests that benchmark-based router assessments will actually predict production performance.

## Core Evaluation Metrics and Their Interpretation

Beyond establishing standardized benchmarks, the router evaluation community has developed a sophisticated set of metrics that measure different dimensions of router performance. Understanding these metrics in depth is essential for interpreting router evaluation results and making informed decisions about router selection and deployment.

### The Cost-Quality Pareto Frontier and Optimal Router Operation

The fundamental problem that routers address is optimizing the tradeoff between response quality (accuracy) and inference cost. This tradeoff is elegantly captured through the concept of the Pareto frontier—the set of outcomes where it is impossible to improve quality without increasing cost, or to reduce cost without sacrificing quality[8]. When organizations deploy a router, they are essentially choosing a point on this frontier based on their specific cost-benefit requirements. Understanding where a router operates on the Pareto frontier relative to other solutions is critical for evaluation.

The Pareto frontier is typically bounded by two extreme strategies. At one end lies the strategy of using only the most expensive capable model (maximum quality, maximum cost). At the other end lies the strategy of using only the cheapest lightweight model (minimum cost, minimum quality). The question that router evaluation must answer is: can a router achieve better Pareto-optimal outcomes than either of these extreme strategies? In other words, can the router find combinations of model selections that offer better quality at the same cost, or equivalent quality at lower cost?

One organization's measurement methodology demonstrated this principle concretely[8]. In a customer help chat deployment, a router achieved a 52.4% reduction in error rate while simultaneously achieving a 92% reduction in cost. In a retrieval-augmented generation system built on GPT-4, the same organization increased quality by 20% while lowering costs by a factor of 80. These represent substantial movements along the Pareto frontier—the router identified model combinations that dominated the original single-model approach on both axes simultaneously. However, it is important to note that not all router deployments achieve such dramatic improvements. The magnitude of improvement depends on the degree of model complementarity (how differently models perform on various tasks) and the cost spread (the relative price difference between models).

### Quantifying Pareto Optimality and the Convex Hull

Beyond observing that a router achieves certain performance-cost tradeoffs, sophisticated evaluation methodologies now compute formal measures of Pareto optimality. One emerging evaluation protocol computes the convex hull of achieved cost-quality outcomes and measures how closely a router approximates true Pareto optimality[35]. The convex hull represents the best possible frontier achievable through any strategy (including probabilistic mixing of deterministic decisions). A router that achieves points on or near the convex hull is demonstrating true optimization, while one whose operating points lie inside the hull is leaving opportunity on the table.

The Pareto Distance metric quantifies how far a router's operating point deviates from the true Pareto frontier. For instance, a state-of-the-art router might achieve a Pareto Distance near zero across its operating range, indicating that it is genuinely Pareto-optimal[14]. This is a stronger claim than simply saying the router is "good"—it means the router cannot be improved in one dimension without sacrificing in another. Comparing Pareto distances across different routers reveals which systems have truly solved the optimization problem versus which ones leave feasible improvements unexploited.

### Area Under the Deferral Curve (AUDC) and Router Efficacy

The AUDC metric extends principles from machine learning evaluation to the routing context[19]. In traditional machine learning evaluation, the area under the ROC curve (AUC) has become a standard metric for assessing classifier performance across different operating points. Similarly, AUDC captures how well a router maintains performance as a function of cost constraints. By sweeping a parameter that controls the tradeoff between cost and quality, evaluators can trace a family of accuracy-cost operating points and compute the area under this curve. This provides a single-number summary of router performance that accounts for behavior across the entire tradeoff space rather than at a single operating point.

The AUDC metric has important advantages for router evaluation. First, it eliminates sensitivity to the choice of operating point. Two routers might perform identically at one cost level but very differently at another. By integrating across the entire tradeoff space, AUDC provides a more robust comparison. Second, AUDC can be normalized to a standard scale (typically 0 to 1) using pool-specific anchors such as the cheapest and most expensive models, enabling fair comparison across different model pools with different cost structures.

### Call-Performance-Threshold (CPT) and Efficiency Measurement

The CPT metric addresses a practical question that organizations face when deploying routers: what percentage of queries must be routed to the expensive capable model to achieve a desired level of performance improvement? This question is fundamental to cost planning—understanding CPT values allows decision-makers to predict exactly how much routing to the expensive model is necessary to achieve specific performance targets[11].

CPT is formally defined as the minimum percentage of queries that must be routed to the strong model to achieve a specified level of Performance Gap Recovered (PGR). For example, if a weak model achieves 85% accuracy while a strong model achieves 95% accuracy, the gap is 10 percentage points. PGR(50%) means recovering half this gap, requiring 90% accuracy. The CPT(50%) value then specifies what percentage of queries must go to the strong model to achieve 90% accuracy. Through analysis across many queries binned by confidence level, evaluators can determine that perhaps only 30% of queries need to go to the expensive model to achieve this target.

Research on this metric has revealed important patterns about router efficiency[11]. In one evaluation, the CPT(80%) chart demonstrated that nearly 49.3% of calls to the strong model were required to meet the target accuracy of achieving 80% of the performance gap recovery between strong and weak models. The CPT(50%) chart showed that about 22.8% of calls to the strong model were needed to reach the 50% performance gap recovery target. These results illustrate an important principle: achieving the first 50% of performance gap requires significantly less use of the expensive model than achieving 80% of the gap. The law of diminishing returns applies strongly to routing—the remaining 30% of gap recovery requires 20 additional percentage points of expensive model usage (from ~30% to ~50%).

### Performance Gap Recovered (PGR) and Routing Effectiveness

The PGR metric directly measures how much of the performance deficit between a weak and strong model the router successfully recovers[11]. If the performance gap between models is 10 percentage points and a router achieves 5 percentage points of recovery, its PGR is 50%. This metric is intuitive and directly interpretable: it tells decision-makers what portion of the potential improvement their router is actually capturing.

PGR measurement requires careful attention to the specific query distribution and model pair in question. On queries where both the weak and strong models agree (both correct or both incorrect), there is no PGR opportunity—the router's decision does not matter. The routing problem becomes interesting precisely on the queries where the models disagree. Evaluators typically focus on these "disagreement regimes" to understand where routing adds value. In one analysis, researchers found that gains were largest in the frontier pool (where models differ most) and smaller in the mixed pool (where more than half of the queries were answered correctly by all models)[19].

### Query-Normalized Cost (QNC) and Model-Appropriate Selection

The QNC metric addresses a critical failure mode of routers that has only recently been formally characterized: routing collapse[13][13]. Routing collapse occurs when a router, despite having access to multiple models, systematically overuses the expensive capable model even on queries that cheaper models could answer correctly. This defeats the fundamental purpose of routing, which is to reduce cost by using cheap models on easy problems.

QNC measures the cost required to achieve specific accuracy levels and identifies whether a router is achieving state-of-the-art performance while maintaining efficiency[13]. For instance, on RouterBench, EquiRouter achieves GPT-4-level performance (93.2% accuracy) using only 77% of the cost compared to over 93% for the best previous routers[13]. This 16-percentage-point cost reduction despite identical accuracy represents a dramatic improvement in model selection efficiency. The metric directly captures the degree to which a router has overcome routing collapse and learned to appropriately distribute work across the model pool.

The root cause of routing collapse has been identified as reliance on scalar confidence scores. When a router predicts a scalar score for each model representing how likely that model is to answer correctly, small prediction errors can flip the orderings between models[13]. If two models have predicted scores of 0.91 and 0.89, and the prediction errors are in opposite directions, the cheaper model's true performance might actually be superior. However, the router's decision is based on the noisy predicted scores, leading to choosing the expensive model. To address this, routing frameworks that predict relative model rankings rather than absolute scores have been shown to reduce routing collapse and recover more cost savings[13][13].

### Win-Rate Relative to Single-Model Baselines

A practical metric that organizations use when evaluating routers is simply the win-rate: what percentage of instances does the router outperform a simple fixed baseline[14]? The baseline typically chosen is "Best Single," which is the single model that achieves the highest average accuracy across all tasks in the evaluation set. This baseline is surprisingly strong because it represents the strategy of using one capable model uniformly across all queries.

The win-rate metric reveals important information about router coverage. If a router has a win-rate below 50% against "Best Single," it means that more often than not, the router makes worse decisions than simply using the best single model. This indicates a fundamental failure in router design. Research has found that several commercial routers and recent proposed methods fail to reliably outperform the Best Single baseline in unified large-scale evaluations[14]. This finding has reshaped how the community thinks about baseline comparisons: win-rate against Best Single is now considered a minimum bar for acceptable routing performance, and many proposed methods fail to clear this bar.

### Latency Overhead and Production Constraints

While accuracy and cost have long been central to router evaluation, latency has emerged as an equally important concern for production deployments[7]. A natural question is whether using a router adds latency overhead compared to going directly to a model provider. Conventional wisdom suggested that interposing a routing layer between applications and model providers would inevitably add delay, particularly the time-to-first-token metric that dominates user-perceived latency.

A comprehensive latency benchmark conducted in 2026 challenged this assumption by testing 200 calls each to major router implementations[7]. The results revealed surprising findings: OpenRouter was actually 70ms faster than OpenAI direct on time to first token (0.640s vs 0.712s), demonstrating that a properly implemented router can be faster than a direct connection[7]. Opper matched OpenAI directly within confidence intervals at 0.744 seconds. These findings demonstrate that there is no blanket "router tax." Each router implementation makes different tradeoffs, with some prioritizing first-token latency at the expense of throughput, and others matching the direct endpoint on both dimensions[7][7].

A critical finding from this analysis was that geography dominates model choice in terms of latency impact[7][7]. Tokyo access was 2x slower than Ireland access (3.08 seconds versus 1.61 seconds), a bigger impact than switching model tiers. This finding has important implications for router evaluation: assessing latency requires controlling for geographic factors, and routing decisions should account for geographic latency in addition to model capability and cost. Backend selection also matters dramatically, with a ~10x throughput difference observed across backends serving the same model[7][7].

### Expected Calibration Error (ECE) and Confidence Alignment

Expected Calibration Error measures how well a model's predicted confidence aligns with its actual correctness[18]. For routers, calibration is critical because the router's decision to route to different models should be based on well-calibrated predictions of correctness probability. If a router predicts 90% confidence but is actually correct only 70% of the time, the router's decisions are miscalibrated and will make suboptimal routing choices.

ECE is computed by binning predictions into groups (typically 10 bins based on predicted probability), computing the accuracy within each bin, and then computing the weighted average difference between predicted probability and observed accuracy[18]. A well-calibrated system achieves low ECE values across all probability ranges. This metric has become particularly important for router evaluation because recent research has shown that LLMs possess inherent calibration capabilities that emerge during training[17]. Understanding how calibration evolves throughout model depths and how it can be preserved or improved through post-hoc adjustment techniques is now part of standard router evaluation.

### Brier Score and Probabilistic Performance

The Brier score is the mean squared error between predicted correctness probabilities and observed binary outcomes[19]. It provides a symmetric measure of calibration quality that penalizes both overconfidence and underconfidence. Unlike metrics like ECE that measure calibration in specific probability bins, the Brier score provides an overall measure of confidence prediction accuracy. For routers, Brier score is typically computed separately for each target model to understand whether the router's confidence predictions are accurate for all models or whether calibration varies by model.

Research indicates that routers can achieve dramatically different Brier scores across different models in their pool, even though their overall routing performance appears similar[19]. This heterogeneity is important because it suggests that a router with good overall performance might have poorly calibrated confidence predictions for specific models, which could lead to suboptimal routing decisions. Evaluators now compute per-model Brier scores and report them as part of comprehensive router evaluation, ensuring that confidence quality is assessed across all models rather than only in aggregate.

### Reliability Diagrams and Visual Calibration Assessment

Reliability diagrams provide a visual representation of model calibration by plotting predicted probability versus observed accuracy across probability bins[18]. The diagonal line represents perfect calibration (where predicted probability matches observed accuracy), and deviations from this diagonal indicate miscalibration. A diagram where the empirical curve lies above the diagonal indicates overconfidence (predicted probability higher than realized accuracy), while curves below the diagonal indicate underconfidence.

For router evaluation, reliability diagrams offer intuitive visualization of whether a router's confidence estimates are trustworthy. A router whose reliability diagram shows strong adherence to the diagonal line across all probability ranges indicates that the router's decisions are well-grounded in accurate self-assessment of model performance. Deviations from the diagonal suggest that calibration adjustment might be needed.

## Specialized Routing Evaluation for Code Generation Tasks

While general-purpose routers are evaluated on broad benchmarks like MMLU and general reasoning tasks, specialized routing evaluation protocols have emerged for code-specific tasks. Code generation represents a distinct evaluation challenge because correctness is determined by test execution rather than human judgment, and there are important distinctions between code generation difficulty levels.

### SWE-bench for Software Engineering and Code Completion

SWE-bench has evolved to include routing-relevant evaluation subsets, particularly SWE-bench Verified, which is a human-filtered subset of 500 instances designed to provide high-confidence evaluation of code-based models[20]. When evaluating routers for code generation, using this carefully curated subset enables reliable assessment of routing decisions without the noise that might be introduced by lower-quality instances. The metric used is straightforward: percentage of instances resolved, which directly measures what fraction of software engineering tasks can be solved by the routed models.

### LiveCodeBench: Continuous Evaluation with Contamination Prevention

LiveCodeBench takes a novel approach to code evaluation that has important implications for router assessment[21]. Rather than using static benchmarks that might become contaminated as they are widely used for model training, LiveCodeBench continuously collects new problems from periodic contests on LeetCode, AtCoder, and Codeforces platforms. This continuous refresh ensures that benchmark problems remain novel and that evaluations cannot rely on problems that appear in model training data.

LiveCodeBench evaluates models across multiple code-related scenarios beyond mere code generation, including self-repair, test output prediction, and code execution[21]. These diverse scenarios reveal different aspects of model capability that routers must account for. Research on this benchmark has shown that different models have distinct strengths: Claude-3-Opus overtakes GPT-4-turbo in test output prediction scenarios, while GPT-4-turbo maintains superiority in pure code generation[21]. For routers, this heterogeneity means that routing decisions must account for task type, not just overall model capability.

### BigCodeBench: Practical and Challenging Programming Tasks

BigCodeBench evaluates LLMs on practical and challenging programming tasks using a full set of 1,140 tasks plus a Hard Set of approximately 150 more user-facing and challenging tasks[22]. The distinction between the full set and hard set is important for router evaluation: routers must be evaluated on both easy and difficult code problems to understand where they effectively defer to capable models and where they appropriately delegate to efficient models.

### Aider Polyglot: Multi-Language Code Evaluation

The Aider Polyglot benchmark extends code evaluation across C++, Go, Java, JavaScript, Python, and Rust through 225 challenging problems from Exercism[23]. A critical feature of this benchmark for routing evaluation is that models receive two attempts, with the second attempt including test failure information from the first attempt. This multi-attempt structure reveals important patterns about model capabilities: some models are significantly better at iterative refinement than at initial generation. A router must understand these differences to make optimal decisions about which model to use for problems where correction capabilities matter.

## Calibration and Confidence Assessment in Router Evaluation

As router evaluation has matured, the importance of calibration—ensuring that a router's confidence estimates align with true model performance—has become increasingly apparent. Recent advances in calibration techniques have opened new possibilities for improving router performance and evaluation fidelity.

### Conformal Prediction for Uncertainty-Aware Routing

Conformal Prediction represents a theoretically principled approach to uncertainty quantification that has been adapted for LLM routing through CP-Router[15]. Unlike heuristic confidence estimation, conformal prediction provides rigorous coverage guarantees: if configured for 90% coverage, the resulting predictions will contain the true answer with at least 90% probability. This formal guarantees make conformal prediction particularly attractive for safety-critical applications where the consequences of miscalibration are severe.

CP-Router demonstrates how conformal prediction can be applied to decide between an LLM and an LLM-based reasoning model (LRM)[15]. The key insight is that reasoning models produce lengthy outputs even for simple queries, which is inefficient. By using conformal prediction to estimate uncertainty, CP-Router can route simple queries to the efficient LLM and reserve the reasoning model for genuinely difficult problems. Experimental evaluation across diverse MCQA benchmarks shows that CP-Router efficiently reduces token usage while maintaining or improving accuracy compared to using the reasoning model alone[15].

### Temperature Scaling and Post-Hoc Calibration

Temperature scaling is a simple yet effective post-hoc calibration method where a single temperature parameter is applied to model logits before computing confidence scores[16]. The temperature scales the softmax distribution: higher temperatures produce more uniform distributions (lower confidence), while lower temperatures produce sharper distributions (higher confidence). By fitting the temperature parameter on a held-out calibration set to minimize negative log-likelihood, one can adjust overall model confidence to align with observed accuracy.

Adaptive Temperature Scaling (ATS) extends this approach by predicting a separate temperature scaling parameter for each token prediction[16]. The intuition is that calibration needs can vary by token position: early tokens might be more reliable than later tokens, or different token types might have different calibration requirements. ATS improves calibration by over 10-50% across evaluation benchmarks compared to prior calibration methods and does not impede performance improvements from reinforcement learning from human feedback[16].

### Calibration Across Layers and Distributed Phenomena

Recent research has revealed that calibration is not solely determined by final-layer components but rather emerges as a distributed phenomenon throughout network depth[17]. Analysis of multiple open-weight models on MMLU reveals a distinct confidence correction phase in upper/later layers, where model confidence is actively recalibrated after decision certainty has been reached. Critically, a low-dimensional calibration direction in the residual stream has been identified whose perturbation significantly improves calibration metrics (ECE and MCE) without harming accuracy[17].

For router evaluation, this finding has important implications. It suggests that calibration quality can be diagnosed and potentially improved by examining model internals rather than only observing final outputs. Routers that understand how calibration varies across model depth might achieve better performance by selectively using intermediate layer representations. This line of research is still emerging but promises to provide deeper insights into what makes some models more suitable for routing than others.

### Platt Scaling and Isotonic Regression

Beyond temperature scaling, classical calibration techniques from machine learning continue to be relevant for router evaluation. Platt scaling applies a logistic function to raw model scores, implementing a sigmoid transformation that can adjust both scale and bias of confidence estimates. Isotonic regression takes a more flexible approach, learning an arbitrary monotonic mapping from raw scores to calibrated probabilities. These techniques have been studied extensively in traditional machine learning and continue to be applicable to routers.

The key distinction between these techniques is the flexibility-bias tradeoff. Temperature scaling is extremely simple (single parameter) but might not capture complex calibration behavior. Platt scaling adds bias adjustment (two parameters) and is often effective in practice. Isotonic regression is most flexible (learning arbitrary monotonic functions) but requires more data to fit reliably and can be prone to overfitting on small calibration sets.

## Production Evaluation: Online Testing and Real-World Deployment

While offline benchmarks provide controlled evaluation environments, the ultimate test of router effectiveness is performance in production environments where real users generate requests according to actual task distributions. This has motivated development of sophisticated online evaluation methodologies.

### Online versus Offline Evaluation Paradigms

A critical distinction exists between offline evaluation (using existing benchmarks) and online evaluation (collecting data from actual user requests)[24]. Offline evaluation enables rapid iteration and comparison across many methods, but it carries risks: the benchmark task distribution might not match the real user distribution, benchmark problems might have become contaminated through public use, and benchmark evaluators (particularly LLM-based judges) might exhibit biases.

Online evaluation, by contrast, directly measures performance on actual user requests under realistic conditions. The tradeoff is that online evaluation is slower (requiring real users to generate sufficient traffic to achieve statistical significance), more expensive (requiring actual model inference), and sometimes ethically fraught (requiring users to potentially receive lower-quality responses during experiments). Despite these challenges, online evaluation is increasingly recognized as essential for understanding router performance in production.

### A/B Testing Routers with Probabilistic Routing

A/B testing provides a controlled mechanism for comparing router variants in production[25]. The standard approach uses probabilistic routing, where application logic rather than network infrastructure determines which model backend fulfills a request. This application-layer routing enables careful manipulation of which prompts, parameters, or models are used for different variants.

A critical consideration in production A/B testing of routers is maintaining consistent user experience through sticky sessions[25]. When a user initiates a multi-turn conversation, they expect consistency in the model's personality and capabilities. If the router switches models between turns (perhaps because a new message triggers different routing logic), the user experiences jarring inconsistency that degrades the experience and invalidates experimental results. Production routers must implement sticky sessions that keep a user on the same model throughout a conversation session, while still allowing router decisions to change for new users.

### Error Handling and Circuit Breaker Patterns

Production router evaluation must account for failure modes that rarely appear in offline testing[25]. If an experimental variant experiences high timeout rates or unusually high error rates compared to the control variant, the production router should automatically revert users to the known-good control model. This circuit breaker pattern prevents experimental routers from causing widespread service degradation. Evaluation of production routers must explicitly assess how these error-handling mechanisms work and whether they successfully prevent cascade failures.

### Configuration Management and Rapid Iteration

Production router evaluation benefits from treating router configuration as data rather than code[25]. By externalizing routing parameters to environment variables or configuration files, operators can modify live service behavior and A/B test configurations without requiring code deployment and restart cycles. This enables rapid experimentation with different routing thresholds, cost parameters, and model combinations. However, evaluators must be careful to distinguish between configuration changes that affect actual router behavior (which should be tracked as variant conditions) and performance variations that reflect random fluctuation or uncontrolled environmental factors.

### Dashboards and Observability for Router Monitoring

As routers move into production, comprehensive observability and monitoring infrastructure becomes essential[58]. A production router monitoring stack typically tracks multiple categories of metrics: availability and health metrics (device availability, CPU utilization, memory utilization), interface and bandwidth metrics (throughput, interface errors, interface utilization), and path performance metrics (latency, jitter, packet loss). For LLM routers, these network-level concepts translate to model-level monitoring: router availability (is the routing decision mechanism responsive?), model health (are individual models responsive?), and end-to-end latency.

Organizations deploying routers have found that establishing dynamic baselines is critical for anomaly detection[58]. Rather than static thresholds (e.g., "alert if latency exceeds 2 seconds"), modern monitoring systems learn the normal behavior pattern of the system and only alert on true deviations. This approach is particularly important for routers, where latency and performance naturally vary based on traffic patterns, model availability, and user request distributions. Correlating multiple signals (accuracy, latency, cost) enables root cause analysis to distinguish between performance degradation due to model issues versus degradation due to network problems or traffic pattern changes.

## Critical Evaluation Challenges and Pitfalls in Router Assessment

Despite the maturation of router evaluation methods, several fundamental challenges persist that can undermine evaluation validity. Understanding these pitfalls is essential for conducting rigorous router assessments.

### Goodhart's Law and Metric Distortion in Router Evaluation

Goodhart's Law states a profound principle about measurement: when we express an organizational goal in terms of a metric, the metric loses its value as a measure of anything[30]. In router evaluation, this problem manifests when developers optimize routers to achieve high scores on benchmark metrics without corresponding improvements in real-world performance. For example, a router that achieves high CPT scores (using less of the expensive model at each performance level) might accomplish this by making suboptimal decisions on high-stakes queries, reducing actual user satisfaction despite the metric improvement.

The problem of gaming router metrics arises precisely because once router evaluation metrics become known, developers can tune their systems to achieve high metric values without achieving the underlying goal[30]. Some problematic patterns that have been observed include: counterfeit data (generating synthetic evaluation results that show good performance), misstate categories (classifying borderline cases in ways that inflate performance), redefine categories (subtly changing how problem difficulty is classified to make problems appear easier), and assign highest priority to least difficult issues (ensuring the router performs well on easy problems while ignoring hard problems).

To mitigate Goodhart's Law effects in router evaluation, evaluators are increasingly adopting multi-metric approaches where no single metric is optimized in isolation. Additionally, audit trails and external verification of evaluation results help detect systematic distortion. Critically, evaluating routers on diverse benchmark sets makes it harder for systems to optimize for one specific metric without making real improvements to underlying capability.

### Benchmark Contamination and Confidence in Router Evaluation

As router evaluation becomes more prominent, the risk that benchmark problems leak into model training data increases[31]. Unlike human exam contamination that requires human-to-human information transfer, LLM model training contamination can occur through subtle mechanisms: training data collection pipelines might inadvertently include benchmark problems, models trained by different organizations might mix data sources, and synthetic data generation might recreate benchmark content.

A framework for analyzing contamination sensitivity in LLM router benchmarks proposes audit methodology that identifies sensitivity to potential contamination cues by comparing deviations between clean-control and noisy conditions[31]. When benchmark problems are systematically deleted, rewritten, or perturbed before being evaluated, genuinely clean benchmarks should show minimal performance differences between noisy and clean conditions. If noisy conditions consistently outperform clean conditions—an "above-baseline anomaly"—it suggests that models are reassembling benchmark-related cues from fragments and reactivating contamination-related memory[31].

Critically, this research demonstrates that even when models obtain similar benchmark scores, their sensitivity to contamination-related cues may differ substantially[31]. Model comparison should therefore not stop at score levels alone, but should also consider whether those scores are equally credible. A router that achieves high performance on a contamination-sensitive benchmark might have learned to exploit benchmark-specific patterns rather than learning generalizable routing strategies.

### Position Bias in LLM Judges and Pairwise Evaluation

Many router evaluation protocols use LLMs as judges to compare outputs from different routed models. The assumption underlying this approach is that LLM judges make fair, unbiased assessments. However, recent research has demonstrated systematic position bias in pairwise LLM judgments where judges preferentially rate earlier-presented options higher than later-presented options (or vice versa), regardless of actual quality[32].

Investigation across 12 judges and two benchmarks with over 100,000 evaluation instances reveals that position bias in capable LLM judges is not due to random chance, but rather is systematic and judge-dependent[32]. Notably, position bias is weakly influenced by the length of prompt components but significantly impacted by the quality gap between solutions[32]. When two model outputs are of similar quality, position bias is pronounced. When quality gaps are large, position bias is reduced. For router evaluation, this finding suggests that evaluating routers on tasks with large quality gaps (where the right model to use is obvious) will show less position bias, while evaluating on fine-grained distinctions between models will exhibit more bias.

Robust router evaluation protocols mitigate position bias through multiple strategies: presenting options in randomized order to different judges, using multiple independent judges and aggregating their assessments, and explicitly measuring and reporting position consistency metrics alongside primary evaluation results.

### Selection Bias and Distribution Shift in Router Training Data

When routers are trained on labeled datasets where data is preferentially selected (e.g., human experts create a dataset of "interesting" routing decisions), systematic selection bias can distort what the router learns[31]. Selection bias is particularly problematic for router evaluation because routers must make decisions on the full distribution of user queries, not just on interesting or difficult cases.

One manifestation of selection bias in router data is when labeled data comes exclusively from queries where model predictions disagreed. In these high-uncertainty regimes, the router learns excellent routing strategies but might fail on the many queries where multiple models agree (or disagree) in obvious ways. A router trained only on interesting disagreement cases might perform poorly on the common cases that generate most traffic.

Addressing selection bias requires evaluating routers on representative, unbiased samples of the task distribution. This often means explicitly including many easy problems where most models succeed and many hard problems where most models fail, not just focusing on the marginal cases. Reporting router performance stratified by difficulty level helps identify whether the router exhibits systematic biases in particular regimes.

### Overfitting to Specific Model Pools and Generalization Failures

Routers trained on specific model pools (e.g., GPT-4, Claude, and Llama) might not generalize to new models that become available later[3]. This generalization challenge arises because routers learn to exploit specific characteristics of their training models: response style, typical error patterns, latency profiles, and cost structures. When new models with different characteristics enter the pool, the router's learned associations between query characteristics and model suitability might be wrong.

RouteLLM addresses this challenge by explicitly measuring transfer learning capabilities where routers are trained on one model pair (strong and weak) and then evaluated on different model pairs[3]. The finding that routers demonstrate significant transfer capabilities even when both the strong and weak models change at test time suggests that routers can learn somewhat generalizable principles. However, transfer performance is typically lower than performance on training models, indicating that generalization remains an open challenge.

### Incomplete Cost Attribution and Hidden Expenses

A subtle pitfall in router evaluation is incomplete cost accounting that omits important expense categories. Evaluations often focus exclusively on model inference costs (the price charged by API providers or the computational cost of running models), but ignore infrastructure costs, operational overhead, and opportunity costs.

When an organization considers implementing a router to reduce costs, they must account for: infrastructure for the routing system itself (computational resources), operational and monitoring costs (personnel time to manage the system), training data collection and labeling costs (creating preference data for router training), and opportunity costs (engineer time spent implementing routing instead of other priorities). A router that saves 20% on model inference costs but adds 10% overhead in infrastructure and operations provides less benefit than the raw numbers suggest.

Additionally, some organizations claim dramatic cost reductions that would benefit from independent verification. One organization's internal measurements showed 52.4% error reduction and 92% cost reduction in a customer help chat deployment, and another showed 20% quality improvement with 80x cost reduction in a RAG system[8]. However, these results are presented as case studies rather than independent benchmarks. Replication of these results across different organizations and deployment scenarios remains limited, making it difficult to assess how representative these outcomes are.

## Recent Advances and Emerging Directions in Router Evaluation

As of April 2026, several emerging directions in router evaluation reflect evolving understanding of the challenges and opportunities in this space.

### Moving Beyond Single Operating Points

Early router evaluation focused on specific operating points: "How much cost reduction does this router achieve at GPT-4-level performance?" More sophisticated evaluation now characterizes router behavior across the entire performance-cost tradeoff space. This shift recognizes that different organizations have different cost-quality preferences, and a router that is excellent at one tradeoff point might be suboptimal at another.

### Multi-Modal and Multi-Task Routing Evaluation

As LLMs increasingly support multimodal inputs (text, images, audio) and diverse task types, router evaluation is expanding beyond text-only, single-task scenarios. Evaluation frameworks like MixEval-X explicitly address multimodal routing, where models have different capabilities across modalities. This requires router evaluation to span diverse input types and ensure that routing strategies account for modality-specific model strengths and weaknesses.

### Real-Time Router Performance Monitoring

Production router deployments increasingly integrate continuous performance monitoring that tracks router decisions in real-time against ground truth labels as they become available[25]. This enables routers to adapt their strategies as feedback accumulates, potentially using an online learning approach where router parameters are updated as new user feedback arrives. Evaluation of such adaptive routers requires different metrics than static routers: tracking not just final performance but also convergence properties and stability.

### Router Evaluation in Cost-Latency-Quality Space

While early router evaluation focused on cost-quality tradeoffs, production deployments reveal the importance of simultaneously optimizing across three dimensions: quality (accuracy), cost (inference expense), and latency (user-perceived delay)[7][7]. Evaluating routers in three-dimensional space is more complex than two-dimensional evaluation but more accurately reflects deployment requirements. An emerging metric is the volume in this three-dimensional space that a router dominates relative to baselines.

## Conclusion

Large language model router evaluation has evolved from an ad-hoc activity into a rigorous, multi-faceted discipline with standardized benchmarks, sophisticated metrics, and established best practices. The maturation of this field reflects recognition that routers represent a critical infrastructure component for cost-effective LLM deployment at scale. Organizations can now reference established benchmarks like RouterBench, RouterArena, and RouterEval when evaluating routing systems, deploy evaluation pipelines that measure performance across multiple dimensions simultaneously, and learn from documented pitfalls and challenges that have emerged from research and production experience.

The breadth of evaluation considerations that must be addressed—from accurate cost attribution to calibration verification to production monitoring—underscores that router evaluation is not a simple problem. A comprehensive evaluation program for routers in production requires attention to benchmark design and contamination risks, multiple complementary metrics that each measure different aspects of router effectiveness, specialized evaluation protocols for specific task types like code generation, rigorous calibration assessment techniques, online evaluation methodologies that validate offline benchmark findings, and vigilance against systematic pitfalls like metric gaming and selection bias.

Looking forward, the router evaluation field will likely see continued refinement of metrics to better capture real-world performance, integration of online learning capabilities that enable routers to adapt based on production feedback, expansion of evaluation to more complex scenarios involving multiple concurrent objectives and diverse modalities, and deeper investigation of how routing decisions should account for task-specific factors rather than only general complexity levels. The convergence between router evaluation best practices and broader practices for evaluating complex ML systems suggests that insights from router evaluation will inform other areas where systems must make decisions among multiple expert components under resource constraints.

For practitioners implementing routers in production, the key takeaway is that evaluation should be comprehensive, multi-faceted, and grounded in understanding of specific production requirements rather than optimizing for generic benchmark scores. An organization's router evaluation program should establish baseline performance without routing, conduct offline benchmarking using multiple established benchmarks stratified by problem difficulty, evaluate on code-specific benchmarks if code generation is part of the workload, validate calibration quality to ensure confident routing decisions, implement production A/B testing with robust error handling, and maintain continuous monitoring of router performance with alerting on meaningful deviations. By following established evaluation practices and remaining vigilant about documented pitfalls, organizations can deploy routers with confidence that their performance claims are well-founded and that actual production performance will match benchmark expectations.

### Citations

1. https://arxiv.org/abs/2403.12031
2. https://arxiv.org/abs/2510.00202
3. https://arxiv.org/abs/2406.18665
4. https://arxiv.org/abs/2503.10657
5. https://github.com/ynulihao/LLMRouterBench/blob/main/evaluation/README.md
6. https://arxiv.org/abs/2410.13754
7. https://opper.ai/blog/llm-router-latency-benchmark-2026
8. https://withmartian.com/post/up-and-to-the-left
9. https://pmc.ncbi.nlm.nih.gov/articles/PMC10664195/
10. https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/mesh-metrics.pdf
11. https://wandb.ai/byyoung3/ML_NEWS3/reports/How-to-train-and-evaluate-an-LLM-router--Vmlldzo5MjU0MTA1
12. https://ufal.mff.cuni.cz/pbml/103/art-bestgen.pdf
13. https://arxiv.org/html/2602.03478v1
14. https://arxiv.org/html/2601.07206v1
15. https://arxiv.org/abs/2505.19970
16. https://arxiv.org/abs/2409.19817
17. https://arxiv.org/abs/2511.00280
18. https://www.youtube.com/watch?v=NDY2fH1FitQ
19. https://arxiv.org/html/2603.20895v2
20. https://www.swebench.com
21. https://livecodebench.github.io
22. https://bigcode-bench.github.io
23. https://epoch.ai/benchmarks/aider-polyglot
24. https://rhesis.ai/post/offline-vs-online-evaluation-llm-applications
25. https://render.com/articles/best-practices-for-running-ai-output-a-b-test-in-production
26. https://red.anthropic.com/2026/mythos-preview/
27. https://openrouter.ai/openai/gpt-4
28. https://deepmind.google/research/publications/34011/
29. https://blog.mdfranz.com/building-a-home-network-observability-stack-with-telegraf-and-influxdb/
30. https://chacocanyon.com/pointlookout/230308.shtml
31. https://arxiv.org/html/2603.21636v1
32. https://arxiv.org/html/2406.07791v4
33. https://distill.pub/2019/advex-bugs-discussion/response-6
34. https://www.mindstudio.ai/blog/what-is-ai-model-router-optimize-cost-llm-providers/
35. https://www.diva-portal.org/smash/get/diva2:650882/FULLTEXT01.pdf
36. https://github.com/BerriAI/litellm/issues/21270
37. https://iternal.ai/token-usage-guide
38. https://arxiv.org/abs/2305.05176
39. https://arxiv.org/html/2404.14618v1
40. https://arxiv.org/abs/2508.12631
41. https://community.ipfire.org/t/getting-martian-source-errors-in-kernel-and-dropping-network/13703
42. https://openrouter.ai/docs/guides/overview/report-feedback
43. https://vllm-semantic-router.com/docs/training/training-overview
44. https://arxiv.org/html/2312.07577v2
45. https://allenai.org/blog/hybrid-preferences-learning-to-route-instances-for-human-vs-ai-feedback-6bed4b68c0a2
46. https://arxiv.org/abs/2402.10099
47. https://www.pusr.com/blog/Failure-Transfer-Mechanism-of-Industrial-Routers
48. https://www.promptfoo.dev/docs/guides/gpt-mmlu-comparison/
49. https://labs.scale.com/leaderboard/humanitys_last_exam
50. https://arxiv.org/html/2406.11456v1
51. https://github.com/vllm-project/semantic-router/issues/1439
52. https://research.google.com/pubs/archive/45569.pdf
53. https://arxiv.org/html/2410.12869v2
54. https://arxiv.org/html/2505.19435v1
55. https://docsbot.ai/models/compare/o1-mini/o1
56. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5810123
57. https://scikit-learn.org/stable/modules/classification_threshold.html
58. https://www.manageengine.com/network-monitoring/tech-topics/what-is-router-monitoring.html

---

## Exa Deep Search  (15 sources)

### 1. [2403.12031] RouterBench: A Benchmark for Multi-LLM Routing System
**URL:** https://arxiv.org/abs/2403.12031
**Published:** 2024-03-18T19:34:08.000Z

[2403.12031] RouterBench: A Benchmark for Multi-LLM Routing System

# Computer Science > Machine Learning

arXiv:2403.12031 (cs)

[Submitted on 18 Mar 2024 (v1), last revised 28 Mar 2024 (this version, v2)]

# Title:RouterBench: A Benchmark for Multi-LLM Routing System

View PDF HTML (experimental)

> Abstract:As the range of applications for Large Language Models (LLMs) continues to grow, the demand for effective serving solutions becomes increasingly critical. Despite the versatility of LLMs, no single model can optimally address all tasks and applications, particularly when balancing performance with cost. This limitation has led to the development of LLM routing systems, which combine the strengths of various models to overcome the constraints of individual LLMs. Yet, the absence of a standardized benchmark for evaluating the performance of LLM routers hinders progress in this area. To bridge this gap, we present RouterBench, a novel evaluation framework designed to systematically assess the efficacy of LLM routing systems, along with a comprehensive dataset comprising over 405k inference outcomes from representative LLMs to support the development of routing strategies. We further propose a theoretical framework for LLM routing, and deliver a comparative analysis of various routing approaches through RouterBench, highlighting their potentials and limitations within our evaluation framework. This work not only formalizes and advances the development of LLM routing systems but also sets a standard for their assessment, paving the way for more accessible and economically viable LLM deployments. The code and data are available at this https URL.

arXiv-issued DOI via DataCite

| Subjects: | Machine Learning (cs.LG); Artificial Intelligence (cs.AI) |
| --- | --- |
| Cite as: | arXiv:2403.12031 [cs.LG] |
| (or arXiv:2403.12031v2 [cs.LG] for this version) |

## Submission history

From: Xiuyu Li [view email] [v1] Mon, 18 Mar 2024 17:59:04 UTC (1,677 KB) [v2] Thu, 28 Mar 2024 17:56:28 UTC (1,356 KB)

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

ScienceCast Toggle

ScienceCast (What is ScienceCast?)

Demos

# Demos

Replicate Toggle

Repl

*… (951 more characters — see results.json for full text)*

---

### 2. RouterBench: Multi-LLM Routing Benchmark
**URL:** https://www.emergentmind.com/papers/2403.12031

RouterBench: Multi-LLM Routing Benchmark

0 }" @focus="focused = true" @click="focused = true; clicked = true; handleQueryChange()" @click.away="clicked = false" @keydown="focused = true" @keydown.escape="setQuery(''); focused = false; clicked = false" @input.debounce.100ms="handleQueryChange();" @input="if ($event.target.value === '') { setQuery('') }" @keyup="if ($event.target.value === '') { setQuery('') }" @keydown.enter.prevent="if (!$event.shiftKey) { $refs.search_form.submit() } else { handleShiftEnter($event) }" maxlength="2000">2403.12031

0">Papers

0">Topics

0">Authors

0">

Recent

Search

2000 character limit reached

# RouterBench: A Benchmark for Multi-LLM Routing System

Published 18 Mar 2024 in cs.LG and cs.AI | (2403.12031v2)

Abstract: As the range of applications for LLMs continues to grow, the demand for effective serving solutions becomes increasingly critical. Despite the versatility of LLMs, no single model can optimally address all tasks and applications, particularly when balancing performance with cost. This limitation has led to the development of LLM routing systems, which combine the strengths of various models to overcome the constraints of individual LLMs. Yet, the absence of a standardized benchmark for evaluating the performance of LLM routers hinders progress in this area. To bridge this gap, we present RouterBench, a novel evaluation framework designed to systematically assess the efficacy of LLM routing systems, along with a comprehensive dataset comprising over 405k inference outcomes from representative LLMs to support the development of routing strategies. We further propose a theoretical framework for LLM routing, and deliver a comparative analysis of various routing approaches through RouterBench, highlighting their potentials and limitations within our evaluation framework. This work not only formalizes and advances the development of LLM routing systems but also sets a standard for their assessment, paving the way for more accessible and economically viable LLM deployments. The code and data are available at https://github.com/withmartian/routerbench.

Authors (8)

1. Qitian Jason Hu
2. Jacob Bieker
3. Xiuyu Li
4. Nan Jiang
5. Benjamin Keigwin
6. Gaurav Ranganath
7. Kurt Keutzer
8. Shriyash Kaustubh Upadhyay

Related Papers

1. A Survey on Evaluation of Large Language Models(2023)
2. State of What Art? A Call for Multi-Prompt LLM Evaluation(2023)
3. Routing to the Expert: Efficient Reward-guided Ensemble of Large Language Models(2023)
4. OrchestraLLM: Efficient Orchestration of Language Models for Dialogue State Tracking(2023)
5. Harnessing the Power of Multiple Minds: Lessons Learned from LLM Routing(2024)

Citations (17)

View on Semantic Scholar

### Summary

- The paper presents a theoretical framework that evaluates multi-LLM routers by balancing efficiency and cost.
- It compiles a comprehensive dataset with over 405k inference results across diverse tasks to benchmark router performance.
- Empir

*… (5,056 more characters — see results.json for full text)*

---

### 3. Untitled
**URL:** https://openreview.net/pdf?id=IVXmV8Uxwh

ROUTERBENCH: A Benchmark for Multi-LLM Routing System
Qitian Jason Hu 1 Jacob Bieker 1 Xiuyu Li 2 Nan Jiang 3 Benjamin Keigwin 1 Gaurav Ranganath 1
Kurt Keutzer 2 Shriyash Kaustubh Upadhyay 1
Abstract
As the range of applications for Large Language
Models (LLMs) continues to grow, the demand
for effective serving solutions becomes increasingly critical. Despite the versatility of LLMs,
no single model can optimally address all tasks
and applications, particularly when balancing performance with cost. This limitation has led to
the development of LLM routing systems, which
combine the strengths of various models to overcome the constraints of individual LLMs. Yet,
the absence of a standardized benchmark for
evaluating the performance of LLM routers hinders progress in this area. To bridge this gap,
we present ROUTERBENCH, a novel evaluation
framework designed to systematically assess the
efficacy of LLM routing systems, along with a
comprehensive dataset comprising over 405k inference outcomes from representative LLMs to
support the development of routing strategies. We
further propose a theoretical framework for LLM
routing, and deliver a comparative analysis of various routing approaches through ROUTERBENCH,
highlighting their potentials and limitations within
our evaluation framework. This work not only
formalizes and advances the development of
LLM routing systems but also sets a standard
for their assessment, paving the way for more
accessible and economically viable LLM deployments. The code and data are available at
https://github.com/withmartian/routerbench.
1. Introduction
Large Language Models (LLMs) have exhibited remarkable
capabilities in addressing a wide range of tasks across academic and industrial scenarios (Bubeck et al., 2023). This
has motivated both researchers and practitioners to intro1Martian 2UC Berkeley 3UC San Diego. Correspondence to:
Qitian Jason Hu.
Preprint.
duce new LLMs, designed for both generic and specialized
use cases, on a near-daily basis 1. However, the proliferation
of LLMs presents a challenge for LLM application builders
to identify the most suitable model for their applications.
While some proprietary models, such as GPT-4, are distinguished by their superior performance, they often incur high
economic costs due to the high API prices.
Many prior works focus on improving the capabilities of
individual LLMs while maintaining low costs. Techniques
such as prompting (Wei et al., 2022), quantization (Lin et al.,
2023; Kim et al., 2023), and system optimization (Kwon
et al., 2023) may reduce a single model’s serving cost, yet
with new models emerging daily, these approaches may not
remain feasible or scalable in long term. Moreover, the
diversity of choices of LLMs available at various price and
performance tiers can be daunting for users attempting to
select and optimize an appropriate model2.
An alternative solution aims to select to optimal LLM for
each input through ”routing.” (Chen et al., 2023

*… (22,000 more characters — see results.json for full text)*

---

### 4. RouterBench: A Benchmark for Multi-LLM Routing System
**URL:** https://arxiv.org/html/2403.12031v2

RouterBench: A Benchmark for Multi-LLM Routing System

# RouterBench: A Benchmark for Multi-LLM Routing System

Qitian Jason Hu Jacob Bieker Xiuyu Li Nan Jiang Benjamin Keigwin Gaurav Ranganath Kurt Keutzer Shriyash Kaustubh Upadhyay

###### Abstract

As the range of applications for Large Language Models (LLMs) continues to grow, the demand for effective serving solutions becomes increasingly critical. Despite the versatility of LLMs, no single model can optimally address all tasks and applications, particularly when balancing performance with cost. This limitation has led to the development of LLM routing systems, which combine the strengths of various models to overcome the constraints of individual LLMs. Yet, the absence of a standardized benchmark for evaluating the performance of LLM routers hinders progress in this area. To bridge this gap, we present RouterBench, a novel evaluation framework designed to systematically assess the efficacy of LLM routing systems, along with a comprehensive dataset comprising over 405k inference outcomes from representative LLMs to support the development of routing strategies. We further propose a theoretical framework for LLM routing, and deliver a comparative analysis of various routing approaches through RouterBench, highlighting their potentials and limitations within our evaluation framework. This work not only formalizes and advances the development of LLM routing systems but also sets a standard for their assessment, paving the way for more accessible and economically viable LLM deployments. The code and data are available at https://github.com/withmartian/routerbench.

Machine Learning, ICML

Figure 1: Left: The RouterBench Construction Process integrates eight datasets with eleven distinct models to develop RouterBench. Detailed format can be found in Appendix A.3. Right: The Model Routing Process shows the method of routing prompts through a router to various LLMs based on specific requests, demonstrating the dynamic allocation of resources.

## 1 Introduction

Large Language Models (LLMs) have exhibited remarkable capabilities in addressing a wide range of tasks across academic and industrial scenarios (Bubeck et al., 2023). This has motivated both researchers and practitioners to introduce new LLMs, designed for both generic and specialized use cases, on a near-daily basis 111As of January 16th, 2024, there are 469,848 models listed on huggingface.com. However, the proliferation of LLMs presents a challenge for LLM application builders to identify the most suitable model for their applications. While some proprietary models, such as GPT-4, are distinguished by their superior performance, they often incur high economic costs due to the high API prices.

Many prior works focus on improving the capabilities of individual LLMs while maintaining low costs. Techniques such as prompting (Wei et al., 2022), quantization (Lin et al., 2023; Kim et al., 2023), and system optimization (Kwon et al., 2023) ma

*… (21,739 more characters — see results.json for full text)*

---

### 5. RouterBench: A Benchmark for Multi-LLM Routing System
**URL:** https://arxiv.org/html/2403.12031v1
**Published:** 2024-03-18T00:00:00.000Z

RouterBench: A Benchmark for Multi-LLM Routing System

License: arXiv.org perpetual non-exclusive license

arXiv:2403.12031v1 [cs.LG] 18 Mar 2024

# RouterBench: A Benchmark for Multi-LLM Routing System

Qitian Jason Hu Jacob Bieker Xiuyu Li Nan Jiang Benjamin Keigwin Gaurav Ranganath Kurt Keutzer Shriyash Kaustubh Upadhyay

###### Abstract

As the range of applications for Large Language Models (LLMs) continues to grow, the demand for effective serving solutions becomes increasingly critical. Despite the versatility of LLMs, no single model can optimally address all tasks and applications, particularly when balancing performance with cost. This limitation has led to the development of LLM routing systems, which combine the strengths of various models to overcome the constraints of individual LLMs. Yet, the absence of a standardized benchmark for evaluating the performance of LLM routers hinders progress in this area. To bridge this gap, we present RouterBench, a novel evaluation framework designed to systematically assess the efficacy of LLM routing systems, along with a comprehensive dataset comprising over 405k inference outcomes from representative LLMs to support the development of routing strategies. We further propose a theoretical framework for LLM routing, and deliver a comparative analysis of various routing approaches through RouterBench, highlighting their potentials and limitations within our evaluation framework. This work not only formalizes and advances the development of LLM routing systems but also sets a standard for their assessment, paving the way for more accessible and economically viable LLM deployments. The code and data are available at https://github.com/withmartian/routerbench.

Machine Learning, ICML

Figure 1: Left: The RouterBench Construction Process integrates eight datasets with eleven distinct models to develop RouterBench. Detailed format can be found in Appendix A.4. Right: The Model Routing Process shows the method of routing prompts through a router to various LLMs based on specific requests, demonstrating the dynamic allocation of resources.

## 1 Introduction

Large Language Models (LLMs) have exhibited remarkable capabilities in addressing a wide range of tasks across academic and industrial scenarios (Bubeck et al., 2023). This has motivated both researchers and practitioners to introduce new LLMs, designed for both generic and specialized use cases, on a near-daily basis 111As of January 16th, 2024, there are 469,848 models listed on huggingface.com. However, the proliferation of LLMs presents a challenge for LLM application builders to identify the most suitable model for their applications. While some proprietary models such as GPT-4 are distinguished by their superior performance, they often incur high economic costs due to the expensive API prices.

Many prior works focus on improving the capabilities of individual LLMs while maintaining low costs. Techniques such as prompting (Wei et al., 2023), qu

*… (21,737 more characters — see results.json for full text)*

---

### 6. [2510.00202] RouterArena: An Open Platform for Comprehensive Comparison of LLM Routers
**URL:** https://arxiv.org/abs/2510.00202
**Published:** 2025-09-30T00:00:00.000Z

[2510.00202] RouterArena: An Open Platform for Comprehensive Comparison of LLM Routers

# Computer Science > Machine Learning

arXiv:2510.00202 (cs)

[Submitted on 30 Sep 2025 (v1), last revised 27 Nov 2025 (this version, v3)]

# Title:RouterArena: An Open Platform for Comprehensive Comparison of LLM Routers

View PDF HTML (experimental)

> Abstract:Today's LLM ecosystem comprises a wide spectrum of models that differ in size, capability, and cost. No single model is optimal for all scenarios; hence, LLM routers have become essential for selecting the most appropriate model under varying circumstances. However, the rapid emergence of various routers makes choosing the right one increasingly challenging. To address this problem, we need a comprehensive router comparison and a standardized leaderboard, similar to those available for models. In this work, we introduce RouterArena, the first open platform enabling comprehensive comparison of LLM routers. RouterArena has (1) a principally constructed dataset with broad knowledge domain coverage, (2) distinguishable difficulty levels for each domain, (3) an extensive list of evaluation metrics, and (4) an automated framework for leaderboard updates. Leveraging our framework, we have produced the initial leaderboard with detailed metrics comparison as shown in Figure 1. Our framework for evaluating new routers is on this https URL. Our leaderboard is on this https URL.

arXiv-issued DOI via DataCite

| Comments: |
| --- |
| Subjects: | Machine Learning (cs.LG) |
| Cite as: | arXiv:2510.00202 [cs.LG] |
| (or arXiv:2510.00202v3 [cs.LG] for this version) |

## Submission history

From: Yifan Lu [view email] [v1] Tue, 30 Sep 2025 19:22:28 UTC (851 KB) [v2] Wed, 12 Nov 2025 02:57:20 UTC (882 KB) [v3] Thu, 27 Nov 2025 20:14:18 UTC (2,031 KB)

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

Influence Flower (What

*… (729 more characters — see results.json for full text)*

---

### 7. RouterArena: An Open Platform for Comprehensive Comparison of LLM Routers - ADS
**URL:** https://ui.adsabs.harvard.edu/abs/2025arXiv251000202L/abstract

RouterArena: An Open Platform for Comprehensive Comparison of LLM Routers - ADS

Now on home page

## ADS

|--

## RouterArena: An Open Platform for Comprehensive Comparison of LLM Routers

;

;

;

;

;

;

- Xing, Jiarong
- Liu, Hongyi
- Zhang, Shenrun
- Cui, Xingqi
- Yuan, Jiayi
- Liu, Rixin
- Lu, Yifan

Today's LLM ecosystem comprises a wide spectrum of models that differ in size, capability, and cost. No single model is optimal for all scenarios; hence, LLM routers have become essential for selecting the most appropriate model under varying circumstances. However, the rapid emergence of various routers makes choosing the right one increasingly challenging. To address this problem, we need a comprehensive router comparison and a standardized leaderboard, similar to those available for models. In this work, we introduce RouterArena, the first open platform enabling comprehensive comparison of LLM routers. RouterArena has (1) a principally constructed dataset with broad knowledge domain coverage, (2) distinguishable difficulty levels for each domain, (3) an extensive list of evaluation metrics, and (4) an automated framework for leaderboard updates. Leveraging our framework, we have produced the initial leaderboard with detailed metrics comparison as shown in Figure 1. Our framework for evaluating new routers is on https://github.com/RouteWorks/RouterArena. Our leaderboard is on https://routeworks.github.io/.

Publication:

arXiv e-prints

Pub Date: September 2025 DOI:

10.48550/arXiv.2510.00202

arXiv: arXiv:2510.00202 Bibcode: 2025arXiv251000202L Keywords:

- Machine Learning

E-Print: 22 pages, 13 figures, 9 tables

full text sources

Preprint

|

🌓

---

### 8. Untitled
**URL:** https://arxiv.org/pdf/2510.00202

ROUTERARENA: AN OPEN PLATFORM FOR COMPREHENSIVE
COMPARISON OF LLM ROUTERS
Yifan Lu*, Rixin Liu*, Jiayi Yuan*, Xingqi Cui, Shenrun Zhang, Hongyi Liu, Jiarong Xing
Rice University
{yifan.lu,rixin.liu,jy101,xc66,sz81,hl87,jxing}@rice.edu
ABSTRACT
Today’s LLM ecosystem comprises a wide spectrum of models that differ in size, capability, and
cost. No single model is optimal for all scenarios; hence, LLM routers have become essential
for selecting the most appropriate model under varying circumstances. However, the rapid emergence of various routers makes choosing the right one increasingly challenging. To address this
problem, we need comprehensive router comparison and a standardized leaderboard, similar to
those available for models. In this work, we introduce ROUTERARENA, the first open platform
enabling comprehensive comparison of LLM routers. ROUTERARENA has (1) a principally constructed dataset with broad knowledge domain coverage, (2) distinguishable difficulty levels for
each domain, (3) an extensive list of evaluation metrics, and (4) an automated framework for
leaderboard updates. Leveraging our framework, we have produced the initial leaderboard with
detailed metrics comparison as shown in Figure 1. Our framework for evaluating new routers is on
https://github.com/RouteWorks/RouterArena. Our leaderboard is on https://routeworks.github.io/
0 20 40 60
Score
1
2
3
4
5
6
7
8
9
10
11
12
MIRT-BERT (66.9)
Azure-Router (66.7)
NIRT-BERT (66.1)
GPT-5 (64.3)
vLLM-SR (64.3)
CARROT (63.9)
RouterBench-MLP (57.6)
NotDiamond (57.3)
GraphRouter (57.2)
RouterBench-KNN (55.5)
RouteLLM (48.1)
RouterDC (33.8)
RouterArena Leaderboard
Academic Routers
Commercial Routers
10
1 10
0 10
1
Inference Cost (USD per 1K queries)
0.35
0.40
0.45
0.50
0.55
0.60
0.65
0.70
0.75
Accuracy
Router Performance vs Cost
CARROT
RouterDC
GraphRouter
KNN
MLP
RouteLLM
MIRT-BERT
NIRT-BERT
NotDiamond
Azure-Router
GPT-5
vLLM-SR
Figure 1: A quick view of ROUTERARENA leaderboard and performance-cost trade-off.
1 Introduction
Large Language Models (LLMs) are rapidly diversifying, offering an ever-wider spectrum of capabilities and inference
costs. This diversity increasingly challenges the prevailing LLM usage pattern in which users manually choose models
for their queries. The difficulty stems from the fact that no single model is universally optimal: powerful models excel
∗These authors contributed equally to this work.
arXiv:2510.00202v3 [cs.LG] 27 Nov 2025
RouterArena: An Open Platform for Comprehensive Comparison of LLM Routers A PREPRINT
at complex tasks but are costly, while smaller models are more efficient yet may struggle on difficult queries. As
a result, LLM routers that automatically select models based on input queries are increasingly recognized as a core
system primitive in practical deployments.
Given its importance and promise, many LLM routers have recently emerged in both industry and academia (Figure 2).
A notable example is GPT-5 [28], which incorporates routing as a ke

*… (22,000 more characters — see results.json for full text)*

---

### 9. RouteWorks/RouterArena
**URL:** https://github.com/RouteWorks/RouterArena
**Published:** 2025-10-05T18:38:19.000Z

# Repository: RouteWorks/RouterArena

RouterArena: An open framework for evaluating LLM routers with standardized datasets, metrics, an automated framework, and a live leaderboard.

- Stars: 74
- Forks: 15
- Watchers: 74
- Open issues: 8
- Primary language: Python
- Languages: Python (99.3%), Shell (0.7%)
- License: Apache License 2.0 (Apache-2.0)
- Topics: arena, llm, llm-router, llm-routing, multi-agent, multi-agent-systems, router-benchmark, router-evaluation, router-leaderboard, routing
- Default branch: main
- Homepage: https://routeworks.github.io/
- Created: 2025-10-05T18:38:19Z
- Last push: 2026-02-18T21:40:18Z
- Contributors: 8 (top: yl231, jiarong0907, RixinLiu, Henry-Shan, codelion, jqxue1999, ZhiboYu1, carlory)

---

 
 

 
 
 
 
 
 
 

 

 Make Router Evaluation Open and Standardized 

 
 
 

**RouterArena** is an open evaluation platform and leaderboard for **LLM routers**—systems that automatically select the best model for a given query. As the LLM ecosystem diversifies with models varying in size, capability, and cost, **routing** has become critical for balancing performance and cost. Yet, LLM routers currently lack a standardized evaluation framework to assess how effectively they trade off accuracy, cost, and other related metrics.

RouterArena bridges this gap by providing an open evaluation platform and benchmarking framework for both open-source and commercial routers. It has the following key features:

- 🌍 **Diverse Data Coverage**: A principly-constructed, diverse evaluation dataset spanning 9 domains and 44 categories with easy, medium, and hard difficulty levels.
- 📊 **Comprehensive Metrics**: Five router-critical metrics measuring accuracy, cost, optimality, robustness, and latency.
- ⚙️ **Automated Evaluation**: An automated evaluation framework to simplify the evaluation process for open-source and commercial routers.
- 🏆 **Live Leaderboard**: A live leaderboard to track the performance of routers across multiple dimensions.

*We aim for RouterArena to serve as a foundation for the community to evaluate, understand, and advance LLM routing systems.*

# Current Leaderboard

For more details, please see our [website](https://routeworks.github.io/leaderboard) and [blog](https://huggingface.co/blog/JerryPotter/who-routes-the-routers).

| Rank | Router | Affiliation | Acc-Cost Arena | Accuracy | Cost/1K Queries | Optimal Selection | Optimal Cost | Optimal Accuracy | Latency | Robustness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 🥇 | [R2-Router](https://arxiv.org/abs/2602.02823/) | 🎓 UCF | 71.60 | 71.23 | $0.06 | 32.38 | 74.16 | 100.00 | — | 45.71 |
| 🥈 | [vLLM‑SR](https://vllm-semantic-router.com/) [[Code]](https://github.com/vllm-project/semantic-router) [[HF]](https://huggingface.co/llm-semantic-router) | 🎓 vLLM SR Team | 67.23 | 66.53 | $0.06 | 94.10 | 90.12 | 100.00 | — | 90.95 |
| 🥉 | [MIRT‑BERT](https://arxiv.org/pdf/2506.01048) [[Code]](https://github.com/Mercidaiha/IRT-Router) | 🎓 UST

*… (9,159 more characters — see results.json for full text)*

---

### 10. RouterArena: An Open Platform for Comprehensive Comparison of LLM Routers
**URL:** https://arxiv.org/html/2510.00202v1

RouterArena: An Open Platform for Comprehensive Comparison of LLM Routers

# RouterArena: An Open Platform for Comprehensive Comparison of LLM Routers

Yifan Lu, Rixin Liu11footnotemark: 1, Jiayi Yuan11footnotemark: 1, Xingqi Cui, Shenrun Zhang, Hongyi Liu, Jiarong Xing Rice University {yifan.lu,rixin.liu,jy101,xc66,sz81,hl87,jxing}@rice.edu These authors contributed equally to this work.

###### Abstract

Today’s LLM ecosystem comprises a wide spectrum of models that differ in size, capability, and cost. No single model is optimal for all scenarios; hence, LLM routers have become essential for selecting the most appropriate model under varying circumstances. However, the rapid emergence of various routers makes choosing the right one increasingly challenging. To address this problem, we need comprehensive router comparison and a standardized leaderboard, similar to those available for models. In this work, we introduce RouterArena, the first open platform enabling comprehensive comparison of LLM routers. RouterArena has (1) a principally constructed dataset with broad knowledge domain coverage, (2) distinguishable difficulty levels for each domain, (3) an extensive list of evaluation metrics, and (4) an automated framework for leaderboard updates. Leveraging our framework, we have produced the initial leaderboard with detailed metrics comparison as shown in Figure 1. We will soon open our platform to the public.

Figure 1: A quick view of RouterArena leaderboard and performance-cost trade-off.

## 1 Introduction

Large Language Models (LLMs) are rapidly diversifying, offering an ever-wider spectrum of capabilities and inference costs. This diversity increasingly challenges the prevailing LLM usage pattern in which users manually choose models for their queries. The difficulty stems from the fact that no single model is universally optimal: powerful models excel at complex tasks but are costly, while smaller models are more efficient yet may struggle on difficult queries. As a result, LLM routers that automatically select models based on input queries are increasingly recognized as a core system primitive in practical deployments.

Given its importance and promise, many LLM routers have recently emerged in both industry and academia (Figure 2). A notable example is GPT-5 [27], which incorporates routing as a key feature by directing user queries to the most suitable model within the OpenAI family. As routers proliferate, the challenge shifts from selecting the right model to selecting the right router. Unfortunately, router evaluation has not kept pace: there is currently no open evaluation platform, akin to LMArena [5], that systematically compares open-source routers [15, 42] and commercial routing services [25, 24] under a unified protocol.

It is urgent to fill this gap by building a Router Arena that can comprehensively evaluate and rank routers, enabling users to understand the status quo and make informed choices. However, unlike model are

*… (22,000 more characters — see results.json for full text)*

---

### 11. lm-sys/RouteLLM
**URL:** https://github.com/lm-sys/routellm
**Published:** 2024-06-03T02:16:57.000Z

# Repository: lm-sys/RouteLLM

A framework for serving and evaluating LLM routers - save LLM costs without compromising quality

- Stars: 4811
- Forks: 374
- Watchers: 37
- Open issues: 39
- Primary language: Python
- Languages: Python
- License: Apache License 2.0 (Apache-2.0)
- Default branch: main
- Created: 2024-06-03T02:16:57Z
- Last push: 2024-08-10T19:10:15Z
- Contributors: 6 (top: iojw, thwu1, olivercarmont, bitnom, eltociear, infwinston)

---

# RouteLLM

RouteLLM is a framework for serving and evaluating LLM routers.

[ [Blog](http://lmsys.org/blog/2024-07-01-routellm/) ] [ [Paper](https://arxiv.org/abs/2406.18665) ]

 
 
 

Our core features include:

- Drop-in replacement for OpenAI's client (or launch an OpenAI-compatible server) to route simpler queries to cheaper models.
- Trained routers are provided out of the box, which we have shown to **reduce costs by up to 85%** while maintaining **95% GPT-4 performance** on widely-used benchmarks like MT Bench.
- Benchmarks also demonstrate that these routers achieve the same performance as commercial offerings while being **>40% cheaper**.
- Easily extend the framework to include new routers and compare the performance of routers across multiple benchmarks.

## Installation

**From PyPI**

```
pip install "routellm[serve,eval]"
```

**From source**

```
git clone https://github.com/lm-sys/RouteLLM.git
cd RouteLLM
pip install -e .[serve,eval]
```

## Quickstart

Let's walkthrough replacing an existing OpenAI client to route queries between LLMs instead of using only a single model.

1. First, let's replace our OpenAI client by initializing the RouteLLM controller with the `mf` router. By default, RouteLLM will use the best-performing config:

```python
import os
from routellm.controller import Controller

os.environ["OPENAI_API_KEY"] = "sk-XXXXXX"
# Replace with your model provider, we use Anyscale's Mixtral here.
os.environ["ANYSCALE_API_KEY"] = "esecret_XXXXXX"

client = Controller(
  routers=["mf"],
  strong_model="gpt-4-1106-preview",
  weak_model="anyscale/mistralai/Mixtral-8x7B-Instruct-v0.1",
)
```

Above, we pick `gpt-4-1106-preview` as the strong model and `anyscale/mistralai/Mixtral-8x7B-Instruct-v0.1` as the weak model, setting the API keys accordingly. You can route between different model pairs or providers by updating the model names as described in [Model Support](#model-support).

Want to route to local models? Check out [Routing to Local Models](examples/routing_to_local_models.md).

1. Each routing request has a *cost threshold* that controls the tradeoff between cost and quality. We should calibrate this based on the types of queries we receive to maximize routing performance. As an example, let's calibrate our threshold for 50% GPT-4 calls using data from Chatbot Arena.

```
> python -m routellm.calibrate_threshold --routers mf --strong-model-pct 0.5 --config config.example.yaml
For 50.0% strong model calls for mf, threshold = 0.11593
```

This means that we want to use

*… (11,433 more characters — see results.json for full text)*

---

### 12. [2406.18665] RouteLLM: Learning to Route LLMs with Preference Data
**URL:** https://arxiv.org/abs/2406.18665
**Published:** 2024-06-26T19:34:23.000Z

[2406.18665] RouteLLM: Learning to Route LLMs with Preference Data

# Computer Science > Machine Learning

arXiv:2406.18665 (cs)

[Submitted on 26 Jun 2024 (v1), last revised 23 Feb 2025 (this version, v4)]

# Title:RouteLLM: Learning to Route LLMs with Preference Data

View PDF HTML (experimental)

> Abstract:Large language models (LLMs) exhibit impressive capabilities across a wide range of tasks, yet the choice of which model to use often involves a trade-off between performance and cost. More powerful models, though effective, come with higher expenses, while less capable models are more cost-effective. To address this dilemma, we propose several efficient router models that dynamically select between a stronger and a weaker LLM during inference, aiming to optimize the balance between cost and response quality. We develop a training framework for these routers leveraging human preference data and data augmentation techniques to enhance performance. Our evaluation on widely-recognized benchmarks shows that our approach significantly reduces costs-by over 2 times in certain cases-without compromising the quality of responses. Interestingly, our router models also demonstrate significant transfer learning capabilities, maintaining their performance even when the strong and weak models are changed at test time. This highlights the potential of these routers to provide a cost-effective yet high-performance solution for deploying LLMs.

arXiv-issued DOI via DataCite

| Subjects: | Machine Learning (cs.LG); Artificial Intelligence (cs.AI); Computation and Language (cs.CL) |
| --- | --- |
| Cite as: | arXiv:2406.18665 [cs.LG] |
| (or arXiv:2406.18665v4 [cs.LG] for this version) |

## Submission history

From: Isaac Ong [view email] [v1] Wed, 26 Jun 2024 18:10:22 UTC (580 KB) [v2] Mon, 1 Jul 2024 05:38:08 UTC (623 KB) [v3] Sun, 21 Jul 2024 10:33:08 UTC (623 KB) [v4] Sun, 23 Feb 2025 08:50:33 UTC (782 KB)

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

Spa

*… (920 more characters — see results.json for full text)*

---

### 13. Untitled
**URL:** https://openreview.net/pdf?id=8sSqNntaMr

Published as a conference paper at ICLR 2025
ROUTELLM: LEARNING TO ROUTE LLMS WITH
PREFERENCE DATA
Isaac Ong∗1 Amjad Almahairi∗2 Vincent Wu1 Wei-Lin Chiang1 Tianhao Wu1
Joseph E. Gonzalez1 M Waleed Kadous3Ion Stoica1,2
1UC Berkeley 2Anyscale 3Canva
ABSTRACT
Large language models (LLMs) excel at a wide range of tasks, but choosing the
right model often involves balancing performance and cost. Powerful models offer
better results but are expensive, while smaller models are more cost-effective but
less capable. To address this trade-off, we introduce a training framework for
learning efficient router models that dynamically select between a stronger and
weaker LLM during inference. Our framework leverages human preference data
and employs data augmentation techniques to enhance performance. Evaluations
on public benchmarks show that our approach can reduce costs by over 2 times
without sacrificing response quality. Moreover, our routers exhibit strong generalization capabilities, maintaining performance even when routing between LLMs
not included in training. This highlights the potential of our framework to deliver
cost-effective, high-performance LLM solutions.
1 INTRODUCTION
Recent advances in large language models (LLMs) have demonstrated remarkable capabilities across
a wide range of natural language tasks. From open-ended conversation and question answering to
text summarization and code generation, LLMs have demonstrated an impressive level of fluency and
understanding (Achiam et al., 2023; Bubeck et al., 2023). This rapid progress has been enabled by a
combination of architectural innovations, such as the Transformer architecture (Vaswani et al., 2017),
as well as scaling up data and training infrastructure (Brown et al., 2020; Radford et al., 2019).
However, not all LLMs are created equal—there exists wide variation in the sizes of different LLMs,
which in turn affects the resources required to serve them. LLMs also differ in terms of the data on
which they are trained, which in turn leads to variations in the strengths, weaknesses, and capabilities
of different models. Broadly speaking, larger models tend to be more capable but come at a higher
cost, while smaller models tend to be less capable but cheaper to serve.
This heterogeneous landscape presents a dilemma in the practical deployment of LLMs. Although
routing all user queries to the largest and most capable model ensures high-quality results, it is
prohibitively expensive. Conversely, routing queries to smaller models can save costs—by more than
50x (e.g., Claude-3 Haiku vs. Opus1)—but may result in lower quality responses, as the smaller
model may not handle complex queries effectively.
LLM routing (Ding et al., 2024; Hu et al., 2024) offers an effective solution by first processing each
user query through a router, which then determines the most suitable LLM to handle the query. The
router can direct simpler queries to smaller models and more complex ones to larger models, thereb

*… (22,000 more characters — see results.json for full text)*

---

### 14. RouteLLM: Learning to Route LLMs from Preference Data | OpenReview
**URL:** https://openreview.net/forum?id=8sSqNntaMr
**Published:** 2024-10-04T08:48:04.000Z

RouteLLM: Learning to Route LLMs from Preference Data | OpenReview

## RouteLLM: Learning to Route LLMs from Preference Data

### Isaac Ong, Amjad Almahairi, Vincent Wu, Wei-Lin Chiang, Tianhao Wu, Joseph E. Gonzalez, M Waleed Kadous, Ion Stoica

ICLR 2025 PosterEveryone Revisions BibTeX CC BY 4.0

Keywords: Large language models, query routing

Abstract: Large language models (LLMs) excel at a wide range of tasks, but choosing the right model often involves balancing performance and cost. Powerful models offer better results but are expensive, while smaller models are more cost-effective but less capable. To address this trade-off, we introduce a training framework for learning efficient router models that dynamically select between a stronger and weaker LLM during inference. Our framework leverages human preference data and employs data augmentation techniques to enhance performance. Evaluations on public benchmarks show that our approach can reduce costs by over 2 times without sacrificing response quality. Moreover, our routers exhibit strong generalization capabilities, maintaining performance even when routing between LLMs not included in training. This highlights the potential of our framework to deliver cost-effective, high-performance LLM solutions.

Primary Area: generative models

Code Of Ethics: I acknowledge that I and all co-authors of this work have read and commit to adhering to the ICLR Code of Ethics.

Submission Guidelines: I certify that this submission complies with the submission instructions as described on https://iclr.cc/Conferences/2025/AuthorGuide.

Anonymous Url: I certify that there is no URL (e.g., github page) that could be used to find authors’ identity.

No Acknowledgement Section: I certify that there is no acknowledgement section in this submission for double blind review.

Submission Number: 13083

Loading

---

### 15. RouteLLM: Learning to Route LLMs with Preference Data - Paper Detail
**URL:** https://deeplearn.org/arxiv/511813/routellm:-learning-to-route-llms-with-preference-data

RouteLLM: Learning to Route LLMs with Preference Data - Paper Detail

### RouteLLM: Learning to Route LLMs with Preference Data

- 0
- Isaac Ong, Amjad Almahairi, Vincent Wu, Wei-Lin Chiang, Tianhao Wu, Joseph E. Gonzalez, M Waleed Kadous, Ion Stoica
- 2024-07-21 11:33:08

### Abstract

Large language models (LLMs) exhibit impressive capabilities across a widerange of tasks, yet the choice of which model to use often involves a trade-offbetween performance and cost. More powerful models, though effective, come withhigher expenses, while less capable models are more cost-effective. To addressthis dilemma, we propose several efficient router models that dynamicallyselect between a stronger and a weaker LLM during inference, aiming to optimizethe balance between cost and response quality. We develop a training frameworkfor these routers leveraging human preference data and data augmentationtechniques to enhance performance. Our evaluation on widely-recognizedbenchmarks shows that our approach significantly reduces costs-by over 2 timesin certain cases-without compromising the quality of responses. Interestingly,our router models also demonstrate significant transfer learning capabilities,maintaining their performance even when the strong and weak models are changedat test time. This highlights the potential of these routers to provide acost-effective yet high-performance solution for deploying LLMs.

### Quick Read (beta)

loading the full paper ...

Example heading Example heading Example heading --

Arxiv PDF Mendeley

---
