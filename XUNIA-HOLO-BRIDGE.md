# XUNIA HOLO Bridge

This repository exposes an optional, training-safe adapter for XUNIA HOLO Forge.

## Boundary

AIT remains the mission-data / GDS side. HOLO Forge remains the training-content side. The bridge does **not** authorize, schedule, or transmit spacecraft commands. It only emits normalized events suitable for simulation, replay, training, and evidence workflows.

```text
AIT telemetry / limits / commands / sequences / EVRs / CCSDS metadata
        |
        v
ait.xunia_bridge
        |
        v
xunia.ait.bridge/1.0 integrity + provenance envelope
        |
        v
NDJSON / HTTPS payload
        |
        v
XUNIA AIT Bridge -> HOLO Forge scenario graph -> human review -> runtime export
```

## Event classes

- `TELEMETRY_SAMPLE`
- `TELEMETRY_LIMIT`
- `COMMAND_DEFINITION`
- `COMMAND_EXECUTION`
- `SEQUENCE_STEP`
- `EVENT_RECORD`
- `CCSDS_PACKET`

Each event includes a deterministic SHA-256 integrity value, mission/source identity, observation time, marking, payload, and provenance.

## Safety / truth boundary

1. Bridge output is data, not command authority.
2. Training exports are limited to PUBLIC or NON_PROPRIETARY representative material unless a later authorized environment explicitly expands handling.
3. Integrity verification detects accidental/tampered payload changes; it is not a digital signature or identity proof.
4. Operational command transmission is outside the HOLO bridge.
5. Human review remains mandatory before HOLO marks generated training content approved.

## Example

```python
from ait.xunia_bridge import telemetry_sample, sequence_step

sample = telemetry_sample(
    mission="REPRESENTATIVE-HX100",
    packet="PUMP_HEALTH",
    field="TEMP_C",
    value=72.5,
    units="C",
    component_id="pump-body",
)

step = sequence_step(
    mission="REPRESENTATIVE-HX100",
    sequence="PUMP-SAFE-SERVICE",
    ordinal=1,
    command="ISOLATE_PUMP",
    instruction="Close the isolation valve before servicing the pump.",
    component_id="isolation-valve",
    expected_state="closed",
)
```
