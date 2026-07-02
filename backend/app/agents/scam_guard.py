from __future__ import annotations

import json
import re
from pathlib import Path

import asyncpg

from app.agents.base import Observation, TurnContext
from app.db import cfti
from app.llm.client import LLMClient

_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "data" / "rbi_registry.json"
_REGISTERED = {
    name.lower() for name in json.loads(_REGISTRY_PATH.read_text())["registered_lenders"]
}

_EXTRACTION_SYSTEM = (
    "You extract the name of a LOAN APP or LENDER a message is asking about the safety, "
    "legitimacy, or trustworthiness of - the kind of thing you'd check against a scam registry. "
    "Reply with strict JSON: {\"entity\": \"<name or null>\"}. "
    "entity MUST be null if: no specific lender/app is named, OR the message is about a "
    "government scheme, tax section/deduction (e.g. 'Section 80DD'), benefit program, or "
    "anything that is not a lender someone could borrow money from."
)


class ScamGuardAgent:
    name = "scam_guard"
    min_trust_level = 0

    def __init__(self, llm: LLMClient, pg_pool: asyncpg.Pool) -> None:
        self._llm = llm
        self._pool = pg_pool

    async def run(self, ctx: TurnContext) -> Observation | None:
        entity = await self._extract_entity(ctx.message)
        if entity is None:
            return None

        is_registered = entity.lower() in _REGISTERED
        report_count = await cfti.count_reports(self._pool, entity, area=None)

        if is_registered:
            return Observation(
                agent=self.name,
                headline=f"{entity} is RBI-registered.",
                details={"entity": entity, "registered": True, "report_count": report_count},
                severity="info",
            )

        # unregistered - log it so the next user who mentions it benefits too (CFTI)
        await cfti.report_threat(self._pool, entity, area=None)

        return Observation(
            agent=self.name,
            headline=f"{entity} is NOT in the RBI registry.",
            details={
                "entity": entity,
                "registered": False,
                "report_count": report_count,
                "interest_rate_estimate": "40-120% annually (typical of unregistered lenders)",
            },
            severity="critical",
            suggested_actions=["See registered loan options", "Find a scheme I qualify for"],
        )

    async def _extract_entity(self, message: str) -> str | None:
        # cheap regex first so demo latency doesn't depend on an LLM round-trip
        # every single turn - fall back to the LLM only when that fails.
        m = re.search(r"\b([A-Z][a-zA-Z]*(?:24|Cash|Loan|Credit|Pay)[A-Za-z0-9]*)\b", message)
        if m:
            return m.group(1)

        try:
            result = await self._llm.complete_json(
                f"Message: {message!r}", system=_EXTRACTION_SYSTEM
            )
            return result.get("entity")
        except Exception:
            return None
