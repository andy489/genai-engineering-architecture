# ADR-003: Use pgvector for Vector Storage

| Field       | Value                                      |
|-------------|--------------------------------------------|
| **Status**  | Accepted                                   |
| **Date**    | 2026-01-15                                 |
| **Authors** | Platform Architecture Team                 |
| **Reviewers** | Engineering Lead, Legal, Finance         |

---

## Context

GloboAssist requires semantic search over 50,000+ product descriptions across all three workloads (Customer Chat, Agent Copilot, Analytics).
We need a vector storage solution that meets the following requirements:

- Integrates with our existing PostgreSQL infrastructure (RDS)
- Supports metadata filtering (category, availability, region)
- Stays within our $500/month retrieval infrastructure budget
- Maintains GDPR compliance — EU customer data must stay in the EU

The team has deep PostgreSQL expertise (5+ years across all backend engineers) but limited experience operating dedicated vector databases.

---

## Decision

Use PostgreSQL with the **pgvector** extension for vector storage. Deploy on the existing Relational Database Service (RDS) instance in both `us-east-1` (NA traffic) and `eu-west-1` (EU traffic) with HNSW indexing.

---

## Alternatives Considered

### 1. Pinecone (managed vector database)

- **Strengths:** Fully managed, strong query performance at scale, purpose-built for vector workloads.
- **Why rejected:** $480/month at our scale (50K vectors, 1536 dimensions) — nearly the full retrieval budget with no room for growth. At the time of evaluation, EU data residency options did not meet Globomantics' specific compliance requirements. Vendor lock-in risk — proprietary API with no migration path.
- **Weighted matrix score:** 72 / 100.

### 2. Self-hosted Qdrant

- **Strengths:** Best-in-class vector search performance, open source, full control over data residency and deployment.
- **Why rejected:** Requires dedicated infrastructure (GPU-optimized instances) and ongoing DevOps investment the team cannot support
  today. Operational overhead of running a new stateful service in two regions.
- **Weighted matrix score:** 62 / 100.

---

## Consequences

### Positive

- **Zero incremental cost** — runs on existing RDS instances, no new infrastructure.
- **Full data residency control** — EU data stays on our RDS in `eu-west-1`, NA data stays in `us-east-1`.
- **Leverages existing expertise** — the team already knows PostgreSQL operations, backup, monitoring, and scaling.
- **Unified data layer** — product metadata and vector embeddings live in the same database, simplifying joins and filtered queries.
- **Large ecosystem** — PostgreSQL tooling, community support, and managed service options reduce long-term risk.

### Negative

- **Potential migration at scale** — pgvector may not match dedicated vector databases in query performance beyond 200K products. This is a known ceiling, not a current problem.
- **HNSW tuning required** — index parameters (`m`, `ef_construction`,   `ef_search`) require experimentation to balance recall vs. latency   for our specific dataset.
- **Not purpose-built** — pgvector is an extension, not a dedicated engine. Advanced features (multi-tenancy, real-time index updates) may lag behind specialized solutions.

---

## Trade-offs Accepted

We accept potentially lower query performance at very high scale in exchange for **operational simplicity**, **cost savings**, and **compliance control**.

This is a deliberate trade-off: we optimize for the team we have and the scale we're at, not for a hypothetical future state.

---

## Review Trigger

Revisit this decision if **any** of the following conditions are met:

- Product count exceeds **200,000** items
- p95 retrieval latency exceeds **200ms** under normal load
- Pinecone or another managed provider offers a compliant EU deployment that meets our data residency requirements
- Team capacity changes to support operating a dedicated vector database

When triggered, create a new review ADR titled **ADR-003-REVIEW** and re-run the weighted decision matrix with updated scores.
