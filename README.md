# 🎫 Ticket Management System API

A production-ready REST API built with **FastAPI** featuring JWT authentication, role-based access control, and a custom **RAG-based AI assistant**.

---

## 📋 Features

| Feature | Details |
|---|---|
| **Authentication** | JWT Bearer tokens via register/login |
| **Roles** | `admin` (full access) / `user` (own tickets only) |
| **Ticket CRUD** | Create, read, update, delete with ownership checks |
| **Filters** | Status, priority, category, created_by |
| **Search** | Full-text search in title + description |
| **Sorting** | By `created_at` or `priority` (asc/desc) |
| **Pagination** | Page + limit with total count |
| **AI Assistant** | Custom RAG: query parser → DB retrieval → response |
| **Database** | SQLite (default) / PostgreSQL compatible |
| **Security** | bcrypt password hashing, JWT expiry |

---

## 🏗️ Project Structure

```
ticket_system/
├── app/
│   ├── main.py               # FastAPI app, routers, middleware
│   ├── database.py           # SQLAlchemy engine + session
│   ├── models/
│   │   ├── user.py           # User ORM model
│   │   └── ticket.py         # Ticket ORM model
│   ├── schemas/
│   │   ├── user.py           # Pydantic request/response schemas
│   │   ├── ticket.py         # Ticket schemas + pagination
│   │   └── ai.py             # AI query schemas
│   ├── routes/
│   │   ├── auth.py           # POST /auth/register, /auth/login
│   │   ├── tickets.py        # Ticket CRUD endpoints
│   │   ├── admin.py          # Admin-only endpoints
│   │   └── ai.py             # POST /ai/query
│   ├── services/
│   │   ├── user_service.py   # Register, login business logic
│   │   ├── ticket_service.py # Ticket CRUD + RBAC logic
│   │   └── admin_service.py  # Admin stats + listing
│   ├── auth/
│   │   └── jwt_handler.py    # JWT create/decode, password hashing
│   ├── core/
│   │   ├── config.py         # Settings from .env
│   │   ├── exceptions.py     # Custom HTTP exceptions
│   │   └── logging_config.py # Structured logging setup
│   └── ai/
│       ├── query_parser.py   # NLP intent detection + entity extraction
│       ├── rag_engine.py     # DB retrieval based on parsed query
│       └── response_generator.py # Format response (template or OpenAI)
├── tests/
│   └── test_main.py          # Pytest unit + integration tests
├── seed.py                   # Database seeder with sample data
├── requirements.txt
├── .env.example
├── Dockerfile
├── postman_collection.json
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & Setup
git clone https://github.com/raunak2910/ticket-management-system.git
cd ticket-management-system/ticket_system
**2. Create Virtual Environment**
python -m venv venv
**3.Install Dependencies**
pip install -r requirements.txt

### 4. Seed Sample Data (Optional)

```bash
python seed.py
```

This creates:
- **Admin**: `admin@example.com` / `admin123`
- **Alice**: `alice@example.com` / `alice123`
- **Bob**: `bob@example.com` / `bob123`
- **Carol**: `carol@example.com` / `carol123`

### 5. Run the Server

```bash
uvicorn app.main:app --reload
```

The API is now running at **http://localhost:8000**

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🔐 Authentication

All protected routes require a Bearer token in the Authorization header:

```http
Authorization: Bearer <your_jwt_token>
```

**Get a token:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "alice123"}'
```

---

## 📡 API Reference

### Auth Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Register new user |
| `POST` | `/auth/login` | Login, receive JWT token |

**Register:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepass123",
  "role": "user"
}
```

**Login Response:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user": { "id": 1, "name": "John Doe", "email": "...", "role": "user" }
}
```

---

### Ticket Endpoints (Authenticated)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/tickets/` | Create a ticket |
| `GET` | `/tickets/` | List tickets (with filters) |
| `GET` | `/tickets/{id}` | Get ticket by ID |
| `PUT` | `/tickets/{id}` | Update ticket |
| `PATCH` | `/tickets/{id}/status` | Update status only |
| `DELETE` | `/tickets/{id}` | Delete ticket |

