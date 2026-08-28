"""Training-safe bridge from AIT mission data into XUNIA HOLO Forge.

The bridge emits normalized, provenance-carrying events. It does not authorize
or execute spacecraft commands and it does not change AIT operational behavior.
"""

from .adapter import ccsds_packet
from .adapter import command_definition
from .adapter import command_execution
from .adapter import event_record
from .adapter import sequence_step
from .adapter import telemetry_limit
from .adapter import telemetry_sample
from .envelope import BridgeEvent
from .envelope import build_event
from .envelope import verify_event
from .ndjson import dump_events
from .ndjson import load_events

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
