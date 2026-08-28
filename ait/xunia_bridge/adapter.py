"""Helpers for projecting AIT concepts into the XUNIA bridge envelope."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from .envelope import BridgeEvent, build_event


def _event(
    kind: str,
    *,
    mission: str,
    source: str,
    payload: Mapping[str, Any],
    observed_at: Optional[str] = None,
    provenance: Optional[Mapping[str, Any]] = None,
) -> BridgeEvent:
    return build_event(
        kind,
        mission=mission,
        source=source,
        payload=payload,
        observed_at=observed_at,
        provenance=provenance,
    )


def telemetry_sample(
    *,
    mission: str,
    packet: str,
    field: str,
    value: Any,
    units: Optional[str] = None,
    observed_at: Optional[str] = None,
    component_id: Optional[str] = None,
    provenance: Optional[Mapping[str, Any]] = None,
) -> BridgeEvent:
    return _event(
        "TELEMETRY_SAMPLE",
        mission=mission,
        source="ait.telemetry:%s.%s" % (packet, field),
        observed_at=observed_at,
        provenance=provenance,
        payload={
            "packet": packet,
            "field": field,
            "value": value,
            "units": units,
            "componentId": component_id,
        },
    )


def telemetry_limit(
    *,
    mission: str,
    packet: str,
    field: str,
    value: Any,
    limit: str,
    severity: str,
    observed_at: Optional[str] = None,
    component_id: Optional[str] = None,
    safety_note: Optional[str] = None,
    provenance: Optional[Mapping[str, Any]] = None,
) -> BridgeEvent:
    return _event(
        "TELEMETRY_LIMIT",
        mission=mission,
        source="ait.limits:%s.%s" % (packet, field),
        observed_at=observed_at,
        provenance=provenance,
        payload={
            "packet": packet,
            "field": field,
            "value": value,
            "limit": limit,
            "severity": severity,
            "componentId": component_id,
            "safetyNote": safety_note,
        },
    )


def command_definition(
    *,
    mission: str,
    name: str,
    opcode: int,
    subsystem: Optional[str] = None,
    description: Optional[str] = None,
    component_id: Optional[str] = None,
    expected_state: Optional[str] = None,
    provenance: Optional[Mapping[str, Any]] = None,
) -> BridgeEvent:
    return _event(
        "COMMAND_DEFINITION",
        mission=mission,
        source="ait.command-dictionary:%s" % name,
        provenance=provenance,
        payload={
            "name": name,
            "opcode": opcode,
            "subsystem": subsystem,
            "description": description,
            "componentId": component_id,
            "expectedState": expected_state,
        },
    )


def command_execution(
    *,
    mission: str,
    name: str,
    status: str,
    observed_at: Optional[str] = None,
    component_id: Optional[str] = None,
    expected_state: Optional[str] = None,
    training_instruction: Optional[str] = None,
    provenance: Optional[Mapping[str, Any]] = None,
) -> BridgeEvent:
    return _event(
        "COMMAND_EXECUTION",
        mission=mission,
        source="ait.command-history:%s" % name,
        observed_at=observed_at,
        provenance=provenance,
        payload={
            "name": name,
            "status": status,
            "componentId": component_id,
            "expectedState": expected_state,
            "trainingInstruction": training_instruction,
        },
    )


def sequence_step(
    *,
    mission: str,
    sequence: str,
    ordinal: int,
    command: str,
    instruction: str,
    component_id: str,
    expected_state: Optional[str] = None,
    safety_note: Optional[str] = None,
    observed_at: Optional[str] = None,
    provenance: Optional[Mapping[str, Any]] = None,
) -> BridgeEvent:
    return _event(
        "SEQUENCE_STEP",
        mission=mission,
        source="ait.sequence:%s" % sequence,
        observed_at=observed_at,
        provenance=provenance,
        payload={
            "sequence": sequence,
            "ordinal": ordinal,
            "command": command,
            "instruction": instruction,
            "componentId": component_id,
            "expectedState": expected_state,
            "safetyNote": safety_note,
        },
    )


def event_record(
    *,
    mission: str,
    name: str,
    message: str,
    severity: str = "INFO",
    observed_at: Optional[str] = None,
    component_id: Optional[str] = None,
    provenance: Optional[Mapping[str, Any]] = None,
) -> BridgeEvent:
    return _event(
        "EVENT_RECORD",
        mission=mission,
        source="ait.evr:%s" % name,
        observed_at=observed_at,
        provenance=provenance,
        payload={
            "name": name,
            "message": message,
            "severity": severity,
            "componentId": component_id,
        },
    )


def ccsds_packet(
    *,
    mission: str,
    apid: int,
    sequence_count: int,
    length: int,
    observed_at: Optional[str] = None,
    provenance: Optional[Mapping[str, Any]] = None,
) -> BridgeEvent:
    return _event(
        "CCSDS_PACKET",
        mission=mission,
        source="ait.ccsds:apid-%s" % apid,
        observed_at=observed_at,
        provenance=provenance,
        payload={"apid": apid, "sequenceCount": sequence_count, "length": length},
    )
