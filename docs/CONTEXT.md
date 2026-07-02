# Project context

One file with the whole picture — what SAHAJ is, why every piece exists, exactly what's built versus what's designed-only, and how to pick the project back up on a fresh machine. Everything here is also spread across `README.md` and the other files in `docs/`; this is the single place that ties it together.

## The pitch

SAHAJ (सहज — Hindi for simple, natural, effortless) is a proactive financial intelligence system for the ~450 million Indians the formal financial system has an account for but doesn't actually serve. It keeps a live model of each user's money situation and mental state — the **Behavioral Financial Twin** — and acts on it *before* a harmful decision gets made, instead of waiting to be asked the right question. It runs over a `*99#` USSD menu on a ₹2,000 feature phone as well as it runs as an installable PWA on a flagship, and it keeps working offline. Built by Krutika Wagh and Rishi Mahajan (VESIT, Chembur, MCA 2025–2027) for the **Nomura Kakushin 2026** hackathon.

Full problem statement: [`PROBLEM.md`](PROBLEM.md). Four people the whole system is built around: **Rajesh** (Swiggy driver, Mumbai, income swings ₹15K–40K, no salary slip), **Priya** (schoolteacher, Thane, sold a ULIP when she asked about an SIP), **Kisan** (paddy farmer, Karnataka, Kisan Credit Card form is in English, branch is 14km away), **Divya** (visually impaired writer, Pune, can't use mainstream finance apps).

## How it's built

Six layers — signal in, context resolved against the Twin, an Orchestrator routes to specialists, ten agents reason on a shared blackboard, one composed reply goes out on whatever channel the user is on, every outcome feeds back into the Twin. Full breakdown: [`ARCHITECTURE.md`](ARCHITECTURE.md). Agent roster and what each one does: [`AGENTS.md`](AGENTS.md). The trust model (data earned, not demanded, five levels): [`PTP.md`](PTP.md).

The original hackathon brief specified a stack built around a hackathon-only LLM endpoint and enterprise tooling (Kafka, Cassandra, Kubernetes, Keycloak, real DigiLocker/Aadhaar/Setu). Since the brief explicitly allows swapping tooling, this build kept the *architecture* and picked free, self-hostable software for nearly every piece — see `ARCHITECTURE.md`'s swap table for the reasoning behind each one. Three things are genuinely, structurally impossible to get for free as an individual: **DigiLocker partner registration**, **Aadhaar eKYC AUA/KUA status**, and a **real `*99#` telecom gateway**. Those stay mocked behind clean interfaces. Everything else — including things that sound expensive, like Kafka, federated learning, and full observability — is real, running, self-hosted software.

## Repo map

| Path | What it is |
|---|---|
| `backend/` | FastAPI service — the LangGraph orchestrator, agents, BFT (Neo4j), PTP gating, and every channel adapter (chat, USSD, voice, WhatsApp, document scan). |
| `frontend/` | React + TypeScript PWA — WhatsApp-style chat tier and a `*99#` USSD simulator tier. |
| `infra/` | `docker-compose.yml` for local dev (one command brings up every data service), plus `infra/k8s/` real Kubernetes manifests and `infra/otel/`, `infra/grafana/` observability config. |
| `docs/` | This file, plus `PROBLEM.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `AGENTS.md`, `PTP.md`. |

## Build status

Development happened issue-by-issue against [github.com/RishiM19/sahaj/issues](https://github.com/RishiM19/sahaj/issues) (13 closed, 4 deliberately left open — see below). `docs/ROADMAP.md` has the live checklist; this is the narrative version.

**Phase 1 — foundation (fully working):** Behavioral Financial Twin in Neo4j with a four-state machine (`STABLE → STRESSED → VULNERABLE → CRISIS`), a LangGraph orchestrator with a genuine shared-blackboard pattern, `phi3:mini` served locally via Ollama as the shared reasoning backbone, PTP trust gating, and both a chat channel and a USSD simulator talking to the same backend. Verified against the golden-path demo: Rajesh asks about an unregistered loan app on WhatsApp, Scam Guard flags it against a real RBI-registry mock and logs it to a CFTI threat store, Cash Flow runs a real Monte Carlo and finds a deficit risk, Life Simulator narrates it, all composed into one reply with the scam alert deterministically prepended (small local models occasionally drop the most important fact when paraphrasing multiple observations — critical safety facts never depend on that, they're always surfaced verbatim).

**Phase 2 — all personas, all channels (fully closed):** the remaining six agents (Scheme Navigator with a real Qdrant RAG index over 20 government schemes, Crisis Intercept, Community Intelligence, Learning & Literacy as blackboard agents; Voice & Accessibility and Document Assist as channel infra at `/api/voice/*` and `/api/document/*`), a real seasonal SIII model (hand-encoded kharif/rabi crop calendar + gig-platform demand cycle + MNREGA, not a flat mean/std), PTP levels 3–4 with a mocked-but-swappable `GovIntegrations` interface, a real WhatsApp Cloud API webhook (verified against Meta's live Graph API — a deliberately invalid token got back a real `OAuthException`, confirming the request shape), OpenSearch full-text search, and a real speech pipeline (faster-whisper + Piper-TTS, Hindi + English voices, verified with an actual audio round trip) and OCR pipeline (Tesseract, not PaddleOCR — PaddlePaddle publishes no wheel for Python 3.14 on any platform, a verified upstream gap, not a shortcut).

**Phase 3 — privacy, scale, production infra (mostly closed, further than originally planned):**
- ✅ **Federated learning** — real Flower + Opacus DP-SGD simulation, 5 clients, verified live: ε≈0.099 against a 0.1 target every round, accuracy climbed 64%→66.5% over 5 rounds on synthetic threat-report data (honestly modest — that's the real cost of a strict privacy budget on 5 small clients, and the actual point of federating is that it improves as real client count grows).
- ✅ **Event backbone** — Redpanda (Kafka-API compatible), verified live: triggered a turn, consumed `sahaj.events` with `rpk`, got the expected `bft.updated`/`scam.alert`/`query.resolved` events.
- ✅ **Setu Account Aggregator** — real REST client verified against Setu's live sandbox (consent-creation endpoint confirmed against their published docs, and a deliberately invalid token got a real `401` back), additive to the existing mock so nothing regressed.
- ✅ **Observability** — OpenTelemetry → Prometheus → Grafana, verified live: a real chat turn's metrics (`sahaj_turns_total`, `sahaj_agent_dispatches_total`, `sahaj_turn_duration_seconds`) landed in Prometheus and were queryable through Grafana's own datasource proxy.
- **~ Kubernetes** — real `Dockerfile`s and manifests in `infra/k8s/`, applied to a live local `kind` cluster. The namespace, all six data-service Deployments, and the frontend Deployment came up and pulled real images (frontend pod reached `Running` on its own custom build). The backend pod's image build got interrupted by a Docker Desktop disk-corruption incident (torch pulling several GB of unneeded CUDA wheels ate all local disk) — root cause is already fixed (CPU-only torch pinned explicitly in `backend/Dockerfile`), just needs a rebuild + `kind load docker-image sahaj-backend:latest --name sahaj` to finish. **This is the very next thing to do when picking the project back up.**
- **Deliberately left open**, not forgotten: **DigiLocker/Aadhaar eKYC** (genuinely blocked — needs institutional backing, no individual sandbox exists), **Keycloak/Vault/OPA/Falco** (protect a multi-tenant production deployment that doesn't exist yet), **village-node deployment** (needs physical Raspberry Pi hardware). All three documented in `docs/ROADMAP.md` with why.

## Resuming from scratch

```bash
git clone https://github.com/RishiM19/sahaj.git && cd sahaj

# data layer
cd infra && docker compose up -d

# LLM backbone — native on macOS (see ARCHITECTURE.md for why, and leave
# real disk headroom — 10GB+ — before building any Docker images here,
# see the Kubernetes note above)
brew install ollama && brew services start ollama && ollama pull phi3:mini

# backend
cd ../backend && cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed && python -m app.seed_schemes && python -m app.seed_search
uvicorn app.main:app --reload --port 8000

# frontend (separate terminal)
cd ../frontend && npm install && npm run dev
```

Open the PWA, pick Rajesh, send the scam-loan message from the golden path above. Grafana's at `localhost:3000` (anonymous admin, dev-only) with a dashboard already provisioned.

## What's never going in this repo

No mention of the tool this was built with, anywhere — commits, code comments, docs, PR text. This was an explicit, standing instruction from day one, not an oversight to preserve. If you ever see it slip in, that's a bug — fix it.
