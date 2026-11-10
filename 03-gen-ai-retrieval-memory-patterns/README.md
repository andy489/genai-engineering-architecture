# GenAI Retrieval and Memory Patterns

Covers the architecture and engineering of Retrieval-Augmented Generation (RAG) systems — from the core five-stage pipeline through hybrid search, query transformation, context and memory management, and production-grade async scaling with caching.

All four modules are consolidated into a single notebook: [`gen-ai-retrieval-memory-patterns.ipynb`](gen-ai-retrieval-memory-patterns.ipynb)

## Modules

| # | Title | Topics |
|---|---|---|
| 01 | Building Scalable RAG Architectures | RAG pipeline stages, vector embeddings, document chunking, hybrid search, query transformation, re-ranking |
| 02 | Optimizing and Scaling RAG for Enterprise Systems | Production-ready RAG, query classification, adaptive retrieval (BM25 + vector), Reciprocal Rank Fusion (RRF), context assembly |
| 03 | Optimizing Context and Memory Management | Retrieval vs. memory, episodic/semantic/procedural memory types, short- and long-term memory augmentation |
| 04 | Caching, Optimizing, and Monitoring Performance | Async RAG pipeline, semantic caching, multi-user concurrency control, enterprise scaling |

## Demo Projects

Each module has hands-on exercises with `start/` (skeleton) and `end/` (completed) states:

- [`01-scalable-rag-demos/`](01-scalable-rag-demos/) — Basic RAG query engine (1.1–1.2) and chunking/hybrid search exercises (1.3–1.5) with LlamaIndex
- [`02-enterprise-rag-demos/`](02-enterprise-rag-demos/) — Production-ready RAG with HyDE, query routing, BM25+vector retrieval, and RRF (2.1–2.2)
- [`03-context-memory-demos/`](03-context-memory-demos/) — Full RAG pipeline with Redis short-term memory and Qdrant long-term memory
- [`04-caching-performance-demos/`](04-caching-performance-demos/) — Async RAG pipeline with semantic cache layer and session-scoped memory isolation

## Diagrams

Key architecture diagrams are stored in [`assets/`](assets/) and rendered inline in the notebook.

## Setup

Demos use Python 3.10+ with dependencies on LlamaIndex, LangChain, OpenAI, Cohere, Redis, Qdrant, and LangSmith. Each demo directory contains a `.env.example` — copy it to `.env` and fill in your API keys before running.
