# GloboAssist Stakeholder Communication Templates

> **Purpose:** These templates show how to frame the same architectural change for different audiences. Copy and adapt them for your own system.
>
> **Change:** Extract retrieval into an independent microservice.

---

## 1. Engineering RFC

> **Audience:** Engineering team, tech leads, DevOps
> **Tone:** Detailed, technical, actionable

### RFC-007: Retrieval Service Extraction

**Status:** Proposed
**Author:** Platform Architecture Team
**Related ADR:** ADR-003 (pgvector selection, review trigger approaching)

#### Motivation

GloboAssist's retrieval logic is currently embedded in the Chat Orchestrator. This creates three problems:

1. **Scaling coupling**: retrieval and orchestration scale together even though they have different resource profiles (I/O-bound vs.memory-bound).
2. **Deployment risk**: any change to retrieval (index tuning, model swap) requires redeploying the full orchestrator.
3. **Testing bottleneck**: retrieval relevance tests run inside the full integration suite instead of independently.

#### Plan

- Extract retrieval behind a **gRPC interface** with the contract `retrieve(query, top_k, filters) → List[Document]`.
- Deploy as an independent service with its own scaling policy.
- Add a **circuit breaker** on the orchestrator → retrieval call (fallback: keyword search over product catalog).
- Route via **feature flag**, 10% canary → 50% → 100% over 2 weeks.

#### Timeline

3 sprints (3 weeks), broken into:

- Sprint 1: Extract code, define gRPC contract, deploy canary.
- Sprint 2: Contract tests, relevance regression suite, 50% rollout.
- Sprint 3: 100% rollout, decommission embedded retrieval, update monitoring dashboards.

#### Rollback

Feature flag routes traffic back to the embedded retrieval path.
No data migration required, pgvector instance is shared. Rollback can be triggered in < 5 minutes.

#### Testing

- **Contract tests:** Verify gRPC interface schema + SLO (p95 < 200ms).
- **Relevance regression:** 200 golden queries, assert nDCG@3 ≥ 0.78.
- **E2E regression:** 50 end-to-end test cases, assert total latency < 2s and response quality > 85%.
- **Load test:** Simulate 500 concurrent users during canary phase.

---

## 2. Product Brief

> **Audience:** Product managers, business stakeholders
> **Tone:** Outcome-focused, no jargon

### What's Changing

We're separating GloboAssist's search capability into its own service, think of it as giving search its own "engine" that can be improved independently.

### Why It Matters for Product

This unblocks the **"similar products" recommendation feature** planned for a future release. Today, improving search quality requires redeploying the entire chat system, which means coordinating with three teams and a two-week release cycle. After this change, the search team can ship improvements weekly, without touching chat or copilot.

It also enables us to **swap in better search models** faster. The current embedding model is a year old; the replacement is ready but blocked by this coupling.

### User Impact

**None during migration.** We're using a feature flag to gradually shift traffic. If anything goes wrong, we roll back in under five minutes. Customers won't see any change until we start shipping search improvements afterward.

### Timeline

3 weeks. No product feature freezes required.

---

## 3. Executive Summary

> **Audience:** VP/C-level leadership
> **Tone:** Cost, risk, and strategic return

### Retrieval Service Extraction: Investment Case

| Dimension              | Detail                                  |
|------------------------|-----------------------------------------|
| **Investment**         | $200/mo additional infrastructure       |
| **Return**             | $400/mo savings from independent scaling + elimination of single point of failure for product search (handles 60% of queries) |
| **Net monthly impact** | +$200/mo savings                        |
| **Timeline**           | 3 weeks                                 |
| **Risk**               | Low, feature-flagged rollback in < 5 min |

### Strategic Impact

- **Enables Q3 revenue feature:** "Similar products" recommendations   (est. +3% cart conversion) are blocked until this is complete.
- **Reduces incident risk:** Currently, a search outage takes down the entire chat system. After extraction, search failures degrade gracefully without affecting chat availability.
- **Technical health score:** Improves from 72 → projected 85 (tracked in quarterly architecture review).

### What We Need

Engineering capacity: 2 engineers for 3 weeks (already allocated in Q2 sprint plan). No additional headcount or budget approval required beyond the $200/mo infrastructure delta.
