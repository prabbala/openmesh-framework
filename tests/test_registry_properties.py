"""Property tests for Domain Registry duplicate rejection and lookup.

Feature: openmesh-framework, Property 9: Domain Registry Duplicate Rejection and Lookup
Validates: Requirements 2.3, 2.4, 2.5
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

_prop_settings = settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])

from packages.core.domain_registry.registration import VALID_RUNTIME_TYPES, DomainRegistration
from packages.core.domain_registry.registry import (
    DomainNotFoundError,
    DomainRegistry,
    DuplicateDomainError,
)
from tests.strategies import domain_registration_strategy

# ── Strategies ───────────────────────────────────────────────────────

_runtime_type_st = st.sampled_from(sorted(VALID_RUNTIME_TYPES))


# ── Property 9: Domain Registry Duplicate Rejection and Lookup ──────


class TestDomainRegistryDuplicateAndLookup:
    """Property 9: Registering a DomainRegistration makes it retrievable.
    Registering a second with the same domain_id is rejected.
    """

    # Feature: openmesh-framework, Property 9: Domain Registry Duplicate Rejection and Lookup
    @given(reg=domain_registration_strategy())
    @_prop_settings
    def test_registered_domain_is_retrievable_by_id(self, reg: DomainRegistration):
        """After registration, get_by_id returns the registration."""
        registry = DomainRegistry()
        registry.register(reg)

        result = registry.get_by_id(reg.domain_id)
        assert result is not None
        assert result.domain_id == reg.domain_id
        assert result.runtime_type == reg.runtime_type
        assert result.observability_adapter == reg.observability_adapter

    # Feature: openmesh-framework, Property 9: Domain Registry Duplicate Rejection and Lookup
    @given(reg=domain_registration_strategy())
    @_prop_settings
    def test_registered_domain_is_retrievable_by_runtime_type(self, reg: DomainRegistration):
        """After registration, get_by_runtime_type includes the registration."""
        registry = DomainRegistry()
        registry.register(reg)

        results = registry.get_by_runtime_type(reg.runtime_type)
        domain_ids = [r.domain_id for r in results]
        assert reg.domain_id in domain_ids

    # Feature: openmesh-framework, Property 9: Domain Registry Duplicate Rejection and Lookup
    @given(reg=domain_registration_strategy())
    @_prop_settings
    def test_duplicate_domain_id_is_rejected(self, reg: DomainRegistration):
        """Registering a second DomainRegistration with the same domain_id fails."""
        registry = DomainRegistry()
        registry.register(reg)

        # Second registration with same domain_id should be rejected
        duplicate = DomainRegistration(
            domain_id=reg.domain_id,
            runtime_type=reg.runtime_type,
            observability_adapter="some.other.Adapter",
            roles=["viewer"],
            tabs=[],
        )
        with pytest.raises(DuplicateDomainError) as exc_info:
            registry.register(duplicate)

        # Error message should be descriptive
        assert reg.domain_id in str(exc_info.value)

    # Feature: openmesh-framework, Property 9: Domain Registry Duplicate Rejection and Lookup
    @given(reg=domain_registration_strategy())
    @_prop_settings
    def test_unregister_removes_domain(self, reg: DomainRegistration):
        """After unregistration, get_by_id returns None."""
        registry = DomainRegistry()
        registry.register(reg)
        registry.unregister(reg.domain_id)

        assert registry.get_by_id(reg.domain_id) is None

    # Feature: openmesh-framework, Property 9: Domain Registry Duplicate Rejection and Lookup
    @given(
        reg=domain_registration_strategy(),
        lob_id=st.from_regex(r"[a-z][a-z0-9\-_]{0,19}", fullmatch=True),
    )
    @_prop_settings
    def test_get_domains_for_scope_filters_by_lob(
        self, reg: DomainRegistration, lob_id: str,
    ):
        """get_domains_for_scope returns only domains whose lob_id is in scope."""
        registry = DomainRegistry()
        registry.register(reg)

        # If the reg's lob_id is in scope, it should be returned
        scope_with = {reg.lob_id}
        results_with = registry.get_domains_for_scope(scope_with)
        assert any(r.domain_id == reg.domain_id for r in results_with)

        # If we use a different lob_id not matching, it should not be returned
        assume(lob_id != reg.lob_id)
        scope_without = {lob_id}
        results_without = registry.get_domains_for_scope(scope_without)
        assert all(r.domain_id != reg.domain_id for r in results_without)

    # Feature: openmesh-framework, Property 9: Domain Registry Duplicate Rejection and Lookup
    @given(
        regs=st.lists(domain_registration_strategy(), min_size=2, max_size=5).filter(
            lambda lst: len({r.domain_id for r in lst}) == len(lst)
        ),
    )
    @_prop_settings
    def test_multiple_registrations_all_retrievable(
        self, regs: list,
    ):
        """Multiple unique registrations are all independently retrievable."""
        registry = DomainRegistry()
        for reg in regs:
            registry.register(reg)

        assert registry.count == len(regs)
        for reg in regs:
            assert registry.get_by_id(reg.domain_id) is not None
