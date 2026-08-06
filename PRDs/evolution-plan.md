# 🧬 Evolution Plan: Docker · Docker Compose · PostgreSQL · FastAPI · Async Python · Redis · Celery · Hybrid Search · LangChain · LangGraph · PydanticAI · MCP · vLLM · Ollama · Evaluation · Production Hardening

**Project:** AI Employees — CoolBreeze AC  
**Date:** 2026-07-26  
**Status:** Planning  
**Version:** v4.0 — 9-Phase Progressive Architecture

---

## 0. Current State Assessment

| Component | Status | Implementation |
|-----------|--------|---------------|
| **Docker** | ❌ None | No containerization; dev setup depends on local Python + MySQL installs |
| **Docker Compose** | ❌ None | Each service started manually in separate terminals; no unified orchestration |
| **PostgreSQL** | ❌ None | MySQL 8.0 only; no PostgreSQL for advanced features (JSONB, full-text search, pgvector) |
| **FastAPI** | ❌ None | Django views only; no auto-generated OpenAPI docs; no native async background tasks |
| **Async Python** | ❌ None | All views and agent calls are synchronous; blocking I/O throughout |
| **Redis** | ❌ None | No caching layer; no message broker; in-memory `queue.Queue` for pub/sub |
| **Celery** | ❌ None | No background task processing; agent runs block the HTTP request until complete |
| **Hybrid Search** | ❌ None | ChromaDB vector-only search with `DefaultEmbeddingFunction` |
| **LangChain** | ✅ Active | `langchain_agents.py` using `create_agent` + `ChatOpenAI` + `@tool` decorators |
| **LangGraph** | ⚠️ Partial | Uses `InMemorySaver` checkpointer only; agents created via high-level `create_agent` (no custom `StateGraph`) |
| **PydanticAI** | ❌ None | No structured output validation; tools return raw `dict` |
| **MCP** | ❌ None | Hardcoded tool schemas; no dynamic tool discovery or external tool servers |
| **vLLM** | ❌ None | DeepSeek API only; no self-hosted inference |
| **Ollama** | ❌ None | No local dev LLM; every call hits cloud API — slow, costly during development |
| **Evaluation** | ❌ None | No RAG evaluation; no agent trajectory scoring; no regression testing for AI quality |
| **Production Hardening** | ❌ None | No security audit; no CI/CD; no load testing; no backup strategy; no disaster recovery plan |

> **Key insight:** The old plan listed technologies in feature order. This v4 restructure follows a **progressive architecture** — infrastructure first (Phase 1), then non-blocking I/O (Phase 2), then background processing (Phase 3), then AI intelligence layers (Phases 4-7), then quality assurance (Phase 8), and finally production readiness (Phase 9). Each phase unlocks the next.

---

## 1. Phase 1: Docker + Docker Compose + PostgreSQL (Infrastructure Foundation)

> **Why first?** Every other phase depends on having a reproducible environment. Docker eliminates "works on my machine." Compose orchestrates all services. PostgreSQL is the database that makes RAG, full-text search, and JSON operations possible. Build the foundation before building the house.

### 1.1 Docker: Containerization

#### Why Docker?

| Problem (Current) | Docker Solution |
|-------------------|----------------|
| "Works on my machine" syndrome — every dev has different Python/MySQL versions | **Identical environment everywhere** — same Docker image on dev, staging, production |
| Manual setup: `pip install -r requirements.txt`, MySQL config, ChromaDB path | **One command: `docker build`** — all dependencies baked into the image |
| OS-specific bugs (Windows paths, Linux permissions) | **Linux containers** — identical kernel environment regardless of host OS |
| No easy rollback — deploy and pray | **Tagged images** — `coolbreeze:v1.2.3` → broken? `docker run coolbreeze:v1.2.2` |
| Secrets in `.env` files floating around | **Docker secrets / build args** — API keys injected at runtime, never in the image |

#### Dockerfile

```dockerfile
# Dockerfile — production-ready multi-stage build
# Stage 1: Build
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim-bookworm

WORKDIR /app

# Create non-root user
RUN groupadd -r coolbreeze && useradd -r -g coolbreeze coolbreeze

# Copy only what's needed from builder
COPY --from=builder /root/.local /home/coolbreeze/.local
COPY . .

# Ensure scripts in .local are usable
ENV PATH=/home/coolbreeze/.local/bin:$PATH

# Collect static files
RUN python manage.py collectstatic --noinput

# Switch to non-root user
USER coolbreeze

# Run with Uvicorn ASGI
CMD ["uvicorn", "dj_ai_employee_main.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
```

#### .dockerignore

```
# .dockerignore — exclude from Docker build context
env/
venv/
.venv/
__pycache__/
*.pyc
*.pyo
.git/
.gitignore
.vscode/
.idea/
chroma_db/
htmlcov/
.coverage
pytest.ini
conftest.py
stress_report.html
test_claude.py
.env
.env.local
*.log
README.md
PRDs/
```

#### Building & Running

```bash
# Build the image
docker build -t coolbreeze:latest .

# Run the container
docker run -d \
  --name coolbreeze-app \
  -p 8000:8000 \
  -e DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY \
  -e DATABASE_URL=postgres://coolbreeze:password@postgres:5432/coolbreeze \
  coolbreeze:latest

# Check logs
docker logs -f coolbreeze-app

# Stop & remove
docker stop coolbreeze-app && docker rm coolbreeze-app
```

| Metric | Without Docker | With Docker |
|--------|---------------|-------------|
| **New dev onboarding** | 30-60 min (Python + MySQL + ChromaDB setup) | 2 min (`docker compose up`) |
| **Production deploy** | Manual pip install + gunicorn restart | `docker pull && docker compose up -d` |
| **Rollback time** | 10-30 min | 10 seconds (`docker compose up -d --no-deps app`) |
| **Environment parity** | ❌ Dev ≠ Prod | ✅ Identical |
| **Build reproducibility** | ❌ Depends on local state | ✅ Deterministic from Dockerfile |

---

### 1.2 Docker Compose: Multi-Service Orchestration

#### Why Docker Compose?

Right now running the project means:
- Terminal 1: `python manage.py runserver` (Django)
- Terminal 2: MySQL needs to be running as a system service
- Terminal 3: `celery -A dj_ai_employee_main worker` (if using Celery)
- Terminal 4: `celery -A dj_ai_employee_main beat` (scheduled tasks)
- Terminal 5: Redis server (if using Redis)
- Terminal 6: vLLM / Ollama (if self-hosting LLM)

That's **6 terminals** to start them all. Docker Compose starts everything with **one command**.

#### docker-compose.yml

```yaml
# docker-compose.yml — full stack for CoolBreeze AC
version: "3.9"

services:
  # ── PostgreSQL ──
  postgres:
    image: pgvector/pgvector:pg16  # PostgreSQL 16 + pgvector extension
    container_name: coolbreeze-postgres
    environment:
      POSTGRES_DB: coolbreeze
      POSTGRES_USER: coolbreeze
      POSTGRES_PASSWORD: ${DB_PASSWORD:-coolbreeze}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql  # Seed data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U coolbreeze"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── Redis ──
  redis:
    image: redis:7-alpine
    container_name: coolbreeze-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # ── Django (ASGI) ──
  app:
    build: .
    container_name: coolbreeze-app
    command: uvicorn dj_ai_employee_main.asgi:application --host 0.0.0.0 --port 8000 --workers 4
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://coolbreeze:${DB_PASSWORD:-coolbreeze}@postgres:5432/coolbreeze
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
      - DJANGO_DEBUG=False
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - chroma_data:/app/chroma_db
      - ./media:/app/media
    restart: unless-stopped

  # ── Celery Worker ──
  worker:
    build: .
    container_name: coolbreeze-worker
    command: celery -A dj_ai_employee_main worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgres://coolbreeze:${DB_PASSWORD:-coolbreeze}@postgres:5432/coolbreeze
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  # ── Celery Beat ──
  beat:
    build: .
    container_name: coolbreeze-beat
    command: celery -A dj_ai_employee_main beat --loglevel=info
    environment:
      - DATABASE_URL=postgres://coolbreeze:${DB_PASSWORD:-coolbreeze}@postgres:5432/coolbreeze
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  # ── vLLM (GPU profile — only starts with --profile gpu) ──
  vllm:
    image: vllm/vllm-openai:latest
    container_name: coolbreeze-vllm
    command: --model Qwen/Qwen2.5-7B-Instruct --port 8001 --max-model-len 8192
    ports:
      - "8001:8001"
    environment:
      - HF_HOME=/model-cache
    volumes:
      - model_cache:/model-cache
      - ~/.cache/huggingface:/root/.cache/huggingface
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    profiles:
      - gpu
    restart: unless-stopped

  # ── Ollama (dev profile — lightweight local LLM, no GPU needed) ──
  ollama:
    image: ollama/ollama:latest
    container_name: coolbreeze-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    profiles:
      - dev
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  chroma_data:
  model_cache:
  ollama_data:
```

#### Environment File

```env
# .env (for docker-compose.yml)
DB_PASSWORD=coolbreeze-secret-password
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
DJANGO_SECRET_KEY=django-insecure-xxxxxxxxxxxxxxxx
```

#### Development vs Production Overrides

```yaml
# docker-compose.override.yml — development overrides (auto-loaded by Compose)
services:
  app:
    environment:
      - DJANGO_DEBUG=True
    volumes:
      - .:/app  # Live code reload
    command: uvicorn dj_ai_employee_main.asgi:application --host 0.0.0.0 --port 8000 --reload

  postgres:
    ports:
      - "5432:5432"  # Expose to host for DB tools

  redis:
    ports:
      - "6379:6379"  # Expose to host for redis-cli
```

#### Daily Commands

```bash
# Start everything (excludes GPU profile)
docker compose up -d

# Start with vLLM (requires GPU)
docker compose --profile gpu up -d

# Start with Ollama for local dev
docker compose --profile dev up -d

# View logs
docker compose logs -f app        # Django only
docker compose logs -f worker     # Celery only
docker compose logs -f            # All services

# Restart just one service
docker compose restart app

# Run Django management commands
docker compose exec app python manage.py migrate
docker compose exec app python manage.py createsuperuser
docker compose exec app python manage.py test

# Stop everything
docker compose down

# Stop + delete volumes (fresh start)
docker compose down -v
```

| Metric | Without Compose | With Compose |
|--------|----------------|-------------|
| **Start all services** | 6 terminal windows + manual commands | `docker compose up -d` (one command) |
| **New dev onboarding** | Install Python 3.12 + MySQL 8 + Redis + ... | `docker compose up -d` |
| **CI/CD pipeline** | Complex setup scripts | `docker compose -f docker-compose.ci.yml up --exit-code-from test` |
| **Service networking** | Manual port management | Auto DNS: `redis` → resolves to Redis container IP |
| **Production parity** | Dev runs SQLite, prod runs MySQL | Identical services in both environments |

