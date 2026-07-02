# Architecture

## System layers

Something comes in — a chat message, a `*99#` dial, a detected income spike — and it moves down through context resolution, routing, and the agent cluster, gets delivered back on whatever channel the user is on, then loops back to sharpen that user's model for next time.

```
1. Signal Ingestion    chat/WhatsApp · USSD · voice · internal triggers
2. Context Engine      BFT lookup · language · behavioral state · trust level
3. Orchestrator        LangGraph — routing, PTP gate, the only voice the user hears
4. Agent Cluster       specialists on a shared blackboard, run in parallel
5. Delivery            same channel back out — USSD menu, chat reply, voice, PWA card
6. Learning loop       every interaction updates the Behavioral Financial Twin
```

Two decisions matter more than the rest:

- **No agent ever talks to the user directly.** The Orchestrator is the only voice. Every specialist writes a typed observation to a shared blackboard; the Orchestrator composes one answer out of those notes and throws out contradictions. This is what keeps ten independent specialists from producing the contradictory mush that most multi-agent demos ship.
- **The learning loop is not cosmetic.** Every outcome — did the user borrow anyway, did they ask for the safer option, did they go silent — gets written back onto the Behavioral Financial Twin. That's the difference between a system that gets the timing right over weeks and one that treats every conversation like the first.

## The agents

Ten specialists work off a shared blackboard, coordinated by a LangGraph orchestrator. Full roster and responsibilities: [`AGENTS.md`](AGENTS.md). This repo currently implements four of the ten as a working slice — see [`ROADMAP.md`](ROADMAP.md) for which.

## The Behavioral Financial Twin (BFT)

A live graph per user, stored in Neo4j: income phase, documented biases, trust level, and a behavioral state that moves `STABLE → STRESSED → VULNERABLE → CRISIS`, recomputed on every interaction. It's what lets the system tell whether someone wants to borrow out of need or out of panic, and pick the timing and tone that actually change the decision — not just the facts.

## Progressive Trust Protocol (PTP)

Data is earned, not demanded. Full spec: [`PTP.md`](PTP.md). Level 0 gets scam alerts with zero sign-up; each level after that unlocks more only once the user has already seen value from the level before it.

## Tech stack — what changed from the original design, and why

The original competition brief specified a stack built around a hackathon-provided LLM endpoint (`KakushIN LLM API`) and a full production-grade platform (Kafka, Flink, Cassandra, Kubernetes, Keycloak, Vault, real DigiLocker/Aadhaar/Setu integrations). None of that endpoint or those credentials exist outside the event, and standing up the full platform isn't a reasonable ask for a repo two people maintain. Since the brief itself explicitly allows swapping tooling, this build keeps the *architecture* — same six layers, same ten agents, same BFT/CFTI/FLSE/SIII/PTP concepts — and picks free, self-hostable software for every piece, with three exceptions that are structurally impossible to get for free and are called out below.

