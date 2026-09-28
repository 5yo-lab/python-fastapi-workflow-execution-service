# Workflow Execution Service

Three-component workflow system: Python REST API (state machine + persistence), Node.js worker (action simulation), React UI (control panel).

## Quick start

```bash
docker compose up --build
```

| Service       | URL                        |
| ------------- | -------------------------- |
| API + Swagger | http://localhost:8000/docs |
| Frontend      | http://localhost:3000      |
| pgAdmin       | http://localhost:5050      |

Smoke test (stack must be running):

```powershell
.\scripts\smoke-test.ps1
```

```bash
./scripts/smoke-test.sh
```

## Local dev (without Docker)

1. Start PostgreSQL and set `DATABASE_URL` (see `python-service/.env.example`).
2. `cd python-service && uv run alembic upgrade head && uv run uvicorn app.main:app --reload`
3. `cd node-worker && npm run worker`
4. `cd frontend && npm run dev`

## Architecture

The API owns the state machine. Manual transitions (`START_VALIDATION`, `START_PROCESSING`, `CANCEL`) go through `POST /workflows/{id}/transitions`. Automated transitions (`APPROVE`, `REJECT`, `COMPLETE`, `FAIL`) are applied only when the worker reports action results — not exposed on the public transitions endpoint.

The worker polls `GET /actions/pending`, claims each action, simulates VALIDATE/PROCESS, and posts results to `POST /actions/{id}/result`.

## API

| Method | Path                          | Purpose                  |
| ------ | ----------------------------- | ------------------------ |
| POST   | `/workflows`                  | Create workflow          |
| GET    | `/workflows`                  | List workflows           |
| GET    | `/workflows/{id}`             | Get workflow             |
| GET    | `/workflows/{id}/history`     | Transition history       |
| GET    | `/workflows/{id}/actions`     | Related actions          |
| POST   | `/workflows/{id}/transitions` | Manual transition        |
| GET    | `/actions/pending`            | Pending actions (worker) |
| POST   | `/actions/{id}/claim`         | Claim action (worker)    |
| POST   | `/actions/{id}/result`        | Report result (worker)   |

Example:

```bash
curl -X POST http://localhost:8000/workflows \
  -H "Content-Type: application/json" \
  -d '{"reference":"order-1","payload":{"customerId":"customer-1","amount":100}}'

curl -X POST http://localhost:8000/workflows/{id}/transitions \
  -H "Content-Type: application/json" \
  -d '{"action":"START_VALIDATION","expectedVersion":1}'
```

Action results use `{ "success": true, "result": {...} }` or `{ "success": false, "error": "..." }` (not the assignment's `status` field).

## Design decisions

- **PostgreSQL** — relational model fits workflows, history, and optimistic locking.
- **Optimistic locking** — `expectedVersion` on transitions; mismatch returns 409 `STALE_VERSION`.
- **Idempotency** — duplicate action results return the existing outcome without double transitions.
- **Retries** — failed actions retry up to 3 attempts before applying REJECT/FAIL.
- **Action claim** — worker must claim before submitting a result (prevents duplicate processing).

## Database (pgAdmin)

Login: `admin@local.dev` / `admin`

Register server (from inside Docker pgAdmin):

| Field    | Value      |
| -------- | ---------- |
| Host     | `postgres` |
| Port     | `5432`     |
| Database | `workflow` |
| Username | `workflow` |
| Password | `workflow` |

From host tools use `localhost:5432` instead of `postgres`.

## Tests

```bash
cd python-service
uv run pytest
```

Requires PostgreSQL at `DATABASE_URL` (default in `.env.example`).

## Limitations

- No authentication
- No action leasing (claim helps but two workers can still race on poll)
- Polling only (no WebSocket/SSE)
- PROCESS step randomly fails (~15%) by design

## Future improvements

- Structured JSON logging in the Python API
- Full correlation ID propagation (headers + logs across all services)
- Action lease / visibility timeout for multi-worker setups
- SSE or WebSocket for live UI updates
- Manual retry from failed states in the UI

## Time spent

~9 hours

## AI usage

Cursor was used as a coding assistant. AI helped with:

- React frontend scaffolding and API wiring
- pytest integration tests
- docker-compose smoke test scripts (`scripts/smoke-test.ps1`, `scripts/smoke-test.sh`)
- Alembic migration boilerplate (table/column definitions, enum autocompletion)

The state machine, service layer, worker polling flow, and Docker troubleshooting were built with AI assistance but reviewed and adjusted manually. All code was read and tested before submission.
