# 🧊 AI Employees — Project Overview

**Project:** CoolBreeze AC Multi-Agent Customer Support System  
**Version:** 1.0  
**Stack:** Django 6.0 / Python 3.12 / DeepSeek V4 Pro / LangChain + LangGraph  
**Deployment:** Railway (Gunicorn + WhiteNoise)  

---

## 1. What Is This?

An intelligent customer support platform for **CoolBreeze AC**, where three AI agents — Support Agent, Manager Agent, and Risk Analyst — collaborate autonomously to handle customer queries, check order statuses, make refund decisions, and detect fraud.

---

## 2. Architecture at a Glance

```
User Chat → Support Agent (Maya) → Tools (orders, deliveries, knowledge base)
                    ↓ escalate
            Manager Agent → Risk Agent (fraud analysis)
                    ↓
              Refund Decision
```

---

## 3. Agent Roles

| Agent | Role | Capabilities |
|-------|------|--------------|
| **Maya** (Support) | First-line customer support | Checks orders, delivery status, refund history, searches company docs |
| **Manager** | Refund decision authority | Reviews escalated cases, consults risk team, approves/denies refunds |
| **Risk Analyst** | Fraud detection | Analyzes customer order & refund patterns, returns risk verdict |

---

## 4. Key Features

- **Multi-agent AI chat** — Three agents collaborate via LangGraph orchestration
- **Tool-augmented agents** — Order lookup, delivery tracking, refund history, knowledge base search
- **RAG knowledge base** — Company documents (PDFs) indexed in ChromaDB for grounded responses
- **Real-time staff dashboard** — SSE streaming of agent tool calls, decisions, and replies
- **Order management** — Customers view orders with embedded AI chat
- **Fraud detection** — Risk Agent analyzes refund-to-order ratios and patterns

---

## 5. Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Django 6.0, Python 3.12 |
| **AI / LLM** | DeepSeek V4 Pro (OpenAI-compatible API) |
| **Agent Framework** | LangChain + LangGraph (tool calling, checkpoints, middleware) |
| **RAG / Knowledge Base** | ChromaDB + PDF ingestion (`pypdf`) |
| **Real-time Streaming** | Server-Sent Events (SSE) via `queue.Queue` pub/sub |
| **Database** | MySQL 8.0 + PyMySQL |
| **Frontend** | Django Templates (Tailwind-style inline CSS) |
| **Deployment** | Railway (Gunicorn + WhiteNoise) |

---

## 6. Project Structure

```
django_ai_employees/
├── dj_ai_employee_main/     # Django project settings, URLs, WSGI
├── orders/                  # Orders app — Product, Order, RefundRequest models
├── support/                 # Support app — agents, tools, RAG, event queue
│   ├── agents.py            # DeepSeek SDK agent loops (support/manager/risk)
│   ├── langchain_agents.py  # LangChain/LangGraph agent orchestration
│   ├── tools.py             # Tool implementations (order lookup, delivery, etc.)
│   ├── rag.py               # ChromaDB RAG for company document search
│   ├── event_queue.py       # In-memory pub/sub for SSE streaming
│   └── documents/           # PDFs for RAG (refund policy, warranty, FAQs)
├── templates/               # Django templates (login, orders, chat, dashboard)
├── static/                  # Static assets (WhiteNoise)
├── tests/                   # pytest test suite
├── data.json                # Seed fixture (products, orders, users, refunds)
├── requirements.txt         # Python dependencies
├── Procfile                 # Railway deployment
└── manage.py                # Django management
```

---

## 7. Test Users

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | Superuser (staff dashboard access) |
| `rathan` | `rathan123` | Customer (5 orders) |
| `dewa` | `dewa123` | Customer (3 orders) |
| `arjun` | `arjun123` | Customer (2 orders) |
| `fraud_test` | `fraud123` | Customer (5 orders, high refund ratio — for fraud testing) |

---

## 8. Quick Start

```bash
git clone https://github.com/mwyzer/django_ai_employees.git
cd django_ai_employees
python -m venv env
source env/Scripts/activate   # Windows
pip install -r requirements.txt

# Create .env with SECRET_KEY, DB_*, DEEPSEEK_API_KEY
# Create MySQL database: ai_employees
python manage.py migrate
python manage.py loaddata data.json
python manage.py runserver
```

Open **http://127.0.0.1:8000/login/**
