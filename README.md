# GenAI Engineering Architecture

A collection of course notebooks covering GenAI system design, architecture patterns, and engineering practices.

## Modules

- [GenAI System Architecture Overview](./01-gen-ai-system-architecture-overview/README.md) — Four-layer architecture, RAG/agents/fine-tuning patterns, scaling, API design, and ADRs. Built around the GloboAssist running example.
- [GenAI Data and Knowledge Layer](./02-gen-ai-data-knowledge-layer/README.md) — Embeddings, vector database internals and operations, knowledge graphs, and production ingestion pipelines.
- [GenAI Retrieval and Memory Patterns](./03-gen-ai-retrieval-memory-patterns/README.md) — RAG pipeline stages, hybrid search, query transformation, context and memory management, async scaling, and caching.
- [GenAI Model Access Layer and Structured Outputs](./04-gen-ai-model-access-layer-structured-outputs/README.md) — Production API patterns, structured output validation, advanced prompting, function calling, multimodal pipelines, fine-tuning, and output quality.
- [GenAI Orchestration and Agent Patterns](./05-gen-ai-orchestration-agent-patterns/README.md) — Multi-step reasoning (ReAct, CoT, ToT), planning systems, multi-agent architectures, tool integration and chaining, error handling and guardrails, and production orchestration best practices.
- [GenAI Inference and Serving Architecture](./06-gen-ai-inference-serving-architecture/README.md) — Model inference, efficient model selection, batching and throughput optimization, GPU scaling, cost engineering, and advanced inference techniques (speculative decoding, quantization, attention optimization).
- [LLMOps: Evaluation, Observability, and Quality](./07-llmops-evaluation-observability-quality/README.md) — LLM evaluation metrics and frameworks, structured logging and observability, automated testing strategies, drift detection, model monitoring, and experiment tracking with MLflow.
- [Reliability, SLOs, and Incident Management for GenAI Systems](./08-reliability-slos-incident-management-gen-ai-systems/README.md) — SLI/SLO/SLA definition for GenAI, resilience patterns (circuit breakers, bulkheads, fallbacks), failure mode analysis, synthetic probes, and incident response with blameless postmortems.
- [Safety and Security Architecture for GenAI Systems](./09-safety-security-architecture-gen-ai-systems/README.md) — Adversarial prompt defense, content moderation, PII protection and privacy-preserving techniques, secure deployment, authentication and authorization, threat modeling, and production hardening.
