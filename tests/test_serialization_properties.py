"""Property tests for DomainRegistration YAML serialization.

Feature: openmesh-framework, Property 1: DomainRegistration YAML Round-Trip
Feature: openmesh-framework, Property 18: Invalid Serialization Error Reporting (YAML)
Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from packages.core.domain_registry.registration import VALID_RUNTIME_TYPES
from packages.core.domain_registry.serialization import (
    SerializationError,
    deserialize_from_yaml,
    serialize_to_yaml,
)
from tests.strategies import domain_registration_strategy

_prop_settings = settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])


# ── Property 1: DomainRegistration YAML Round-Trip ──────────────────


class TestDomainRegistrationYAMLRoundTrip:
    """Property 1: For any valid DomainRegistration, serializing to YAML
    then deserializing SHALL produce an equivalent object.
    """

    # Feature: openmesh-framework, Property 1: DomainRegistration YAML Round-Trip
    @given(reg=domain_registration_strategy())
    @_prop_settings
    def test_yaml_round_trip(self, reg):
        """Serialize → deserialize produces equivalent DomainRegistration."""
        yaml_str = serialize_to_yaml(reg)
        result = deserialize_from_yaml(yaml_str)

        assert result.domain_id == reg.domain_id
        assert result.runtime_type == reg.runtime_type
        assert result.observability_adapter == reg.observability_adapter
        assert result.roles == reg.roles
        assert result.tabs == reg.tabs
        assert result.entity_id == reg.entity_id
        assert result.lob_id == reg.lob_id

    # Feature: openmesh-framework, Property 1: DomainRegistration YAML Round-Trip
    @given(reg=domain_registration_strategy())
    @_prop_settings
    def test_yaml_round_trip_with_metadata(self, reg):
        """Round-trip preserves metadata when present."""
        reg.metadata = {"version": "1.0.0", "description": "test domain"}
        yaml_str = serialize_to_yaml(reg)
        result = deserialize_from_yaml(yaml_str)

        assert result.metadata == reg.metadata

    # Feature: openmesh-framework, Property 1: DomainRegistration YAML Round-Trip
    @given(reg=domain_registration_strategy())
    @_prop_settings
    def test_serialized_yaml_is_valid_string(self, reg):
        """Serialized output is a non-empty YAML string."""
        yaml_str = serialize_to_yaml(reg)
        assert isinstance(yaml_str, str)
        assert len(yaml_str) > 0
        assert "domain_id:" in yaml_str


# ── Property 18: Invalid Serialization Error Reporting (YAML) ───────


class TestInvalidYAMLErrorReporting:
    """Property 18: Invalid YAML SHALL return descriptive validation errors
    listing all invalid or missing fields.
    """

    # Feature: openmesh-framework, Property 18: Invalid Serialization Error Reporting (YAML)
    def test_completely_empty_yaml(self):
        """Empty YAML raises SerializationError."""
        with pytest.raises(SerializationError) as exc_info:
            deserialize_from_yaml("")
        assert exc_info.value.field_errors

    # Feature: openmesh-framework, Property 18: Invalid Serialization Error Reporting (YAML)
    def test_yaml_with_no_required_fields(self):
        """YAML with no required fields lists all missing fields."""
        with pytest.raises(SerializationError) as exc_info:
            deserialize_from_yaml("foo: bar\n")

        error = exc_info.value
        missing_fields = {e["field"] for e in error.field_errors}
        assert "domain_id" in missing_fields
        assert "runtime_type" in missing_fields
        assert "observability_adapter" in missing_fields
        assert "roles" in missing_fields
        assert "tabs" in missing_fields

    # Feature: openmesh-framework, Property 18: Invalid Serialization Error Reporting (YAML)
    @given(
        bad_runtime=st.from_regex(r"[a-z]{1,15}", fullmatch=True).filter(
            lambda s: s not in VALID_RUNTIME_TYPES
        ),
    )
    @_prop_settings
    def test_invalid_runtime_type_reported(self, bad_runtime):
        """Invalid runtime_type is reported in field errors."""
        yaml_str = (
            f"domain_id: test-domain\n"
            f"runtime_type: {bad_runtime}\n"
            f"observability_adapter: some.Adapter\n"
            f"roles:\n  - admin\n"
            f"tabs: []\n"
        )
        with pytest.raises(SerializationError) as exc_info:
            deserialize_from_yaml(yaml_str)

        error_fields = {e["field"] for e in exc_info.value.field_errors}
        assert "runtime_type" in error_fields

    # Feature: openmesh-framework, Property 18: Invalid Serialization Error Reporting (YAML)
    def test_missing_multiple_fields_reports_all(self):
        """When multiple fields are missing, all are reported."""
        yaml_str = "domain_id: test-domain\n"
        with pytest.raises(SerializationError) as exc_info:
            deserialize_from_yaml(yaml_str)

        error = exc_info.value
        missing_fields = {e["field"] for e in error.field_errors}
        assert "runtime_type" in missing_fields
        assert "observability_adapter" in missing_fields
        assert "roles" in missing_fields
        assert "tabs" in missing_fields
        assert "domain_id" not in missing_fields

    # Feature: openmesh-framework, Property 18: Invalid Serialization Error Reporting (YAML)
    def test_malformed_yaml_syntax(self):
        """Malformed YAML syntax raises SerializationError."""
        with pytest.raises(SerializationError) as exc_info:
            deserialize_from_yaml("{{{{invalid yaml::::")

        assert len(exc_info.value.field_errors) > 0

    # Feature: openmesh-framework, Property 18: Invalid Serialization Error Reporting (YAML)
    def test_empty_roles_list_rejected(self):
        """An empty roles list is rejected."""
        yaml_str = (
            "domain_id: test-domain\n"
            "runtime_type: server\n"
            "observability_adapter: some.Adapter\n"
            "roles: []\n"
            "tabs: []\n"
        )
        with pytest.raises(SerializationError) as exc_info:
            deserialize_from_yaml(yaml_str)

        error_fields = {e["field"] for e in exc_info.value.field_errors}
        assert "roles" in error_fields

    # Feature: openmesh-framework, Property 18: Invalid Serialization Error Reporting (YAML)
    def test_non_list_yaml_value(self):
        """YAML that is not a mapping raises SerializationError."""
        with pytest.raises(SerializationError):
            deserialize_from_yaml("- item1\n- item2\n")
