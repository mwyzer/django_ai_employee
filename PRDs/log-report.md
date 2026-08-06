# 📝 Log Report: evolution-plan.md Changelog

**File:** `PRDs/evolution-plan.md`  
**Project:** AI Employees — CoolBreeze AC  
**First Created:** 2026-07-25

---

## Change History

### v4.0 — 2026-07-26 — 9-Phase Progressive Architecture (Major Restructure)

**Status:** ✅ Complete — Complete architectural restructure from 12-technology format to 9-phase progressive format

#### The Pivot

Previous versions (v1.0–v3.0) listed technologies in feature-first order:
1. LangChain → 2. LangGraph → 3. PydanticAI → 4. Hybrid Search → 5. vLLM → 6. MCP → 7. Async → 8. Redis → 9. Celery → 10. Docker → 11. Compose → 12. PostgreSQL

v4.0 restructures into **progressive dependency order** — infrastructure first, then non-blocking I/O, then background processing, then AI layers, then quality assurance, then production readiness:

| Phase | Technologies | Why Here |
|-------|-------------|----------|
| **1** | Docker · Compose · PostgreSQL | Foundation — everything runs on this |
| **2** | Async Python · FastAPI | Non-blocking I/O — required before adding more services |
| **3** | Redis · Celery | Background processing + caching — needed by agents |
| **4** | Hybrid Search (ChromaDB + Whoosh + PG FTS) | Better RAG — feeds better answers to agents |
| **5** | LangChain · LangGraph · PydanticAI | Custom agent graph — the brain |
| **6** | MCP (Model Context Protocol) | Tool discoverability — makes agents extensible |
| **7** | vLLM · Ollama · GPU | Self-hosted LLM — 10x cheaper, 5x faster, private |
| **8** | Evaluation · Observability | Quality assurance — measure what matters |
| **9** | Production Hardening | Bulletproof — security, CI/CD, backups |

#### New Technologies Added (4)
- **FastAPI** — Sidecar alongside Django for OpenAPI docs, WebSocket streaming, async endpoints
- **Ollama** — Lightweight local LLM for development (CPU-only, no GPU needed)
- **Evaluation** — RAGAS pipeline, agent trajectory scoring, LLM-as-Judge
- **Production Hardening** — bandit, pip-audit, detect-secrets, Locust load testing, CI/CD, backups

#### Structural Changes
- Merged 16 sections into 13 sections (0 + 9 phases + roadmap + risks + metrics + ELI5)
- Section 0 Current State: 12 rows → 16 rows (added FastAPI, Ollama, Evaluation, Production Hardening)
- Each phase includes: Why section, code samples, deliverables table, before/after metrics
- New: Phase dependency Mermaid diagram showing unlock chain
- New: Quick-start by Compose profile (dev, gpu, monitoring)
- ELI5: Consolidated all 12 individual analogies into one unified 16-technology comparison table

#### Companion Files Updated
- `progress-report.md` — 12-phase matrix → 9-phase matrix, 16-technology status
- `log-report.md` — This entry (v4.0)

---

### v3.0 — 2026-07-26 — Docker · Docker Compose · PostgreSQL

**Status:** ✅ Complete — All 17 sections finalized

#### Added Sections
- **Section 10** — Docker: Containerization
  - Multi-stage Dockerfile (python:3.12-slim-bookworm)
  - .dockerignore with 20+ exclusion patterns
  - Build, run, log, stop commands
  - 5-row benefits comparison table
- **Section 11** — Docker Compose: Multi-Service Orchestration
  - docker-compose.yml with 7 services (postgres, redis, app, worker, beat, vllm)
  - Healthchecks for postgres & redis
  - Named volumes (postgres_data, redis_data, chroma_data, model_cache)
  - GPU support for vLLM service
- **Section 12** — PostgreSQL Migration
  - Migration strategy (pgvector/pg16 image)
  - Django settings changes (psycopg2, DATABASE_URL)
  - pgvector for vector search
  - JSONB field examples
  - Full-text search (tsvector)
  - MySQL→PostgreSQL cutover script

