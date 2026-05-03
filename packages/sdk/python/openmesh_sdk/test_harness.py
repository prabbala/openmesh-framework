"""Test Harness — provides a test runner for adapter developers.

Adapter developers can use this harness to validate their adapters
against the ObservabilityAdapterInterface contract before publishing.
"""

from __future__ import annotations

import sys
from typing import Any, Type

from .validator import AdapterValidator, ValidationReport


def run_validation(
    adapter_class: Type, *args: Any, verbose: bool = True, **kwargs: Any
) -> ValidationReport:
    """Run full validation on an adapter class and print results.

    Args:
        adapter_class: The adapter class to validate.
        verbose: If True, print detailed results to stdout.

    Returns:
        ValidationReport with pass/fail for each method.
    """
    validator = AdapterValidator()
    report = validator.validate(adapter_class, *args, **kwargs)

    if verbose:
        print(f"\n{'='*60}")
        print(f"  Adapter Validation: {report.adapter_name}")
        print(f"{'='*60}")

        for result in report.results:
            status = "PASS" if result.passed else "FAIL"
            icon = "✓" if result.passed else "✗"
            print(f"  {icon} [{status}] {result.method_name}: {result.message}")

        print(f"{'='*60}")
        if report.passed:
            print(f"  Result: ALL CHECKS PASSED")
        else:
            failed = len(report.failures)
            total = len(report.results)
            print(f"  Result: {failed}/{total} checks FAILED")
        print(f"{'='*60}\n")

    return report


def validate_and_exit(adapter_class: Type, *args: Any, **kwargs: Any) -> None:
    """Run validation and exit with appropriate code.

    Exit code 0 if all checks pass, 1 if any fail.
    Intended for use as a CLI entry point.
    """
    report = run_validation(adapter_class, *args, **kwargs)
    sys.exit(0 if report.passed else 1)
