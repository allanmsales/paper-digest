# Paper Digest

Helps a person learn an AI/ML paper. Reading comes first: the reader reads the paper and
self-reports understanding, and the tool then helps with the gaps. Learning converges on the
paper (only the prerequisites that feed into it), never branches away from it.

Work in small, testable steps. Each step is shipped and verified before the next one starts.

## Folder organization: by domain, not by layer

Everything related to one domain lives in **one folder**: its router, schemas, agent/service
logic, and anything else specific to it. Do **not** create layer folders such as `routers/`,
`controllers/`, `schemas/`, `services/` or `agents/` that group code of different domains together.

Shared, domain-agnostic code is the only exception:
- `core/`: app-wide setup (config; later the database).
- `clients/`: wrappers around external systems (e.g. the Claude agent runner).

```
src/paper_digest/
  main.py        # FastAPI app; includes each domain's router
  core/          # config.py, db.py (SQLite via SQLModel, file in data/)
  clients/       # claude.py: ask_claude/warm_claude (cached paper, Haiku), ask_claude_once (one-off, e.g. Sonnet summary), run_agent (Agent SDK); tts.py: local Kokoro TTS (ONNX, model in data/models)
  reader/        # PDF fetching/parsing, Paper table (router, pdf.py, models.py, store.py)
  analyser/      # Paper Analyzer agent (router, schemas, agent)
  splitter/      # Subject Splitter agent + analyse→split pipeline (router, schemas, agent, service)
  explainer/     # Explain, Summary (+ sections), Analogy, section Check, anchored Ask; one shared prompt cache; saves summaries + gap signals
  feed/          # Learning feed: splitter concepts -> posts (lesson/flip/quiz), gaps-first sessions of 8
  podcast/       # Host/author interview script (Sonnet) voiced by Kokoro into data/podcasts/<paper_id>.mp3
  users/         # Accounts (scrypt hashes), cookie sessions, admin CRUD; every other router requires sign-in
                 # Per-user rows (user_id): Signal, PostView, Lookup, CheckAttempt, LibraryEntry.
                 # Per-paper rows stay shared: summary, feed posts, podcast.
                 # init_db adds new nullable columns to existing tables; keep new columns nullable.
                 # First admin: `uv run python -m paper_digest.users.cli <email> --admin`

web/src/
  reader/        # PDF reader UI (same domain names as the backend)
  explainer/     # Explain popover, Summary card, Check card, Ask thread, Analogy, lookups panel
  feed/          # Feed page (/?feed=<paper_id>), post cards
  podcast/       # Podcast card on the reader: generate, play, transcript
  users/         # Login page, admin page (/?admin), user menu
```

Rules:
- A new feature goes into an existing domain or gets its own folder with its own `router.py` / `schemas.py`.
- Each domain's router uses its domain name as the URL prefix (`/reader`, `/analyser`, `/splitter`, `/explainer`, `/feed`, `/podcast`).
- Each domain owns its tables (`models.py`) and DB access (`store.py`). Papers are keyed by the sha256 of their extracted text.
- Cross-domain imports are fine when they are one-way (e.g. `splitter` uses `analyser`); avoid cycles.
- The frontend mirrors the backend domains under `web/src/<domain>/`.

## Running

- Everything: `docker compose up` (API on 8000, web on 5173; both hot-reload).
- API: `uv run uvicorn --app-dir src paper_digest.main:app --reload` (or `docker compose up`), port 8000.
- Web: `cd web && npm install && npm run dev`, port 5173. Vite proxies `/api/*` to the API (the prefix is stripped).
