# Intelligent Task Management System

## Role Track
Backend

## Tech Stack
- Language: Python 3.13
- Framework: FastAPI, Pydantic
- Database: MySQL 8.0
- Cache: Redis (via `redis` client in `app/core/cache.py`)
- Other tools: SQLAlchemy, Alembic, Uvicorn, PyMySQL

## Project Description
This project is a lightweight task management backend API that supports creating, reading, updating, and deleting tasks.  
Each task includes title, description, status, priority, and tags. Tasks may **depend on other tasks** (stored in `task_dependencies`): a task cannot be marked `completed` until every **direct** prerequisite task is `completed`. **Hot reads** (`GET /tasks/{task_id}` and `GET /tasks/{task_id}/dependencies`) are backed by **Redis** with TTL-based invalidation on writes. The service is designed with clean layering (`routes -> crud -> models`) so it is easy to maintain and extend.

## Architecture & scaling

Design assumptions for **100k+ tasks**, component boundaries, indexing, caching, dependency-graph costs, and a prioritized roadmap are documented in **[docs/architecture.md](docs/architecture.md)**.

## Features Implemented
- [x] Health check endpoint (`GET /health`)
- [x] Create task (`POST /tasks`)
- [x] List tasks (`GET /tasks`) with **filtering** (status, priority, tag), **sorting** (`created_at`, `priority`, `status`, `id`), and **pagination** (`page`, `page_size`, `total`, `total_pages`)
- [x] Database indexes for list queries (initial single-column indexes in `089627fac660_add_indexes_for_task_filtering`; composite index `idx_tasks_status_priority_created_at` and dependency-table indexes in `24077f4738ab_add_indexes_for_the_task_table_and_`)
- [x] Get task by ID (`GET /tasks/{task_id}`)
- [x] Update task (`PUT /tasks/{task_id}`)
- [x] Delete task (`DELETE /tasks/{task_id}`)
- [x] **Task dependencies:** add / list / remove dependency edges (`POST`, `GET`, `DELETE` under `/tasks/{task_id}/dependencies`)
- [x] **Completion rule:** `PUT /tasks/{task_id}` with `status: "completed"` is rejected if any direct dependency is not `completed`
- [x] **Cycle prevention:** adding a dependency that would create a directed cycle returns `400`
- [x] MySQL persistence with SQLAlchemy ORM
- [x] Database schema migration with Alembic (including `task_dependencies` in `52575d1e52dd_add_task_dependencies_table`)
- [x] Input validation for status/priority/title length
- [x] **Performance:** SQLAlchemy **connection pool** tuning (`pool_size`, `max_overflow`, `pool_recycle`, `pool_timeout`) in `app/core/db.py`
- [x] **Caching:** Redis keys `task:{id}` and `task_deps:{id}`; invalidated on task update/delete and on dependency add/remove
- [x] **Latency visibility:** HTTP middleware adds **`X-Process-Time`** response header and logs per-request duration in ms
- [x] **Load script:** `benchmark.py` (concurrent `GET /tasks/{id}` against a running server)
- [x] **System design:** architecture and scaling notes ([docs/architecture.md](docs/architecture.md))

## Setup Instructions
1. **Prerequisites**
   - Python 3.13 or newer
   - MySQL 8.0 running locally
   - **Redis** running locally (default `localhost:6379`) for cached read paths
   - `pip` and virtual environment support

2. **Installation steps**
   - Clone repository
   - Create virtual environment and install dependencies:
     - `python -m venv .venv`
     - Windows PowerShell: `.venv\Scripts\Activate.ps1`
     - `pip install fastapi uvicorn sqlalchemy alembic pymysql pydantic-settings redis requests`

3. **Configuration**
   - Create/update `.env` in project root:
     - `APP_NAME=Task Manager API`
     - `DATABASE_URL=mysql+pymysql://<username>:<password>@127.0.0.1:3306/task_manager?charset=utf8mb4`
     - `REDIS_URL=redis://localhost:6379/0` (defined for future use; `RedisCache` in `app/core/cache.py` currently uses `host=localhost`, `port=6379`)
     - `CACHE_ENABLED=true`, `CACHE_TTL=300` — present on `Settings`; CRUD calls `cache.set(...)` **without** a TTL argument today, so keys use the **`RedisCache.set` default (3600s)**. Pass `settings.CACHE_TTL` into `cache.set` from `get_task` / `get_task_dependencies` if you want 300s expiry.
   - Create database in MySQL (if not exists):
     - `CREATE DATABASE task_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`

4. **Running the application**
   - Run migrations:
     - `alembic upgrade head`
   - Start API server:
     - `uvicorn app.main:app --reload`
   - Open docs:
     - Swagger UI: `http://127.0.0.1:8000/docs`
     - ReDoc: `http://127.0.0.1:8000/redoc`

5. **Optional: quick load test**
   - Start the API, ensure at least one task exists (e.g. id `1`), install `requests`, then run: `python benchmark.py`
   - Inspect response header **`X-Process-Time`** on any request to see server-side processing time in milliseconds.

## API Documentation

