# What Every Data / Backend Engineer Should Know About AI

A pragmatic Q&A bank for engineers who don't build models for a living but increasingly need to *use* AI, build on top of LLMs, and collaborate with ML teams. Covers core concepts, the modern AI workflow, RAG/agents, prompting, evaluation, safety, productivity, and career-level skills.

---

## 1. Mental Models

### 1. What is "AI" today, in practice?
For most engineering work today, "AI" means:
1. Classical ML (supervised models for prediction/classification, recommenders, time-series).
2. Deep learning (CV, NLP, speech).
3. Foundation models / LLMs (GPT, Claude, Gemini, Llama, Mistral) used via prompting, RAG, fine-tuning, or agents.
4. Multimodal models (vision + language + audio).
Engineers integrate these into products, data pipelines, and dev workflows.

### 2. ML vs Deep Learning vs Generative AI vs Agents.
- **ML**: statistical patterns from data — linear, trees, gradient boosting, etc.
- **Deep learning**: neural nets with many layers — CV, NLP, speech.
- **Generative AI**: models that produce new content (text, image, code, audio).
- **Agents**: LLMs that pick + chain tools (search, code exec, APIs) to accomplish goals.
You'll encounter all four in modern stacks.

### 3. What is a foundation model?
A large model pretrained on broad data, usable across many tasks via prompting / fine-tuning. LLMs are the most visible kind. They're general-purpose primitives — like a CPU, you compose around them rather than treating each as bespoke.

### 4. Training vs inference vs fine-tuning vs prompting — fastest mental map.
- **Training** (pretraining): build a model from scratch, huge compute, only big labs.
- **Fine-tuning**: adapt an existing model to your task — moderate compute.
- **PEFT / LoRA**: cheap fine-tuning of small adapters on a frozen base.
- **Prompting**: change the input — zero training, instant.
- **RAG**: prompting + retrieved context — change behavior without training.
- **Inference**: running the trained model. This is what your prod serves.

### 5. Tokens, context window, parameters.
- **Token**: a chunk of text (~¾ of a word). Models read/write in tokens; pricing and limits are per token.
- **Context window**: max tokens (input + output) per call (8k → 1M+).
- **Parameters**: weights of the model (1.5B, 7B, 70B, 405B). More ≠ always better; quality also depends on data and post-training.

### 6. Why LLMs hallucinate.
They predict the next token; "true" and "plausible" can diverge. They don't *know* facts; they pattern-match. Mitigations: RAG (give them facts), function calling (let them ask), citations (ground claims), eval gates, smaller temperature, narrower scope of question.

### 7. Probabilistic, not deterministic.
LLMs sample outputs. Two calls with same input can differ. Mitigate with `temperature=0`, `seed` (where supported), schema-constrained outputs (JSON mode, function calling). Design downstream systems to tolerate variance, validate outputs, and retry.

### 8. Cost of being wrong.
Classify your use case by cost-of-error: low (autocomplete suggestion), medium (draft email), high (financial decision, medical advice). Higher cost → smaller temperature, stricter validation, human review, more conservative prompts, fallback paths.

---

## 2. The Modern AI / LLM Workflow

### 9. End-to-end LLM app workflow.
1. **Frame the task** clearly: inputs, outputs, success metric.
2. **Pick a baseline** model (start with the most capable, then optimize).
3. **Prompt design** + small eval set (10–100 examples).
4. **Retrieve context** (RAG) if knowledge is needed.
5. **Test** on golden examples + LLM-as-judge + edge cases.
6. **Ship** behind a feature flag with logging.
7. **Monitor** quality, cost, latency.
8. **Iterate** prompt → retrieval → model → fine-tune in that order of effort.

### 10. Classical ML workflow.
Define problem → gather data → EDA → feature engineering → train baseline → iterate models + features → eval on holdout → register → deploy (online/batch) → monitor → retrain. Same skeleton fits classical ML, deep learning, and LLM fine-tuning.

### 11. When to use ML at all.
Use ML when (a) the input → output mapping is fuzzy and (b) you have data showing the mapping. If you can write rules, write rules. ML adds maintenance burden — data drift, retraining, monitoring. Don't ML what `if/else` solves cleaner.

### 12. When to reach for an LLM.
Tasks needing language understanding, generation, summarization, classification of free text, code work, multi-step reasoning with tools, structured extraction from unstructured input. Use specialized models for narrow tasks (classification can be a fine-tuned BERT for 1/100 the cost).

### 13. When NOT to use an LLM.
Deterministic computations, simple lookups, transactions requiring strict correctness, latency-critical hot paths (<10 ms), high-volume real-time scoring with stable schema. Don't ship an LLM where a regex would do — cost and reliability bite.

