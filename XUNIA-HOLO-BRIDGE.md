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
        +---- append-only NDJSON spool
        |
        +---- optional best-effort HTTPS forwarding
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

## Native read-only server plugin

`ait.xunia_bridge.plugin.XuniaHoloBridgePlugin` can subscribe to an AIT telemetry stream after a PacketHandler has annotated packets with their packet UID. The plugin decodes the packet using the existing AIT telemetry dictionary, projects selected fields into bridge events, detects configured AIT limit violations, writes every projected event to an append-only NDJSON spool, and can optionally batch-forward the same events to XUNIA.

The local spool is the reliability/audit path. HTTP forwarding is optional and best-effort. An HTTP failure or full forwarding queue does not interrupt packet processing; events already written to the spool remain available for later replay.

Example AIT server configuration:

```yaml
server:
  plugins:
    - plugin:
        name: ait.xunia_bridge.plugin.XuniaHoloBridgePlugin
        inputs:
          - telem_stream
        outputs: []
        mission: REPRESENTATIVE-HX100
        marking: NON_PROPRIETARY
        spool_path: ./data/xunia-holo-bridge.ndjson
        endpoint: http://127.0.0.1:3000/api/holoforge/ait
        batch_size: 50
        queue_size: 1000
        http_timeout: 1.0
        include_fields:
          - PUMP_HEALTH.TEMP_C
          - PUMP_HEALTH.PRESSURE_KPA
        field_map:
          PUMP_HEALTH.TEMP_C:
            componentId: pump-body
            safetyNote: Stop the representative pump before service.
          PUMP_HEALTH.PRESSURE_KPA:
            componentId: pump-body
```

For disconnected or benchmark operation, omit `endpoint`; the plugin will remain spool-only.

## Safety / truth boundary

1. Bridge output is data, not command authority.
2. Training exports are limited to PUBLIC or NON_PROPRIETARY representative material unless a later authorized environment explicitly expands handling.
3. Integrity verification detects accidental/tampered payload changes; it is not a digital signature or identity proof.
4. Operational command transmission is outside the HOLO bridge.
5. Human review remains mandatory before HOLO marks generated training content approved.
6. The native plugin is telemetry-read-only; it subscribes to inbound telemetry and exposes no AIT command publication API.
7. Authentication, TLS trust, network segmentation, authorization, and mission-specific configuration control must be supplied by the deployment environment before non-representative integration.

## SDK example

```python
from ait.xunia_bridge import sequence_step, telemetry_sample

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
