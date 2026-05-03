"""Tests for reference adapter validation and SDK validator.

Tests:
- Task 14.4: All reference adapters pass SDK validation
- Property 24: Scaffold-to-Validation Round-Trip
- Property 19: Adapter Interface Contract (additional coverage)
"""

from __future__ import annotations

import os
import shutil
import tempfile

import pytest

from packages.observability.adapters.server.adapter import ServerAdapter
from packages.observability.adapters.serverless.adapter import ServerlessAdapter
from packages.observability.adapters.kubernetes.adapter import KubernetesAdapter
from packages.observability.adapters.gpu.adapter import GPUAdapter
from packages.observability.adapters.streaming.adapter import StreamingAdapter
from packages.observability.interface.adapter import (
    AdapterMetadata,
    HealthCheck,
    HealthStatus,
    Metric,
    ObservabilityAdapterInterface,
    PanelDefinition,
)
from packages.sdk.python.openmesh_sdk.validator import AdapterValidator
from packages.sdk.python.openmesh_sdk.scaffold import scaffold_adapter


# ── Reference Adapter Validation ─────────────────────────────────────

REFERENCE_ADAPTERS = [
    ("server", ServerAdapter),
    ("serverless", ServerlessAdapter),
    ("kubernetes", KubernetesAdapter),
    ("gpu", GPUAdapter),
    ("streaming", StreamingAdapter),
]


class TestReferenceAdapterValidation:
    """All 5 reference adapters pass SDK validation."""

    @pytest.mark.parametrize("name,adapter_class", REFERENCE_ADAPTERS)
    def test_adapter_passes_validation(self, name, adapter_class):
        """Reference adapter passes all SDK validation checks."""
        validator = AdapterValidator()
        report = validator.validate(adapter_class)
        assert report.passed, f"{name} adapter failed: {[r.message for r in report.failures]}"

    @pytest.mark.parametrize("name,adapter_class", REFERENCE_ADAPTERS)
    def test_adapter_health_checks_valid(self, name, adapter_class):
        """Reference adapter returns valid HealthCheck objects."""
        adapter = adapter_class()
        checks = adapter.get_health_checks()
        assert len(checks) > 0
        for check in checks:
            assert isinstance(check, HealthCheck)
            assert isinstance(check.name, str) and check.name
            assert isinstance(check.status, HealthStatus)

    @pytest.mark.parametrize("name,adapter_class", REFERENCE_ADAPTERS)
    def test_adapter_metrics_valid(self, name, adapter_class):
        """Reference adapter returns valid Metric objects."""
        adapter = adapter_class()
        metrics = adapter.get_metrics()
        assert len(metrics) > 0
        for metric in metrics:
            assert isinstance(metric, Metric)
            assert isinstance(metric.metric_name, str) and metric.metric_name
            assert isinstance(metric.value, (int, float))
            assert isinstance(metric.unit, str) and metric.unit

    @pytest.mark.parametrize("name,adapter_class", REFERENCE_ADAPTERS)
    def test_adapter_panels_valid(self, name, adapter_class):
        """Reference adapter returns valid PanelDefinition objects."""
        adapter = adapter_class()
        panels = adapter.get_panel_definitions()
        assert len(panels) > 0
        for panel in panels:
            assert isinstance(panel, PanelDefinition)
            assert isinstance(panel.title, str) and panel.title
            assert isinstance(panel.data_source_key, str) and panel.data_source_key
            assert isinstance(panel.visualization_type, str) and panel.visualization_type
            assert isinstance(panel.required_role, str) and panel.required_role

    @pytest.mark.parametrize("name,adapter_class", REFERENCE_ADAPTERS)
    def test_adapter_metadata_valid(self, name, adapter_class):
        """Reference adapter returns valid AdapterMetadata."""
        adapter = adapter_class()
        meta = adapter.get_adapter_metadata()
        assert isinstance(meta, AdapterMetadata)
        assert isinstance(meta.name, str) and meta.name
        assert isinstance(meta.version, str) and meta.version
        assert isinstance(meta.supported_runtime_types, list) and meta.supported_runtime_types
        assert name in meta.supported_runtime_types[0]
        assert isinstance(meta.description, str) and meta.description

    @pytest.mark.parametrize("name,adapter_class", REFERENCE_ADAPTERS)
    def test_adapter_emit_health_event(self, name, adapter_class):
        """Reference adapter can emit valid MeshHealthEvent objects."""
        from packages.observability.interface.adapter import MeshHealthEvent, Severity
        adapter = adapter_class(entity_id="test-entity", domain="test-domain")
        event = adapter.emit_health_event(Severity.INFO, "Test event")
        assert isinstance(event, MeshHealthEvent)
        assert event.entity_id == "test-entity"
        assert event.domain == "test-domain"
        assert event.severity == Severity.INFO


# ── Property 24: Scaffold-to-Validation Round-Trip ───────────────────

# Feature: openmesh-framework, Property 24: Scaffold-to-Validation Round-Trip
class TestScaffoldValidationRoundTrip:
    """Generated adapter passes SDK validation without modifications."""

    def test_scaffold_generates_valid_adapter(self):
        """Scaffold command generates an adapter that passes validation."""
        tmpdir = tempfile.mkdtemp()
        try:
            pkg_path = scaffold_adapter(
                adapter_name="test-scaffold",
                output_dir=tmpdir,
                runtime_type="server",
                description="Test scaffolded adapter",
            )

            # Verify files were created
            assert os.path.exists(os.path.join(pkg_path, "__init__.py"))
            assert os.path.exists(os.path.join(pkg_path, "adapter.py"))
            assert os.path.exists(os.path.join(pkg_path, "README.md"))
            assert os.path.exists(os.path.join(pkg_path, "test_adapter.py"))

            # Import and validate the generated adapter
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "test_scaffold.adapter",
                os.path.join(pkg_path, "adapter.py"),
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            adapter_class = getattr(module, "TestScaffoldAdapter")
            validator = AdapterValidator()
            report = validator.validate(adapter_class)
            assert report.passed, f"Scaffold validation failed: {[r.message for r in report.failures]}"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_scaffold_with_different_runtime_types(self):
        """Scaffold works for all supported runtime types."""
        for rt in ["server", "serverless", "kubernetes", "gpu", "streaming"]:
            tmpdir = tempfile.mkdtemp()
            try:
                pkg_path = scaffold_adapter(
                    adapter_name=f"test-{rt}",
                    output_dir=tmpdir,
                    runtime_type=rt,
                )
                assert os.path.exists(os.path.join(pkg_path, "adapter.py"))
            finally:
                shutil.rmtree(tmpdir, ignore_errors=True)
