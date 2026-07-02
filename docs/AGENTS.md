# The ten agents

All ten read from and write to the same shared blackboard, propagated with the current user's BFT context. None of them talk to the user directly — the Orchestrator composes one response out of whatever they wrote.

| Agent | What it does | Status |
|---|---|---|
| **Financial Psyche** | Reads emotional cues and documented biases from the incoming signal and the BFT history; sets/updates the behavioral state. | Phase 1 |
| **Scam Guard** | Checks every request against the CFTI threat network and the RBI-registered-lender list. | Phase 1 |
| **Cash Flow** | Runs SIII-style income projections and flags upcoming deficits. | Phase 1 (rule-based projection; real SIII model in Phase 2) |
| **Life Simulator** | Turns a Monte Carlo pass over the user's income into a spoken "what happens next" narrative (FLSE). | Phase 1 (simplified pass count; full 10,000-pass engine in Phase 2) |
| **Scheme Navigator** | Matches the user to government schemes via the Qdrant RAG index. | Phase 2 |
| **Crisis Intercept** | Steps in when the behavioral state hits `CRISIS`; offers a human handoff. | Phase 2 |
| **Community Intelligence** | Feeds and reads the federated scam-signal network (CFTI). | Phase 3 (federation requires multiple real clients) |
| **Learning & Literacy** | Explains a concept only at the moment it's relevant, in the user's own terms. | Phase 2 |
| **Voice & Accessibility** | Handles speech in and out; the voice-only path end to end. | Phase 2 |
| **Document Assist** | Reads physical documents with OCR and fills forms field by field. | Phase 2 |

## Why a blackboard instead of a chain

A naive multi-agent system chains agents and lets each one talk to the user in turn, or lets the "smartest" agent have the final word. Both produce answers that contradict each other across a conversation, because each agent only sees its own slice of context. SAHAJ's agents all read the *same* BFT-derived context off the blackboard before they reason, so their findings already agree by construction — Scam Guard isn't going to say "this lender's fine" while Cash Flow says "you can't afford this" from different premises, because they started from the same premises. The Orchestrator's actual job is picking which of several *true* observations matters most right now, not reconciling contradictions.

## Progressive Trust Protocol gates which agents even run

Not every agent has data to work with at every trust level — see [`PTP.md`](PTP.md). At Level 0, only Scam Guard and Community Intelligence run (they need no personal data). Cash Flow needs an income range (Level 2). Document Assist and full scheme enrollment need DigiLocker (Level 4).
