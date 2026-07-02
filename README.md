# SAHAJ

**सहज** — Hindi for simple, natural, effortless.

A proactive financial intelligence system for the ~450 million Indians the formal financial system has an account for, but doesn't actually serve. SAHAJ keeps a live model of each user's money situation and mental state — the **Behavioral Financial Twin** — and acts on it before a harmful decision gets made, instead of waiting to be asked the right question. It runs over a `*99#` USSD menu on a feature phone as well as it runs as an installable PWA on a flagship, and it keeps working offline.

Built by Krutika Wagh and Rishi Mahajan (VESIT, Chembur) for Nomura Kakushin 2026.

## Why this exists

Read [`docs/PROBLEM.md`](docs/PROBLEM.md) for the full brief, but in short: account ownership in India is basically solved (PMJDY, UPI). Being *served* by the system is a different problem, and it's the one nobody's building for. A Swiggy driver with no salary slip, a schoolteacher sold a ULIP instead of an SIP, a farmer who knows the Kisan Credit Card exists but can't read the form, a visually impaired writer locked out of every mainstream finance app — none of that is an edge case. SAHAJ exists because no system has ever modelled who these people actually are.

## What's in this repo

| Path | What it is |
|---|---|
| [`backend/`](backend/) | FastAPI service: the LangGraph orchestrator, ten specialist agents on a shared blackboard, the Behavioral Financial Twin (Neo4j), Progressive Trust Protocol gating, and the channel adapters (chat/WhatsApp-style, USSD simulator). |
| [`frontend/`](frontend/) | React + TypeScript PWA — a WhatsApp-style chat tier and a `*99#` USSD simulator tier, built against the same backend API. |
| [`infra/`](infra/) | `docker-compose.yml` bringing up every self-hosted piece of the stack (Neo4j, MongoDB, Redis, Qdrant, Ollama) with one command. |
| [`docs/`](docs/) | Architecture, the tech-stack decisions and why, the build roadmap, the agent roster, and the Progressive Trust Protocol spec. |

## Quick start

```bash
# 1. bring up the data layer
cd infra && docker compose up -d

# 2. run the LLM natively (macOS: keeps it off Docker Desktop's small default
#    VM memory limit and gets Metal acceleration - see docs/ARCHITECTURE.md)
brew install ollama && brew services start ollama
ollama pull phi3:mini   # one-time, ~2.4GB

# 3. seed demo data - personas into Neo4j, schemes into Qdrant + OpenSearch
cd ../backend && cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed
python -m app.seed_schemes
python -m app.seed_search

# 4. optional - voices for the /api/voice/* speech pipeline (~120MB)
python -m piper.download_voices --download-dir app/data/voices hi_IN-pratham-medium en_US-lessac-medium

# 5. run the backend
uvicorn app.main:app --reload --port 8000

# 6. run the frontend (separate terminal)
cd ../frontend && npm install && npm run dev
```

Open the PWA, pick the Rajesh persona, and send: *"Ek loan app mila hai friend ne share kiya. ₹15,000 chahiye. Is this safe?"* — that's the golden-path demo traced end to end in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Status

This is an active build, not a finished product. See [`docs/ROADMAP.md`](docs/ROADMAP.md) for what's actually running versus what's designed-but-not-built, and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for exactly which pieces of the original stack were swapped for free/self-hostable equivalents and why.

## License

MIT — see [`LICENSE`](LICENSE).
