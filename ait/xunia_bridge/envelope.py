"""Canonical event envelope used by the XUNIA HOLO bridge."""

from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from hashlib import sha256
from typing import Any
from typing import Dict
from typing import Mapping
from typing import Optional


EVENT_TYPES = {
    "TELEMETRY_SAMPLE",
    "TELEMETRY_LIMIT",
    "COMMAND_DEFINITION",
    "COMMAND_EXECUTION",
    "SEQUENCE_STEP",
    "EVENT_RECORD",
    "CCSDS_PACKET",
}


def _canonical(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(unsigned: Mapping[str, Any]) -> str:
    return sha256(_canonical(unsigned).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class BridgeEvent:
    schema_version: str
    event_id: str
    event_type: str
    observed_at: str
    mission: str
    source: str
    marking: str
    payload: Dict[str, Any]
    provenance: Dict[str, Any]
    integrity_sha256: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_event(
    event_type: str,
    *,
    mission: str,
    source: str,
    payload: Mapping[str, Any],
    observed_at: Optional[str] = None,
    marking: str = "NON_PROPRIETARY",
    provenance: Optional[Mapping[str, Any]] = None,
) -> BridgeEvent:
    if event_type not in EVENT_TYPES:
        raise ValueError("Unsupported XUNIA bridge event type: %s" % event_type)
    if not mission.strip() or not source.strip():
        raise ValueError("mission and source are required")
    if marking not in {"PUBLIC", "NON_PROPRIETARY"}:
        raise ValueError("Only PUBLIC/NON_PROPRIETARY bridge markings are supported")

    timestamp = observed_at or datetime.now(timezone.utc).isoformat()
    unsigned = {
        "schema_version": "xunia.ait.bridge/1.0",
        "event_type": event_type,
        "observed_at": timestamp,
        "mission": mission,
        "source": source,
        "marking": marking,
        "payload": dict(payload),
        "provenance": dict(provenance or {}),
    }
    digest = _digest(unsigned)
    return BridgeEvent(
        event_id="ait-%s" % digest[:20],
        integrity_sha256=digest,
        **unsigned,
    )


def verify_event(event: Mapping[str, Any]) -> bool:
    try:
        if event.get("schema_version") != "xunia.ait.bridge/1.0":
            return False
        if event.get("event_type") not in EVENT_TYPES:
            return False
        if event.get("marking") not in {"PUBLIC", "NON_PROPRIETARY"}:
            return False
        for field in ("observed_at", "mission", "source"):
            value = event.get(field)
            if not isinstance(value, str) or not value.strip():
                return False
        if not isinstance(event.get("payload"), Mapping):
            return False
        if not isinstance(event.get("provenance"), Mapping):
            return False
        unsigned = {
            "schema_version": event["schema_version"],
            "event_type": event["event_type"],
            "observed_at": event["observed_at"],
            "mission": event["mission"],
            "source": event["source"],
            "marking": event["marking"],
            "payload": event["payload"],
            "provenance": event["provenance"],
        }
        digest = _digest(unsigned)
        return (
            event.get("integrity_sha256") == digest
            and event.get("event_id") == "ait-%s" % digest[:20]
        )
    except (KeyError, TypeError, ValueError):
        return False
