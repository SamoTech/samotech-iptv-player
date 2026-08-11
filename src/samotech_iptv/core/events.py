"""Domain event base types.

All domain events inherit from ``DomainEvent``.  The application layer
publishes events; the infrastructure layer (message bus / callbacks)
subscribes to them.  Core defines only the contract — no dispatch logic.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import ClassVar

__all__ = ["DomainEvent", "EventId"]

#: Type alias for event identifiers.
EventId = str


@dataclass(frozen=True)
class DomainEvent:
    """Immutable base for all domain events.

    Subclass and add domain-specific fields::

        @dataclass(frozen=True)
        class ChannelSelected(DomainEvent):
            channel_id: str
    """

    event_name: ClassVar[str] = "DomainEvent"

    event_id: EventId = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
