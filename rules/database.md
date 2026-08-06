# 🗄 Database Configuration

**Project:** AI Employees — CoolBreeze AC  
**Engine:** MySQL 8.0  
**ORM:** Django ORM with PyMySQL  

---

## 1. Database Engine

```python
# dj_ai_employee_main/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config("DB_NAME"),        # ai_employees
        'USER': config("DB_USER"),        # root
        'PASSWORD': config("DB_PASSWORD"),
        'HOST': config("DB_HOST"),        # localhost
        'PORT': config("DB_PORT"),        # 3306
    }
}
```

All credentials are stored in `.env` via `python-decouple`.

---

## 2. Environment Variables

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

---

## 3. Setup Instructions

### 3.1 Prerequisites

- MySQL 8.0+ installed and running
- Python 3.12+

### 3.2 Create the Database

```bash
# Via MySQL CLI
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS ai_employees CHARACTER SET utf8mb4;"
```

### 3.3 Run Migrations

```bash
python manage.py migrate
```

This creates all tables defined in the `orders` and `support` Django apps.

### 3.4 Load Seed Data

```bash
python manage.py loaddata data.json
```

The `data.json` fixture seeds:
- **Users** — 5 test accounts (admin + 4 customers)
- **Products** — CoolBreeze AC product catalog
- **Orders** — Sample orders across different statuses
- **RefundRequests** — Historical refund records
- **Conversations/Messages/AgentLogs** — Sample chat history

---

## 4. Django Installed Apps

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'orders',   # Custom: Product, Order, RefundRequest
    'support',  # Custom: Conversation, Message, AgentLog
]
```

---

## 5. Tables Overview

### Orders App (`orders`)

| Table | Django Model | Description |
|-------|-------------|-------------|
| `orders_product` | `Product` | AC product catalog |
| `orders_order` | `Order` | Customer orders with status tracking |
| `orders_refundrequest` | `RefundRequest` | Refund requests linked to orders |

### Support App (`support`)

| Table | Django Model | Description |
|-------|-------------|-------------|
| `support_conversation` | `Conversation` | Chat sessions (user + order) |
| `support_message` | `Message` | Individual chat messages |
| `support_agentlog` | `AgentLog` | Agent activity log (tool calls, decisions) |

### Built-in Django Tables

| Table | Purpose |
|-------|---------|
| `auth_user` | User accounts and authentication |
| `django_session` | Session storage |
| `django_migrations` | Migration history |
| `django_admin_log` | Admin panel change log |

---

## 6. Connection Settings

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Engine** | `django.db.backends.mysql` | MySQL backend |
| **Driver** | PyMySQL | Installed via `requirements.txt` |
| **Charset** | `utf8mb4` | Full Unicode support (emojis) |
| **Host** | `localhost` (dev) / Railway (prod) | Configured via `.env` |

---

## 7. Entity Relationship Diagram (ERD)

```
┌─────────────────┐       ┌──────────────────────┐
│    auth_user     │       │    orders_product     │
│─────────────────│       │──────────────────────│
│ id (PK)         │       │ id (PK)              │
│ username        │       │ name                 │
│ password        │       │ description          │
│ email           │       │ price                │
│ is_staff        │       │ category             │
│ first_name      │       │ in_stock             │
└───────┬─────────┘       └──────────┬───────────┘
        │                            │
        │ 1:N                        │ 1:N
        ▼                            ▼
┌─────────────────┐       ┌──────────────────────┐
│   orders_order   │       │ support_conversation │
│─────────────────│       │──────────────────────│
│ id (PK)         │◄──────│ order_id (FK)        │
│ user_id (FK)    │       │ user_id (FK)         │
│ product_id (FK) │       │ id (PK)              │
│ product_name    │       │ created_at           │
│ amount          │       └──────────┬───────────┘
│ status          │                  │
│ carrier         │                  │ 1:N
│ tracking_number │       ┌──────────┴───────────┐
│ delivery        │       │                      │
│ created_at      │       ▼                      ▼
│ updated_at      │  ┌──────────────┐  ┌──────────────────┐
└───────┬─────────┘  │support_message│  │ support_agentlog │
        │             │──────────────│  │──────────────────│
        │ 1:N         │ id (PK)      │  │ id (PK)          │
        ▼             │ conversation │  │ conversation (FK)│
┌──────────────────┐  │   _id (FK)   │  │ event_type       │
│orders_refundreq  │  │ role         │  │ message          │
│──────────────────│  │ content      │  │ created_at       │
│ id (PK)          │  │ created_at   │  └──────────────────┘
│ order_id (FK)    │  └──────────────┘
│ user_id (FK)     │
│ reason           │
│ status           │
│ created_at       │
└──────────────────┘
```

---

## 8. ChromaDB (Vector Database)

In addition to MySQL, the project uses **ChromaDB** as a vector store for the RAG knowledge base:

| Property | Value |
|----------|-------|
| **Location** | `chroma_db/` (local persistent storage) |
| **Purpose** | Store document embeddings for semantic search |
| **Documents** | PDFs in `support/documents/` (refund policy, warranty, FAQs) |
| **Ingestion** | `support/rag.py` → `load_documents()` |

```python
# Load/reload documents into ChromaDB
python manage.py shell
>>> from support.rag import load_documents
>>> load_documents()
```

---

## 9. Migration Files

```
orders/migrations/
├── 0001_initial.py          # Product, Order models
├── 0002_rename_...py        # Field renames / adjustments

support/migrations/
├── 0001_initial.py          # Conversation, Message, AgentLog
├── 0002_alter_message_role.py
```
