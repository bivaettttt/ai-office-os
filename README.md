# AI Office OS

AI Office OS is a local office simulation with a FastAPI backend, Next.js frontend, websocket world sync, and a small task orchestration loop.

## Project Structure

- `apps/frontend`: Next.js UI.
- `apps/backend`: FastAPI API, websocket layer, world state, simulation, task orchestration, agent runtime modules.
- `packages/types`: shared TypeScript domain types: `Agent`, `Department`, `Task`, `Event`, `WorldState`, `AgentStatus`, `TaskStatus`.
- `packages/protocol`: websocket message contracts and protocol documentation.
- `packages/config`: shared TypeScript config contracts.
- `packages/shared`: reserved shared runtime utilities.
- `scripts`: local development scripts.

## Install

```bash
npm install
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/backend/requirements.txt
```

## Environment

Copy the example values and adjust only what you need:

```bash
cp .env.example apps/backend/.env
```

For frontend overrides, use `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` in `apps/frontend/.env.local`.

### LLM Provider Layer

The LLM layer is isolated from tools and execution. Only local Ollama is
supported as a real provider. The safe mock provider is used by default for
tests and fallback:

```bash
LLM_PROVIDER=mock
LLM_REAL_CALLS_ENABLED=false
LLM_REASONING_ENABLED=false
LLM_REASONING_RATE_LIMIT_PER_MINUTE=20
LLM_REASONING_RATE_LIMIT_PER_PURPOSE=8
LLM_REASONING_CACHE_TTL_SECONDS=120
LLM_PROMPT_LOG_ENABLED=true
LLM_MAX_PROMPT_CHARS=12000
```

Local Ollama configuration:

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

External LLM providers are intentionally not supported. Prompt logs store
previews only and redact obvious secrets.

## Development Commands

Run both apps locally:

```bash
npm run dev
```

Run backend only:

```bash
npm run backend
```

Run frontend only:

```bash
npm run frontend
```

Manual backend command:

```bash
cd apps/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Manual frontend command:

```bash
cd apps/frontend
npm run dev
```

## Local URLs

- Frontend: `http://localhost:3000`
- Backend: `http://127.0.0.1:8000`
- WebSocket: `ws://127.0.0.1:8000/ws`
- World state: `http://127.0.0.1:8000/world`

## Verification

```bash
cd apps/backend
python3 -m compileall app
python3 -m pytest
cd ../..
npm run frontend:typecheck
npm --prefix apps/frontend run lint
npm --prefix apps/frontend run build
```

Backend tests can also be run from the repository root:

```bash
npm run backend:test
```

Frontend type-check can also be run from the repository root:

```bash
npm run frontend:typecheck
```

## Persistence

Local JSON persistence is enabled by default:

- Flag: `PERSISTENCE_ENABLED=true`
- Path: `apps/backend/storage/world_state.json`

The backend saves the current `WorldState`, including tasks, once per second and on graceful shutdown.

To reset local state:

```bash
rm -f apps/backend/storage/world_state.json
```

To disable persistence:

```bash
PERSISTENCE_ENABLED=false npm run backend
```

## Repository Hygiene

Do not commit generated dependencies, build output, caches, local env files, logs,
or local persistence state:

- `node_modules/`
- `apps/frontend/.next/`
- `dist/`, `build/`, `coverage/`
- `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`
- `.DS_Store`
- `.env`, `.env.*`, `*.local` except committed examples such as `.env.example`
- `apps/backend/storage/world_state.json`
- `tmp/`, `temp/`, `.cache/`, `logs/`, `*.log`, `*.tmp`

The local persistence file is `apps/backend/storage/world_state.json`. Reset the
local office state with:

```bash
rm -f apps/backend/storage/world_state.json
```

Legacy backend modules under `apps/backend/app/agents`,
`apps/backend/app/tools`, and `apps/backend/app/runtime` are compatibility code.
Tools that run shell commands or write files must not be used by new autonomous
runtime flows without explicit permissions, sandboxing, allowlists, and audit
logging.

## Development Checklist

Before committing, run:

```bash
npm run backend:test
npm run frontend:typecheck
npm --prefix apps/frontend run lint
npm --prefix apps/frontend run build
```

## WebSocket Protocol

The protocol is documented in `packages/protocol/websocket.md`.

Current stable server messages:

- `server.hello`
- `world.snapshot`
- `world.update`
- `event.broadcast`
- `error`

Current stable client messages:

- `client.hello`
- `world.subscribe`
- `world.get`

Task creation currently uses HTTP `POST /tasks`.