---

### 1.3 PostgreSQL: Production Database

#### Why PostgreSQL Over MySQL?

| Feature | MySQL 8.0 (current) | PostgreSQL 16 (target) |
|---------|--------------------|------------------------|
| **JSON field operations** | `JSON_EXTRACT()` — cumbersome | `->>` and `@>` operators — native, clean |
| **Full-text search** | Limited, separate index needed | Built-in `tsvector` + `GIN` index + ranking |
| **Vector embeddings (pgvector)** | ❌ Not available | ✅ `pgvector` extension — store embeddings alongside data |
| **Array columns** | ❌ JSON workaround | ✅ Native `TEXT[]`, `INT[]` column types |
| **Concurrent writes** | Row-level locking can cause contention | MVCC — readers never block writers |
| **Django ORM support** | Good (via `mysqlclient`/`PyMySQL`) | Excellent — Django's officially recommended DB |
| **Geospatial (future)** | Basic spatial indexes | PostGIS — industry standard |
| **Connection handling** | Connection-per-thread | Connection pooling via `pgbouncer` |

#### Key Feature: pgvector for Hybrid RAG

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Store document chunks with embeddings
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(384),  -- BGE-small-en-v1.5 dimension
    doc_type VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- HNSW index for fast ANN search
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- Hybrid query: vector similarity + keyword match + metadata filter
SELECT content, doc_type,
       1 - (embedding <=> '[0.123, 0.456, ...]'::vector) AS similarity,
       ts_rank(to_tsvector('english', content), plainto_tsquery('english', 'warranty AC-5000')) AS text_rank
FROM document_chunks
WHERE doc_type = 'warranty'
  AND to_tsvector('english', content) @@ plainto_tsquery('english', 'warranty AC-5000')
ORDER BY (similarity * 0.7 + text_rank * 0.3) DESC
LIMIT 3;
```

#### Django Configuration

```python
# dj_ai_employee_main/settings.py — switch to PostgreSQL
import os
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default='postgres://coolbreeze:password@localhost:5432/coolbreeze',
        conn_max_age=600,
        conn_health_checks=True,
    )
}
```

#### Django Model with pgvector

```python
# New: support/models.py — document chunks with pgvector
from django.db import models
from pgvector.django import VectorField, HnswIndex

class DocumentChunk(models.Model):
    content = models.TextField()
    embedding = VectorField(dimensions=384)  # BGE-small-en-v1.5
    doc_type = models.CharField(max_length=50)  # "policy", "faq", "warranty"
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            HnswIndex(
                name='document_chunks_embedding_idx',
                fields=['embedding'],
                opclasses=['vector_cosine_ops'],
            )
        ]
```

#### Full-Text Search with PostgreSQL

```python
# New: support/search.py — PostgreSQL full-text search
from django.contrib.postgres.search import (
    SearchVector, SearchQuery, SearchRank, SearchHeadline
)
from .models import DocumentChunk

def pg_full_text_search(query: str, doc_type: str | None = None) -> list[dict]:
    """PostgreSQL full-text search with ranking and headlines."""
    search_query = SearchQuery(query, config='english')
    search_vector = SearchVector('content', weight='A', config='english')

    qs = DocumentChunk.objects.annotate(
        rank=SearchRank(search_vector, search_query),
        headline=SearchHeadline(
            'content', search_query,
            start_sel='<mark>', stop_sel='</mark>',
            max_words=50, max_fragments=2
        )
    ).filter(rank__gt=0.01)

    if doc_type:
        qs = qs.filter(doc_type=doc_type)

    return [
        {
            'content': chunk.content,
            'doc_type': chunk.doc_type,
            'rank': chunk.rank,
            'headline': chunk.headline,
        }
        for chunk in qs.order_by('-rank')[:5]
    ]
```

#### Migration Path: MySQL → PostgreSQL

```bash
# Step 1: Dump MySQL data as JSON
python manage.py dumpdata --indent 2 --output mysql_dump.json

# Step 2: Switch settings.py to PostgreSQL

# Step 3: Install PostgreSQL driver + pgvector
pip install psycopg2-binary pgvector dj-database-url

# Step 4: Run migrations on PostgreSQL
python manage.py migrate

# Step 5: Load data into PostgreSQL
python manage.py loaddata mysql_dump.json

