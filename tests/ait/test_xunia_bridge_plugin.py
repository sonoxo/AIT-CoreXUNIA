from ait.xunia_bridge.plugin import AitTelemetryProjector


class FakeFieldDefinition:
    units = "C"


class FakePacketDefinition:
    fieldmap = {"TEMP_C": FakeFieldDefinition()}


class FakePacket:
    _defn = FakePacketDefinition()

    def _getattr(self, field_name):
        assert field_name == "TEMP_C"
        return 121.0


class FakeLimitDefinition:
    def error(self, value):
        return value > 120

    def warn(self, value):
        return value > 100


def test_projector_emits_sample_and_limit_with_component_binding():
    projector = AitTelemetryProjector(
        "REPRESENTATIVE-HX100",
        include_fields=["PUMP_HEALTH.TEMP_C"],
        field_map={
            "PUMP_HEALTH.TEMP_C": {
                "componentId": "pump-body",
                "safetyNote": "Stop the representative pump before service.",
            }
        },
    )

    events = projector.project_packet(
        "PUMP_HEALTH",
        FakePacket(),
        {"TEMP_C": FakeLimitDefinition()},
        observed_at="2026-08-28T20:00:00+00:00",
    )

    assert [event.event_type for event in events] == [
        "TELEMETRY_SAMPLE",
        "TELEMETRY_LIMIT",
    ]
    assert events[0].payload["componentId"] == "pump-body"
    assert events[0].payload["units"] == "C"
    assert events[1].payload["limit"] == "ERROR_LIMIT"
    assert events[1].payload["severity"] == "ERROR"
    assert events[1].payload["safetyNote"] == (
        "Stop the representative pump before service."
    )
    assert all(event.marking == "NON_PROPRIETARY" for event in events)