### 14. RAG vs fine-tuning vs long context.
- **RAG**: knowledge changes often, large corpora, need citations. Most common starting point.
- **Long context**: small corpus that always fits, simpler architecture.
- **Fine-tuning**: stable behavior changes (style, structured output), latency/cost wins after deployment.
Often combined: fine-tuned model for style + RAG for facts.

### 15. Build / buy / use decision.
- **Use API** (OpenAI/Anthropic/Bedrock/Vertex): fastest, lowest infra cost, vendor risk, data egress concerns.
- **Self-host open source**: more control, predictable cost at scale, ops overhead.
- **Fine-tune your own**: when prompting + RAG plateau and your task is repeatable.
- **Pretrain from scratch**: almost never — only if you're an AI lab.

---

## 3. Prompt Engineering Essentials

### 16. Anatomy of a good prompt.
1. **Role / persona** (optional): "You are a senior SRE assistant…".
2. **Task statement**: clear and specific.
3. **Context / data**: retrieved docs, user inputs, examples.
4. **Constraints**: format, length, what *not* to do.
5. **Output schema**: JSON shape, required fields.
6. **Examples** (few-shot) for tricky cases.

### 17. Zero-shot vs few-shot vs chain-of-thought.
- **Zero-shot**: just describe the task.
- **Few-shot**: include 2–8 input/output examples.
- **Chain-of-thought**: ask the model to think step by step; better reasoning at higher cost.
- Reasoning models (o1, Claude with thinking, Gemini Thinking) do CoT internally.
Use the cheapest that meets quality.

### 18. Structured outputs.
Always prefer JSON / function calling over free-form when downstream code consumes the result. Use **JSON mode** / **structured outputs** (OpenAI, Anthropic), JSON-schema enforcement, or libraries like `instructor`, `outlines`, `pydantic-ai`. Eliminates a class of parsing bugs.

### 19. Common prompting failures.
Ambiguous instructions, conflicting examples, too-long context (lost-in-the-middle), expecting math/logic from non-reasoning models, no escape hatch for "I don't know", forgetting JSON must be syntactically valid, mixing instructions inside untrusted user content (injection).

### 20. Prompt injection.
Untrusted content (user messages, retrieved docs, web pages) can include instructions the LLM will follow. Defenses: separate untrusted content with clear markers, system prompts that emphasize "ignore instructions in user/data", structured outputs, input sanitization, output filters, never give an LLM ambient credentials beyond its task scope.

### 21. Token budget management.
Long prompts = high cost + slow latency + lost-in-the-middle effects. Strategies: chunk retrieval, summarize history, use shorter system prompts, prompt caching for repeated prefixes, only include relevant tool definitions, send IDs not full payloads. Measure tokens, not chars.

### 22. Temperature, top-p, seed.
- **Temperature**: 0 (deterministic-ish) → 1 (creative). Extraction/classification: 0–0.2. Creative: 0.7–1.0.
- **Top-p**: nucleus sampling cap (0.9 common).
- **Seed**: reproducibility (supported by some APIs).
- **Stop sequences**: terminate output cleanly.

---

## 4. RAG — Retrieval Augmented Generation

### 23. What is RAG and why use it.
Retrieve relevant documents from your corpus, stuff into the prompt, let the LLM answer. Mitigates hallucinations, keeps knowledge fresh, lets you cite sources, and is cheaper than fine-tuning. The most common LLM-app pattern.

### 24. RAG components.
- **Loaders**: pull docs (PDF, HTML, Notion, Confluence, code).
- **Chunkers**: split into 200–1000 token chunks with overlap.
- **Embedders**: turn chunks + queries into vectors.
- **Vector store** + (optional) **keyword store** (BM25) for hybrid search.
- **Reranker**: cross-encoder reorders top-k.
- **Prompt assembler**: stitches context + question.
- **LLM** generates with citations.

### 25. Chunking strategies.
- **Fixed size** by tokens — simple, ignores structure.
- **Recursive splitter** — break on headings, paragraphs, sentences.
- **Semantic chunking** — embedding-based boundaries.
- **Domain-specific** — code by function, docs by section, transcripts by speaker turn.
Add overlap (10–20%) so concepts spanning boundaries aren't lost.

### 26. Embedding choice.
Use a model fit for your domain and language. Options: `text-embedding-3-large` (OpenAI), `bge-large-en` (open), Cohere, Voyage. Test recall@k on a golden set, not vendor benchmarks. Don't mix models in one index.

