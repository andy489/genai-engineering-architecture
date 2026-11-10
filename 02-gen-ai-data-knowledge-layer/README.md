# GenAI Data and Knowledge Layer

A four-module course covering the data infrastructure that powers modern GenAI systems: how raw text becomes searchable embeddings, the internals and operations of vector databases, knowledge graph design and construction, and production-grade ingestion pipeline architecture.

All modules are consolidated into a single notebook: [`genai-data-knowledge-layer.ipynb`](genai-data-knowledge-layer.ipynb)

---

## Modules

| # | Module | Topics |
|---|---|---|
| 01 | Embeddings and Vector Stores Fundamentals | Vector representations, semantic similarity metrics, embedding model comparison, MTEB |
| 02 | Vector Database Architecture and Operations | HNSW, IVF, PQ, storage strategies, Pinecone/Weaviate/Qdrant/Chroma/pgvector, schema design, production ops |
| 03 | Knowledge Graphs and Structured Knowledge | RDF/OWL, NER, relation extraction, LLM-based graph construction, hybrid retrieval, SPARQL/Cypher |
| 04 | Production Pipelines, Advanced Preprocessing and Synthetic Data | Pipeline architecture, chunking strategies, multi-modal handling, metadata enrichment, Airflow, synthetic QA generation |

---

## Demo Projects

| Directory | Module | Description |
|---|---|---|
| [`01-embeddings-demos/`](01-embeddings-demos/) | 01 | Batch embedding generation with rate limiting, caching, and semantic similarity search |
| [`02-knowledge-graphs-demos/`](02-knowledge-graphs-demos/) | 02 | LangChain graph extraction, graph neural networks, node embeddings, duplicate entity detection |
| [`03-production-pipeline-demos/`](03-production-pipeline-demos/) | 03 | Chunking strategies, metadata enrichment, PDF processing, Airflow DAG orchestration, synthetic data generation |

---

## Assets

The [`assets/`](assets/) directory contains 11 educational diagrams extracted from the slides:

| File | Description |
|---|---|
| `01-text-to-vector-embedding.png` | Text to vector transformation diagram |
| `02-embedding-pipeline-txt-model-vector.png` | Full embedding pipeline: text → model → vector |
| `03-hnsw-flat-graph.png` | HNSW flat layer graph structure |
| `04-hnsw-hierarchical-layers.png` | HNSW hierarchical multi-layer architecture |
| `05-hnsw-entry-point-search.png` | HNSW search entry point and traversal |
| `06-knowledge-graph-example.png` | Knowledge graph example with entities and relations |
| `07-rag-vector-graph-architecture.png` | RAG architecture combining vector store and knowledge graph |
| `08-relation-extraction-example.png` | Relation extraction from text to triples |
| `09-pipeline-orchestration-architecture.png` | Full production pipeline orchestration |
| `10-metadata-injection-flow.png` | Metadata context injection into chunks |
| `11-synthetic-data-generation.png` | Synthetic QA pair generation with LLM |

---

## Setup

The demos use Python. Install dependencies as needed per demo file (LangChain, OpenAI SDK, Airflow, etc. are referenced in the demo scripts). The notebook itself requires only the Python standard library plus `IPython` for diagram rendering.
