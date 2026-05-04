"""SA-MA Entry Point — Bootstrap and run Sports-Avatar Mesh Architecture."""

from __future__ import annotations

from .preset import create_sa_pnp


def main() -> None:
    pnp = create_sa_pnp(jwt_secret="change-me-in-production", log_level="INFO")
    print(f"SA-MA bootstrapped: {len(pnp.loaded_domains)} domains, "
          f"{len(pnp.loaded_adapters)} adapters")
    for domain in pnp.loaded_domains:
        families = pnp.hierarchy.list_product_families(domain_id=domain.domain_id)
        print(f"  Product: {domain.domain_id}")
        for f in families:
            print(f"    └── product_type: {f.name}")


if __name__ == "__main__":
    main()
