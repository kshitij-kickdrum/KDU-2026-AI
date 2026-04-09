# FastAPI Production Template — Design Document

## 1. Overview

A reusable FastAPI boilerplate that any developer can clone and extend. The goal is to have authentication, database, security, logging, and testing already wired up so new projects don't start from scratch.

**Out of scope:** Business logic, feature-specific endpoints, frontend.

---

## 2. Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Framework | FastAPI | Async support, auto docs, Pydantic built-in |
| Database | PostgreSQL | Production standard, async support |
| ORM | SQLAlchemy (async) | Flexible, widely used |
| Migrations | Alembic | Standard for SQLAlchemy |
| Auth | JWT (python-jose) | Stateless, simple to extend |
| Password Hashing | bcrypt (passlib) | Industry standard |
| Validation | Pydantic v2 | Built into FastAPI |
| Config | pydantic-settings | Reads from .env, type-safe |
| Testing | pytest + httpx | Async test support |
| Logging | structlog (JSON) | Structured, parseable logs |

---

## 3. Project Structure

Domain-based structure — all files related to a feature live together. Adding a new domain means adding one folder, not touching multiple directories.

```
app/
├── auth/
│   ├── router.py            # register, login routes
│   ├── schemas.py           # RegisterRequest, LoginRequest, TokenResponse
│   ├── service.py           # auth business logic (hash password, create token)
│   ├── dependencies.py      # get_current_user, require_admin
│   └── exceptions.py        # UserAlreadyExists, InvalidCredentials
├── users/
│   ├── router.py            # GET /users/me
│   ├── schemas.py           # UserResponse (no password_hash)
│   ├── models.py            # User SQLAlchemy model
│   ├── service.py           # user DB operations
│   └── exceptions.py        # UserNotFound
├── admin/
│   ├── router.py            # GET /admin/users
│   └── schemas.py           # AdminUserListResponse
├── core/
│   ├── config.py            # env-based settings
│   ├── security.py          # JWT encode/decode, password hashing
│   ├── logging.py           # logger setup
│   └── exceptions.py        # base app exception class
├── db/
│   ├── base.py              # base model (id, created_at, updated_at)
│   └── session.py           # async engine + session factory
└── main.py                  # app init, router registration, CORS, lifespan
tests/
├── conftest.py              # test DB setup, fixtures, test client
├── auth/
│   └── test_auth.py
├── users/
│   └── test_users.py
└── admin/
    └── test_admin.py
.env.example
alembic/
```

---

## 4. Database

### User Model

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| email | String | Unique, indexed |
| password_hash | String | bcrypt hash, never plain text |
| full_name | String | |
| role | Enum | `user` or `admin` |
| created_at | DateTime | Auto-set on insert |
| updated_at | DateTime | Auto-updated on change |

### Base Model

All models inherit from a `Base` that provides `id`, `created_at`, and `updated_at` automatically.

### Sessions

Async SQLAlchemy session injected per request via FastAPI dependency. Connection pooling configured via `pool_size` and `max_overflow` settings.

---

## 5. API Endpoints

| Method | Path | Description | Auth | Role |
|---|---|---|---|---|
| POST | `/api/v1/auth/register` | Create new user account | No | — |
| POST | `/api/v1/auth/login` | Login, returns JWT | No | — |
| GET | `/api/v1/users/me` | Get own profile | Yes | Any |
| GET | `/api/v1/admin/users` | List all users | Yes | Admin |
| GET | `/api/v1/health` | Health check | No | — |

### Request / Response Examples

**POST /api/v1/auth/register**
```json
// Request
{ "email": "user@example.com", "password": "Pass@1234", "full_name": "John Doe" }

// Response 201
{ "id": "uuid", "email": "user@example.com", "full_name": "John Doe", "role": "user" }
```

**POST /api/v1/auth/login**
```json
// Request
{ "email": "user@example.com", "password": "Pass@1234" }

// Response 200
{ "access_token": "<jwt>", "token_type": "bearer" }
```

**GET /api/v1/users/me** — requires `Authorization: Bearer <token>`
```json
// Response 200
{ "id": "uuid", "email": "user@example.com", "full_name": "John Doe", "role": "user" }
```

**GET /api/v1/admin/users** — requires admin role, supports pagination
```
Query params: ?limit=20&offset=0
```
```json
// Response 200
{
  "total": 100,
  "limit": 20,
  "offset": 0,
  "items": [{ "id": "uuid", "email": "user@example.com", "role": "user" }]
}
```

### Standard Error Response

Every error across all endpoints returns this shape:
```json
{ "code": "EMAIL_ALREADY_EXISTS", "message": "A user with this email already exists." }
```

---

## 6. Authentication & Authorization

- JWT signed with `HS256` using `SECRET_KEY` from env
- Access token expires in 30 minutes; no refresh tokens in v1
- Token payload contains: `sub` (user id), `role`, `exp`, `iat`
- Token decoded and user fetched on every protected request via a `get_current_user` dependency

**Dependency chain:**
```
get_db_session → get_current_user → require_admin
```
- `get_db_session` — injects async DB session per request
- `get_current_user` — decodes JWT, fetches user from DB, raises `401` if invalid
- `require_admin` — checks `current_user.role == "admin"`, raises `403` if not

