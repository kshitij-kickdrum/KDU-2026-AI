# Agent Context — FastAPI Production Template

This file gives AI coding assistants the context needed to generate code that fits this project's conventions.

---

## What this project is

A reusable FastAPI boilerplate with authentication, PostgreSQL, structured logging, and testing pre-wired. It is not a business application — it is a starting point for one.

---

## Tech Stack

- **FastAPI** with async throughout
- **PostgreSQL** via async SQLAlchemy
- **Alembic** for migrations
- **Pydantic v2** for request/response schemas (DTOs)
- **pydantic-settings** for env-based config
- **passlib + bcrypt** for password hashing
- **python-jose** for JWT
- **structlog** for JSON logging
- **pytest + httpx** for async testing

---

## Folder Structure

Domain-based. Every domain is self-contained.

```
app/
├── auth/           # register, login, JWT, dependencies, auth exceptions
├── users/          # user model, /users/me route, user schemas
├── admin/          # admin-only routes, admin schemas
├── core/           # config, security, logging, base exception
├── db/             # base model, async session factory
└── main.py         # app init, router registration, CORS, lifespan
tests/
├── auth/
├── users/
├── admin/
└── conftest.py
```

When adding a new domain, create a new folder with: `router.py`, `schemas.py`, `models.py`, `service.py`, `exceptions.py`.

---

## Key Conventions

### Schemas (DTOs)
- Pydantic schemas in `schemas.py` are the only types that cross the API boundary
- Never return a SQLAlchemy model directly from a route
- Use `model_config = ConfigDict(from_attributes=True)` on response schemas
- Mapping from ORM to schema happens at the **route level**, not inside the service
- Example names: `RegisterRequest`, `LoginRequest`, `TokenResponse`, `UserResponse`

### Services
- Contain business logic and DB operations
- Accept a `db: AsyncSession` as a parameter
- May return ORM objects internally — the route decides what schema to map to
- Raise domain exceptions, never HTTP exceptions

### Exceptions
- All custom exceptions inherit from `AppException` in `core/exceptions.py`
- Domain exceptions live in `<domain>/exceptions.py`
- Routes do not catch exceptions — the global handler in `main.py` maps them to HTTP responses
- Exception → HTTP status mapping:
  - `UserAlreadyExists` → 409
  - `InvalidCredentials` → 401
  - `UserNotFound` → 404
  - `ForbiddenAction` → 403
  - Pydantic validation error → 422
  - Unhandled → 500

### Dependencies
Dependency chain (defined in `auth/dependencies.py`):
```
get_db_session → get_current_user → require_admin
```
- `get_db_session`: injects `AsyncSession` per request
- `get_current_user`: decodes JWT, returns User ORM object, raises 401 if invalid
- `require_admin`: checks `user.role == "admin"`, raises 403 if not

### JWT
- Signed with `HS256` using `SECRET_KEY` from env
- Payload fields: `sub` (user id), `role`, `exp`, `iat`
- Expiry: 30 minutes
- No refresh tokens in v1

### Password Hashing
- Always hash with bcrypt via passlib
- Never store or log plain text passwords
- Never return `password_hash` in any response schema

### Error Response Shape
All errors return:
```json
{ "code": "SNAKE_CASE_ERROR_CODE", "message": "Human readable message." }
```

### Logging
- Use `structlog` logger, never `print`
- Every log entry includes: `timestamp`, `level`, `message`, `request_id`, `method`, `path`, `status_code`, `latency_ms`
- Never log passwords, tokens, or any PII

### Config
- All settings come from `.env` via `core/config.py` (pydantic-settings)
- Never hardcode secrets, URLs, or environment-specific values

---

## Database

### User Model (in `users/models.py`)
Fields: `id` (UUID), `email`, `password_hash`, `full_name`, `role` (enum: user/admin), `created_at`, `updated_at`

### Base Model (in `db/base.py`)
All models inherit from `Base` which provides `id`, `created_at`, `updated_at` automatically. Timestamps are timezone-aware UTC.

---

## API Endpoints

| Method | Path | Auth | Role |
|---|---|---|---|
| POST | `/api/v1/auth/register` | No | — |
| POST | `/api/v1/auth/login` | No | — |
| GET | `/api/v1/users/me` | Yes | Any |
| GET | `/api/v1/admin/users?limit=20&offset=0` | Yes | Admin |
| GET | `/api/v1/health` | No | — |

---

## Testing

- Use `tests/conftest.py` fixtures: async test client, test DB session, seeded user and admin
- Routes use dependency overrides to inject test DB session — do not mock ORM internals
- Each test should be isolated — no shared state between tests
- Priority test scenarios: auth flows, permission boundaries, validation failures, error response shape
