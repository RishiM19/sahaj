"""Event backbone - Redpanda (Kafka-API-compatible), replacing the
in-process asyncio flow Phase 1 shipped with. See docs/ARCHITECTURE.md for
why Redpanda over raw Kafka + Zookeeper + Confluent Schema Registry.

One topic (`sahaj.events`) carries the event types the exec summary's
Layer 2 diagram named - `bft.updated`, `scam.alert`, `query.resolved` - with
a `type` field distinguishing them, rather than provisioning five separate
topics for a system with no per-topic retention/ACL needs yet.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from aiokafka import AIOKafkaProducer

from app.config import get_settings

_logger = logging.getLogger(__name__)
TOPIC = "sahaj.events"


class EventBus:
    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None

    async def _get_producer(self) -> AIOKafkaProducer:
        if self._producer is None:
            producer = AIOKafkaProducer(
                bootstrap_servers=get_settings().kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode(),
            )
            await producer.start()
            self._producer = producer
        return self._producer

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        try:
            producer = await self._get_producer()
            await producer.send_and_wait(
                TOPIC, {"type": event_type, "at": datetime.now(UTC).isoformat(), **payload}
            )
        except Exception:
            # the event backbone is an observability/analytics side-channel -
            # a turn must never fail just because Redpanda is unreachable
            _logger.exception("failed to publish event %r", event_type)

    async def close(self) -> None:
        if self._producer is not None:
            await self._producer.stop()


_shared: EventBus | None = None


def get_event_bus() -> EventBus:
    global _shared
    if _shared is None:
        _shared = EventBus()
    return _shared
