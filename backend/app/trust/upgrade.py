"""Turns a trust-level request into whatever PTP Level actually requires -
see docs/PTP.md. Levels 0-2 just need data already on the Twin (a name, an
income range); levels 3-4 route through the mocked GovIntegrations consent
flow before the level is granted. This is the one place that enforces "data
is earned, not demanded" - app/channels/chat.py never sets a trust level
directly.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.bft.service import BFTService
from app.integrations.gov import GovIntegrations


class TrustUpgradeError(Exception):
    pass


@dataclass
class TrustUpgradeResult:
    level: int
    detail: str


class TrustUpgradeService:
    def __init__(self, bft: BFTService, gov: GovIntegrations) -> None:
        self._bft = bft
        self._gov = gov

    async def raise_level(self, phone: str, target_level: int) -> TrustUpgradeResult:
        if target_level not in range(5):
            raise TrustUpgradeError("trust level must be between 0 and 4")

        snapshot = await self._bft.get_or_create_user(phone)
        if target_level <= snapshot.trust_level:
            raise TrustUpgradeError(
                f"already at trust level {snapshot.trust_level}, nothing to raise"
            )

        if target_level >= 1 and not snapshot.name:
            raise TrustUpgradeError("Level 1 needs a name on file first")

        if target_level >= 2 and not snapshot.income_samples:
            raise TrustUpgradeError("Level 2 needs at least one income sample first")

        if target_level >= 3:
            consent = await self._gov.request_upi_consent(phone)
            await self._gov.fetch_account_data(
                consent.consent_id, [s.amount for s in snapshot.income_samples]
            )
            await self._bft.set_income_verified(phone, True)

        if target_level >= 4:
            await self._gov.link_digilocker(phone)
            await self._bft.set_digilocker_linked(phone, True)

        await self._bft.set_trust_level(phone, target_level)
        return TrustUpgradeResult(
            level=target_level, detail=self._describe(target_level)
        )

    @staticmethod
    def _describe(level: int) -> str:
        return {
            0: "No data shared.",
            1: "Name on file - personalised scheme matching unlocked.",
            2: "Income range shared - cash-flow projections unlocked.",
            3: "UPI consent granted via Account Aggregator - income now verified, not self-declared.",
            4: "DigiLocker linked - full scheme enrollment and document-verified flows unlocked.",
        }[level]
