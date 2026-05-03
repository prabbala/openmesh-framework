"""Property tests for MeshHealthEvent JSON serialization and adapter interface.

Feature: openmesh-framework, Property 2: MeshHealthEvent JSON Round-Trip
Feature: openmesh-framework, Property 18: Invalid Serialization Error Reporting (JSON)
Feature: openmesh-framework, Property 19: Adapter Interface Contract
Validates: Requirements 3.2, 3.3, 3.4, 3.5, 15.1, 15.2, 15.3, 15.4, 15.5
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from packages.observability.interface.adapter import (
    AdapterMetadata,
    HealthCheck as HCheck,
    HealthStatus,
    MeshHealthEvent,
    Metric,
    ObservabilityAdapterInterface,
    PanelDefinition,
    Severity,
)
from packages.observability.interface.events import (
    EventSerializationError,
    VALID_SEVERITIES,
    deserialize_from_json,
    serialize_to_json,
)

_prop_settings = settings(
    max_examples=100, suppress_health_check=[HealthCheck.too_slow]
)

# ── Strategies ───────────────────────────────────────────────────────

_severity_strategy = st.sampled_from(list(Severity))

_id_strategy = st.from_regex(r"[a-z][a-z0-9\-]{0,19}", fullmatch=True)

_text_strategy = st.from_regex(r"[A-Za-z][A-Za-z0-9 ]{0,49}", fullmatch=True)

# Timestamps: aware datetimes in a reasonable range
_timestamp_strategy = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2030, 12, 31),
    timezones=st.just(timezone.utc),
)


@st.composite
def mesh_health_event_strategy(draw):
    """Generate valid MeshHealthEvent objects."""
    return MeshHealthEvent(
        entity_id=draw(_id_strategy),
        domain=draw(_id_strategy),
        severity=draw(_severity_strategy),
        message=draw(_text_strategy),
        timestamp=draw(_timestamp_strategy),
        metadata=draw(st.just({})),
    )


# ── Property 2: MeshHealthEvent JSON Round-Trip ─────────────────────


class TestMeshHealthEventJSONRoundTrip:
    """Property 2: For any valid MeshHealthEvent, serializing to JSON
    then deserializing SHALL produce an equivalent object.
    """

    # Feature: openmesh-framework, Property 2: MeshHealthEvent JSON Round-Trip
    @given(event=mesh_health_event_strategy())
    @_prop_settings
    def test_json_round_trip(self, event: MeshHealthEvent):
        """Serialize → deserialize produces equivalent MeshHealthEvent."""
        json_str = serialize_to_json(event)
        result = deserialize_from_json(json_str)

        assert result.entity_id == event.entity_id
        assert result.domain == event.domain
        assert result.severity == event.severity
        assert result.message == event.message
        assert result.timestamp == event.timestamp

    # Feature: openmesh-framework, Property 2: MeshHealthEvent JSON Round-Trip
    @given(event=mesh_health_event_strategy())
    @_prop_settings
    def test_json_round_trip_with_metadata(self, event: MeshHealthEvent):
        """Round-trip preserves metadata when present."""
        event.metadata = {"source": "test", "count": 42}
        json_str = serialize_to_json(event)
        result = deserialize_from_json(json_str)

        assert result.metadata == event.metadata

    # Feature: openmesh-framework, Property 2: MeshHealthEvent JSON Round-Trip
    @given(event=mesh_health_event_strategy())
    @_prop_settings
    def test_serialized_json_is_valid_string(self, event: MeshHealthEvent):
        """Serialized output is a non-empty JSON string."""
        json_str = serialize_to_json(event)
        assert isinstance(json_str, str)
        assert len(json_str) > 0
        assert '"entity_id"' in json_str
        assert '"severity"' in json_str


# ── Property 18: Invalid Serialization Error Reporting (JSON) ───────


class TestInvalidJSONErrorReporting:
    """Property 18: Invalid JSON SHALL return descriptive validation errors
    listing all invalid or missing fields. Severity not in
    {Critical, Warning, Info} SHALL be rejected.
    """

    # Feature: openmesh-framework, Property 18: Invalid Serialization Error Reporting (JSON)
    def test_completely_empty_json(self):
        """Empty string raises EventSerializationError."""
        with pytest.raises(EventSerializationError) as exc_info:
            deserialize_from_json("")
        assert exc_info.value.field_errors

    # Feature: openmesh-framework, Property 18: Invalid Serialization Error Reporting (JSON)
    def test_json_with_no_required_fields(self):
        """JSON object with no required fields lists all missing fields."""
        with pytest.raises(EventSerializationError) as exc_info:
            deserialize_from_json('{"foo": "bar"}')

        error = exc_info.value
        missing_fields = {e["field"] for e in error.field_errors}
        assert "entity_id" in missing_fields
        assert "domain" in missing_fields
        assert "severity" in missing_fields
        assert "message" in missing_fields
        assert "timestamp" in missing_fields

    # Feature: openmesh-framework, Property 18: Invalid Serialization Error Reporting (JSON)
    @given(
        bad_severity=st.from_regex(r"[a-z]{1,15}", fullmatch=True).filter(
            lambda s: s not in VALID_SEVERITIES
        ),
    )
    @_prop_settings
    def test_invalid_severity_reported(self, bad_severity: str):
        """Invalid severity value is reported in field errors."""
        json_str = (
            '{"entity_id": "e1", "domain": "d1", '
            f'"severity": "{bad_severity}", '
            '"message": "test", "timestamp": "2025-01-01T00:00:00+00:00"}'
        )
        with pytest.raises(EventSerializationError) as exc_info:
            deserialize_from_json(json_str)

        error_fields = {e["field"] for e in exc_info.value.field_errors}
        assert "severity" in error_fields

    # Feature: openmesh-framework, Property 18: Invalid Serialization Error Reporting (JSON)
    def test_missing_multiple_fields_reports_all(self):
        """When multiple fields are missing, all are reported."""
        json_str = '{"entity_id": "e1"}'
        with pytest.raises(EventSerializationError) as exc_info:
            deserialize_from_json(json_str)

        error = exc_info.value
        missing_fields = {e["field"] for e in error.field_errors}
        assert "domain" in missing_fields
        assert "severity" in missing_fields
        assert "message" in missing_fields
        assert "timestamp" in missing_fields
        assert "entity_id" not in missing_fields

    # Feature: openmesh-framework, Property 18: Invalid Serialization Error Reporting (JSON)
    def test_malformed_json_syntax(self):
        """Malformed JSON raises EventSerializationError."""
        with pytest.raises(EventSerializationError) as exc_info:
            deserialize_from_json("{invalid json!!!")

        assert len(exc_info.value.field_errors) > 0

    # Feature: openmesh-framework, Property 18: Invalid Serialization Error Reporting (JSON)
    def test_non_object_json(self):
        """JSON array raises EventSerializationError."""
        with pytest.raises(EventSerializationError):
            deserialize_from_json('[1, 2, 3]')

    # Feature: openmesh-framework, Property 18: Invalid Serialization Error Reporting (JSON)
    def test_invalid_timestamp_format(self):
        """Non-ISO timestamp is reported in field errors."""
        json_str = (
            '{"entity_id": "e1", "domain": "d1", '
            '"severity": "Critical", "message": "test", '
            '"timestamp": "not-a-date"}'
        )
        with pytest.raises(EventSerializationError) as exc_info:
            deserialize_from_json(json_str)

        error_fields = {e["field"] for e in exc_info.value.field_errors}
        assert "timestamp" in error_fields


# ── Property 19: Adapter Interface Contract ─────────────────────────


class _ValidTestAdapter(ObservabilityAdapterInterface):
    """A minimal valid adapter for contract testing."""

    def get_health_checks(self):
        return [
            HCheck(name="cpu", status=HealthStatus.HEALTHY, detail="OK"),
            HCheck(name="mem", status=HealthStatus.DEGRADED, detail="High"),
        ]

    def get_metrics(self):
        return [
            Metric(
                metric_name="cpu_usage",
                value=45.2,
                unit="percent",
                timestamp=datetime.now(timezone.utc),
            ),
        ]

    def get_panel_definitions(self):
        return [
            PanelDefinition(
                title="CPU Panel",
                data_source_key="cpu_metrics",
                visualization_type="line_chart",
                required_role="operator",
            ),
        ]

    def get_adapter_metadata(self):
        return AdapterMetadata(
            name="test-adapter",
            version="1.0.0",
            supported_runtime_types=["server"],
            description="A test adapter",
        )


class TestAdapterInterfaceContract:
    """Property 19: Any adapter implementing ObservabilityAdapterInterface
    SHALL return correctly typed objects from each method.
    """

    def setup_method(self):
        self.adapter = _ValidTestAdapter()

    # Feature: openmesh-framework, Property 19: Adapter Interface Contract
    def test_get_health_checks_returns_health_check_objects(self):
        """get_health_checks returns List[HealthCheck] with name and status."""
        checks = self.adapter.get_health_checks()
        assert isinstance(checks, list)
        assert len(checks) > 0
        for check in checks:
            assert isinstance(check, HCheck)
            assert isinstance(check.name, str) and check.name
            assert isinstance(check.status, HealthStatus)

    # Feature: openmesh-framework, Property 19: Adapter Interface Contract
    def test_get_metrics_returns_metric_objects(self):
        """get_metrics returns List[Metric] with metric_name/value/unit/timestamp."""
        metrics = self.adapter.get_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        for metric in metrics:
            assert isinstance(metric, Metric)
            assert isinstance(metric.metric_name, str) and metric.metric_name
            assert isinstance(metric.value, (int, float))
            assert isinstance(metric.unit, str) and metric.unit
            assert isinstance(metric.timestamp, datetime)

    # Feature: openmesh-framework, Property 19: Adapter Interface Contract
    def test_get_panel_definitions_returns_panel_objects(self):
        """get_panel_definitions returns List[PanelDefinition] with required fields."""
        panels = self.adapter.get_panel_definitions()
        assert isinstance(panels, list)
        assert len(panels) > 0
        for panel in panels:
            assert isinstance(panel, PanelDefinition)
            assert isinstance(panel.title, str) and panel.title
            assert isinstance(panel.data_source_key, str) and panel.data_source_key
            assert isinstance(panel.visualization_type, str)
            assert isinstance(panel.required_role, str) and panel.required_role

    # Feature: openmesh-framework, Property 19: Adapter Interface Contract
    def test_get_adapter_metadata_returns_metadata(self):
        """get_adapter_metadata returns AdapterMetadata with all fields."""
        meta = self.adapter.get_adapter_metadata()
        assert isinstance(meta, AdapterMetadata)
        assert isinstance(meta.name, str) and meta.name
        assert isinstance(meta.version, str) and meta.version
        assert isinstance(meta.supported_runtime_types, list)
        assert len(meta.supported_runtime_types) > 0
        assert isinstance(meta.description, str) and meta.description

    # Feature: openmesh-framework, Property 19: Adapter Interface Contract
    def test_adapter_is_subclass_of_interface(self):
        """Valid adapter is a subclass of ObservabilityAdapterInterface."""
        assert isinstance(self.adapter, ObservabilityAdapterInterface)

    # Feature: openmesh-framework, Property 19: Adapter Interface Contract
    def test_cannot_instantiate_abstract_interface(self):
        """ObservabilityAdapterInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ObservabilityAdapterInterface()  # type: ignore[abstract]

    # Feature: openmesh-framework, Property 19: Adapter Interface Contract
    def test_incomplete_adapter_cannot_instantiate(self):
        """An adapter missing required methods cannot be instantiated."""

        class IncompleteAdapter(ObservabilityAdapterInterface):
            def get_health_checks(self):
                return []
            # Missing: get_metrics, get_panel_definitions, get_adapter_metadata

        with pytest.raises(TypeError):
            IncompleteAdapter()  # type: ignore[abstract]
