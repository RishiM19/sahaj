# Progressive Trust Protocol (PTP)

Data is earned, not demanded. Every level unlocks more only after the user has already seen value at the level below it — nobody is asked for DigiLocker before they've had a single scam alert land correctly.

| Level | Data given | What unlocks | Agents unlocked |
|---|---|---|---|
| 0 | Nothing | Regional scam alerts and area threat reports. No sign-up; full CFTI benefit with zero personal data. | Scam Guard, Community Intelligence |
| 1 | Phone + name | Personalised scheme eligibility, basic guidance. | + Scheme Navigator, Learning & Literacy |
| 2 | Income range | Cash-flow projections, behavioral nudges, deficit warnings. | + Cash Flow, Financial Psyche (full depth) |
| 3 | UPI consent (Account Aggregator) | Transaction monitoring, proactive distress detection. | + Life Simulator (real transaction data instead of declared income) |
| 4 | DigiLocker | Full scheme enrollment, credit-building, life simulations against verified documents. | + Document Assist, Crisis Intercept human handoff |

## How this is enforced in code

`backend/app/trust/ptp.py` is the single place that decides, given a user's stored trust level, which agents the orchestrator is even allowed to dispatch for a given turn. This is a hard gate, not a soft hint to the LLM — an agent that needs Level 3 data simply never runs for a Level 1 user, regardless of what the conversation is about. Raising your own trust level is always an explicit, user-initiated action (never inferred, never defaulted up).
