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
Each task includes title, description, status, priority, and tags. The service is designed with clean layering (`routes -> crud -> models`) so it is easy to maintain and extend.

## Features Implemented
- [x] Health check endpoint (`GET /health`)
- [x] Create task (`POST /tasks`)
- [x] List tasks (`GET /tasks`)
- [x] Get task by ID (`GET /tasks/{task_id}`)
- [x] Update task (`PUT /tasks/{task_id}`)
- [x] Delete task (`DELETE /tasks/{task_id}`)
- [x] MySQL persistence with SQLAlchemy ORM
- [x] Database schema migration with Alembic
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
- **Response:** Array of task objects (newest first by `id desc`)

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

### 6) Delete Task
- **Endpoint:** `DELETE /tasks/{task_id}`
- **Response:** `204 No Content`

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

## Design Trade-offs
- Using synchronous SQLAlchemy sessions keeps implementation simple, but may provide lower throughput than async stack under high concurrency.
- Storing `tags` as JSON is flexible, but advanced querying/filtering on tags is less efficient than a normalized many-to-many schema.
- Single service architecture is easier to ship quickly, but large-scale growth may require decomposition and more infrastructure.

## Challenges & Solutions
- **Challenge:** Keeping API enum values aligned between validation and persistence.  
  **Solution:** Defined status/priority consistently in Pydantic schemas and SQLAlchemy enums.
- **Challenge:** Managing schema creation safely.  
  **Solution:** Added Alembic migration (`create_tasks_table`) to version database changes.
- **Challenge:** Avoiding repeated DB session boilerplate.  
  **Solution:** Implemented dependency-injected `get_db()` session lifecycle in FastAPI.

## Known Limitations
- No authentication/authorization yet (all task endpoints are public).
- No pagination/filtering/search on task list endpoint.
- No automated test suite currently included.
- No CI/CD pipeline or containerization config in this repository.
- Error handling is basic and does not yet include standardized error codes.

## Future Improvements
- Add JWT-based authentication and user-level task ownership.
- Add pagination, filtering (status/priority), keyword search, and sorting.
- Add comprehensive unit/integration tests and API contract tests.
- Add Docker and docker-compose for one-command local startup.
- Add CI pipeline (lint, test, migration check).
- Add observability (structured logs, metrics, tracing).

## Time Spent (up to now)
Approximately 2 hours
