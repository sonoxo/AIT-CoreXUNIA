"""Replayable line-oriented transport for XUNIA bridge events."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable
from typing import List
from typing import Mapping
from typing import Union

from .envelope import BridgeEvent
from .envelope import verify_event

PathLike = Union[str, Path]


def dump_events(path: PathLike, events: Iterable[BridgeEvent]) -> int:
    destination = Path(path)
    count = 0
    with destination.open("w", encoding="utf-8") as stream:
        for event in events:
            stream.write(json.dumps(event.to_dict(), sort_keys=True))
            stream.write("\n")
            count += 1
    return count


def load_events(path: PathLike, *, verify: bool = True) -> List[Mapping[str, object]]:
    source = Path(path)
    events: List[Mapping[str, object]] = []
    with source.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            event = json.loads(line)
            if verify and not verify_event(event):
                raise ValueError("Invalid XUNIA bridge event on line %s" % line_number)
            events.append(event)
    return events
