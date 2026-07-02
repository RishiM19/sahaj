"""Mocked government/regulated-partner integrations - PTP Levels 3 (UPI
consent via Account Aggregator) and 4 (DigiLocker).

Both real integrations need credentials an individual project can't get on
its own: Setu's Account Aggregator SDK needs a registered FIU (financial
information user) entity, and DigiLocker needs partner registration (see
docs/ARCHITECTURE.md, "What changed from the original design"). Setu does
run a free developer sandbox, unlike DigiLocker/Aadhaar eKYC, which makes
level 3 realistic to wire up for real later (tracked as a separate issue) -
level 4 stays mocked until SAHAJ has an institutional backer.

This module is the single place that would change when either integration
goes from mocked to real - nothing in app/trust/upgrade.py or the agents
should need to know the difference.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class ConsentResult:
    consent_id: str
    status: str  # "ACTIVE" - mirrors the Setu AA SDK's ConsentStatus values
    granted_at: str


@dataclass
class VerifiedAccountData:
    consent_id: str
    weekly_income_samples: list[float]
    fetched_at: str


@dataclass
class DigiLockerLink:
    link_id: str
    documents: list[str] = field(default_factory=list)
    linked_at: str = ""


class GovIntegrations:
    """Mock implementation. A real one would wrap the Setu AA SDK and the
    DigiLocker API behind these same three methods."""

    async def request_upi_consent(self, phone: str) -> ConsentResult:
        return ConsentResult(
            consent_id=f"mock-consent-{uuid.uuid4().hex[:12]}",
            status="ACTIVE",
            granted_at=datetime.now(UTC).isoformat(),
        )

    async def fetch_account_data(
        self, consent_id: str, declared_income_samples: list[float]
    ) -> VerifiedAccountData:
        # a real Account Aggregator pull would return actual bank transaction
        # data; the mock confirms the user's self-declared income instead of
        # inventing different numbers, so downstream agents see "verified"
        # data that's still consistent with what's already on the BFT
        return VerifiedAccountData(
            consent_id=consent_id,
            weekly_income_samples=list(declared_income_samples),
            fetched_at=datetime.now(UTC).isoformat(),
        )

    async def link_digilocker(self, phone: str) -> DigiLockerLink:
        return DigiLockerLink(
            link_id=f"mock-digilocker-{uuid.uuid4().hex[:12]}",
            documents=["Aadhaar", "PAN"],
            linked_at=datetime.now(UTC).isoformat(),
        )


_shared: GovIntegrations | None = None


def get_gov_integrations() -> GovIntegrations:
    global _shared
    if _shared is None:
        _shared = GovIntegrations()
    return _shared
