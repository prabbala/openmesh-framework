"""Hypothesis strategies for OpenMesh Framework property tests.

Provides reusable generators for DomainRegistration, MeshHealthEvent,
hierarchy nodes, and related objects.
"""

from __future__ import annotations

from hypothesis import strategies as st

from packages.core.domain_registry.registration import VALID_RUNTIME_TYPES

# ── Primitives ───────────────────────────────────────────────────────

_id_chars = "abcdefghijklmnopqrstuvwxyz0123456789"

_id_strategy = st.from_regex(r"[a-z][a-z0-9\-_]{0,19}", fullmatch=True)

_name_strategy = st.from_regex(r"[A-Za-z][A-Za-z0-9 \-_]{0,29}", fullmatch=True)

_runtime_type_strategy = st.sampled_from(sorted(VALID_RUNTIME_TYPES))

_role_strategy = st.sampled_from([
    "superuser", "admin", "operator", "auditor",
    "manager", "staff", "viewer",
])

_adapter_strategy = st.from_regex(r"[a-z][a-z_.]{2,30}", fullmatch=True)


# ── DomainRegistration ──────────────────────────────────────────────

_tab_strategy = st.fixed_dictionaries({
    "title": _name_strategy,
    "panel_type": st.sampled_from([
        "health_grid", "metric_chart", "timeline", "severity_chart",
    ]),
    "data_source": st.sampled_from([
        "health_checks", "metrics", "events", "logs",
    ]),
})


@st.composite
def domain_registration_strategy(draw):
    """Generate valid DomainRegistration objects."""
    from packages.core.domain_registry.registration import DomainRegistration

    return DomainRegistration(
        domain_id=draw(_id_strategy),
        runtime_type=draw(_runtime_type_strategy),
        observability_adapter=draw(_adapter_strategy),
        roles=draw(st.lists(_role_strategy, min_size=1, max_size=3)),
        tabs=draw(st.lists(_tab_strategy, min_size=0, max_size=2)),
        entity_id=draw(_id_strategy),
        lob_id=draw(_id_strategy),
        metadata=draw(st.just({})),
    )
