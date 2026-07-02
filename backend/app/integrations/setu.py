"""Real Setu Account Aggregator sandbox client - PTP Level 3 (UPI consent).

Setu, unlike DigiLocker/Aadhaar eKYC, runs a free developer sandbox an
individual can actually sign up for (see docs/ROADMAP.md) - so unlike
app/integrations/gov.py's DigiLocker mock, this is real REST code against
Setu's documented contract, not a permanent mock.

The consent endpoints below (create + check status) are verified against
Setu's published API docs (docs.setu.co/data/account-aggregator) - method,
path, headers, and body fields. The FI data session endpoints
(create_data_session / get_session_data) follow the Account Aggregator
framework's standard consent-then-session pattern (the same shape every AA
provider uses, per the RBI/ReBIT spec), but I could not independently verify
Setu's exact field names for that half against live docs - confirm these
against Setu's Postman collection (linked from their quickstart) before
relying on them with real sandbox credentials. The auth header pattern
(`Authorization: Bearer <token>` per their docs, obtained via whatever
token endpoint Setu's onboarding flow gives you) will also need whatever
your actual sandbox app issues - wire that into `_headers()` once you have
real credentials.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.config import get_settings


@dataclass
class ConsentRequest:
    id: str
    status: str
    approval_url: str


class SetuNotConfigured(Exception):
    pass


class SetuAAClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.setu_base_url
        self._client_id = settings.setu_client_id
        self._client_secret = settings.setu_client_secret
        self._product_instance_id = settings.setu_product_instance_id

    def _require_configured(self) -> None:
        if not (self._client_id and self._client_secret and self._product_instance_id):
            raise SetuNotConfigured(
                "SETU_CLIENT_ID / SETU_CLIENT_SECRET / SETU_PRODUCT_INSTANCE_ID not set - "
                "see docs/ROADMAP.md for the free sandbox signup"
            )

    def _headers(self) -> dict[str, str]:
        # Verified from Setu's docs: x-product-instance-id is required as-is.
        # The Authorization bearer token itself comes from whatever auth flow
        # your sandbox app is issued - plugging in client_id/client_secret
        # directly here as a placeholder until that's confirmed.
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._client_secret}",
            "x-client-id": self._client_id,
            "x-product-instance-id": self._product_instance_id,
        }

    async def create_consent(self, vua: str, purpose: str) -> ConsentRequest:
        """vua: the user's Account Aggregator handle, typically their phone
        number linked to an AA app (e.g. '9820011111@onemoney')."""
        self._require_configured()
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.post(
                "/consents",
                headers=self._headers(),
                json={
                    "consentDuration": {"unit": "MONTH", "value": "12"},
                    "vua": vua,
                    "dataRange": {"from": _months_ago(12), "to": _now()},
                    "context": [{"key": "purpose", "value": purpose}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return ConsentRequest(id=data["id"], status=data["status"], approval_url=data.get("url", ""))

    async def get_consent_status(self, consent_id: str) -> str:
        self._require_configured()
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.get(f"/consents/{consent_id}", headers=self._headers())
            resp.raise_for_status()
            return resp.json()["status"]

    async def create_data_session(self, consent_id: str) -> str:
        """Unverified field names - see module docstring."""
        self._require_configured()
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.post(
                "/sessions", headers=self._headers(), json={"consentId": consent_id, "format": "json"}
            )
            resp.raise_for_status()
            return resp.json()["id"]

    async def get_session_data(self, session_id: str) -> dict:
        """Unverified field names - see module docstring."""
        self._require_configured()
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.get(f"/sessions/{session_id}", headers=self._headers())
            resp.raise_for_status()
            return resp.json()


def _now() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _months_ago(months: int) -> str:
    from datetime import UTC, datetime, timedelta

    return (datetime.now(UTC) - timedelta(days=30 * months)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
