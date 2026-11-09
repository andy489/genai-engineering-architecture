# GenAI System Architecture Overview

A practical, end-to-end guide to designing, scaling, integrating, and documenting production-grade GenAI systems. All five modules are consolidated into a single notebook that follows the evolution of **GloboAssist** — a real-time customer support platform for a mid-size e-commerce company — from a minimal MVP to a production architecture.

## Notebook

All modules are in one place: **[genai-system-architecture-overview.ipynb](genai-system-architecture-overview.ipynb)**

## Modules

| # | Title | Key topics |
|---|---|---|
| 01 | Understanding Core GenAI System Components | Four-layer architecture, layer contracts, sync/async, stateful/stateless, monolith vs. microservices |
| 02 | Evaluating Architectural Patterns and Trade-offs | RAG, agents, fine-tuning, hybrid; trade-off triangle; hosting strategies; weighted decision framework |
| 03 | Scaling and Optimizing GenAI Performance | Layer-specific scaling, bottleneck resolution, concurrency strategies, KPIs and dashboards |
| 04 | Integrating and Designing APIs for GenAI Systems | Streaming APIs, cancellation, adapter pattern, modular contracts, multi-turn state management |
| 05 | Documenting Architecture Decisions | C4 model, sequence/data flow diagrams, ADRs, roadmaps, technical debt management |

## Demo Directories

| Directory | Module | Description |
|---|---|---|
| [`02-tradeoff-evaluation-demos/`](02-tradeoff-evaluation-demos/) | 02 | Weighted decision matrix spreadsheet for vector database evaluation |
| [`03-performance-demos/`](03-performance-demos/) | 03 | Runnable Python bottleneck demo (`uv run bottleneck_demo.py`) |
| [`04-api-integration-demos/`](04-api-integration-demos/) | 04 | Adapter pattern and state management demos (`uv run state_management_demo.py`) |
| [`05-architecture-docs-demos/`](05-architecture-docs-demos/) | 05 | C4 Mermaid diagrams, a complete ADR, architecture roadmap, and stakeholder templates |

## Assets

The [`assets/`](assets/) directory contains 18 architecture diagrams extracted from the course slides, including sequence diagrams, system architecture flows, the trade-off triangle, C4 model diagrams, and the adapter pattern UML.

## Setup

The bottleneck demo and state management demo use [uv](https://docs.astral.sh/uv/#installation) for dependency management. Install uv then run:

```bash
uv run 03-performance-demos/bottleneck_demo.py
uv run 04-api-integration-demos/state_management_demo.py
```

Alternatively, install dependencies manually:

```bash
pip install -r 03-performance-demos/requirements.txt
python 03-performance-demos/bottleneck_demo.py
```

Mermaid diagrams in `05-architecture-docs-demos/` can be rendered at [mermaid.live](https://mermaid.live) or with the [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli).
