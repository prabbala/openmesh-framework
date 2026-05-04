"""EA-MA Entry Point — Bootstrap and run the Empirical-AiS Mesh Architecture.

Usage:
    python -m ea_ma.main
"""

from __future__ import annotations

from .preset import create_eais_pnp


def main() -> None:
    """Bootstrap EA-MA and print full product catalog."""
    pnp = create_eais_pnp(
        jwt_secret="change-me-in-production",
        log_level="INFO",
    )

    # Product catalog snapshot
    snap = pnp.catalog.snapshot()
    print(f"\n{'='*60}")
    print(f"  {snap.entity_name} — Product Catalog")
    print(f"{'='*60}")
    print(f"  Products: {len(snap.products)}  |  "
          f"Verticals: {snap.total_verticals}  |  "
          f"Adapters: {snap.total_adapters}")
    print(f"{'='*60}")

    for p in snap.products:
        status = "✓" if p.adapter_resolved else "✗"
        print(f"\n  [{status}] {p.product_name} ({p.domain_id})")
        print(f"      runtime: {p.runtime_type}  |  LOB: {p.lob_id}")
        if p.verticals:
            for v in p.verticals:
                print(f"      └── {v}")

    # Compliance summary
    comp = pnp.get_compliance_summary()
    print(f"\n{'='*60}")
    print(f"  Compliance Summary")
    print(f"{'='*60}")
    print(f"  Audit records: {comp['total_audit_records']}")
    print(f"  Custom roles: {', '.join(comp['custom_roles'])}")
    for did, fw in comp["compliance_frameworks"].items():
        print(f"  {did}: {fw}")
    print()


if __name__ == "__main__":
    main()