### 27. Hybrid search.
Combine **dense** (vector) and **sparse** (BM25 / keyword) retrieval, then merge (reciprocal rank fusion). Dense handles paraphrase, sparse handles exact terms (model numbers, function names). Both perform better than either alone for most enterprise corpora.

### 28. Rerankers.
Cross-encoder model that takes (query, passage) pairs and scores. Run on top-N from retriever to produce top-K for the prompt. Massive precision boost. Examples: Cohere Rerank, bge-reranker, Voyage rerank.

### 29. Evaluating RAG quality.
- **Retrieval**: recall@k, MRR — does the right doc come back?
- **Generation**: groundedness (claims supported by retrieved docs), answer relevance, citation correctness.
- **End-to-end**: human eval, LLM-as-judge, A/B in production.
Tools: Ragas, TruLens, LangSmith, Phoenix.

### 30. Common RAG failure modes.
Bad chunking (loses context), wrong embedding model for the language/domain, retrieval recall low (right doc not in top-k), prompt loses context to "lost in the middle", LLM ignores citations, retrieval works but model paraphrases away the facts. Diagnose each stage independently.

---

## 5. Agents & Tool Use

### 31. What is an agent?
An LLM in a loop: at each step it picks an action (call a tool, reply to user), observes the result, and continues until done. Capable of multi-step reasoning, but expensive, slow, and harder to verify than single-shot LLM calls.

### 32. Tools / function calling.
LLM is given a list of tool schemas (name, args, description). It can decide to "call" one; your code executes it and returns the result; LLM continues. Foundational primitive for agents, structured outputs, and giving LLMs access to real data and actions.

### 33. Patterns: reflection, planning, react.
- **ReAct**: reason → act → observe → reason loop.
- **Planner-executor**: planner LLM lays out steps, executor runs them.
- **Reflection**: LLM critiques and revises its own output.
- **Multi-agent**: specialized agents (researcher, coder, reviewer) collaborate.
Add complexity only when it earns its keep on your evals.

### 34. Guardrails for agents.
Hard caps on tool calls per request, total tokens, time budget. Tool allowlists per use case. Dry-run mode for destructive tools. Approval steps for high-stakes actions (sending email, executing trades). Log everything for replay.

### 35. Agent evaluation.
Trace-level metrics: success rate on tasks, average steps, average cost, tool-call accuracy, error recovery. Replayable traces (LangSmith, Langfuse) are essential — debugging by reading logs only is painful.

### 36. When agents are overkill.
For single-purpose extraction, classification, summarization, or one-shot generation, a direct prompt is faster, cheaper, and more reliable. Use agents when the workflow truly branches based on intermediate results.

---

## 6. Evaluation & Testing

### 37. Why eval is the bottleneck.
Without an eval, you can't tell if a prompt change, model swap, or new retriever helps or hurts. Engineers from traditional SWE backgrounds often skip this — and ship regressions. Build an eval before iterating.

### 38. Golden datasets.
Curate 50–500 representative inputs with expected outputs / criteria. Cover happy paths, edge cases, adversarial inputs, common mistakes. Refresh quarterly. Treat them like critical test fixtures — they are.

### 39. LLM as judge.
Use a strong LLM to grade outputs of another LLM against a rubric. Fast, scalable, biased (favors models from same family, longer answers). Calibrate against human ratings on a sample. Useful for ranking and regression catching, not final truth.

### 40. Pairwise comparison.
Show two outputs (A vs B) to judge/human, pick winner. More robust than absolute scoring. Aggregate into Elo / win-rate. Common for benchmarking models or prompt variants.

### 41. Online metrics.
Real users beat any offline eval. Track satisfaction (thumbs up/down), task completion, follow-up rate, business KPIs. A/B test prompt + model + retrieval changes. Always have a kill switch.

### 42. Regression testing for LLM apps.
- Static unit tests on prompt rendering (templates compile, schemas validate).
- Golden-set eval in CI: run a subset on every PR, full suite nightly.
- Block deploy on regression beyond a threshold.
- Track quality + cost + latency over time, not just point-in-time pass/fail.

---

## 7. Productivity — Using AI as an Engineer

### 43. AI coding assistants.
Copilot, Cursor, Windsurf, Cline, Aider, Claude Code, Continue.dev — IDE-integrated LLMs that suggest/edit/refactor. Productivity gains real but vary by task: ~20–55% on focused tasks, less on systems-level work. Use them; verify their output.

### 44. How to use AI assistants well.
- Treat suggestions as drafts; review every line.
- Give them context (file paths, intent, constraints).
- Pair with your tests — refuse to merge without them.
- Don't outsource design decisions to the LLM.
- Watch for confidently wrong code: subtle race conditions, security holes, deprecated APIs.