**Register flow:** validate input → check email unique → hash password → insert user

**Login flow:** fetch user by email → verify password hash → return JWT

**Custom exceptions:**

| Exception | Raised when | HTTP |
|---|---|---|
| `UserAlreadyExists` | Email taken on register | 409 |
| `InvalidCredentials` | Wrong email or password | 401 |
| `UserNotFound` | User ID not in DB | 404 |
| `ForbiddenAction` | Insufficient role | 403 |

All domain exceptions inherit from a base `AppException` in `core/exceptions.py` and are caught by the global handler in `main.py`.

---

## 7. Security

- Passwords hashed with bcrypt, never logged or returned in responses
- Password rules: min 8 chars, 1 uppercase, 1 digit, 1 special character (enforced via Pydantic validator)
- Email format validated by Pydantic
- All secrets (DB URL, secret key) read from `.env`, never hardcoded
- CORS configured explicitly — wildcard `*` only in development

---

## 8. Error Handling

Global exception handlers registered in `main.py`:

| Scenario | HTTP Status |
|---|---|
| Request body / query / path validation error | 422 |
| Bad or expired token | 401 |
| Forbidden (wrong role) | 403 |
| Resource not found | 404 |
| Duplicate resource (email exists) | 409 |
| Unhandled server error | 500 |

All return the standard error shape from Section 5. Domain exceptions (`AppException` subclasses) are mapped to their status codes by the global handler — routes do not catch exceptions themselves.

---

## 9. Logging

- JSON structured logging via `structlog`
- Each log entry includes: `timestamp`, `level`, `message`, `request_id`, `method`, `path`, `status_code`, `latency_ms`
- `request_id` generated per request via middleware and passed through the entire request lifecycle
- Log level controlled by env var: `LOG_LEVEL=DEBUG` (dev) / `LOG_LEVEL=INFO` (prod)
- Never log passwords, tokens, or PII

---

## 10. Configuration

All config read from `.env` via `pydantic-settings`:

| Variable | Description |
|---|---|
| `DATABASE_URL` | Async PostgreSQL connection string |
| `SECRET_KEY` | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token TTL (default: 30) |
| `LOG_LEVEL` | DEBUG / INFO / WARNING |
| `CORS_ORIGINS` | Comma-separated allowed origins |
| `ENVIRONMENT` | development / production |

---

## 11. Testing

- Separate test database, never touches the main DB
- Routes use dependency overrides to inject a test DB session — no patching or mocking of internals
- DB is cleaned up between tests via transaction rollback or table truncation
- `conftest.py` provides fixtures: async test client, test DB session, pre-seeded user and admin

**What to test (priority order):**

| Module | Scenarios |
|---|---|
| Auth | Register success, duplicate email → 409, login success, wrong password → 401 |
| Protected routes | Valid token → 200, missing token → 401, expired token → 401 |
| RBAC | User on admin route → 403, admin on admin route → 200 |
| Validation | Bad email → 422, weak password → 422 |
| Error responses | All errors return standard `{code, message}` shape |

Target: 70%+ coverage. Priority is correctness of auth flows and permission boundaries over raw coverage number.

---

## 12. Lifespan & Startup

App lifespan is managed via FastAPI's `lifespan` context in `main.py`:

- **Startup:** initialise logger, verify DB connection
- **Shutdown:** close DB connection pool

This replaces deprecated `@app.on_event("startup")` handlers.

---

## 13. Rules & Conventions

These rules apply across the entire codebase. Every contributor and AI tool working on this project must follow them.

### Structure
- One domain = one folder. Never spread a domain's files across multiple directories.
- `core/` is for shared infrastructure only — not for business logic.
- `main.py` only wires things together — no business logic, no DB calls.

### Schemas
- Pydantic schemas are the only types that cross the API boundary — never return a SQLAlchemy model from a route.
- Every route must declare an explicit `response_model`.
- `password_hash` must never appear in any response schema.
- Mapping from ORM object to response schema happens at the route level, not inside the service.

### Services
- Services raise domain exceptions — never `HTTPException`.
- Services accept `db: AsyncSession` as a parameter — never import a global session.
- Services may return ORM objects internally; the route decides the response schema.

### Exceptions
- All custom exceptions inherit from `AppException` in `core/exceptions.py`.
- Routes do not catch exceptions — the global handler in `main.py` maps them to HTTP responses.
- Never raise a bare `Exception` or `HTTPException` from a service.

### Security
- Never hardcode secrets, URLs, or credentials — all come from `.env` via `core/config.py`.
- Never log or return `password_hash`, raw passwords, or JWT tokens.
- Always hash passwords with bcrypt before storing.

### Logging
- Use `structlog` logger only — never use `print` or the standard `logging` module directly.
- Never log passwords, tokens, or PII.

---

## 14. How to Extend

To add a new domain (e.g., `posts`):
1. Create `app/posts/` with `router.py`, `schemas.py`, `models.py`, `service.py`, `exceptions.py`
2. Register router in `main.py`
3. Create Alembic migration