#### Updated Sections
- **Section 0** — Current State: Added Docker ❌, Docker Compose ❌, PostgreSQL ❌ rows
- **Section 13** — Roadmap: Added Phases 10 (wk 19-20), 11 (wk 21-22), 12 (wk 23-24)
- **Section 14** — Risk Assessment: Added 7 new risks (Docker image size, PostgreSQL migration, Compose networking, pgvector perf, Docker licensing, secrets leakage)
- **Section 15** — Success Metrics: Added 8 new metrics (onboarding time, deploy time, rollback time, dev/prod parity, PostgreSQL query speed, JSONB, full-text search, vector storage)
- **Section 16** — ELI5: Added 3 subsections (🐳 Docker, 🐙 Docker Compose, 🗃 PostgreSQL) + 3 Big Picture rows + 3 comparison table rows

#### Title Update
```
v2: "LangChain · LangGraph · PydanticAI · Hybrid Search · vLLM · MCP · Async Python · Redis · Celery"
v3: "... · Docker · Docker Compose · PostgreSQL" (12 technologies)
```

---

### v2.0 — 2026-07-25 — Async Python · Redis · Celery

#### Added Sections
- **Section 7** — Async Python: Non-Blocking Django
  - Async views, Uvicorn ASGI, async ORM, async agents
  - 4-row benefits comparison table
- **Section 8** — Redis: Cache & Message Broker
  - Pub/Sub replacing queue.Queue
  - Cache layer (orders, refunds, embeddings)
  - Rate limiter (10 req/min per user)
  - SSE with Redis Pub/Sub
  - Dockerized Redis setup
- **Section 9** — Celery: Background Task Processing
  - process_agent_message task (auto-retry 3x)
  - Celery Beat (cleanup, daily reports)
  - Flower monitoring dashboard
  - Non-blocking view returning 202 Accepted

#### Updated Sections
- **Section 0** — Current State: Added Async ❌, Redis ❌, Celery ❌ rows
- **Section 13** — Roadmap: Added Phases 7 (wk 13-14), 8 (wk 15-16), 9 (wk 17-18)
- **Section 14** — Risk Assessment: Added 4 new risks
- **Section 15** — Success Metrics: Added 5 new metrics
- **Section 16** — ELI5: Added 3 subsections (⚡ Async, 🗄 Redis, 📦 Celery) + Big Picture updates

---

### v1.0 — 2026-07-25 — Initial 6 Technologies

#### Created Sections (0-6, 13-16)
- **Section 0** — Current State Assessment (6 techs)
- **Section 1** — LangChain Enhancements (streaming, retry, token tracking, prompt templates)
- **Section 2** — LangGraph: Custom StateGraph (StateGraph, SqliteSaver, 4 nodes)
- **Section 3** — PydanticAI Integration (typed tools, ManagerResponse, hybrid strategy)
- **Section 4** — Hybrid Search / RAG 2.0 (ChromaDB + Whoosh BM25 + RRF)
- **Section 5** — vLLM: Self-Hosted LLM (LLMRouter, 4 recommended models)
- **Section 6** — MCP: Model Context Protocol (FastMCP servers, MultiServerMCPClient)
- **Section 13** — Implementation Roadmap (Phases 1-6, Weeks 1-12)
- **Section 14** — Risk Assessment (8 risks)
- **Section 15** — Success Metrics (9 metrics)
- **Section 16** — ELI5 + Big Picture (6 techs in baby language)

---

## File Stats

| Date | Version | Sections | Techs | Risks | Metrics | ELI5 Sections | Lines (est.) |
|------|---------|----------|-------|-------|---------|--------------|-------------|
| Jul 25 | v1.0 | 13 | 6 | 8 | 9 | 6 | ~850 |
| Jul 25 | v2.0 | 16 | 9 | 12 | 14 | 9 | ~1,300 |
| Jul 26 | v3.0 | 17 | 12 | 19 | 22 | 12 | ~1,485 |

---

## Pending: Not Yet Documented

- [ ] Actual code implementation (all phases are ⬜ Not Started)
- [ ] Test results / benchmarks
- [ ] Screenshots / diagrams (currently all ASCII/Mermaid)
- [ ] Migration runbook (step-by-step production cutover guide)
- [ ] Cost estimates (GPU rental, Docker registry, Railway scaling)
- [ ] Security review (MCP transport auth, Redis ACLs, PostgreSQL RLS)