### Base URL
`http://127.0.0.1:8000`

### 1) Health Check
- **Endpoint:** `GET /health`
- **Response headers:** Every response includes **`X-Process-Time`** (e.g. `12.34ms`) from the timing middleware in `app/main.py`.
- **Response:**
```json
{
  "status": "ok"
}
```

### 2) Create Task
- **Endpoint:** `POST /tasks`
- **Request Body Example:**
```json
{
  "title": "Finish backend README",
  "description": "Write complete setup and API docs",
  "status": "pending",
  "priority": "high",
  "tags": ["docs", "backend"]
}
```
- **Response Example (201):**
```json
{
  "id": 1,
  "title": "Finish backend README",
  "description": "Write complete setup and API docs",
  "status": "pending",
  "priority": "high",
  "tags": ["docs", "backend"],
  "created_at": "2026-04-18T18:25:31",
  "updated_at": "2026-04-18T18:25:31"
}
```

### 3) List Tasks
- **Endpoint:** `GET /tasks`
- **Response model:** `TaskListOut` — a paginated envelope (not a bare array).

**Query parameters**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `status` | No | — | Filter by task status: `pending`, `in_progress`, or `completed` |
| `priority` | No | — | Filter by priority: `low`, `medium`, or `high` |
| `tag` | No | — | Filter tasks whose `tags` JSON array **contains** this tag (MySQL `JSON_CONTAINS`) |
| `sort_by` | No | `created_at` | Sort field: `created_at`, `priority`, `status`, or `id` |
| `sort_order` | No | `desc` | Sort direction: `asc` or `desc` |
| `page` | No | `1` | Page number (≥ 1) |
| `page_size` | No | `20` | Page size (1–100) |

**Example request**

`GET /tasks?status=pending&priority=high&tag=docs&sort_by=created_at&sort_order=desc&page=1&page_size=20`

**Response example (200)**

