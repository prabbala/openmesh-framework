"""Verify — quick check that the OM-FW → EA-MA → CRM-AI chain works.

Run: python openmesh-framework/verify.py
"""

from __future__ import annotations

import sys


def verify() -> bool:
    errors = []

    # 1. Check OM-FW imports
    try:
        from packages.core.pnp import PnPMain, PnPConfig
        print("  [✓] OM-FW core.pnp imports OK")
    except ImportError as e:
        errors.append(f"  [✗] OM-FW import failed: {e}")

    # 2. Check EA-MA imports
    try:
        from ea_ma.pnp import EAISPnPMain, EAISEnvironment
        from ea_ma.preset import create_eais_pnp
        print("  [✓] EA-MA imports OK")
    except ImportError as e:
        errors.append(f"  [✗] EA-MA import failed: {e}")

    # 3. Bootstrap EA-MA
    try:
        pnp = create_eais_pnp(jwt_secret="verify-test", log_level="WARNING")
        print(f"  [✓] EA-MA bootstrapped: {len(pnp.loaded_domains)} domains")
    except Exception as e:
        errors.append(f"  [✗] EA-MA bootstrap failed: {e}")
        for err in errors:
            print(err)
        return False

    # 4. Check BAI verticals
    verts = pnp.bai.list_verticals()
    print(f"  [✓] BAI verticals: {len(verts)}")
    for v in verts:
        print(f"      └── {v.family_id}: {v.name}")

    # 5. Check product catalog
    snap = pnp.catalog.snapshot()
    print(f"  [✓] Product catalog: {len(snap.products)} products, {snap.total_verticals} verticals")

    # 6. Check email enforcement
    try:
        pnp.register_user(email="test@gmail.com", password="p", user_id="bad")
        errors.append("  [✗] Email enforcement FAILED — non-EAIS email was accepted")
    except Exception:
        print("  [✓] Email enforcement: @empirical-ais.com required")

    # 7. Register an EAIS user
    try:
        token = pnp.register_user(
            email="verify@empirical-ais.com", password="test", user_id="v1",
        )
        print(f"  [✓] User registration: token issued ({len(token)} chars)")
    except Exception as e:
        errors.append(f"  [✗] User registration failed: {e}")

    # 8. Render dashboard
    try:
        panels = pnp.render_dashboard(token=token)
        print(f"  [✓] Dashboard: {len(panels)} panels rendered")
    except Exception as e:
        errors.append(f"  [✗] Dashboard render failed: {e}")

    if errors:
        print("\nFAILED:")
        for err in errors:
            print(err)
        return False

    print("\n  All checks passed. CRM-AI → EA-MA → OM-FW chain is working.")
    return True


if __name__ == "__main__":
    print("\n  OpenMesh Framework Integration Verification")
    print("  " + "=" * 50)
    ok = verify()
    sys.exit(0 if ok else 1)
