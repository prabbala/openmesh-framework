"""Shared pytest fixtures for the OpenMesh Framework test suite."""

import pytest


@pytest.fixture
def sample_entity_id():
    """Provide a sample entity ID for tests."""
    return "test-entity-001"


@pytest.fixture
def sample_tenant_id():
    """Provide a sample tenant ID for tests."""
    return "test-tenant-001"


@pytest.fixture
def sample_domain_id():
    """Provide a sample domain ID for tests."""
    return "test-domain-001"


@pytest.fixture
def sample_lob_id():
    """Provide a sample LOB ID for tests."""
    return "test-lob-001"