```json
{
  "items": [
    {
      "id": 1,
      "title": "Finish backend README",
      "description": "Write complete setup and API docs",
      "status": "pending",
      "priority": "high",
      "tags": ["docs", "backend"],
      "created_at": "2026-04-18T18:25:31",
      "updated_at": "2026-04-18T18:25:31"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### 4) Get Task by ID
- **Endpoint:** `GET /tasks/{task_id}`
- **Caching:** Responses are served from **Redis** key `task:{task_id}` when present (JSON serialized `TaskOut`). Cache is cleared on `PUT` / `DELETE` for that task.
- **Success Response:** Task object
- **Error Response (404):**
```json
{
  "detail": "Task not found"
}
```

### 5) Update Task
- **Endpoint:** `PUT /tasks/{task_id}`
- **Request Body Example (partial updates allowed):**
```json
{
  "status": "in_progress",
  "priority": "medium"
}
```
- **Response:** Updated task object
- **Dependency rule:** If the payload sets `status` to `completed`, every **direct** dependency (see §7–8) whose `depends_on_task_id` points at another task must have that task’s `status` equal to `completed`. Otherwise the update fails (dependency validation raises an error before commit).

### 6) Delete Task
- **Endpoint:** `DELETE /tasks/{task_id}`
- **Response:** `204 No Content`
- **Note:** Dependency rows where this task is the **dependent** (`task_id`) are removed automatically (`ON DELETE CASCADE`). A task that is still referenced as `depends_on_task_id` by others may be **blocked from deletion** by the database (`ON DELETE RESTRICT` on that foreign key).

### 7) Add Task Dependency
- **Endpoint:** `POST /tasks/{task_id}/dependencies`
- **Semantics:** Task `task_id` **depends on** task `depends_on_task_id` — the prerequisite must be completed before `task_id` can be completed.
- **Request body:**
```json
{
  "depends_on_task_id": 2
}
```
- **Response (201):** `DependencyOut` — `id`, `task_id`, `depends_on_task_id`, and `depends_on_task_title` (title of the prerequisite task).
- **Errors (400):** Missing tasks, self-dependency, duplicate edge, or **circular dependency** (detected with a BFS in CRUD before insert). Example body:
```json
{
  "detail": "不能创建循环依赖"
}
```

### 8) List Task Dependencies (direct)
- **Endpoint:** `GET /tasks/{task_id}/dependencies`
- **Caching:** Results may be read from **Redis** key `task_deps:{task_id}`; invalidated when dependencies are added/removed or the task is updated/deleted.
- **Response (200):** Array of `DependencyOut` — **immediate** prerequisites only (one hop). To walk a full prerequisite chain, a client can repeat requests or extend the API with a dedicated transitive/tree endpoint.

### 9) Remove Task Dependency
- **Endpoint:** `DELETE /tasks/{task_id}/dependencies/{depends_on_task_id}`
- **Response:** `204 No Content`
- **Errors (404):** Dependency edge not found (message in `detail`).

### Field Constraints
- `title`: required, `1-200` chars
- `status`: `pending | in_progress | completed`
- `priority`: `low | medium | high`
- `tags`: optional string array

## Design Decisions
- Chose **FastAPI** for fast development speed, automatic OpenAPI docs, and strong request validation.
- Chose **SQLAlchemy ORM + MySQL** for structured relational data, clear schema modeling, and maintainable database access.
- Chose **Alembic** to keep schema evolution explicit and reproducible across environments.
- Used layered structure (`api/routes`, `crud`, `models`, `schemas`) to separate concerns:
  - Route handlers keep HTTP logic simple.
  - CRUD layer centralizes DB operations.
  - Schemas enforce API contracts.
- **List endpoint:** filtering and sorting are implemented in the CRUD layer; `sort_by` is restricted to an allow-list mapped to real columns to avoid invalid sort keys. Pagination returns both `items` and `total` so clients can build UI without guessing. The list route uses the query parameter `status` (filter); FastAPI’s HTTP status helpers are imported as `http_status` in code so the name `status` does not clash with `fastapi.status`.
- **Performance:** composite index `idx_tasks_status_priority_created_at` on `tasks` plus indexes on `task_dependencies.task_id` and `task_dependencies.depends_on_task_id` (see migration `24077f4738ab`) support filtered list queries and dependency lookups. SQLAlchemy engine uses an explicit connection pool to reduce handshake overhead under concurrency.
- **Caching:** Redis stores denormalized JSON for single-task and per-task dependency list reads; write paths delete affected keys so list endpoints do not return stale graphs.
- **Dependencies:** `task_dependencies` stores directed edges with DB-level uniqueness and a check constraint preventing self-edges; cycle detection is enforced in application code on insert.

## Design Trade-offs
- Using synchronous SQLAlchemy sessions keeps implementation simple, but may provide lower throughput than async stack under high concurrency.
- Storing `tags` as JSON is flexible, but advanced querying/filtering on tags is less efficient than a normalized many-to-many schema.
- An intermediate migration (`52575d1e52dd`) removed single-column list indexes on `tasks`; a later revision (`24077f4738ab`) adds a **composite** list index and dependency-table indexes—different shape than the original three single-column indexes, tuned for common filter+sort patterns.
- Single service architecture is easier to ship quickly, but large-scale growth may require decomposition and more infrastructure.

## Challenges & Solutions
- **Challenge:** Keeping API enum values aligned between validation and persistence.  
  **Solution:** Defined status/priority consistently in Pydantic schemas and SQLAlchemy enums.
- **Challenge:** Managing schema creation safely.  
  **Solution:** Added Alembic migration (`create_tasks_table`) to version database changes.
- **Challenge:** Avoiding repeated DB session boilerplate.  
  **Solution:** Implemented dependency-injected `get_db()` session lifecycle in FastAPI.
- **Challenge:** Filtering by `tags` stored as MySQL JSON while keeping a single-table model.  
  **Solution:** Use `JSON_CONTAINS` via SQLAlchemy `func.json_contains` for optional `tag` filter; document that `tags` must be a JSON array of strings for the filter to match.
- **Challenge:** Preventing circular task dependencies while keeping the graph in relational tables.  
  **Solution:** Before inserting an edge, run a BFS from the proposed prerequisite toward tasks that depend on it; if the dependent task is reachable, reject the insert.
- **Challenge:** Keeping hot read paths fast without stale reads after updates.  
  **Solution:** Redis cache for `get_task` / `get_task_dependencies` with explicit key deletion after mutations that affect those views.

## Performance notes (< 100 ms goal)
- Treat **100 ms** as a **local / low-latency** target for **simple reads** (e.g. cached `GET /tasks/{id}`, `GET /health`) under small datasets; measure using **`X-Process-Time`**, `benchmark.py`, or an external tool (wrk, hey).
- **Writes** (`PUT` with dependency checks, `POST` dependencies with BFS) can exceed 100 ms as data or graph depth grows—document separate SLOs for read vs write if needed.
- **Redis must be reachable** for cached code paths; there is no in-process fallback if Redis is unavailable (startup or first cache call may error until Redis is up).

## Known Limitations
- `CACHE_ENABLED` / `REDIS_URL` in settings are not yet fully wired into `RedisCache` (client uses default host/port); tune `app/core/cache.py` to parse `REDIS_URL` for non-local deployments.
- No authentication/authorization yet (all task endpoints are public).
- No dedicated **transitive dependency tree** HTTP endpoint yet; `GET /tasks/{task_id}/dependencies` returns **direct** edges only.
- No full-text or keyword search on title/description yet (only status/priority/tag filters).
- No automated test suite currently included.
- No CI/CD pipeline or containerization config in this repository.
- Error handling is basic and does not yet include standardized error codes.

## Future Improvements
- Add JWT-based authentication and user-level task ownership.
- Wire `REDIS_URL` and `CACHE_ENABLED` end-to-end (lazy Redis connection, graceful degradation when cache is off).
- Add keyword / full-text search on title and description.
- Add comprehensive unit/integration tests and API contract tests.
- Add Docker and docker-compose for one-command local startup.
- Add CI pipeline (lint, test, migration check).
- Add observability (structured logs, metrics, tracing).

## Time Spent (up to now)
Approximately 4 hours
