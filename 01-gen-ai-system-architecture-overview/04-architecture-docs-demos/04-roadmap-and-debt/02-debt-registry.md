# Technical debt register

| ID | Debt item | Type | Impact | Effort | Priority | Phase | Status | Notes |
|----|-----------|------|:------:|:------:|----------|-------|--------|-------|
| `DEBT-001` | Prompt templates hardcoded in code | Deliberate | 3 | S | **High (quick win)** | Phase 2 | Open | Templates live inline in `prompt_builder.py`. Move them to versioned `templates/*.j2` so product can iterate without a redeploy. Tied to the upcoming **prompt-versioning** feature ([#1247](../issues/1247)) — pay down at the same time. |
| `DEBT-002` | No automated retrieval relevance testing | Accidental | 4 | M | Medium | Phase 2 | Open | Generation is covered by the eval harness; retrieval is not. Need a frozen golden set with **nDCG@10** in CI. See the [retrieval-eval RFC](../rfcs/0014-retrieval-eval.md). Blocks any future embedding-model swap (cf. `DEBT-004`). |
| `DEBT-003` | Session TTL too aggressive (dropped sessions) | Accidental | 4 | S | **Critical (quick win)** | Phase 1 | In progress | Sessions evict after 5 min of inactivity, dropping multi-turn context mid-conversation. Fix: config bump + sliding-window expiry. PR [#1392](../pulls/1392) up for review. User reports trace to mid-September. |
| `DEBT-004` | Embedding model outdated (`ada-002` → `text-embedding-3-large`) | Environmental | 3 | M | Medium | Phase 2 | Open | Vendor has deprecated `ada-002`. Migration requires re-indexing ~2M docs plus the relevance harness from `DEBT-002`. Expected cost: **+18%**, but materially better recall on long-tail queries. |
| `DEBT-005` | No circuit breaker on LLM API calls | Deliberate | 5 | S | **Critical (quick win)** | Phase 1 | In progress | Shipped without one to hit the launch date. A single provider outage now cascades to full app downtime. Plan: `pybreaker` around `LLMClient.call()`, plus retry-after handling. |

### Legend

- **Type** — `Deliberate` (strategic shortcut) · `Accidental` (didn't realize at the time) · `Environmental` (ecosystem changed)
- **Impact** — 1 (cosmetic) → 5 (production-blocking)
- **Effort** — `S` ≤ 2 days · `M` ≤ 1 sprint · `L` > 1 sprint
- **Quick win** — high impact, low effort. Address immediately, don't wait for a roadmap slot.
