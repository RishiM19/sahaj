# Roadmap

Three phases, same boundary we'd defend to a judge: phases 1 and 2 are things you can actually run and click through today; phase 3 is designed and interface-scaffolded but needs infrastructure (real federation clients, real gov API credentials, a real cluster) that doesn't make sense to stand up before there are real users.

Every unchecked item below is also a tracked [GitHub issue](https://github.com/RishiM19/sahaj/issues), labelled `phase-2` or `phase-3` — that's the place to pick up individual pieces of work rather than this file.

## Phase 1 — Foundation & first slice ✅ building now

- [x] Behavioral Financial Twin in Neo4j — schema + four-state machine (`STABLE → STRESSED → VULNERABLE → CRISIS`)
- [x] LangGraph orchestrator with the shared-blackboard pattern
- [x] Ollama serving `phi3:mini` as the shared model backbone
- [x] Four agents live: **Financial Psyche**, **Scam Guard**, **Cash Flow**, **Life Simulator**
- [x] FastAPI backend, chat channel (WhatsApp/PWA-tier) + USSD simulator channel
- [x] Progressive Trust Protocol levels 0–2 gating agent depth
- [x] React PWA — chat screen + USSD screen, talking to the real backend
- [x] Golden-path demo: Rajesh's WhatsApp scam-alert scenario, traced end to end

## Phase 2 — All personas, all channels

- [x] Scheme Navigator, Crisis Intercept, Community Intelligence, Learning & Literacy, Document Assist — 5 of the remaining 6 agents
- [x] Scheme RAG over Qdrant — 20-scheme real seed set (growing toward 400+ is separate, ongoing work)
- [x] Seasonal & Irregular Income Intelligence (SIII) — structured crop-calendar/gig-demand/MNREGA seasonality on top of the Monte Carlo, not a flat mean/std (see `app/agents/seasonal.py`; a model trained on real gig/crop-yield datasets is out of reach without institutional data access)
- [x] Financial Life Simulation Engine (FLSE) — shares Cash Flow's 10,000-pass Monte Carlo engine directly, so the narrated story and the numeric warning can't drift apart
- [x] Speech pipeline: faster-whisper (STT) + Piper-TTS (TTS), voice-first path for the Divya persona - `/api/voice/transcribe`, `/api/voice/speak`, `/api/voice/turn` (2 voices shipped: Hindi and English; growing toward the full 22 is separate, ongoing work)
- [x] Document-assist pipeline (Kisan/Divya form-filling flow) - `/api/document/scan`, Tesseract instead of PaddleOCR (see docs/ARCHITECTURE.md), gated at PTP Level 4
- [x] WhatsApp Cloud API webhook code (`/api/whatsapp/webhook`) - real verification handshake and message send/receive against Meta's actual API, verified against the live Graph API (a deliberately invalid token got a real `OAuthException` back, proving the request shape is correct). What's *not* done: a Meta developer account, business verification, and a test phone number - manual sign-up steps at developers.facebook.com/apps that this code can't do on your behalf. Once you have `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, and `WHATSAPP_VERIFY_TOKEN` from that sandbox, drop them into `.env` and point Meta's webhook config at `https://<your-tunnel>/api/whatsapp/webhook` (ngrok or similar for local dev) - no code changes needed.
- [ ] PTP levels 3–4 (UPI consent, DigiLocker-gated flows — against the mocked `GovIntegrations` interface)
- [x] OpenSearch for full-text scheme/threat search

## Phase 3 — Privacy, scale, production deployment (designed, not live)

- [x] Community Financial Threat Intelligence (CFTI) as genuine federated learning via Flower, with Opacus differential privacy (ε = 0.1) - `backend/app/federated/`, `python -m app.federated.run_simulation`. Real Flower FedAvg across 5 simulated clients, real Opacus DP-SGD hitting ε≈0.099 against the ε=0.1 target every round; accuracy climbed 64%→66.5% over 5 rounds on synthetic per-client threat-report data (nobody outside a real multi-device deployment has actual per-user CFTI histories to federate over - see the module docstrings). That accuracy is honestly modest, which is the expected utility cost of a strict ε=0.1 budget on 5 small clients - it should improve as real client count grows, which is the actual point of federating in the first place.
- [x] Kafka-compatible event backbone (Redpanda) - `sahaj.events` topic, `bft.updated`/`scam.alert`/`query.resolved` published from the orchestrator, verified live with `rpk topic consume`
- [x] Real Setu Account Aggregator sandbox integration - `app/integrations/setu.py`, `/api/chat/trust/consent/{start,finalize}`, additive to the existing mocked PTP Level 3 path rather than replacing it. Consent creation/status endpoints verified against Setu's published docs (method, path, headers, body fields) and against their live sandbox - a deliberately invalid token got back a real `401 Bad token; invalid JSON`, confirming the request shape is correct. FI data-session field names are best-effort (the AA framework's standard consent-then-session pattern, but I couldn't independently verify Setu's exact session field names against live docs) - flagged in the module docstring to confirm against Setu's Postman collection once you have real sandbox credentials.
- [ ] Real DigiLocker / Aadhaar eKYC integration (requires partner/AUA-KUA registration — out of reach until SAHAJ has an institutional backer)
- [~] Kubernetes manifests exercised against a real cluster - `infra/k8s/`, plus real `Dockerfile`s for both apps. Applied to a local `kind` cluster: namespace, all six data-service Deployments (Neo4j/Postgres/Redis/Qdrant/OpenSearch/Mongo) and the frontend Deployment came up and pulled real images successfully - the frontend pod reached `Running` on its own built image. The backend Deployment is applied but its image build got interrupted (see below) - re-running `docker build` + `kind load docker-image` is the one step left to see the backend pod go `Running` too.
- [ ] Keycloak, Vault, OPA, Falco — full identity/secrets/policy/runtime-security stack
- [x] OpenTelemetry + Prometheus/Grafana observability - `app/observability.py` exports traces + metrics over OTLP to the Collector (`infra/otel/`), which Prometheus scrapes and Grafana visualizes (`infra/grafana/`, "SAHAJ Overview" dashboard auto-provisioned). Verified the full chain live: triggered a turn, watched `sahaj_turns_total`, `sahaj_agent_dispatches_total`, and `sahaj_turn_duration_seconds` land in Prometheus and be queryable through Grafana's own datasource proxy.
- [ ] Village-node deployment (Raspberry Pi 4 / repurposed Android at CSC centres) for offline batch-sync

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for exactly what each swap in phases 1–2 replaced and why, and [`AGENTS.md`](AGENTS.md) for what each of the ten agents does.
