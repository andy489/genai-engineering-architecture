# Reliability, SLOs, and Incident Management for GenAI Systems

Production reliability engineering for GenAI systems: defining and measuring SLIs/SLOs/SLAs, applying resilience patterns, and running effective incident response. Covers the gap between uptime monitoring and quality-aware reliability, from failure mode analysis through blameless postmortems.

All four modules are consolidated into a single notebook: [`reliability-slos-incident-management-gen-ai-systems.ipynb`](reliability-slos-incident-management-gen-ai-systems.ipynb)

## Modules

| # | Title | Topics |
|---|---|---|
| 01 | Production Reliability Fundamentals | Uptime vs. reliability, GenAI dependency graph, soft failures, graceful degradation, failure mode analysis, synthetic probes |
| 02 | SLIs, SLOs, and SLAs for GenAI Services | SLI domains, latency/error/quality/cost SLIs, SLO baselines, error budgets, SLA translation |
| 03 | Failure Handling and Resilience Patterns | Timeouts, bounded retries, circuit breakers, bulkheads, fallbacks, Redis cache, idempotent tool calls |
| 04 | Incident Response and Operational Excellence | Incident lifecycle, on-call roles, severity classification, signal correlation, retrieval drift, postmortems |

## Demos

| Directory | Description |
|---|---|
| [`01-production-reliability-demos/`](01-production-reliability-demos/) | Health check endpoints and synthetic probes with OpenTelemetry |
| [`02-slis-slos-demos/`](02-slis-slos-demos/) | Prometheus SLI instrumentation in FastAPI; SLO dashboards and burn-rate alerts |
| [`03-resilience-patterns-demos/`](03-resilience-patterns-demos/) | HTTPX retry/circuit breaker implementation; Toxiproxy chaos testing with Redis fallbacks |
| [`04-incident-response-demos/`](04-incident-response-demos/) | Prometheus AlertManager escalation; blameless postmortem workflow with MTTR tracking |

## Assets

The [`assets/`](assets/) directory contains architecture diagrams extracted from the course:

- `01-genai-dependency-graph.png` — Full GenAI request flow with orchestrator, retrieval, model, and tool boundaries
- `02-dependency-boundaries-stress-signals.png` — Dependency boundary groupings and alert indicator positions
- `03-latency-slis-by-request-stage.png` — Per-stage SLI breakdown across retrieval, model inference, and tools
- `04-one-request-three-views.png` — Correlating metrics, traces, and logs via shared `request_id` and `timestamp`
