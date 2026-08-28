"""Read-only AIT server plugin for the XUNIA HOLO training bridge.

The plugin mirrors decoded telemetry into the XUNIA bridge envelope. It never
publishes or executes AIT commands. Local NDJSON spooling is the reliability
path; optional HTTP forwarding is best-effort and cannot interrupt AIT packet
processing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

import gevent
import requests
from gevent.queue import Full, Queue

from ait.core import limits, log, tlm
from ait.core.server.plugin import Plugin

from .adapter import telemetry_limit, telemetry_sample
from .envelope import BridgeEvent, build_event


class AitTelemetryProjector:
    """Project decoded AIT packets into training-safe bridge events."""

    def __init__(
        self,
        mission: str,
        *,
        marking: str = "NON_PROPRIETARY",
        include_fields: Optional[Iterable[str]] = None,
        field_map: Optional[Mapping[str, Mapping[str, object]]] = None,
    ):
        if not mission.strip():
            raise ValueError("mission is required")
        if marking not in {"PUBLIC", "NON_PROPRIETARY"}:
            raise ValueError("marking must be PUBLIC or NON_PROPRIETARY")
        self.mission = mission
        self.marking = marking
        self.include_fields = set(include_fields or [])
        self.field_map = dict(field_map or {})

    def _included(self, key: str) -> bool:
        return not self.include_fields or key in self.include_fields

    def project_packet(
        self,
        packet_name: str,
        decoded: Any,
        limit_definitions: Mapping[str, Any],
        *,
        observed_at: Optional[str] = None,
    ) -> list[BridgeEvent]:
        events = []
        for field_name, field_definition in decoded._defn.fieldmap.items():
            key = "%s.%s" % (packet_name, field_name)
            if not self._included(key):
                continue

            value = decoded._getattr(field_name)
            mapping = dict(self.field_map.get(key, {}))
            component_id = mapping.get("componentId")
            if not isinstance(component_id, str):
                component_id = None
            safety_note = mapping.get("safetyNote")
            if not isinstance(safety_note, str):
                safety_note = None
            provenance = {
                "aitPacket": packet_name,
                "aitField": field_name,
                "bridgeMode": "READ_ONLY_TRAINING_EXPORT",
            }
            sample = telemetry_sample(
                mission=self.mission,
                packet=packet_name,
                field=field_name,
                value=value,
                units=getattr(field_definition, "units", None),
                component_id=component_id,
                observed_at=observed_at,
                provenance=provenance,
            )
            if self.marking == "PUBLIC":
                sample = _with_marking(sample, "PUBLIC")
            events.append(sample)

            limit_definition = limit_definitions.get(field_name)
            if limit_definition is None:
                continue
            severity = None
            limit_name = None
            if limit_definition.error(value):
                severity = "ERROR"
                limit_name = "ERROR_LIMIT"
            elif limit_definition.warn(value):
                severity = "WARNING"
                limit_name = "WARNING_LIMIT"
            if severity is None or limit_name is None:
                continue

            limit_event = telemetry_limit(
                mission=self.mission,
                packet=packet_name,
                field=field_name,
                value=value,
                limit=limit_name,
                severity=severity,
                component_id=component_id,
                safety_note=safety_note,
                observed_at=observed_at,
                provenance=provenance,
            )
            if self.marking == "PUBLIC":
                limit_event = _with_marking(limit_event, "PUBLIC")
            events.append(limit_event)
        return events


def _with_marking(event: BridgeEvent, marking: str) -> BridgeEvent:
    return build_event(
        event.event_type,
        mission=event.mission,
        source=event.source,
        payload=event.payload,
        observed_at=event.observed_at,
        marking=marking,
        provenance=event.provenance,
    )


class XuniaHoloBridgePlugin(Plugin):
    """Mirror AIT telemetry into the XUNIA HOLO bridge without command authority."""

    def __init__(
        self,
        inputs,
        outputs,
        mission,
        spool_path="xunia-holo-bridge.ndjson",
        endpoint=None,
        batch_size=50,
        queue_size=1000,
        http_timeout=1.0,
        marking="NON_PROPRIETARY",
        include_fields=None,
        field_map=None,
        **kwargs,
    ):
        super(XuniaHoloBridgePlugin, self).__init__(inputs, outputs, **kwargs)
        self.projector = AitTelemetryProjector(
            mission,
            marking=marking,
            include_fields=include_fields,
            field_map=field_map,
        )
        self.spool_path = Path(spool_path)
        self.spool_path.parent.mkdir(parents=True, exist_ok=True)
        self.endpoint = endpoint
        self.batch_size = max(1, int(batch_size))
        self.http_timeout = max(0.1, float(http_timeout))
        self.queue = Queue(maxsize=max(1, int(queue_size)))
        self.packet_dict: Dict[int, Any] = {
            definition.uid: definition for _key, definition in tlm.getDefaultDict().items()
        }
        self.limit_dict: Dict[str, Dict[str, Any]] = {}
        for key, definition in limits.getDefaultDict().items():
            packet_name, field_name = key.split(".", 1)
            self.limit_dict.setdefault(packet_name, {})[field_name] = definition
        if self.endpoint:
            gevent.spawn(self._forward_worker)
        log.info("Starting read-only XUNIA HOLO bridge telemetry export")

    def process(self, input_data, topic=None, **kwargs):
        """Decode one telemetry packet, spool bridge events, and queue HTTP forwarding."""
        try:
            packet_id, packet_data = int(input_data[0]), input_data[1]
            packet_definition = self.packet_dict[packet_id]
            decoded = tlm.Packet(packet_definition, data=bytearray(packet_data))
            events = self.projector.project_packet(
                packet_definition.name,
                decoded,
                self.limit_dict.get(packet_definition.name, {}),
            )
            self._spool(events)
            if self.endpoint and events:
                try:
                    self.queue.put_nowait(events)
                except Full:
                    log.warn(
                        "XUNIA HOLO bridge HTTP queue full; events remain preserved in NDJSON spool"
                    )
        except Exception as error:
            log.error("XUNIA HOLO bridge export skipped packet: {}".format(error))

    def _spool(self, events: Iterable[BridgeEvent]):
        with self.spool_path.open("a", encoding="utf-8") as stream:
            for event in events:
                stream.write(json.dumps(event.to_dict(), sort_keys=True))
                stream.write("\n")

    def _forward_worker(self):
        pending = []
        while True:
            events = self.queue.get()
            pending.extend(events)
            while len(pending) < self.batch_size and not self.queue.empty():
                pending.extend(self.queue.get_nowait())
            batch = pending[: self.batch_size]
            del pending[: self.batch_size]
            try:
                response = requests.post(
                    self.endpoint,
                    json={"events": [event.to_dict() for event in batch]},
                    timeout=self.http_timeout,
                )
                response.raise_for_status()
            except Exception as error:
                log.warn(
                    "XUNIA HOLO bridge HTTP forwarding failed; NDJSON spool remains authoritative: {}".format(
                        error
                    )
                )
