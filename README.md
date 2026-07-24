# 🧊 AI Employees — Multi-Agent Customer Support System

An intelligent customer support platform for **CoolBreeze AC**, powered by **DeepSeek V4 Pro** and **LangChain/LangGraph**. Three AI agents — Support Agent, Manager Agent, and Risk Analyst — collaborate autonomously to handle customer queries, check order statuses, and make refund decisions.

---

## 🏗 Architecture

```
User Chat → Support Agent (Maya) → Tools (orders, deliveries, knowledge base)
                    ↓ escalate
            Manager Agent → Risk Agent (fraud analysis)
                    ↓
              Refund Decision
```

### Agent Roles

| Agent | Role | Capabilities |
|-------|------|--------------|
| **Maya** (Support) | First-line customer support | Checks orders, delivery status, refund history, searches company docs |
| **Manager** | Refund decision authority | Reviews escalated cases, consults risk team, approves/denies refunds |
| **Risk Analyst** | Fraud detection | Analyzes customer order & refund patterns, returns risk verdict |

### Live Dashboard

A staff-only dashboard shows real-time agent activity via **Server-Sent Events (SSE)**, streaming tool calls, agent decisions, and final replies as they happen.

---

## 🛠 Tech Stack

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

## 📦 Project Structure

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
├── templates/               # Django templates (orders, support chat, dashboard)
├── static/                  # Static assets (WhiteNoise)
├── data.json                # Seed fixture (products, orders, users, refunds)
├── requirements.txt         # Python dependencies
├── Procfile                 # Railway deployment
└── manage.py                # Django management
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- MySQL 8.0+
- DeepSeek API key ([platform.deepseek.com](https://platform.deepseek.com))

### Setup

```bash
# Clone the repo
git clone https://github.com/mwyzer/django_ai_employees.git
cd django_ai_employee

# Create virtual environment
python -m venv env
source env/Scripts/activate   # Windows
# source env/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
SECRET_KEY=django-insecure-your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=ai_employees
DB_USER=root
DB_PASSWORD=your-mysql-password
DB_HOST=localhost
DB_PORT=3306

DEEPSEEK_API_KEY=sk-your-deepseek-api-key
DEEPSEEK_MODEL=deepseek-chat
```

### Database & Seed Data

```bash
# Create MySQL database
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS ai_employees CHARACTER SET utf8mb4;"

# Run migrations
python manage.py migrate

# Load seed data (products, orders, users, refunds, conversations)
python manage.py loaddata data.json
```

### Run

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/login/

---

## 👥 Test Users

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | Superuser (staff dashboard access) |
| `rathan` | `rathan123` | Customer (5 orders) |
| `priya` | `priya123` | Customer (3 orders) |
| `arjun` | `arjun123` | Customer (2 orders) |
| `fraud_test` | `fraud123` | Customer (5 orders, high refund ratio — for fraud testing) |

---

## 🔍 How It Works

1. **User logs in** → sees their orders on the orders page
2. **Clicks an order** → opens the AI chat interface
3. **Types a message** → Support Agent (Maya) responds using tools:
   - `get_order_details` — fetches order status and tracking info
   - `check_delivery_status` — checks live tracking via carrier
   - `get_refund_history` — reviews past refunds
   - `search_knowledge_base` — queries company docs via ChromaDB RAG
   - `escalate_to_manager` — escalates complex refund decisions
4. **Manager Agent** reviews the case and can consult the **Risk Agent**
5. **Risk Agent** analyzes fraud patterns (refund-to-order ratio, recent activity)
6. **Final reply** is delivered to the user in the chat interface
7. **Staff dashboard** at `/support/dashboard/` shows all conversations with real-time streaming

---

## 🧪 API Endpoints

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /login/` | Public | Login page |
| `POST /login/` | Public | Authenticate |
| `GET /orders/` | Login required | User's orders list |
| `GET /orders/<id>/` | Login required | Order detail + AI chat |
| `POST /support/chat/<id>/` | Login required | Send message to AI agent |
| `GET /support/dashboard/` | Staff only | Admin dashboard |
| `GET /support/dashboard/<id>/` | Staff only | Conversation detail |
| `GET /support/dashboard/stream/<id>/` | Staff only | SSE real-time stream |

---

## 🧠 AI Implementation Details

Two implementations are available:

| Approach | File | Use Case |
|----------|------|----------|
| **LangChain/LangGraph** | `support/langchain_agents.py` | Currently active — full agent orchestration with checkpoints and middleware |
| **Raw OpenAI SDK** | `support/agents.py` | Direct DeepSeek API calls with custom tool loops |

Both use `https://api.deepseek.com/v1` as the base URL with OpenAI-compatible `chat/completions` endpoint.

### RAG (Retrieval-Augmented Generation)

Company documents (PDFs) are stored in `support/documents/` and indexed by ChromaDB. When a customer asks about refund policies or warranty, the agent retrieves relevant chunks and uses them to ground its response.

Load/reload documents:
```python
python manage.py shell
>>> from support.rag import load_documents
>>> load_documents()
```

---

## 🚢 Deployment (Railway)

The app is configured for Railway deployment via `Procfile`:

```
web: gunicorn dj_ai_employee_main.wsgi --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 300
```

Static files are served via **WhiteNoise**. Set all environment variables from `.env` in Railway's dashboard.

---

## 📄 License

MIT