### 45. AI for code review.
LLMs can pre-review PRs for style, obvious bugs, missing tests, security smells. Useful as a *first* pass, not a replacement for senior review. Tools: CodeRabbit, Greptile, GitHub Copilot review, custom GH Actions calling an LLM.

### 46. AI for docs and design.
Drafting design docs, READMEs, API docs, architecture diagrams (Mermaid), runbooks. Big speedup; you still own the content. Use LLMs to explain unfamiliar codebases by piping in files and asking targeted questions.

### 47. AI for data work.
Generating SQL from natural language (with schema in prompt), explaining slow queries, suggesting indexes, drafting dbt models, summarizing data quality reports. Always verify output on a sample — LLMs invent column names confidently.

### 48. AI for debugging and ops.
Paste a stack trace + relevant code → likely cause + fix. Summarize logs around an incident. Generate Prometheus queries / Splunk queries from descriptions. Great accelerator; not a substitute for reading code carefully on hard bugs.

### 49. Limits and risks of AI assistants.
Code may be plagiarized (license risk), insecure (SQL injection, hardcoded secrets, weak crypto), outdated (older library versions), confidently wrong on rare APIs, leaking private code via cloud APIs (use enterprise tiers with no-train policies). Set company policy before adoption.

---

## 8. Safety, Privacy, Compliance

### 50. Responsible AI basics.
Know your model's intended use, document training data sources, evaluate across demographic slices, provide opt-outs, log decisions, allow appeals on automated decisions. Concrete frameworks: NIST AI RMF, ISO/IEC 42001, EU AI Act risk tiers.

### 51. PII and data privacy.
Don't send PII to third-party LLMs without contractual protection. Use enterprise endpoints (zero-retention), redact PII before sending (Presidio, Microsoft Purview), prefer on-prem / VPC-private endpoints for sensitive data. GDPR / HIPAA / CCPA still apply.

### 52. Copyright and licensing.
LLM-generated code may resemble training data. Use vendor commitments (Copilot indemnification, OpenAI IP protection), avoid known proprietary names in prompts, scan generated code for license headers. Same caution for images / text.

### 53. Bias and fairness.
LLMs reflect their training data. Test outputs across user demographics, languages, dialects, geographies. Measure refusal rates, sentiment, accuracy by slice. Mitigations: better prompts, fine-tuning on diverse data, post-processing, human review for high-stakes use.

### 54. Auditability.
For regulated industries (finance, health, hiring), log every model call: input, output, model version, prompt version, retrieved docs, user, timestamp, decision. Be able to reproduce any decision. Treat this like financial transaction logging.

### 55. Security — new attack surface.
Top risks (OWASP LLM Top 10): prompt injection, insecure output handling (LLM output executed without sanitization), training data poisoning, model DoS (huge inputs), supply chain (poisoned weights), sensitive info disclosure, insecure plugin design, excessive agency (over-broad tools), overreliance, model theft.

### 56. Red-teaming.
Adversarial testing: try to jailbreak the model, exfiltrate data via prompt injection, abuse agents, get it to produce harmful content. Internal red team or vendors (Lakera, HiddenLayer). Findings drive guardrails, prompt revisions, system architecture changes.

---

## 9. Operating AI in Production

### 57. Logging & observability for AI apps.
Per-request log: prompt, response, model, temperature, tokens (in/out), tool calls, latency, cost, user_id, trace_id. Persist with PII handling rules. Use platforms (LangSmith, Langfuse, Phoenix, Helicone) or build on top of OpenTelemetry.

### 58. Cost monitoring.
Per-feature, per-user, per-tenant cost dashboards. Alert on anomalies (cost suddenly 10× — usually a runaway agent or unhandled retry). Set hard caps. Compare $/successful task across model choices.

### 59. Latency monitoring.
TTFT (time to first token) for streaming UIs matters more than total time. Track p50/p95/p99 separately. Streaming hides slow models from users perceptually; measure user-perceived latency end-to-end.

### 60. Fallbacks and graceful degradation.
Primary model down → fallback model. RAG retriever down → "I don't have enough info" rather than hallucinate. Time budget exceeded → return partial best-effort response. Always have a deterministic fallback for the worst case.

### 61. Caching.
- **Exact**: identical prompt → cached response.
- **Semantic**: embed query, return cached response if similar enough.
- **Prompt prefix caching** (Anthropic / OpenAI): pay once for the long system prompt, reuse cheaply.
Big wins for repetitive workloads; risk of staleness — version cache keys with prompt version.