**Query Parameters for GET `/tickets/`:**

| Param | Values | Description |
|-------|--------|-------------|
| `status` | `open`, `in_progress`, `closed` | Filter by status |
| `priority` | `low`, `medium`, `high` | Filter by priority |
| `category` | any string | Filter by category |
| `search` | any string | Search title & description |
| `sort_by` | `created_at`, `priority` | Sort field |
| `sort_order` | `asc`, `desc` | Sort direction |
| `page` | integer ≥ 1 | Page number |
| `limit` | 1–100 | Results per page |

---

### Admin Endpoints (Admin role required)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin/tickets` | All tickets + full filters |
| `GET` | `/admin/stats` | System-wide statistics |

**Stats Response:**
```json
{
  "total_tickets": 42,
  "open_tickets": 15,
  "in_progress_tickets": 12,
  "closed_tickets": 15,
  "high_priority_tickets": 8,
  "medium_priority_tickets": 20,
  "low_priority_tickets": 14,
  "total_users": 5
}
```

---

### AI Assistant Endpoint

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/ai/query` | Natural language ticket query |

**Request:**
```json
{ "query": "Show all high priority open tickets" }
```

**Response:**
```json
{
  "query": "Show all high priority open tickets",
  "answer": "🎫 Found 3 ticket(s) [priority=high | status=open]\n...",
  "data": [...],
  "query_type": "list_tickets"
}
```

**Supported Query Examples:**
```
"What is the status of ticket 12?"
"Show all high priority open tickets"
"Summarize ticket 5"
"Which tickets were created by Alice?"
"How many tickets are open?"
"List all critical in-progress tickets"
"Show tickets created by user id 3"
```

---

## 🤖 How the RAG AI Works

```
User Query
    │
    ▼
┌─────────────────┐
│  Query Parser   │  ← Rule-based NLP: detect intent + extract entities
│  (query_parser) │    (ticket ID, status, priority, username)
└────────┬────────┘
         │ ParsedQuery
         ▼
┌─────────────────┐
│   RAG Engine    │  ← Retrieve from SQLite/PostgreSQL based on intent
│  (rag_engine)   │    NO vector DB, NO embeddings — pure SQL retrieval
└────────┬────────┘
         │ Context Dict
         ▼
┌──────────────────────┐
│  Response Generator  │  ← Template-based formatting
│ (response_generator) │    OR OpenAI GPT-3.5 (if API key set)
└──────────────────────┘
         │
         ▼
   Natural Language Answer + Structured Data
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v

# With coverage
pip install pytest-cov
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## 🗄️ Database

### Switch to PostgreSQL

1. Install driver: `pip install psycopg2-binary`
2. Update `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/ticketsdb
```

### Schema Overview

**users** table:
- `id`, `name`, `email` (unique), `password` (bcrypt), `role`, `created_at`

**tickets** table:
- `id`, `title`, `description`, `status`, `priority`, `category`
- `created_by` → FK to users
- `assigned_to` → FK to users (nullable)
- `created_at`, `updated_at`

---

## 🔧 Configuration

All settings via `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./tickets.db` | DB connection string |
| `SECRET_KEY` | (change this!) | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token TTL (24h) |
| `OPENAI_API_KEY` | `` (empty) | Optional: enables GPT responses |
| `DEBUG` | `False` | Enable debug mode |

---

## 📦 Tech Stack

- **FastAPI** — Modern async web framework
- **SQLAlchemy** — ORM with SQLite/PostgreSQL support
- **Pydantic v2** — Data validation and serialization
- **python-jose** — JWT creation and verification
- **passlib + bcrypt** — Secure password hashing
- **httpx** — Async HTTP client (optional OpenAI calls)
- **pytest** — Unit and integration testing
