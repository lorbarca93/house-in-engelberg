"""Tests for top-level package exports and lazy optional imports."""

import importlib


def test_package_imports_without_optional_dependencies():
    """Importing the package should not require SciPy unless MC APIs are used."""
    pkg = importlib.import_module("engelberg")

    assert pkg.HORIZONS[0] == 5
    assert callable(pkg.create_base_case_config)


def test_lazy_monte_carlo_export_raises_without_scipy():
    """Optional Monte Carlo exports should fail only when accessed."""
    pkg = importlib.import_module("engelberg")

    try:
        _ = pkg.run_monte_carlo_simulation
    except ModuleNotFoundError as exc:
        assert "scipy" in str(exc).lower()
    else:
        # If SciPy is available, lazy loading should still resolve the symbol.
        assert callable(pkg.run_monte_carlo_simulation)
