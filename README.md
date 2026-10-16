# Paper Digest

Paper Digest helps you **learn an AI/ML research paper**, not just skim it. You read the paper first,
and the app helps with the parts you find hard. Every lesson, quiz and explanation leads back to the
paper itself.

What you can do with a paper:

| Feature | What it does |
|---|---|
| **Reader** | Open a paper by URL (e.g. an arXiv PDF link) or upload a PDF. |
| **Explain** | Select any text → a short, plain-language explanation of what it means *in this paper*. Optional "guess first". |
| **Paper in 3 lines** | Problem · Idea · Result, written for a non-expert. |
| **Analogy** | An everyday analogy for any explanation, mapped back to the paper's terms. |
| **Check** | Section by section, write what you understood; get ✓/✗ per key idea and where to reread. |
| **Ask** | A small chat thread tied to one idea you missed. |
| **Learning feed** | Short posts (lessons, flip cards, quizzes) on the concepts the paper builds on, your weak spots first. |
| **Podcast & video** | An interview-style audio episode and a narrated explainer video of the paper. |
| **Progress** | Your progress, a knowledge map of the paper's concepts, and a score. |

---

## Quick start (Docker)

You only need **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** (or Docker Engine
with Compose v2.24+) and an AI provider key (see [AI providers](#ai-providers)).

```bash
git clone https://github.com/allanmsales/paper-digest.git
cd paper-digest
docker compose up --build
```

The first build takes a few minutes. When the logs show `Application startup complete`, open
**<http://localhost:5173>**.

### First run

On a fresh install a setup screen walks you through two steps:

1. **Your account:** create the admin account for your computer.
2. **AI provider:** pick a provider, paste your key, click **Test connection**, then **Save**.

That's it. Open a paper and start reading. You can change the provider any time in **Admin**
(top-right menu → Admin), and add accounts for other people there too.

> No `.env` file is needed. If you prefer, copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY`;
> it is used only when no provider is saved in the app.

### Everyday use

```bash
docker compose up        # start (add -d to run in the background)
docker compose down      # stop
```

Both the API and the web app reload automatically when you edit code.

---

## AI providers

The admin picks one provider for the whole app. Each provider uses two models:

- **Fast model:** many small calls (Explain, Check, Ask). Pick a cheap, quick model.
- **Smart model:** occasional long writing (summary, feed, podcast, video). Pick a stronger model.

| Provider | Key | Notes |
|---|---|---|
| **Anthropic (Claude)** | [console.anthropic.com](https://console.anthropic.com/) | Recommended. Best results, and lookups are cheap thanks to prompt caching. Defaults: `claude-haiku-4-5` (fast) and `claude-sonnet-5-5` (smart). |
| **OpenAI** | [platform.openai.com](https://platform.openai.com/) | Click **Load models**, then pick a small model as fast and a strong one as smart. |
| **Other OpenAI-compatible API** | Depends on the server | Any server with `/v1/chat/completions`: Ollama, vLLM, OpenRouter… Enter the base URL (ending in `/v1`) and choose how the key is sent (`Authorization: Bearer` or `x-api-key`). |

**Rough cost with Anthropic.** About $0.10–0.30 to prepare a new paper (summary, sections, feed).
After that, each lookup costs a fraction of a cent. Podcast and video each make one extra call to the
smart model, and only when you ask for them.

**About your key.** It is stored only in your local database (`data/paper_digest.db`), never sent back
to the browser, and never committed: `data/` is git-ignored and excluded from the Docker image.

---

## Your data

Everything lives in the `data/` folder next to the code:

| Path | What |
|---|---|
| `data/paper_digest.db` | Accounts, AI settings, papers, your progress (SQLite) |
| `data/models/` | The local text-to-speech voice model (~340 MB, downloaded on first podcast/video) |
| `data/podcasts/`, `data/videos/` | Generated audio |

- **Start over:** stop the app and delete `data/paper_digest.db`. The setup screen appears again.
- **Back up:** copy the `data/` folder.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| **Port 8000 or 5173 is already in use** | Stop the other app, or change the left side of `ports:` in `docker-compose.yml` (e.g. `"5174:5173"`). |
| **"No AI provider is set up"** banner | An admin must add one in **Admin → AI provider**. |
| **Test connection fails** | Check the key and model names. For OpenAI-compatible servers, check the base URL ends in `/v1` and the key header is right. |
| **The first podcast or video is slow** | The voice model (~340 MB) downloads once into `data/models/`. |
| **A code change has no effect** | File watching through Docker on macOS sometimes misses edits. Run `docker compose restart api`. |
| **Slow on Apple Silicon** | The API image is built for `linux/amd64` (see `docker-compose.yml`) and runs under emulation. It works, just slower. |
| **Locked out of every admin account** | Create a new admin (it asks for a password): `docker compose exec -it api uv run python -m paper_digest.users.cli you@example.com --admin`. Other users' passwords can be changed in **Admin**. |

---

## Running without Docker (development)

You need **Python 3.12** with [uv](https://docs.astral.sh/uv/) and **Node 22**.

```bash
# API, http://localhost:8000
uv sync
uv run uvicorn --app-dir src paper_digest.main:app --reload

# Web, http://localhost:5173 (in a second terminal)
cd web
npm install
npm run dev
```

The web dev server forwards `/api/*` to the API.

## Project structure

The code is organized **by domain**: each feature has one folder with its router, schemas, models and
logic, in the backend (`src/paper_digest/<domain>/`) and the frontend (`web/src/<domain>/`). See
[CLAUDE.md](CLAUDE.md) for the full map and conventions.