| Concern | Original spec | This build | Why |
|---|---|---|---|
| LLM inference | KakushIN LLM API (event-only endpoint) | **Ollama**, self-hosted, serving `phi3:mini` (3.8B, quantized) | Same model the original spec recommended for CPU-only inference — just served locally instead of through an endpoint that only exists during the event. Genuinely free, and closer to the "works with no signal" story than a cloud API ever was. Run natively on the dev machine rather than in Docker — Docker Desktop's default VM memory ceiling is too small to hold phi3:mini alongside the rest of the stack and the model process gets killed mid-generation; running it as a native `brew services` process also gets Metal acceleration on Apple Silicon instead of being boxed in. |
| Agent orchestration | LangGraph 0.2.55 | LangGraph (current) | Unchanged — already free and open source. |
| Embeddings / RAG | sentence-transformers, Qdrant | Unchanged | Free, self-hosted. |
| Speech (STT/TTS) | faster-whisper, Piper-TTS | Unchanged | Free, open weights, run locally - see `/api/voice/*`. |
| OCR | PaddleOCR | **Tesseract** (via `pytesseract`) | PaddlePaddle - PaddleOCR's underlying framework - publishes no wheel at all for Python 3.14 on any platform; `pip install paddlepaddle` fails outright. Tesseract is free/open-source either way, and the same `OCRService` interface (`app/ocr/service.py`) makes swapping back a one-file change once PaddlePaddle catches up. |
| BFT graph store | Neo4j Community | Unchanged | Neo4j Community Edition is free and self-hostable via Docker. |
| User profiles | MongoDB | Unchanged | Free, self-hosted. |
| Threat time-series (CFTI) | Apache Cassandra | **Postgres** for the prototype | Cassandra is free too, but its operational overhead (multi-node by design) buys nothing at prototype scale. Documented as the production swap once CFTI needs to shard across regions — the access layer is written behind an interface so the swap doesn't touch agent code. |
| Search | Elasticsearch | **OpenSearch** | Elasticsearch's post-7.10 license isn't fully open source; OpenSearch is the Apache-2.0 fork with the same API. Deferred to Phase 2 — not needed for the current agent slice. |
| Cache / sessions | Redis | Unchanged | Free, self-hosted. |
| Event backbone | Kafka + Confluent Schema Registry + Flink | **Redpanda** (Kafka-API compatible, single binary, free) - `app/events/bus.py` | Kafka's own operational footprint (Zookeeper, a schema registry, Flink) is disproportionate to what a two-person team needs; Redpanda speaks the same wire protocol on one binary. Stream *processing* (Flink's job) is still deferred - right now the orchestrator publishes events, nothing yet consumes them for real-time aggregation. |
| USSD gateway | NPCI `*99#` aggregator | **Local USSD simulator** (Go handler, same session protocol) | Real `*99#` aggregator access requires a bank/telecom sponsorship no individual developer can get. The Go handler and session logic are real; only the last hop (an actual telecom gateway) is simulated. |
| WhatsApp | Meta WhatsApp Business API v20 (on-prem) | **Meta WhatsApp Cloud API**, free developer/sandbox tier | Meta's own hosted replacement for the on-prem Business API. Same webhook contract, free for development-volume messaging with a test number. |
| Federated learning / DP | Flower, Opacus | Unchanged - `app/federated/`, real simulation | Free, open source. Runs 5 simulated clients locally (`python -m app.federated.run_simulation`) since real per-user CFTI histories don't exist outside an actual deployment; not yet wired into the live CFTI store in `app/db/cfti.py` - that integration needs enough real client devices for federation to mean anything more than what the simulation already proves out. |
| Observability | OpenTelemetry, Prometheus, Grafana | Unchanged - `app/observability.py`, `infra/otel/`, `infra/grafana/` | Free, self-hosted. Backend exports traces/metrics over OTLP to a Collector, which Prometheus scrapes and Grafana visualizes via an auto-provisioned dashboard - verified live with real generated traffic, not just containers running idle. |
| Identity / secrets / policy | Keycloak, Vault, OPA | JWT auth + `.env` for the prototype; Keycloak/Vault/OPA documented for Phase 3 | Free either way — deferred because they protect a multi-tenant production deployment that doesn't exist yet. |
| Container orchestration | Kubernetes | `docker compose` for local dev; real manifests in `infra/k8s/`, applied to a `kind` cluster | Free either way. Building the backend's Docker image (torch + the rest of `requirements.txt`) pulled several GB of CUDA/GPU wheels nobody needs on this CPU-only stack and exhausted local disk mid-build, which corrupted Docker Desktop's VM and needed a restart to recover — fixed by pinning the CPU-only torch wheel index in `backend/Dockerfile` explicitly. Worth knowing before you run this build yourself: make sure Docker Desktop has real headroom (10GB+) first. |
| **DigiLocker API** | Real integration | **Mocked behind a `GovIntegrations` interface** | Requires registering as a DigiLocker partner entity — not something available to an individual outside a company/institution. |
| **Aadhaar eKYC (UIDAI)** | Real integration | **Mocked behind the same interface** | Requires licensed AUA/KUA status under UIDAI regulations — legally restricted to authorized entities, not obtainable for a personal project regardless of budget. |
| **Setu Account Aggregator** | Setu AA SDK | **Real REST client** (`app/integrations/setu.py`), config-driven; the mocked path in `app/integrations/gov.py` stays as the default until real sandbox credentials are set | Setu offers a free developer sandbox, unlike DigiLocker/Aadhaar — verified the consent-creation request against their live sandbox with an intentionally invalid token and got back a real, correctly-shaped `401`, confirming the endpoint/headers/body are right. Just needs real `SETU_CLIENT_ID`/`SETU_CLIENT_SECRET` from your own sandbox signup. |

Everything not marked "mocked" above is real, running software in this repo, not a stub — it's just self-hosted instead of paid-for.