# Step 6: Enable pgvector extension (run once)
# psql -U coolbreeze -d coolbreeze -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Step 7: Verify
python manage.py test
```

#### Benefits Summary

| Metric | MySQL (Current) | PostgreSQL (Target) |
|--------|----------------|---------------------|
| **Vector search** | ❌ ChromaDB only | ✅ pgvector — embeddings in same DB |
| **Full-text search** | ⚠️ Limited | ✅ Built-in + ranking + highlighting |
| **JSON operations** | ⚠️ `JSON_EXTRACT()` | ✅ `->>` native operators |
| **Concurrent reads/writes** | ⚠️ Row locking | ✅ MVCC — no reader blocking |
| **Django recommendation** | Supported | Officially recommended |
| **AI-native features** | ❌ None | ✅ pgvector, pgai, pgvectorscale |

---

### 1.4 Phase 1 Deliverables

| Deliverable | Tool | Effort |
|------------|------|--------|
| Multi-stage Dockerfile | Docker | 2 days |
| docker-compose.yml (7 services) | Docker Compose | 2 days |
| PostgreSQL migration | Django + pgvector | 3 days |
| Full test suite passing on new stack | pytest | 1 day |
| `docker compose up` from scratch works | All | 1 day |

---
## 2. Phase 2: Async Python + FastAPI (Non-Blocking Architecture)

> **⚠️ Safety guarantee:** Django is **not modified, replaced, or restructured** in this phase. No Django file is edited. Django's `asgi.py`, `settings.py`, `urls.py`, views, templates, admin, and ORM remain exactly as they are today. FastAPI runs as a **separate Uvicorn process** on a different port (8001), importing Django's ORM via `django.setup()` but never touching Django's HTTP layer. A lightweight nginx reverse proxy routes `/api/*` and `/ws/*` to FastAPI; everything else goes to Django unchanged.
>
> **Why now?** Phase 1 gave us containers and a database. But Django views still block while waiting for LLM responses. A 3-second DeepSeek call means the worker can handle only 0.33 requests/second. FastAPI + async rewrites that equation.

### 2.1 Why Async Python?

| Problem (Synchronous) | Async Solution |
|-----------------------|----------------|
| `response = requests.post(url, json=payload)` — **blocks** the entire thread for 3 seconds while DeepSeek responds | `response = await httpx.AsyncClient().post(url, json=payload)` — yields control, thread handles other requests |
| 1 worker = 1 request at a time. 4 workers = 4 simultaneous users | 1 worker = **thousands** of concurrent requests (all I/O-bound waiting) |
| Agent calls `lookup_order()` which blocks on MySQL query | `await sync_to_async(lookup_order)()` — DB query runs in thread pool, doesn't block event loop |
| No WebSocket support — can't stream agent thoughts to frontend | ASGI enables WebSocket + SSE streaming natively |

### 2.2 FastAPI Sidecar Architecture

**Pattern:** FastAPI runs **alongside** Django, not instead of it. Django handles admin, ORM, migrations, and existing views — completely untouched. FastAPI handles the AI endpoints with async, OpenAPI docs, and WebSocket streaming from a separate process. nginx routes traffic by URL prefix.

```
                         Browser
                           │
                    GET /orders/123/
                           │
                           ▼
                    ┌──────────────┐
                    │    nginx     │  Reverse Proxy (:80)
                    │              │
                    │ /api/* ──────────▶ FastAPI (:8001)
                    │ /ws/*  ──────────▶ FastAPI (:8001)
                    │ /docs  ──────────▶ FastAPI (:8001)
                    │ /*     ──────────▶ Django  (:8000)
                    └──────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  Django  │ │ FastAPI  │ │PostgreSQL│
        │  :8000   │ │  :8001   │ │  :5432   │
        │          │ │          │ │          │
        │ • Admin  │ │ • /api/* │ │ Shared   │
        │ • ORM    │◄┼─imports──┤ │ Database │
        │ • Views  │ │ • /ws/*  │ │          │
        │ • Templ. │ │ • /docs  │ │          │
        └──────────┘ └──────────┘ └──────────┘
              │                          │
              └──────────┬───────────────┘
                         │
              Django ORM ← shared models
              (FastAPI calls django.setup() once at startup)
```

| Boundary | Django's Territory | FastAPI's Territory |
|----------|-------------------|---------------------|
| **URLs** | `/admin/`, `/orders/`, `/support/`, `/login/`, `/static/` | `/api/chat`, `/api/agent/run`, `/ws/stream`, `/docs` |
| **HTTP Layer** | Django views + templates (unchanged) | FastAPI routes + Pydantic models |
| **Business Logic** | `support/agents.py`, `support/tools.py` (shared) | Calls into the same `support/` modules |
| **Database** | Django ORM (unchanged) | Django ORM via `django.setup()` |

#### FastAPI App Setup

```python
# New: api/main.py — FastAPI sidecar application
from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from pydantic import BaseModel
import redis.asyncio as redis
import os
import django
import asyncio

# Bootstrap Django so we can use ORM
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dj_ai_employee_main.settings")
django.setup()

app = FastAPI(
    title="CoolBreeze AI API",
    version="1.0.0",
    description="Async AI endpoints for CoolBreeze AC customer support",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    """Connect Redis for rate limiting."""
    redis_client = redis.from_url(
        f"redis://{os.environ.get('REDIS_HOST', 'localhost')}:6379",
        encoding="utf-8",
        decode_responses=True,
    )
    await FastAPILimiter.init(redis_client)

# ── Pydantic Models ──

class ChatRequest(BaseModel):
    user_id: str
    message: str
    order_id: str | None = None

class ChatResponse(BaseModel):
    reply: str
    agent: str  # "maya", "alex", "sam"
    confidence: float
    tool_calls: list[dict] = []

class AgentRunRequest(BaseModel):
    user_id: str
    agent_type: str  # "support", "order_lookup", "manager", "risk"
    context: dict = {}

# ── Async Endpoints ──

@app.post("/api/chat", response_model=ChatResponse,
          dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """Async chat endpoint — doesn't block the worker."""
    # Offload LLM call to Celery (see Phase 3), return immediately
    from support.tasks import process_chat_message
    task = process_chat_message.delay(
        user_id=request.user_id,
        message=request.message,
        order_id=request.order_id,
    )
    return ChatResponse(
        reply="Processing your request...",
        agent="maya",
        confidence=1.0,
        tool_calls=[],
    )

@app.post("/api/agent/run", response_model=ChatResponse)
async def run_agent(request: AgentRunRequest):
    """Run a specific agent type with context."""
    # This will use LangGraph in Phase 5
    from support.agents import run_agent_async
    result = await run_agent_async(
        agent_type=request.agent_type,
        user_id=request.user_id,
        context=request.context,
    )
    return ChatResponse(**result)

# ── WebSocket for streaming ──

from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/stream/{user_id}")
async def websocket_stream(websocket: WebSocket, user_id: str):
    """Stream agent thoughts and tool calls in real-time."""
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            # Stream agent response token by token
            from support.agents import stream_agent_response
            async for token in stream_agent_response(user_id, message):
                await websocket.send_json({"type": "token", "content": token})
            await websocket.send_json({"type": "done"})
    except WebSocketDisconnect:
        pass

# ── Dependency injection ──

async def get_redis() -> redis.Redis:
    client = redis.from_url(
        f"redis://{os.environ.get('REDIS_HOST', 'localhost')}:6379"
    )
    try:
        yield client
    finally:
        await client.close()

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "fastapi-sidecar"}
```

#### Async Database Access

```python
# support/agents.py — async agent runner
from asgiref.sync import sync_to_async
import httpx

@sync_to_async
def lookup_order_sync(order_id: str) -> dict:
    """Synchronous ORM call wrapped for async."""
    from orders.models import Order
    try:
        order = Order.objects.select_related('user').get(id=order_id)
        return {
            "id": order.id,
            "status": order.status,
            "total": str(order.total),
            "customer": order.user.get_full_name(),
        }
    except Order.DoesNotExist:
        return {"error": "Order not found"}

async def run_agent_async(
    agent_type: str,
    user_id: str,
    context: dict,
) -> dict:
    """Async agent runner — no blocking!"""
    # Look up order (async wrapper around sync ORM)
    if order_id := context.get("order_id"):
        order_data = await lookup_order_sync(order_id)
        context["order"] = order_data

    # Call LLM (non-blocking HTTP)
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}"},
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": get_system_prompt(agent_type)},
                    {"role": "user", "content": str(context)},
                ],
            },
        )

    data = response.json()
    return {
        "reply": data["choices"][0]["message"]["content"],
        "agent": agent_type,
        "confidence": 0.95,
        "tool_calls": [],
    }
```

### 2.3 Django + FastAPI Coexistence (Reverse-Proxy Approach)

> **⚠️ Django untouched:** Django's `asgi.py`, URL patterns, templates, admin, and views remain completely unmodified. FastAPI runs as a **separate Uvicorn process** on a different port. A lightweight nginx reverse proxy routes `/api/*` and `/ws/*` to FastAPI and everything else to Django. Zero changes to any Django file.

```
Browser Request: GET /orders/123/
        │
        ▼
   ┌──────────┐
   │  nginx   │  (reverse proxy — routes by URL prefix)
   │  :80     │
   └────┬─────┘
        │
        ├── /api/* , /ws/* , /docs ──▶ FastAPI (Uvicorn :8001)
        │
        └── everything else ─────────▶ Django  (Uvicorn :8000)
                  /admin/
                  /orders/
                  /support/
                  /login/
                  /static/
```

#### Why Two Processes Instead of Mounting?

| Approach | Django Impact | URL Changes | Risk |
|----------|--------------|-------------|------|
| **Mount FastAPI inside Django** (`WSGIMiddleware`) | Django `asgi.py` must be rewritten | All Django URLs shift to `/django/` prefix | 🟡 Templates break, bookmarks break, tests break |
| **Mount Django inside FastAPI** (`WSGIMiddleware`) | Django `asgi.py` rewritten; Django becomes sub-app | All Django URLs shift to `/django/` prefix | 🔴 Django demoted, all URLs change |
| ✅ **Reverse proxy (nginx)** — two separate Uvicorn processes | **Zero Django files changed** | **Zero URL changes** | 🟢 Safest |

#### Nginx Reverse Proxy Config

```nginx
# nginx.conf — added to docker-compose as a lightweight router
server {
    listen 80;

    # FastAPI: AI endpoints + Swagger docs + WebSocket
    location /api/ {
        proxy_pass http://fastapi:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # WebSocket support for /ws/stream/
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300s;
    }

    location /ws/ {
        proxy_pass http://fastapi:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300s;
    }

    location /docs {
        proxy_pass http://fastapi:8001;
    }

    location /openapi.json {
        proxy_pass http://fastapi:8001;
    }

    # Django: everything else (admin, orders, support, login, static)
    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Docker Compose Addition

```yaml
# docker-compose.yml — add nginx + fastapi services (Phase 2, additive)
nginx:
  image: nginx:alpine
  container_name: coolbreeze-nginx
  ports:
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
  depends_on:
    - app
    - fastapi
  restart: unless-stopped

# FastAPI as a SEPARATE service — NOT inside Django
fastapi:
  build: .
  container_name: coolbreeze-fastapi
  command: uvicorn api.main:app --host 0.0.0.0 --port 8001 --workers 2
  environment:
    - DATABASE_URL=postgres://coolbreeze:${DB_PASSWORD:-coolbreeze}@postgres:5432/coolbreeze
    - REDIS_HOST=redis
    - REDIS_PORT=6379
    - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
  restart: unless-stopped
```

#### What Django Does NOT Change

| Django File | Modified? | Reason |
|------------|:---------:|--------|
| `dj_ai_employee_main/asgi.py` | ❌ No | Django's own ASGI stays exactly as-is |
| `dj_ai_employee_main/wsgi.py` | ❌ No | Preserved for WSGI compatibility |
| `dj_ai_employee_main/settings.py` | ❌ No | No FastAPI config needed here |
| `dj_ai_employee_main/urls.py` | ❌ No | Django URL patterns unchanged |
| `templates/` (all) | ❌ No | Template URLs stay at `/orders/`, `/login/`, etc. |
| `orders/views.py` | ❌ No | Existing views unchanged |
| `support/views.py` | ❌ No | Existing views unchanged |
| `support/urls.py` | ❌ No | Existing URL patterns unchanged |
| `support/models.py` | ❌ No | Django ORM exports used by FastAPI via `django.setup()` |

> **Key principle:** FastAPI **imports** Django's ORM and business logic (via `django.setup()`) but never touches Django's HTTP layer, URL routing, templates, or admin. Django is a **peer service**, not a sub-application.

### 2.4 Phase 2 Deliverables

| Deliverable | Effort |
|------------|--------|
| FastAPI sidecar with `/api/chat`, `/api/agent/run`, `/ws/stream` | 3 days |
| Async agent runner with `httpx` + `sync_to_async` | 2 days |
| Pydantic models for all API contracts | 1 day |
| Auto-generated OpenAPI docs at `/docs` | Free (FastAPI built-in) |
| WebSocket streaming endpoint | 1 day |

| Metric | Sync (Current) | Async (After) |
|--------|---------------|---------------|
| **Max concurrent users (4 workers)** | ~4 | ~1,000+ (I/O-bound) |
| **Time to first byte (LLM call)** | 3-10 sec (blocking) | Instant + streaming tokens |
| **API documentation** | None | Auto-generated Swagger UI |
| **WebSocket support** | ❌ | ✅ Real-time streaming |
| **Type safety (API contracts)** | ❌ manual `dict` | ✅ Pydantic validation |

---

## 3. Phase 3: Redis + Celery (Background Processing)

> **Why now?** Async helps with I/O wait, but LLM calls still take 3-10 seconds. Celery moves them off the web server entirely. Redis provides caching, pub/sub, and rate limiting that every subsequent phase needs.

### 3.1 Redis: The Swiss Army Knife

#### Redis Use Cases in CoolBreeze

```
┌─────────────────────────────────────────────────────────────────┐
│                        REDIS (in-memory)                        │
│                                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │    CACHE     │ │   PUB/SUB    │ │ RATE LIMITER │           │
│  │              │ │              │ │              │           │
│  │ order:123 →  │ │ channel:     │ │ ratelimit:   │           │
│  │ {status,...} │ │  agent_maya  │ │  user:42 →   │           │
│  │ TTL: 5 min   │ │              │ │  8/10 req    │           │
│  │              │ │ "I found     │ │  TTL: 60s    │           │
│  │ user:7:      │ │  the order"  │ │              │           │
│  │ refunds →    │ │ → all        │ │ 401 when     │           │
│  │  [r1,r2]     │ │  listeners   │ │  exceeded    │           │
│  │ TTL: 1 hr    │ │  notified    │ │              │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
│                                                                 │
│  ┌──────────────┐ ┌──────────────────────────────────┐        │
│  │ CELERY       │ │    SESSION / CONVERSATION        │        │
│  │ BROKER       │ │                                  │        │
│  │              │ │  session:abc123 → [               │        │
│  │ task queues: │ │    {role:user, msg:"..."},       │        │
│  │  • default   │ │    {role:assistant, msg:"..."},  │        │
│  │  • high_pri  │ │  ]                               │        │
│  │  • low_pri   │ │  TTL: 24 hr                      │        │
│  └──────────────┘ └──────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

#### Redis Implementation

```python
# New: support/redis_client.py
import redis
import json
import os
from typing import Any
from functools import wraps

redis_client = redis.Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    decode_responses=True,
)

# ── Caching ──

def cache_result(ttl: int = 300, prefix: str = "cache"):
    """Decorator: cache function results in Redis."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{prefix}:{func.__name__}:{args}:{kwargs}"
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)
            result = func(*args, **kwargs)
            redis_client.setex(key, ttl, json.dumps(result, default=str))
            return result
        return wrapper
    return decorator

@cache_result(ttl=300, prefix="order")
def get_order(order_id: str) -> dict:
    """Fetch order from DB, cached for 5 minutes."""
    from orders.models import Order
    order = Order.objects.get(id=order_id)
    return {"id": order.id, "status": order.status, "total": str(order.total)}

# ── Pub/Sub ──

class RedisPubSub:
    """Publish/subscribe for real-time agent communication."""

    def publish(self, channel: str, message: dict):
        """Publish a message to a channel."""
        redis_client.publish(channel, json.dumps(message))

    def subscribe(self, channel: str):
        """Create a pub/sub listener for a channel."""
        pubsub = redis_client.pubsub()
        pubsub.subscribe(channel)
        return pubsub

    def agent_announce(self, agent_name: str, event: str, data: dict):
        """Announce an agent event to all listeners."""
        self.publish(
            f"agent_{agent_name}",
            {"event": event, "data": data, "timestamp": "now"},
        )

# ── Rate Limiter ──

class RateLimiter:
    """Token-bucket rate limiter using Redis."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds

    def is_allowed(self, user_id: str) -> bool:
        key = f"ratelimit:{user_id}"
        current = redis_client.get(key)

        if current is None:
            redis_client.setex(key, self.window, 1)
            return True

        count = int(current)
        if count >= self.max_requests:
            return False

        redis_client.incr(key)
        return True

# ── Session Store ──

class RedisSessionStore:
    """Store conversation history in Redis."""

    def add_message(self, session_id: str, role: str, content: str):
        key = f"session:{session_id}"
        message = {"role": role, "content": content}
        redis_client.rpush(key, json.dumps(message))
        redis_client.expire(key, 86400)  # 24 hours

    def get_history(self, session_id: str, limit: int = 20) -> list[dict]:
        key = f"session:{session_id}"
        messages = redis_client.lrange(key, -limit, -1)
        return [json.loads(m) for m in messages]
```

### 3.2 Celery: Background Task Processing

#### Why Celery?

| Problem (Current) | Celery Solution |
|-------------------|----------------|
| Agent LLM call blocks HTTP request for 3-10 seconds | Offload to Celery task → user gets instant acknowledgment |
| No retry mechanism — LLM API error = user sees 500 | Celery auto-retry with exponential backoff |
| No scheduled jobs — manual cleanup | Celery Beat: scheduled cleanup, reports, health checks |
| No visibility into task queues | Flower dashboard: real-time monitoring |

#### Celery Configuration

```python
# dj_ai_employee_main/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dj_ai_employee_main.settings")

app = Celery("dj_ai_employee_main")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# settings.py additions:
CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = "redis://redis:6379/1"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Kuala_Lumpur"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes max
```

#### Agent Tasks

```python
# New: support/tasks.py
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
import logging

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,  # seconds
    autoretry_for=(Exception,),
)
def process_chat_message(self, user_id: str, message: str, order_id: str | None = None):
    """Process a chat message with LLM agent (runs in background)."""
    from support.agents import run_support_agent

    try:
        result = run_support_agent(
            user_id=user_id,
            message=message,
            order_id=order_id,
        )
        # Store result in Redis for the FastAPI endpoint to pick up
        from support.redis_client import redis_client
        redis_client.setex(
            f"result:{self.request.id}",
            300,  # 5 minute TTL
            json.dumps(result),
        )
        return result

    except Exception as exc:
        logger.error(f"Agent task failed (attempt {self.request.retries}): {exc}")
        raise self.retry(exc=exc, countdown=5 * (2 ** self.request.retries))

@shared_task
def generate_daily_report():
    """Scheduled: generate daily support report at midnight."""
    from support.tracking_data import generate_report
    report = generate_report()
    # Store or email the report
    return report

@shared_task
def cleanup_old_sessions():
    """Scheduled: clean up expired Redis sessions at 3 AM."""
    from support.redis_client import redis_client
    # Sessions auto-expire, but we can add extra cleanup here
    pass

@shared_task
def warm_embeddings_cache():
    """Scheduled: pre-compute embeddings for frequently accessed documents."""
    from support.rag import precompute_embeddings
    precompute_embeddings()
```

#### Celery Beat Schedule

```python
# dj_ai_employee_main/settings.py — Celery Beat schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "daily-report": {
        "task": "support.tasks.generate_daily_report",
        "schedule": crontab(hour=0, minute=0),  # Midnight
    },
    "cleanup-sessions": {
        "task": "support.tasks.cleanup_old_sessions",
        "schedule": crontab(hour=3, minute=0),  # 3 AM
    },
    "warm-embeddings": {
        "task": "support.tasks.warm_embeddings_cache",
        "schedule": crontab(hour=6, minute=0),  # 6 AM
    },
}
```

#### Flower Monitoring

```bash
# docker-compose.yml addition:
flower:
  build: .
  container_name: coolbreeze-flower
  command: celery -A dj_ai_employee_main flower --port=5555
  ports:
    - "5555:5555"
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
  depends_on:
    - redis
```

### 3.3 Phase 3 Deliverables

| Deliverable | Effort |
|------------|--------|
| Redis caching layer (order, user, embeddings) | 2 days |
| Redis pub/sub for inter-agent communication | 1 day |
| Token-bucket rate limiter | 1 day |
| Redis session store for conversation history | 1 day |
| Celery integration + agent tasks | 2 days |
| Celery Beat schedule (reports, cleanup) | 1 day |
| Flower monitoring dashboard | 1 day |

| Metric | Without Phase 3 | With Phase 3 |
|--------|----------------|-------------|
| **LLM call blocks user** | ✅ Yes (3-10 sec wait) | ❌ No (instant ack + polling) |
| **Cache hit rate** | 0% (every request hits DB) | ~70% for order/refund lookups |
| **Retry on LLM failure** | ❌ User sees 500 | ✅ 3 retries + exponential backoff |
| **Scheduled tasks** | ❌ Manual | ✅ Auto-generated reports, cleanup |
| **Task visibility** | ❌ None | ✅ Flower dashboard |
| **Rate limiting** | ❌ None | ✅ 10 req/min per user |

---
## 4. Phase 4: Hybrid Search RAG 2.0 (Dense + Sparse Fusion)

> **Why now?** The infrastructure is stable (Phases 1-3). Now we upgrade the brain. ChromaDB vector-only search misses exact keyword matches like "AC-5000 warranty." Hybrid search combines the best of dense (semantic) and sparse (keyword) retrieval plus RRF fusion.

### 4.1 Why Hybrid Search?

| Current (ChromaDB Only) | Hybrid Search |
|--------------------------|---------------|
| "My AC-5000 is leaking" → finds general leak documents, not AC-5000 specific | Dense finds "leaking AC units" semantically; Sparse matches "AC-5000" exactly → **both in top results** |
| "warranty" → misses documents that say "guarantee" or "coverage" | Dense embeddings catch synonyms and paraphrases |
| Exact model numbers lost in embedding | BM25 preserves exact tokens and term frequency |
| No ranking fusion | RRF merges results: `score = Σ 1/(k + rank_i)` |

### 4.2 Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    HYBRID RAG PIPELINE                       │
│                                                              │
│  User Query: "My AC-5000 is leaking water"                  │
│       │                                                      │
│       ├────────────────┬─────────────────────┐               │
│       ▼                ▼                     ▼               │
│  ┌──────────┐   ┌──────────────┐   ┌──────────────────┐    │
│  │ ChromaDB │   │  Whoosh BM25 │   │  PostgreSQL FTS   │    │
│  │ (Dense)  │   │  (Sparse)    │   │  (Sparse + JSON)  │    │
│  │          │   │              │   │                   │    │
│  │ cosine   │   │  TF-IDF +    │   │  tsvector +       │    │
│  │ sim on   │   │  BM25 scoring│   │  ts_rank +        │    │
│  │ BGE-small│   │  on content  │   │  ts_headline      │    │
│  └────┬─────┘   └──────┬───────┘   └────────┬──────────┘    │
│       │                │                     │               │
│       │  Top-10        │  Top-10             │  Top-10       │
│       ▼                ▼                     ▼               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              RRF (Reciprocal Rank Fusion)              │  │
│  │                                                       │  │
│  │  score(doc) = Σ 1/(60 + rank_chroma)                  │  │
│  │             + 1/(60 + rank_whoosh)                    │  │
│  │             + 1/(60 + rank_pgfts)                     │  │
│  │                                                       │  │
│  │  → Unified ranked list                                │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Optional: BGE-Reranker-v2-m3 (Cross-Encoder)  │  │
│  │         Re-rank top-10 with cross-attention            │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│              Top-3 chunks → LLM context                      │
└──────────────────────────────────────────────────────────────┘
```

### 4.3 Implementation

#### BGE Small Embeddings (replaces DefaultEmbeddingFunction)

```python
# Update: support/rag.py
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
import os

CHROMA_PATH = os.environ.get("CHROMA_PATH", "chroma_db")

# BGE-small-en-v1.5 — 384 dimensions, state-of-the-art for retrieval
bge_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-small-en-v1.5",
    device="cpu",  # or "cuda" if GPU available
)

chroma_client = PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(
    name="coolbreeze_docs",
    embedding_function=bge_ef,
    metadata={"hnsw:space": "cosine"},
)
```

#### Whoosh BM25 Index

```python
# New: support/whoosh_search.py
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
import os

WHOOSH_INDEX_PATH = os.environ.get("WHOOSH_INDEX_PATH", "whoosh_index")

schema = Schema(
    id=ID(stored=True, unique=True),
    content=TEXT(stored=True),
    doc_type=TEXT(stored=True),
)

def get_or_create_index():
    if not os.path.exists(WHOOSH_INDEX_PATH):
        os.makedirs(WHOOSH_INDEX_PATH)
        return create_in(WHOOSH_INDEX_PATH, schema)
    return open_dir(WHOOSH_INDEX_PATH)

def index_document(doc_id: str, content: str, doc_type: str):
    """Index a document in Whoosh for BM25 retrieval."""
    idx = get_or_create_index()
    writer = idx.writer()
    writer.update_document(id=doc_id, content=content, doc_type=doc_type)
    writer.commit()

def bm25_search(query: str, top_k: int = 10) -> list[dict]:
    """BM25 sparse retrieval."""
    idx = get_or_create_index()
    with idx.searcher() as searcher:
        parser = QueryParser("content", idx.schema)
        q = parser.parse(query)
        results = searcher.search(q, limit=top_k)
        return [
            {"id": r["id"], "content": r["content"],
             "score": r.score, "doc_type": r["doc_type"]}
            for r in results
        ]
```

#### PostgreSQL Full-Text Search (reprise from Phase 1)

```python
# support/pg_search.py — using Phase 1's PostgreSQL FTS
from django.contrib.postgres.search import (
    SearchVector, SearchQuery, SearchRank, SearchHeadline
)
from support.models import DocumentChunk

def pg_full_text_search(query: str, top_k: int = 10) -> list[dict]:
    """PostgreSQL full-text search with ranking."""
    search_query = SearchQuery(query, config='english')
    search_vector = SearchVector('content', weight='A', config='english')

    chunks = DocumentChunk.objects.annotate(
        rank=SearchRank(search_vector, search_query),
        headline=SearchHeadline('content', search_query,
                                start_sel='<mark>', stop_sel='</mark>',
                                max_words=50, max_fragments=2),
    ).filter(rank__gt=0.01).order_by('-rank')[:top_k]

    return [
        {"id": str(c.id), "content": c.content,
         "score": c.rank, "doc_type": c.doc_type,
         "headline": c.headline}
        for c in chunks
    ]
```

#### RRF Fusion + Hybrid Search

```python
# New: support/hybrid_search.py
from support.rag import collection as chroma_collection
from support.whoosh_search import bm25_search
from support.pg_search import pg_full_text_search

def reciprocal_rank_fusion(
    result_lists: list[list[dict]],
    k: int = 60,
) -> list[dict]:
    """RRF: merge multiple ranked lists into one."""
    scores = {}

    for results in result_lists:
        for rank, doc in enumerate(results):
            doc_id = doc["id"]
            if doc_id not in scores:
                scores[doc_id] = {"score": 0, "doc": doc}
            scores[doc_id]["score"] += 1.0 / (k + rank + 1)

    return sorted(
        [{"score": v["score"], **v["doc"]} for v in scores.values()],
        key=lambda x: x["score"],
        reverse=True,
    )

def hybrid_search(query: str, top_k: int = 3) -> list[dict]:
    """Hybrid search: ChromaDB dense + Whoosh sparse + PG FTS → RRF fusion."""

    # Dense: ChromaDB with BGE-small embeddings
    dense_results_raw = chroma_collection.query(
        query_texts=[query],
        n_results=10,
    )
    dense = [
        {"id": id_, "content": doc, "score": 1 - dist}
        for id_, doc, dist in zip(
            dense_results_raw["ids"][0],
            dense_results_raw["documents"][0],
            dense_results_raw["distances"][0],
        )
    ]

    # Sparse 1: Whoosh BM25
    sparse_whoosh = bm25_search(query, top_k=10)

    # Sparse 2: PostgreSQL full-text search
    sparse_pg = pg_full_text_search(query, top_k=10)

    # Fuse with RRF
    fused = reciprocal_rank_fusion([dense, sparse_whoosh, sparse_pg])

    return fused[:top_k]
```

#### Optional: BGE Reranker

```python
# New: support/reranker.py
from FlagEmbedding import FlagReranker

reranker = FlagReranker(
    'BAAI/bge-reranker-v2-m3',
    use_fp16=True,
)

def rerank(query: str, documents: list[dict], top_k: int = 3) -> list[dict]:
    """Cross-encoder reranking for better precision."""
    pairs = [[query, doc["content"]] for doc in documents]
    scores = reranker.compute_score(pairs)

    for doc, score in zip(documents, scores):
        doc["rerank_score"] = float(score)

    return sorted(documents, key=lambda x: x["rerank_score"], reverse=True)[:top_k]
```

### 4.4 Phase 4 Deliverables

| Deliverable | Effort |
|------------|--------|
| Replace DefaultEmbeddingFunction with BGE-small-en-v1.5 | 1 day |
| Whoosh BM25 index + search | 2 days |
| PostgreSQL full-text search integration | 1 day |
| RRF fusion algorithm | 1 day |
| Optional BGE-Reranker-v2-m3 | 1 day |
| Re-index all documents (3 indexes) | 1 day |

| Metric | Vector Only (Current) | Hybrid (After) |
|--------|----------------------|----------------|
| **Recall@5** | ~65% | ~85% |
| **Precision@3** | ~50% | ~75% |
| **"AC-5000 warranty" finds exact doc** | ❌ Unreliable | ✅ BM25 exact match |
| **"leaking" finds "water damage" docs** | ✅ Semantic | ✅ Semantic + keyword |
| **Document types filterable** | ❌ | ✅ PostgreSQL JSONB metadata |

---

## 5. Phase 5: Agentic — LangChain + LangGraph + PydanticAI

> **Why now?** The RAG pipeline is solid (Phase 4). Now we make the agents truly intelligent. Move from `create_agent` (black box) to a custom `StateGraph`. Add PydanticAI for type-safe tool I/O. This is where the AI stops being a chatbot and starts being an employee.

### 5.1 From `create_agent` to Custom `StateGraph`

#### Current (Black Box)

```python
# Current: support/langchain_agents.py
from langchain.agents import create_agent

agent = create_agent(
    llm=ChatOpenAI(model="deepseek-chat"),
    tools=[lookup_order, check_warranty],
    checkpointer=InMemorySaver(),
)
# ❌ Can't see/modify the graph
# ❌ Can't add conditional routing
# ❌ Can't add human-in-the-loop nodes
```

#### Target (Own the Graph)

```python
# New: support/langgraph_agents.py
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_openai import ChatOpenAI
from typing import Annotated, TypedDict
import operator

# ── State Definition ──

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]  # Append-only message history
    user_id: str
    order_id: str | None
    order_data: dict | None
    tool_results: dict
    confidence: float
    next_step: str  # Routing: "support" | "tools" | "manager" | "risk" | "end"
    requires_human: bool

# ── Node Functions ──

def support_node(state: AgentState) -> AgentState:
    """Maya: front-line support agent."""
    llm = ChatOpenAI(model="deepseek-chat", temperature=0.3)
    prompt = """
    You are Maya, CoolBreeze AC support agent.
    Your role: understand the customer's problem, gather information,
    and either resolve it or escalate.

    Customer message: {user_message}
    Order context: {order_data}

    Respond helpfully and determine next steps.
    """
    response = llm.invoke(prompt.format(
        user_message=state["messages"][-1].content if state["messages"] else "",
        order_data=state.get("order_data", "No order data"),
    ))
    return {
        "messages": [response],
        "next_step": "tools" if "order" in response.content.lower() else "end",
    }

def tools_node(state: AgentState) -> AgentState:
    """Execute tool calls: lookup orders, check warranty, process refund."""
    from support.tools import lookup_order, check_warranty, process_refund

    results = {}
    # Parse the LLM's request for tools
    last_message = state["messages"][-1].content

    if "lookup" in last_message.lower() and state.get("order_id"):
        results["order"] = lookup_order(state["order_id"])

    if "warranty" in last_message.lower():
        results["warranty"] = check_warranty(state.get("order_id", ""))

    return {
        "tool_results": results,
        "next_step": "manager" if "refund" in last_message.lower() else "support",
    }

def manager_node(state: AgentState) -> AgentState:
    """Alex: handles refunds, cancellations, escalated issues."""
    llm = ChatOpenAI(model="deepseek-chat", temperature=0.1)
    prompt = """
    You are Alex, CoolBreeze AC manager.
    You handle: refunds, cancellations, escalated complaints.

    Customer issue: {messages}
    Tool results: {tool_results}

    Decide: approve refund, deny refund, or need more info.
    Respond with structured decision.
    """
    response = llm.invoke(prompt.format(
        messages=state["messages"][-3:],
        tool_results=state.get("tool_results", {}),
    ))
    return {
        "messages": [response],
        "next_step": "risk",
    }

def risk_node(state: AgentState) -> AgentState:
    """Sam: fraud/risk assessment."""
    llm = ChatOpenAI(model="deepseek-chat", temperature=0.0)
    prompt = """
    You are Sam, risk assessment specialist.
    Review the refund decision and flag any fraud risks.

    Order: {order_data}
    Manager decision: {messages}

    Output: RISK_SCORE (0-100), FLAGS (list), RECOMMENDATION
    """
    response = llm.invoke(prompt.format(
        order_data=state.get("order_data", {}),
        messages=state["messages"][-1].content,
    ))
    return {
        "messages": [response],
        "next_step": "end",
    }

# ── Router Function ──

def router(state: AgentState) -> str:
    """Route to the next node based on state."""
    return state["next_step"]

# ── Build the Graph ──

checkpointer = PostgresSaver.from_conn_string(
    "postgres://coolbreeze:password@postgres:5432/coolbreeze"
)

graph = StateGraph(AgentState)

# Add nodes
graph.add_node("support", support_node)
graph.add_node("tools", tools_node)
graph.add_node("manager", manager_node)
graph.add_node("risk", risk_node)

# Add edges with conditional routing
graph.add_edge(START, "support")
graph.add_conditional_edges("support", router, {
    "tools": "tools",
    "end": END,
})
graph.add_conditional_edges("tools", router, {
    "manager": "manager",
    "support": "support",
})
graph.add_conditional_edges("manager", router, {
    "risk": "risk",
    "end": END,
})
graph.add_edge("risk", END)

app = graph.compile(checkpointer=checkpointer)
```

### 5.2 PydanticAI: Typed Tool I/O

#### Problem: Tools Return Raw Dicts

```python
# Current: tools return dict, LLM might misparse
def lookup_order(order_id: str) -> dict:
    return {"id": order_id, "status": "shipped", "total": "499.99"}
    # ❌ No validation
    # ❌ LLM might hallucinate fields
    # ❌ No type safety in tests
```

#### Solution: PydanticAI Models

```python
# New: support/pydantic_tools.py
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class OrderLookupOutput(BaseModel):
    """Structured output from order lookup tool."""
    order_id: str
    status: OrderStatus
    total: float = Field(ge=0, description="Order total in USD")
    customer_name: str
    items: list[str]
    created_at: datetime

class RefundDecision(str, Enum):
    APPROVE = "approve"
    DENY = "deny"
    NEED_MORE_INFO = "need_more_info"

class ManagerResponse(BaseModel):
    """Structured output from manager agent."""
    decision: RefundDecision
    reason: str = Field(min_length=10, max_length=500)
    refund_amount: float | None = Field(None, ge=0)
    follow_up_required: bool = False
    risk_flags: list[str] = []

class WarrantyOutput(BaseModel):
    """Structured output from warranty check."""
    is_covered: bool
    warranty_expiry: datetime | None
    coverage_details: str
    next_steps: list[str]

# ── Tool implementations with typed output ──

def lookup_order(order_id: str) -> OrderLookupOutput:
    """Look up an order and return structured, validated output."""
    from orders.models import Order
    order = Order.objects.select_related('user').get(id=order_id)
    return OrderLookupOutput(
        order_id=order.id,
        status=OrderStatus(order.status),
        total=float(order.total),
        customer_name=order.user.get_full_name(),
        items=[item.name for item in order.items.all()],
        created_at=order.created_at,
    )

def check_warranty(order_id: str) -> WarrantyOutput:
    """Check warranty status — returns validated WarrantyOutput."""
    from datetime import datetime, timedelta
    order = lookup_order(order_id)
    # Assume 1-year warranty from purchase
    expiry = order.created_at + timedelta(days=365)
    is_covered = expiry > datetime.now()
    return WarrantyOutput(
        is_covered=is_covered,
        warranty_expiry=expiry,
        coverage_details="1-year standard warranty covering parts and labor",
        next_steps=[
            "File warranty claim at coolbreeze.com/claims"
        ] if is_covered else [
            "Warranty expired. Offer out-of-warranty repair at $79 diagnostic fee."
        ],
    )
```

### 5.3 Phase 5 Deliverables

| Deliverable | Effort |
|------------|--------|
| Custom StateGraph with 4 nodes (support, tools, manager, risk) | 4 days |
| PostgresSaver checkpointer (replace InMemorySaver) | 1 day |
| PydanticAI models for all tool I/O | 2 days |
| Conditional routing logic | 1 day |
| Integration tests for graph paths | 2 days |

| Metric | create_agent (Current) | Custom StateGraph (After) |
|--------|----------------------|--------------------------|
| **Graph visibility** | ❌ Black box | ✅ Fully visible |
| **Custom routing** | ❌ | ✅ Conditional edges |
| **Human-in-the-loop** | ❌ | ✅ Pause at risk_node |
| **Tool validation** | ❌ raw dict | ✅ Pydantic validated |
| **Checkpointer** | InMemorySaver (volatile) | PostgresSaver (persistent) |
| **Multi-agent routing** | ❌ | ✅ support → tools → manager → risk |

---

## 6. Phase 6: MCP (Model Context Protocol)

> **Why now?** We have structured tools (Phase 5). MCP makes them discoverable, reusable, and framework-agnostic. Instead of hardcoding tool schemas in 3 different agents, tools become self-describing servers that any agent (LangChain, PydanticAI, raw API) can discover and use.

### 6.1 MCP Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    MCP ARCHITECTURE                          │
│                                                              │
│  ┌─────────────────┐                                         │
│  │  CoolBreeze App │  (MCP Host)                             │
│  │                 │                                         │
│  │  MultiServerMCPClient                                    │
│  │       │                                                   │
│  │       ├──────────┬──────────────┐                         │
│  │       ▼          ▼              ▼                         │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────┐                    │
│  │  │ Tools   │ │Knowledge│ │ External │                    │
│  │  │ Server  │ │  Base   │ │  Server  │                    │
│  │  │         │ │ Server  │ │          │                    │
│  │  │ stdio   │ │  stdio  │ │ HTTP+SSE │                    │
│  │  │         │ │         │ │          │                    │
│  │  │ lookup  │ │ hybrid  │ │ ship-    │                    │
│  │  │ order   │ │ search  │ │ engine   │                    │
│  │  │ warranty│ │ pg+bm25 │ │ MCP      │                    │
│  │  │ refund  │ │         │ │ server   │                    │
│  │  └─────────┘ └─────────┘ └──────────┘                    │
│  └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

### 6.2 Tool Server (FastMCP)

```python
# New: mcp_servers/tools_server.py
from fastmcp import FastMCP
from support.pydantic_tools import (
    lookup_order, check_warranty,
    OrderLookupOutput, WarrantyOutput,
)

mcp = FastMCP("CoolBreeze Tools Server ☕❄️")

@mcp.tool()
def lookup_order_tool(order_id: str) -> OrderLookupOutput:
    """Look up an order by ID. Returns order status, items, total, and customer info."""
    return lookup_order(order_id)

@mcp.tool()
def check_warranty_tool(order_id: str) -> WarrantyOutput:
    """Check warranty coverage for an order. Returns coverage status and next steps."""
    return check_warranty(order_id)

@mcp.tool()
def process_refund_tool(order_id: str, amount: float, reason: str) -> dict:
    """Process a refund for an order. Requires manager approval."""
    from support.tools import process_refund
    return process_refund(order_id=order_id, amount=amount, reason=reason)

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### 6.3 Knowledge Base Server (FastMCP)

```python
# New: mcp_servers/knowledge_base_server.py
from fastmcp import FastMCP
from support.hybrid_search import hybrid_search

mcp = FastMCP("CoolBreeze Knowledge Base 📚")

@mcp.tool()
def search_knowledge_base(query: str, top_k: int = 3) -> list[dict]:
    """Search the CoolBreeze knowledge base using hybrid search (dense + sparse)."""
    return hybrid_search(query, top_k=top_k)

@mcp.tool()
def get_document(doc_id: str) -> dict:
    """Retrieve a specific document by ID."""
    from support.rag import collection
    result = collection.get(ids=[doc_id])
    if result["documents"]:
        return {"id": doc_id, "content": result["documents"][0]}
    return {"error": "Document not found"}

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### 6.4 MCP Client Integration

```python
# New: support/mcp_client.py
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
import asyncio

async def create_mcp_agent():
    """Create a LangChain agent that discovers tools via MCP."""

    # Connect to MCP servers
    servers = [
        StdioServerParameters(
            command="python",
            args=["-m", "mcp_servers.tools_server"],
        ),
        StdioServerParameters(
            command="python",
            args=["-m", "mcp_servers.knowledge_base_server"],
        ),
    ]

    all_tools = []
    for server_params in servers:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                all_tools.extend(tools)

    # Create agent with dynamically loaded tools
    llm = ChatOpenAI(model="deepseek-chat")
    agent = create_react_agent(llm, all_tools)

    return agent

# Synchronous wrapper for Django
def get_mcp_agent():
    return asyncio.run(create_mcp_agent())
```

### 6.5 MCP Tool Discovery Flow

```mermaid
sequenceDiagram
    participant Agent as LangChain Agent
    participant Client as MCP Client
    participant Tools as Tools Server
    participant KB as Knowledge Base Server

    Agent->>Client: list_tools()
    Client->>Tools: tools/list (JSON-RPC)
    Tools-->>Client: [lookup_order, check_warranty, process_refund]
    Client->>KB: tools/list (JSON-RPC)
    KB-->>Client: [search_kb, get_document]
    Client-->>Agent: 5 tools discovered

    Agent->>Agent: User: "Warranty on AC-5000?"
    Agent->>Client: call_tool("check_warranty", order_id="123")
    Client->>Tools: tools/call (JSON-RPC)
    Tools-->>Client: WarrantyOutput(covered=True, ...)
    Client-->>Agent: Structured result

    Agent->>Client: call_tool("search_kb", query="AC-5000 warranty")
    Client->>KB: tools/call (JSON-RPC)
    KB-->>Client: [top-3 documents]
    Client-->>Agent: Search results

    Agent-->>Agent: Synthesize response
```

### 6.6 Phase 6 Deliverables

| Deliverable | Effort |
|------------|--------|
| FastMCP Tools Server (3 tools) | 2 days |
| FastMCP Knowledge Base Server (2 tools) | 1 day |
| MCP Client integration (LangChain + LangGraph) | 2 days |
| docker-compose MCP service entries | 1 day |

| Metric | Hardcoded Tools (Current) | MCP (After) |
|--------|--------------------------|-------------|
| **Add a new tool** | Edit 3 files (agent, tools, schemas) | Add `@mcp.tool()` to 1 file — auto-discovered |
| **Tool discovery** | ❌ Manual (read source code) | ✅ `list_tools()` — self-documenting |
| **Framework agnostic** | ❌ Tied to LangChain `@tool` decorator | ✅ Works with any MCP-compatible framework |
| **Tool isolation** | ❌ Crash = crash entire app | ✅ Tool servers are separate processes |
| **External tool integration** | ❌ Custom code for each | ✅ `pip install stripe-mcp-server` — done |

---

## 7. Phase 7: vLLM + Ollama + GPU (Self-Hosted LLM)

> **Why now?** We have a full agentic system (Phases 5-6). Every call goes to DeepSeek's cloud API — $0.50/1M tokens, 3s latency, data leaves our network. Self-hosting with vLLM (production) and Ollama (development) cuts cost 10x, latency 5x, and keeps data private.

### 7.1 Why Self-Host?

| Cloud API (Current) | Self-Hosted (After) |
|--------------------|-------------------|
| **Cost:** $0.50/1M tokens (~$5/month for 10K conversations) | **Cost:** $0.05/1M tokens (electricity only, ~$0.50/month) |
| **Latency:** 2-5 seconds (network + API queue) | **Latency:** 0.3-1.0 seconds (local GPU) |
| **Privacy:** All data sent to DeepSeek servers | **Privacy:** Data never leaves your GPU |
| **Rate limits:** API quotas + throttling | **No limits:** Your GPU, your rules |
| **Model choice:** DeepSeek only | **Any open model:** Qwen, Llama, Mistral, DeepSeek, etc. |

### 7.2 vLLM: Production Self-Hosting (GPU Required)

```yaml
# docker-compose.yml (already in Phase 1):
vllm:
  image: vllm/vllm-openai:latest
  container_name: coolbreeze-vllm
  command: >
    --model Qwen/Qwen2.5-7B-Instruct
    --port 8001
    --max-model-len 8192
    --gpu-memory-utilization 0.90
    --enable-prefix-caching
  ports:
    - "8001:8001"
  environment:
    - HF_HOME=/model-cache
  volumes:
    - model_cache:/model-cache
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
  profiles:
    - gpu
```

### 7.3 Ollama: Development Self-Hosting (No GPU Required)

```yaml
# docker-compose.yml (already in Phase 1):
ollama:
  image: ollama/ollama:latest
  container_name: coolbreeze-ollama
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
  profiles:
    - dev
```

Setup:
```bash
# Pull model (runs on CPU, sufficient for dev)
docker compose --profile dev up -d
docker compose exec ollama ollama pull qwen2.5:7b

# Or for lighter-weight dev: qwen2.5:3b (faster, less RAM)
docker compose exec ollama ollama pull qwen2.5:3b

# Test
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:7b",
  "prompt": "Hello from CoolBreeze!",
  "stream": false
}'
```

### 7.4 LLM Router: Smart Model Selection

```python
# New: support/llm_router.py
from langchain_openai import ChatOpenAI
from ollama import Client as OllamaClient
import os

class LLMRouter:
    """Route LLM calls to the best available backend."""

    def __init__(self):
        self._ollama = None
        self._vllm = None
        self._deepseek = None

    @property
    def ollama(self) -> OllamaClient:
        if self._ollama is None:
            self._ollama = OllamaClient(
                host=os.environ.get("OLLAMA_HOST", "http://ollama:11434")
            )
        return self._ollama

    @property
    def vllm(self) -> ChatOpenAI:
        if self._vllm is None:
            self._vllm = ChatOpenAI(
                model=os.environ.get("VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
                base_url=os.environ.get("VLLM_BASE_URL", "http://vllm:8001/v1"),
                api_key="not-needed",
            )
        return self._vllm

    @property
    def deepseek(self) -> ChatOpenAI:
        if self._deepseek is None:
            self._deepseek = ChatOpenAI(
                model="deepseek-chat",
                api_key=os.environ["DEEPSEEK_API_KEY"],
            )
        return self._deepseek

    def get_llm(self, task: str = "default") -> ChatOpenAI:
        """Select the best LLM backend based on task and availability."""

        # Priority: vLLM (production) > Ollama (dev) > DeepSeek (fallback)
        priority = os.environ.get("LLM_PRIORITY", "vllm,ollama,deepseek").split(",")

        for backend in priority:
            backend = backend.strip()
            if backend == "vllm":
                try:
                    # Quick health check
                    self.vllm.invoke("ping")
                    return self.vllm
                except Exception:
                    continue
            elif backend == "ollama":
                try:
                    self.ollama.list()
                    return ChatOpenAI(
                        model=os.environ.get("OLLAMA_MODEL", "qwen2.5:7b"),
                        base_url="http://ollama:11434/v1",
                        api_key="ollama",
                    )
                except Exception:
                    continue
            elif backend == "deepseek":
                return self.deepseek

        # Ultimate fallback
        return self.deepseek


# Usage in agents:
router = LLMRouter()

def support_node(state: AgentState) -> AgentState:
    llm = router.get_llm(task="support")  # Auto-selects best available
    response = llm.invoke(prompt)
    # ...
```

### 7.5 Phase 7 Deliverables

| Deliverable | Effort |
|------------|--------|
| vLLM Docker profile + GPU config | 1 day |
| Ollama Docker profile + model pull | 1 day |
| LLM Router with auto-failover | 2 days |
| Update all agents to use LLMRouter | 1 day |
| benchmark script (latency + cost comparison) | 1 day |

| Metric | Cloud API (DeepSeek) | vLLM (Qwen 7B) | Ollama (Qwen 7B) |
|--------|---------------------|----------------|-------------------|
| **Latency (p50)** | ~3 seconds | ~0.5 seconds | ~2 seconds (CPU) |
| **Cost/1M tokens** | $0.50 | ~$0.02 (electricity) | ~$0.01 (electricity) |
| **Monthly (10K convos)** | ~$5 | ~$0.20 | ~$0.10 |
| **Data privacy** | ❌ Cloud | ✅ Local GPU | ✅ Local CPU |
| **GPU required** | N/A | ✅ NVIDIA (8GB+ VRAM) | ❌ CPU only |
| **Throughput** | Rate-limited | ~50 req/s (7B model) | ~5 req/s (CPU) |

---
## 8. Phase 8: Evaluation + Observability (Quality Assurance)

> **Why now?** The system does everything (Phases 1-7). But how good is "good"? We need metrics: Is the RAG retrieving relevant docs? Are agents making correct decisions? Is the system healthy? Evaluation and observability turn "it seems fine" into "87.3% answer correctness with p95 latency of 1.2s."

### 8.1 RAG Evaluation (RAGAS)

#### What RAGAS Measures

| Metric | What It Means | Target |
|--------|--------------|--------|
| **Context Precision** | Of the retrieved documents, how many are actually relevant? | > 0.80 |
| **Context Recall** | Of all relevant documents, how many were retrieved? | > 0.75 |
| **Faithfulness** | Does the answer come from the retrieved docs (not hallucinated)? | > 0.90 |
| **Answer Relevancy** | Does the answer actually address the user's question? | > 0.85 |

```python
# New: evaluation/eval_rag.py
from ragas import evaluate
from ragas.metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy,
)
from datasets import Dataset

# Test dataset: question, ground truth, and retrieved context
eval_data = Dataset.from_dict({
    "question": [
        "What is the warranty on AC-5000?",
        "How do I return a leaking unit?",
        "Can I get a refund if installed 6 months ago?",
    ],
    "answer": [
        "AC-5000 has a 1-year standard warranty covering parts and labor.",
        "Visit coolbreeze.com/returns or contact support for a leaking unit.",
        "Refunds are available within 30 days; after that, warranty repair applies.",
    ],
    "contexts": [
        ["AC-5000 warranty: 1 year, parts and labor, standard terms."],
        ["Return policy: visit website or call support. Leaking units qualify."],
        ["Refund policy: 30 days. Warranty: 1 year repair service after 30 days."],
    ],
    "ground_truth": [
        "AC-5000 comes with a 1-year standard warranty covering parts and labor.",
        "To return a leaking unit, visit coolbreeze.com/returns or contact customer support.",
        "Refunds are only available within 30 days of purchase. After 30 days, warranty repair applies.",
    ],
})

# Run evaluation
result = evaluate(
    eval_data,
    metrics=[
        context_precision,
        context_recall,
        faithfulness,
        answer_relevancy,
    ],
)

print(f"Context Precision: {result['context_precision']:.3f}")
print(f"Context Recall:    {result['context_recall']:.3f}")
print(f"Faithfulness:      {result['faithfulness']:.3f}")
print(f"Answer Relevancy:  {result['answer_relevancy']:.3f}")
```

### 8.2 Agent Trajectory Evaluation

```python
# New: evaluation/eval_agents.py
from pydantic import BaseModel

class AgentTrajectory(BaseModel):
    """Record an agent's full decision path."""
    user_message: str
    expected_outcome: str  # "refund_approved", "info_provided", "escalated"
    actual_nodes_visited: list[str]  # ["support", "tools", "manager", "risk"]
    actual_outcome: str
    tool_calls_made: list[str]
    response_time_ms: float
    confidence: float
    hallucination_flags: list[str] = []

class AgentEvalResult(BaseModel):
    trajectory: AgentTrajectory
    correctness: float  # 0-1
    efficiency: float   # was the path optimal?
    helpfulness: float  # 0-1

# Test suite
def test_refund_trajectory():
    """Agent should follow support→tools→manager→risk for refund requests."""
    result = run_agent_scenario(
        user_message="I want a refund for my AC-5000, it's leaking",
        order_id="123",
    )
    assert "tools" in result.trajectory.actual_nodes_visited
    assert "manager" in result.trajectory.actual_nodes_visited
    assert "risk" in result.trajectory.actual_nodes_visited
    assert result.correctness > 0.7

def test_simple_question_trajectory():
    """Simple questions should not trigger manager/risk nodes."""
    result = run_agent_scenario(
        user_message="What are your business hours?",
    )
    assert "manager" not in result.trajectory.actual_nodes_visited
    assert "risk" not in result.trajectory.actual_nodes_visited
    assert result.efficiency > 0.8

def test_rag_quality():
    """RAG should retrieve AC-5000 warranty doc for warranty questions."""
    result = run_agent_scenario(
        user_message="Is my AC-5000 still under warranty?",
        order_id="WARRANTY-TEST-001",
    )
    assert result.trajectory.confidence > 0.7
    assert result.correctness > 0.8
```

### 8.3 LLM-as-Judge

```python
# New: evaluation/llm_judge.py
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

class JudgeScore(BaseModel):
    correctness: int = Field(ge=1, le=5, description="Factual accuracy of the response")
    helpfulness: int = Field(ge=1, le=5, description="How helpful was the response")
    tone: int = Field(ge=1, le=5, description="Appropriateness of tone (1=hostile, 5=perfect)")
    hallucination: bool = Field(description="Does the response contain fabricated information?")

def judge_response(question: str, answer: str, ground_truth: str) -> JudgeScore:
    """Use an LLM to evaluate another LLM's output."""
    llm = ChatOpenAI(model="deepseek-chat", temperature=0.0)

    prompt = f"""
    You are an impartial judge evaluating AI customer support quality.

    Question: {question}
    AI Response: {answer}
    Ground Truth: {ground_truth}

    Score the response on:
    - correctness (1-5): Are the facts right?
    - helpfulness (1-5): Did it actually help the customer?
    - tone (1-5): Was it polite and appropriate?
    - hallucination (true/false): Are there fabricated details?

    Output as JSON.
    """

    response = llm.invoke(prompt)
    return JudgeScore.model_validate_json(response.content)
```

### 8.4 Observability: Prometheus + Grafana + LangFuse

#### Prometheus Metrics

```python
# New: support/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# LLM metrics
agent_latency = Histogram(
    "agent_latency_seconds",
    "Agent response time",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    labelnames=["agent_type", "model"],
)

tool_calls = Counter(
    "tool_calls_total",
    "Total tool invocations",
    labelnames=["tool_name", "agent_type"],
)

llm_tokens = Counter(
    "llm_token_count",
    "LLM token usage",
    labelnames=["model", "direction"],  # "input" or "output"
)

# System metrics
active_sessions = Gauge(
    "active_sessions",
    "Number of active customer sessions",
)

rag_cache_hits = Counter(
    "rag_cache_hits_total",
    "RAG embedding cache hits/misses",
    labelnames=["status"],  # "hit" or "miss"
)

# FastAPI endpoint
from fastapi import FastAPI, Response

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

#### Prometheus Config

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'coolbreeze'
    static_configs:
      - targets: ['app:8001']
  - job_name: 'celery'
    static_configs:
      - targets: ['flower:5555']
```

#### LangFuse LLM Tracing

```python
# New: support/langfuse_tracing.py
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context
import os

langfuse = Langfuse(
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
)

@observe(as_type="generation")
def traced_llm_call(prompt: str, model: str = "deepseek-chat") -> str:
    """LLM call with automatic tracing to LangFuse."""
    langfuse_context.update_current_observation(
        model=model,
        input=prompt,
    )
    # ... LLM call ...
    langfuse_context.update_current_observation(
        output=response_text,
        usage={"input_tokens": input_tokens, "output_tokens": output_tokens},
    )
    return response_text
```

### 8.5 Phase 8 Deliverables

| Deliverable | Effort |
|------------|--------|
| RAGAS evaluation pipeline (4 metrics) | 2 days |
| Agent trajectory test suite | 2 days |
| LLM-as-Judge scoring | 1 day |
| Prometheus metrics + `/metrics` endpoint | 2 days |
| Grafana dashboard (4 panels) | 1 day |
| LangFuse LLM tracing | 1 day |
| CI quality gate (block deploy if scores drop) | 1 day |

| Metric | Current | Target |
|--------|---------|--------|
| **RAG context precision** | Unknown | > 0.80 |
| **Agent answer correctness** | Unknown | > 0.85 |
| **p95 latency** | ~8 sec (sync + cloud LLM) | < 2 sec |
| **Hallucination rate** | Unknown | < 5% |
| **Observability** | ❌ Zero | ✅ Full dashboards + alerts |

---

## 9. Phase 9: Production Hardening

> **Why now?** The system is feature-complete (Phases 1-8). Now we make it bulletproof. Security audits, load testing, CI/CD, backups, and disaster recovery. This is the difference between a cool demo and a production system.

### 9.1 Security Audit

```bash
# Static analysis
pip install bandit detect-secrets pip-audit

# Bandit: Python security scanner
bandit -r . -f json -o bandit_report.json

# pip-audit: dependency vulnerability scanner
pip-audit --output pip_audit_report.json

# detect-secrets: find leaked secrets in code
detect-secrets scan --all-files > secrets_report.json

# checkov: IaC security (Dockerfile, docker-compose.yml)
checkov --directory . --output json > checkov_report.json
```

### 9.2 Load Testing with Locust

```python
# locustfile.py (upgrade existing)
from locust import HttpUser, task, between, events
import random

class CoolBreezeUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def chat_simple(self):
        """Most common: simple support questions."""
        questions = [
            "What are your business hours?",
            "How do I clean my AC filter?",
            "Do you offer installation?",
        ]
        self.client.post("/api/chat", json={
            "user_id": f"user_{random.randint(1, 1000)}",
            "message": random.choice(questions),
        })

    @task(2)
    def chat_with_order(self):
        """Order-related queries (hits DB + tools)."""
        self.client.post("/api/chat", json={
            "user_id": f"user_{random.randint(1, 1000)}",
            "message": "What's the status of my order?",
            "order_id": str(random.randint(1000, 9999)),
        })

    @task(1)
    def refund_request(self):
        """Heavy path: triggers full agent pipeline."""
        self.client.post("/api/chat", json={
            "user_id": f"user_{random.randint(1, 1000)}",
            "message": "I want a refund, my unit is defective",
            "order_id": str(random.randint(1000, 9999)),
        })

    @task(1)
    def websocket_stream(self):
        """WebSocket streaming load."""
        # Simulated via HTTP for Locust compatibility
        self.client.post("/api/agent/run", json={
            "user_id": f"user_{random.randint(1, 1000)}",
            "agent_type": "support",
            "context": {"message": "Tell me about warranties"},
        })

# Target metrics
# 100 concurrent users, < 1% error rate, p95 < 3s
# Run: locust -f locustfile.py --headless -u 100 -r 10 -t 5m
```

### 9.3 GitHub Actions CI/CD

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_DB: coolbreeze
          POSTGRES_USER: coolbreeze
          POSTGRES_PASSWORD: testpass
        ports:
          - 5432:5432
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: postgres://coolbreeze:testpass@localhost:5432/coolbreeze
          REDIS_HOST: localhost
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
        run: pytest --cov --cov-report=xml

      - name: Security audit
        run: |
          pip install bandit pip-audit
          bandit -r . -ll
          pip-audit

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml

  quality-gate:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: RAGAS evaluation
        run: pytest evaluation/ --json-report

      - name: Check quality thresholds
        run: python evaluation/check_thresholds.py
        # Fails if: context_precision < 0.75 or faithfulness < 0.85
```

### 9.4 Backup Strategy

```bash
#!/bin/bash
# scripts/backup.sh — PostgreSQL backup
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB="coolbreeze"

# Full backup
pg_dump -U coolbreeze -h postgres $DB | gzip > "$BACKUP_DIR/${DB}_${TIMESTAMP}.sql.gz"

# Keep last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup complete: ${DB}_${TIMESTAMP}.sql.gz"
```

### 9.5 Phase 9 Deliverables

| Deliverable | Effort |
|------------|--------|
| bandit + pip-audit + detect-secrets audit | 1 day |
| Locust load testing (100 concurrent users) | 1 day |
| GitHub Actions CI/CD pipeline | 2 days |
| pg_dump backup script + cron | 1 day |
| Disaster recovery runbook | 1 day |

| Metric | Current | Target |
|--------|---------|--------|
| **Security vulnerabilities** | Unknown | 0 critical/high |
| **Max concurrent users** | ~4 (sync) | 100+ (async + Celery + vLLM) |
| **Deploy process** | Manual | `git push` → CI → auto-deploy |
| **Backup frequency** | Never | Daily + on-demand |
| **Recovery time** | Unknown | < 1 hour |

---

## 10. 9-Phase Roadmap (Summary)

| Phase | Technology | Why This Order | Effort | Cumulative |
|-------|-----------|----------------|--------|-----------|
| **1** | 🐳 Docker · 🐙 Compose · 🐘 PostgreSQL | Foundation: everything else runs on this | 9 days | 9 days |
| **2** | ⚡ Async · 🚀 FastAPI | Non-blocking I/O: required before adding more services | 7 days | 16 days |
| **3** | 📦 Redis · 🔄 Celery | Background processing + caching: needed by agents | 9 days | 25 days |
| **4** | 🔍 Hybrid Search (ChromaDB + Whoosh + PG) | Better RAG: feeds better answers to agents | 7 days | 32 days |
| **5** | 🧠 LangChain · LangGraph · PydanticAI | Custom agent graph: the brain of the operation | 10 days | 42 days |
| **6** | 🔌 MCP (Model Context Protocol) | Tool discoverability: makes agents extensible | 6 days | 48 days |
| **7** | 🖥️ vLLM · 🦙 Ollama · GPU | Self-hosted LLM: 10x cheaper, 5x faster, private | 6 days | 54 days |
| **8** | 📊 Evaluation · 👁️ Observability | Quality assurance: measure what matters | 8 days | 62 days |
| **9** | 🛡️ Production Hardening | Bulletproof: security, load testing, CI/CD, backups | 6 days | 68 days |

**Total Estimated Effort:** 68 working days (~14 weeks)

### Phase Dependencies

```mermaid
graph TD
    P1[Phase 1: Docker + Compose + PG] --> P2[Phase 2: Async + FastAPI]
    P1 --> P3[Phase 3: Redis + Celery]
    P2 --> P4[Phase 4: Hybrid Search RAG]
    P3 --> P4
    P2 --> P5[Phase 5: Agentic]
    P3 --> P5
    P4 --> P5
    P5 --> P6[Phase 6: MCP]
    P4 --> P7[Phase 7: vLLM + Ollama]
    P6 --> P7
    P5 --> P8[Phase 8: Evaluation]
    P7 --> P8
    P1 --> P9[Phase 9: Production Hardening]
    P2 --> P9
    P3 --> P9
    P5 --> P9
    P8 --> P9
```

### Quick-Start by Profile

```bash
# Minimal dev (Phase 1-3): Django + PostgreSQL + Redis + Celery
docker compose up -d

# Dev with local LLM (Phase 1-3 + Phase 7): adds Ollama
docker compose --profile dev up -d

# Production (all phases): adds vLLM GPU
docker compose --profile gpu up -d

# Full stack with monitoring (Phase 8)
docker compose --profile gpu --profile monitoring up -d
```

---

## 11. Risk Assessment

| Risk | Severity | Likelihood | Mitigation |
|------|----------|-----------|------------|
| **PostgreSQL migration breaks data** | High | Low | Full dump → test on staging → verify with test suite before production cutover |
| **vLLM GPU not available / too expensive** | Medium | Medium | LLM Router auto-falls back to DeepSeek API; Ollama runs on CPU for dev |
| **LangGraph custom graph has bugs** | Medium | Medium | Extensive integration tests per trajectory; can fall back to `create_agent` if needed |
| **Hybrid search recall worse than vector-only** | Low | Low | A/B test before full rollout; keep ChromaDB-only path as fallback |
| **MCP adds latency** | Medium | Low | MCP servers run locally (stdio) — sub-millisecond overhead; HTTP+SSE only for external services |
| **Celery task backlog during traffic spikes** | High | Medium | Auto-scale workers; Redis backpressure; Flower alerts on queue depth > 100 |
| **Ollama too slow for production** | Medium | High | Ollama is explicitly dev-only; vLLM or DeepSeek API for production traffic |
| **68-day estimate is wrong** | Low | High | Phases 1-3 deliver value independently; each phase is a shippable increment |

---

## 12. Success Metrics

| Category | Metric | Baseline | Target |
|----------|--------|----------|--------|
| **Latency** | p95 API response time | ~8 sec | < 2 sec |
| **Throughput** | Max concurrent users | ~4 | 100+ |
| **Cost** | LLM cost per 1K conversations | ~$0.50 | < $0.05 (self-hosted) |
| **RAG Quality** | Context precision | Unknown | > 0.80 |
| **RAG Quality** | Faithfulness | Unknown | > 0.90 |
| **Agent Quality** | Answer correctness (LLM judge) | Unknown | > 0.85 |
| **Reliability** | Error rate (non-4xx) | ~5% | < 1% |
| **Dev Experience** | Onboarding time | 30-60 min | < 5 min |
| **Deploy Speed** | Time from commit to production | Manual (hours) | < 10 min (CI/CD) |
| **Security** | Critical vulnerabilities | Unknown | 0 |

---

## 13. ELI5: The Kitchen Analogy (v4.0 — Updated)

> Imagine you're running a coffee shop called CoolBreeze. Here's what each technology does, explained like you're 5.

| Technology | Kitchen Analogy | What Changes |
|-----------|----------------|-------------|
| 🐳 **Docker** | The entire shop packed in a perfect shipping box. Open it anywhere — identical. | No more "works on my machine" |
| 🐙 **Docker Compose** | One button that turns on the espresso machine, oven, fridge, lights, and music. All at once. | 1 command instead of 6 terminals |
| 🐘 **PostgreSQL** | Super-powered filing cabinet that can do math, search, and find patterns. | MySQL → PostgreSQL |
| ⚡ **Async Python** | Barista makes 100 coffees at once — starts one, while it brews helps another. | 100x more customers served |
| 🚀 **FastAPI** | Self-updating menu board that lists every possible order (Swagger docs). | API docs appear automatically |
| 📦 **Redis** | Barista's photographic memory + walkie-talkie for all staff + bouncer at the door. | Cache + pub/sub + rate limiter |
| 🔄 **Celery** | Take order → give buzzer → kitchen cooks → buzzer rings. Nobody waits at the counter. | Background tasks + retries |
| 🔍 **Hybrid Search** | Two librarians: one knows what things MEAN, the other knows exact WORDS. Together they find everything. | Dense + sparse retrieval |
| 🧠 **LangGraph** | Recipe book that says: "If customer asks about refund, send to manager. If manager approves, check for fraud." | Custom agent routing |
| ✅ **PydanticAI** | Order form with checkboxes — can't write "pizza" in the "coffee size" field. | Typed tool I/O |
| 🔌 **MCP** | USB-C port for tools. Plug in any tool and it just works, no manual wiring. | Dynamic tool discovery |
| 🖥️ **vLLM** | Your own private chef in the back — faster, cheaper, nobody else can taste the food. | Self-hosted LLM (GPU) |
| 🦙 **Ollama** | Practice chef for the training room — doesn't need the expensive kitchen, but makes real food. | Local dev LLM (CPU) |
| 📊 **Evaluation** | Health inspector who grades every dish: "This answer is 87% correct, tone was friendly!" | RAGAS + LLM judge |
| 👁️ **Observability** | Dashboard showing: orders/second, average wait time, which barista is busiest. | Prometheus + Grafana |
| 🛡️ **Production Hardening** | Fire extinguishers, security cameras, backup generators, emergency procedures. | Security + CI/CD + backups |

### Big Picture

| Before | After |
|--------|-------|
| ☕ **Coffee cart** — 1 barista, 1 coffee at a time, no kitchen, no memory | 🏢 **Full-service café** — kitchen, walkie-talkies, private chef, security cameras, 100 baristas |
| Manual setup, "works on my machine" | `docker compose up` — identical everywhere |
| Blocking sync — freezes on every LLM call | Async + Celery — never blocks |
| Cloud API — $5/month, 3 sec latency, no privacy | Self-hosted — $0.50/month, 0.5 sec, 100% private |
| No quality metrics — "seems fine" | Full evaluation + dashboards + CI quality gate |
| **Database** | 🗄️ Filing cabinet | 🧠 Supercomputer |
