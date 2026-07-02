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

- [ ] Remaining six agents: Scheme Navigator, Crisis Intercept, Community Intelligence, Learning & Literacy, Voice & Accessibility, Document Assist
- [ ] Scheme RAG over Qdrant (400+ government schemes — starting with a real seed set, not synthetic)
- [ ] Seasonal & Irregular Income Intelligence (SIII) — real model over gig/crop/MNREGA income patterns, not the Phase 1 rule-of-thumb version
- [ ] Financial Life Simulation Engine (FLSE) — real 10,000-pass Monte Carlo, not the Phase 1 simplified version
- [ ] Speech pipeline: faster-whisper (STT) + Piper-TTS (TTS), voice-first path for the Divya persona
- [ ] PaddleOCR document-assist pipeline (Kisan/Divya form-filling flow)
- [ ] Real WhatsApp Cloud API webhook (sandbox number) replacing the chat simulator
- [ ] PTP levels 3–4 (UPI consent, DigiLocker-gated flows — against the mocked `GovIntegrations` interface)
- [ ] OpenSearch for full-text scheme/threat search

## Phase 3 — Privacy, scale, production deployment (designed, not live)

- [ ] Community Financial Threat Intelligence (CFTI) as genuine federated learning via Flower, with Opacus differential privacy (ε = 0.1)
- [ ] Kafka-compatible event backbone (Redpanda) replacing the in-process bus
- [ ] Real Setu Account Aggregator sandbox integration
- [ ] Real DigiLocker / Aadhaar eKYC integration (requires partner/AUA-KUA registration — out of reach until SAHAJ has an institutional backer)
- [ ] Kubernetes manifests exercised against a real cluster (currently scaffolded only)
- [ ] Keycloak, Vault, OPA, Falco — full identity/secrets/policy/runtime-security stack
- [ ] OpenTelemetry + Prometheus/Grafana observability
- [ ] Village-node deployment (Raspberry Pi 4 / repurposed Android at CSC centres) for offline batch-sync

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for exactly what each swap in phases 1–2 replaced and why, and [`AGENTS.md`](AGENTS.md) for what each of the ten agents does.