### 62. Rate limiting and quotas.
Per-user, per-API-key, per-tenant. Different limits per cost tier. Without limits, one user (or bug) can blow the monthly budget in hours. Combine with circuit breakers on upstream LLM providers (they have outages).

### 63. Feature flags for AI features.
Roll out to 1% → 10% → 100%. Allow per-tenant override. Kill switch to a previous model version. Combine with online metrics to roll back automatically on regression.

---

## 10. Skills Engineers Should Build

### 64. Core data skills.
SQL, Python, distributed compute (Spark or equivalent), data modeling, batch + streaming pipelines, schema evolution, data quality. These don't go away when AI shows up — they become more valuable because AI systems are data-hungry.

### 65. Core SWE skills.
Strong reasoning about correctness, testing, observability, security, debugging, code review, system design. AI assistants amplify good engineers and amplify bad habits — invest in fundamentals.

### 66. AI-adjacent skills to add.
- Solid mental model of how transformers / LLMs work at a high level.
- Prompt engineering and structured outputs.
- RAG architecture: chunking, embeddings, vector DBs, retrieval eval.
- Tool / function calling and basic agent patterns.
- LLM evaluation: golden sets, LLM-as-judge, online A/B.
- Cost and latency optimization for LLM workloads.
- AI safety basics: prompt injection, PII, policy.

### 67. Math and ML you actually need.
You don't need a PhD. You do need:
- Probability and statistics (distributions, tests, sampling).
- Linear algebra basics (vectors, similarity).
- Loss functions, gradient descent, overfitting concepts.
- Embeddings, similarity, dimensionality.
- Cross-validation and metric design.
Enough to *collaborate* with ML engineers and reason about results.

### 68. Tools to be comfortable with.
- **Frameworks**: PyTorch (read it, don't have to write training code).
- **LLM SDKs**: OpenAI, Anthropic, Bedrock, Vertex.
- **Orchestration**: LangChain / LlamaIndex / LangGraph or DIY.
- **Vector DBs**: pgvector + at least one specialized (Pinecone/Weaviate/Qdrant).
- **Eval**: LangSmith / Phoenix / Ragas.
- **Serving**: vLLM / Triton / KServe basics.
- **MLOps**: MLflow / W&B / Vertex / SageMaker.

### 69. Soft skills.
Communicate uncertainty clearly (LLMs are probabilistic). Translate between business stakeholders and ML teams. Push back on AI hype when a simpler solution wins. Insist on evals before iteration. Document model assumptions and limitations.

### 70. Staying current.
Read: Hacker News, Latent Space podcast, Simon Willison's blog, Andrej Karpathy's videos, Anthropic / OpenAI cookbooks, papers (Attention Is All You Need, GPT-3, InstructGPT, Llama 2/3, RAG, DPO, RLHF, ReAct, Toolformer). Build small projects monthly — reading alone doesn't stick.

---

## 11. Career & Org-Level Thinking

### 71. Career paths intersecting AI.
- **Data engineer**: pipelines for AI training/serving, feature stores, vector data.
- **ML/AI engineer**: model training + serving + evaluation.
- **AI platform engineer**: GPU clusters, training infra, serving infra.
- **AI application engineer**: products on top of LLMs.
- **AI safety/governance**: policy, red-teaming, compliance.
- **Research**: novel architectures, training methods.
All of these are growing; most engineers will end up somewhere on the spectrum.

### 72. Adopting AI inside your team.
Pilot use case → pick clear metric → run with one team → eval → expand. Don't ship a chatbot without a problem statement. Common winners early: internal docs Q&A, support ticket triage, code review assistants, marketing copy drafting, log/incident summarization.

### 73. Org maturity stages.
1. Ad-hoc API calls in apps.
2. Shared prompt library + basic eval.
3. RAG platform + vector store + monitoring.
4. Fine-tuning + multi-model routing + cost dashboards.
5. Multi-team AI platform + governance + safety + on-prem.
Most orgs are at stages 1–3; pretend you're at 5 only if you actually are.

### 74. Failure stories to learn from.
Lawyer's case-citations hallucinated. Customer support bot promising refunds it can't honor. Healthcare chatbot recommending dangerous advice. Image generator producing biased outputs. Recurring theme: shipped without evals, guardrails, or human-in-the-loop for high-stakes actions.

### 75. The honest summary.
AI tools are now part of the engineering toolkit, like databases or Git. Learn enough to (a) make informed build/buy decisions, (b) ship LLM features safely, (c) be productive using AI as a daily assistant, and (d) talk credibly with ML peers. You don't need to invent the next architecture; you do need to integrate this generation of tools well into reliable systems.
