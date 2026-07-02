# Progressive Trust Protocol (PTP)

Data is earned, not demanded. Every level unlocks more only after the user has already seen value at the level below it — nobody is asked for DigiLocker before they've had a single scam alert land correctly.

| Level | Data given | What unlocks | Agents unlocked |
|---|---|---|---|
| 0 | Nothing | Regional scam alerts, area threat reports, and the crisis safety net. No sign-up; full CFTI benefit with zero personal data. | Financial Psyche, Scam Guard, Crisis Intercept, Community Intelligence |
| 1 | Phone + name | Personalised scheme eligibility, just-in-time explanations. | + Scheme Navigator, Learning & Literacy |
| 2 | Income range | Cash-flow projections, deficit warnings, life simulations. | + Cash Flow, Life Simulator |
| 3 | UPI consent (Account Aggregator) | Transaction monitoring, proactive distress detection - upgrades Cash Flow/Life Simulator from self-declared income to verified transaction data rather than unlocking a new agent. | *(upgrade, not a new agent - see Phase 2 roadmap)* |
| 4 | DigiLocker | Full scheme enrollment, credit-building, document-verified form-filling. | + Document Assist |

Crisis Intercept deliberately never requires more than Level 0 to *detect* a crisis and surface it — nobody loses the safety net for having shared less data. What Level 3+ actually gates in production is the human-handoff *fulfillment* (routing to a real advisor needs a verified way to follow up), not the detection itself; the Phase 1/2 implementation only covers detection.

## How this is enforced in code

`backend/app/trust/ptp.py` is the single place that decides, given a user's stored trust level, which agents the orchestrator is even allowed to dispatch for a given turn. This is a hard gate, not a soft hint to the LLM — an agent that needs Level 3 data simply never runs for a Level 1 user, regardless of what the conversation is about. Raising your own trust level is always an explicit, user-initiated action (never inferred, never defaulted up).
