# Intelligent Task Management System

## Role Track
Backend

## Tech Stack
- Language: Python 3.13
- Framework: FastAPI, Pydantic
- Database: MySQL 8.0
- Other tools: SQLAlchemy, Alembic, Uvicorn, PyMySQL

## Project Description
This project is a lightweight task management backend API that supports creating, reading, updating, and deleting tasks.  
Each task includes title, description, status, priority, and tags. Tasks may **depend on other tasks** (stored in `task_dependencies`): a task cannot be marked `completed` until every **direct** prerequisite task is `completed`. The service is designed with clean layering (`routes -> crud -> models`) so it is easy to maintain and extend.

## Features Implemented
- [x] Health check endpoint (`GET /health`)
- [x] Create task (`POST /tasks`)
- [x] List tasks (`GET /tasks`) with **filtering** (status, priority, tag), **sorting** (`created_at`, `priority`, `status`, `id`), and **pagination** (`page`, `page_size`, `total`, `total_pages`)
- [x] Database indexes for common list queries (`status`, `priority`, `created_at`) via Alembic migration `089627fac660_add_indexes_for_task_filtering`
- [x] Get task by ID (`GET /tasks/{task_id}`)
- [x] Update task (`PUT /tasks/{task_id}`)
- [x] Delete task (`DELETE /tasks/{task_id}`)
- [x] **Task dependencies:** add / list / remove dependency edges (`POST`, `GET`, `DELETE` under `/tasks/{task_id}/dependencies`)
- [x] **Completion rule:** `PUT /tasks/{task_id}` with `status: "completed"` is rejected if any direct dependency is not `completed`
- [x] **Cycle prevention:** adding a dependency that would create a directed cycle returns `400`
- [x] MySQL persistence with SQLAlchemy ORM
- [x] Database schema migration with Alembic (including `task_dependencies` in `52575d1e52dd_add_task_dependencies_table`)
- [x] Input validation for status/priority/title length

## Setup Instructions
1. **Prerequisites**
   - Python 3.13 or newer
   - MySQL 8.0 running locally
   - `pip` and virtual environment support

2. **Installation steps**
   - Clone repository
   - Create virtual environment and install dependencies:
     - `python -m venv .venv`
     - Windows PowerShell: `.venv\Scripts\Activate.ps1`
     - `pip install fastapi uvicorn sqlalchemy alembic pymysql pydantic-settings`

3. **Configuration**
   - Create/update `.env` in project root:
     - `APP_NAME=Task Manager API`
     - `DATABASE_URL=mysql+pymysql://<username>:<password>@127.0.0.1:3306/task_manager?charset=utf8mb4`
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

## API Documentation

### Base URL
`http://127.0.0.1:8000`

### 1) Health Check
- **Endpoint:** `GET /health`
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
- **Performance:** partial indexes on `status`, `priority`, and `created_at` support typical filtered/sorted list queries at scale.
- **Dependencies:** `task_dependencies` stores directed edges with DB-level uniqueness and a check constraint preventing self-edges; cycle detection is enforced in application code on insert.

## Design Trade-offs
- Using synchronous SQLAlchemy sessions keeps implementation simple, but may provide lower throughput than async stack under high concurrency.
- Storing `tags` as JSON is flexible, but advanced querying/filtering on tags is less efficient than a normalized many-to-many schema.
- The Alembic revision `52575d1e52dd_add_task_dependencies_table` **drops** the earlier `tasks` list indexes (`ix_tasks_status`, `ix_tasks_priority`, `ix_tasks_created_at`) as part of the autogenerated migration; if you still need those for large lists, consider re-adding them in a follow-up migration.
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

## Known Limitations
- No authentication/authorization yet (all task endpoints are public).
- No dedicated **transitive dependency tree** HTTP endpoint yet; `GET /tasks/{task_id}/dependencies` returns **direct** edges only.
- No full-text or keyword search on title/description yet (only status/priority/tag filters).
- No automated test suite currently included.
- No CI/CD pipeline or containerization config in this repository.
- Error handling is basic and does not yet include standardized error codes.

## Future Improvements
- Add JWT-based authentication and user-level task ownership.
- Add keyword / full-text search on title and description.
- Add comprehensive unit/integration tests and API contract tests.
- Add Docker and docker-compose for one-command local startup.
- Add CI pipeline (lint, test, migration check).
- Add observability (structured logs, metrics, tracing).

## Time Spent (up to now)
Approximately 3 hours
