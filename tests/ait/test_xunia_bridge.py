from pathlib import Path

from ait.xunia_bridge import (
    command_execution,
    dump_events,
    load_events,
    sequence_step,
    telemetry_limit,
    telemetry_sample,
    verify_event,
)


def test_bridge_events_are_integrity_verified(tmp_path: Path):
    events = [
        telemetry_sample(
            mission="REPRESENTATIVE-HX100",
            packet="PUMP_HEALTH",
            field="TEMP_C",
            value=72.5,
            units="C",
            component_id="pump-body",
            observed_at="2026-08-28T20:00:00+00:00",
            provenance={
                "dictionary": "representative-tlm.yaml",
                "sourceClass": "TEST_FIXTURE",
            },
        ),
        telemetry_limit(
            mission="REPRESENTATIVE-HX100",
            packet="PUMP_HEALTH",
            field="TEMP_C",
            value=121.0,
            limit="RED_HIGH",
            severity="CRITICAL",
            component_id="pump-body",
            safety_note="Stop the representative pump and inspect thermal state.",
            observed_at="2026-08-28T20:00:05+00:00",
        ),
        command_execution(
            mission="REPRESENTATIVE-HX100",
            name="ISOLATE_PUMP",
            status="SIMULATED",
            component_id="isolation-valve",
            expected_state="closed",
            training_instruction="Close the isolation valve before servicing the pump.",
            observed_at="2026-08-28T20:00:10+00:00",
        ),
        sequence_step(
            mission="REPRESENTATIVE-HX100",
            sequence="PUMP-SAFE-SERVICE",
            ordinal=1,
            command="ISOLATE_PUMP",
            instruction="Close the isolation valve before servicing the pump.",
            component_id="isolation-valve",
            expected_state="closed",
            observed_at="2026-08-28T20:00:15+00:00",
        ),
    ]

    assert all(verify_event(event.to_dict()) for event in events)

    tampered = events[0].to_dict()
    tampered["payload"]["value"] = 999
    assert not verify_event(tampered)

    output = tmp_path / "bridge.ndjson"
    assert dump_events(output, events) == 4
    replay = load_events(output)
    assert [event["event_type"] for event in replay] == [
        "TELEMETRY_SAMPLE",
        "TELEMETRY_LIMIT",
        "COMMAND_EXECUTION",
        "SEQUENCE_STEP",
    ]
