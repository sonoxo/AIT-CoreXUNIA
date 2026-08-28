"""Training-safe bridge from AIT mission data into XUNIA HOLO Forge.

The bridge emits normalized, provenance-carrying events. It does not authorize
or execute spacecraft commands and it does not change AIT operational behavior.
"""

from .envelope import BridgeEvent, build_event, verify_event
from .adapter import (
    ccsds_packet,
    command_definition,
    command_execution,
    event_record,
    sequence_step,
    telemetry_limit,
    telemetry_sample,
)
from .ndjson import dump_events, load_events

__all__ = [
    "BridgeEvent",
    "build_event",
    "verify_event",
    "telemetry_sample",
    "telemetry_limit",
    "command_definition",
    "command_execution",
    "sequence_step",
    "event_record",
    "ccsds_packet",
    "dump_events",
    "load_events",
]
