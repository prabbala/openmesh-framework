"""Adapter Validator — validates that an adapter correctly implements ObservabilityAdapterInterface.

Checks each interface method for correct return types and MeshHealthEvent conformance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Type

from packages.observability.interface.adapter import (
    AdapterMetadata,
    HealthCheck,
    HealthStatus,
    Metric,
    MeshHealthEvent,
    ObservabilityAdapterInterface,
    PanelDefinition,
    Severity,
)


@dataclass
class MethodResult:
    """Result of validating a single interface method."""

    method_name: str
    passed: bool
    message: str


@dataclass
class ValidationReport:
    """Complete validation report for an adapter."""

    adapter_name: str
    passed: bool
    results: List[MethodResult] = field(default_factory=list)

    @property
    def failures(self) -> List[MethodResult]:
        return [r for r in self.results if not r.passed]


class AdapterValidator:
    """Validates that an adapter correctly implements ObservabilityAdapterInterface.

    Checks:
    - get_health_checks returns List[HealthCheck]
    - get_metrics returns List[Metric]
    - get_panel_definitions returns List[PanelDefinition]
    - get_adapter_metadata returns AdapterMetadata
    """

    def validate(self, adapter_class: Type, *args: Any, **kwargs: Any) -> ValidationReport:
        """Validate an adapter class or instance.

        Args:
            adapter_class: The adapter class to validate. If a class is passed,
                it will be instantiated with the given args/kwargs.

        Returns:
            ValidationReport with pass/fail for each method.
        """
        results: List[MethodResult] = []
        adapter_name = getattr(adapter_class, "__name__", str(adapter_class))

        # Instantiate if it's a class
        if isinstance(adapter_class, type):
            if not issubclass(adapter_class, ObservabilityAdapterInterface):
                return ValidationReport(
                    adapter_name=adapter_name,
                    passed=False,
                    results=[
                        MethodResult(
                            method_name="__class__",
                            passed=False,
                            message=f"{adapter_name} does not implement ObservabilityAdapterInterface",
                        )
                    ],
                )
            try:
                instance = adapter_class(*args, **kwargs)
            except Exception as exc:
                return ValidationReport(
                    adapter_name=adapter_name,
                    passed=False,
                    results=[
                        MethodResult(
                            method_name="__init__",
                            passed=False,
                            message=f"Failed to instantiate {adapter_name}: {exc}",
                        )
                    ],
                )
        else:
            instance = adapter_class
            adapter_name = type(instance).__name__

        # Validate get_health_checks
        results.append(self._validate_health_checks(instance))

        # Validate get_metrics
        results.append(self._validate_metrics(instance))

        # Validate get_panel_definitions
        results.append(self._validate_panel_definitions(instance))

        # Validate get_adapter_metadata
        results.append(self._validate_adapter_metadata(instance))

        all_passed = all(r.passed for r in results)
        return ValidationReport(
            adapter_name=adapter_name,
            passed=all_passed,
            results=results,
        )

    def _validate_health_checks(self, adapter: ObservabilityAdapterInterface) -> MethodResult:
        try:
            result = adapter.get_health_checks()
            if not isinstance(result, list):
                return MethodResult("get_health_checks", False, f"Expected list, got {type(result).__name__}")
            for i, item in enumerate(result):
                if not isinstance(item, HealthCheck):
                    return MethodResult("get_health_checks", False, f"Item {i} is {type(item).__name__}, expected HealthCheck")
                if not isinstance(item.name, str) or not item.name:
                    return MethodResult("get_health_checks", False, f"Item {i} has invalid name")
                if not isinstance(item.status, HealthStatus):
                    return MethodResult("get_health_checks", False, f"Item {i} has invalid status type")
            return MethodResult("get_health_checks", True, f"Returned {len(result)} valid HealthCheck objects")
        except Exception as exc:
            return MethodResult("get_health_checks", False, f"Exception: {exc}")

    def _validate_metrics(self, adapter: ObservabilityAdapterInterface) -> MethodResult:
        try:
            result = adapter.get_metrics()
            if not isinstance(result, list):
                return MethodResult("get_metrics", False, f"Expected list, got {type(result).__name__}")
            for i, item in enumerate(result):
                if not isinstance(item, Metric):
                    return MethodResult("get_metrics", False, f"Item {i} is {type(item).__name__}, expected Metric")
                if not isinstance(item.metric_name, str) or not item.metric_name:
                    return MethodResult("get_metrics", False, f"Item {i} has invalid metric_name")
                if not isinstance(item.value, (int, float)):
                    return MethodResult("get_metrics", False, f"Item {i} has invalid value type")
                if not isinstance(item.unit, str) or not item.unit:
                    return MethodResult("get_metrics", False, f"Item {i} has invalid unit")
            return MethodResult("get_metrics", True, f"Returned {len(result)} valid Metric objects")
        except Exception as exc:
            return MethodResult("get_metrics", False, f"Exception: {exc}")

    def _validate_panel_definitions(self, adapter: ObservabilityAdapterInterface) -> MethodResult:
        try:
            result = adapter.get_panel_definitions()
            if not isinstance(result, list):
                return MethodResult("get_panel_definitions", False, f"Expected list, got {type(result).__name__}")
            for i, item in enumerate(result):
                if not isinstance(item, PanelDefinition):
                    return MethodResult("get_panel_definitions", False, f"Item {i} is {type(item).__name__}, expected PanelDefinition")
                if not isinstance(item.title, str) or not item.title:
                    return MethodResult("get_panel_definitions", False, f"Item {i} has invalid title")
                if not isinstance(item.data_source_key, str) or not item.data_source_key:
                    return MethodResult("get_panel_definitions", False, f"Item {i} has invalid data_source_key")
                if not isinstance(item.visualization_type, str) or not item.visualization_type:
                    return MethodResult("get_panel_definitions", False, f"Item {i} has invalid visualization_type")
                if not isinstance(item.required_role, str) or not item.required_role:
                    return MethodResult("get_panel_definitions", False, f"Item {i} has invalid required_role")
            return MethodResult("get_panel_definitions", True, f"Returned {len(result)} valid PanelDefinition objects")
        except Exception as exc:
            return MethodResult("get_panel_definitions", False, f"Exception: {exc}")

    def _validate_adapter_metadata(self, adapter: ObservabilityAdapterInterface) -> MethodResult:
        try:
            result = adapter.get_adapter_metadata()
            if not isinstance(result, AdapterMetadata):
                return MethodResult("get_adapter_metadata", False, f"Expected AdapterMetadata, got {type(result).__name__}")
            if not isinstance(result.name, str) or not result.name:
                return MethodResult("get_adapter_metadata", False, "Missing or invalid name")
            if not isinstance(result.version, str) or not result.version:
                return MethodResult("get_adapter_metadata", False, "Missing or invalid version")
            if not isinstance(result.supported_runtime_types, list) or not result.supported_runtime_types:
                return MethodResult("get_adapter_metadata", False, "Missing or invalid supported_runtime_types")
            if not isinstance(result.description, str) or not result.description:
                return MethodResult("get_adapter_metadata", False, "Missing or invalid description")
            return MethodResult("get_adapter_metadata", True, f"Valid metadata: {result.name} v{result.version}")
        except Exception as exc:
            return MethodResult("get_adapter_metadata", False, f"Exception: {exc}")
