"""
Engelberg Property Investment Simulation Package

A professional-grade toolkit for analyzing co-ownership rental investments
in Engelberg, Switzerland.
"""

# Package metadata
__version__ = "1.0.0"
__author__ = "Engelberg Investment Team"

# Export commonly used classes and functions
from engelberg.core import (
    HORIZONS,
    FinancingParams,
    RentalParams,
    ExpenseParams,
    SeasonalParams,
    BaseCaseConfig,
    load_assumptions_from_json,
    create_base_case_config,
    get_projection_defaults,
    compute_annual_cash_flows,
    compute_15_year_projection,
    calculate_irrs_from_projection,
    apply_sensitivity,
    export_base_case_to_json,
    export_sensitivity_to_json,
    export_monte_carlo_to_json,
    export_monte_carlo_sensitivity_to_json,
)


# Lazily import optional analysis/Monte Carlo symbols so importing
# `engelberg.core` does not require SciPy unless those APIs are used.
_LAZY_EXPORTS = {
    'run_base_case_analysis': ('engelberg.analysis', 'run_base_case_analysis'),
    'run_sensitivity_analysis': ('engelberg.analysis', 'run_sensitivity_analysis'),
    'run_cash_on_cash_sensitivity_analysis': ('engelberg.analysis', 'run_cash_on_cash_sensitivity_analysis'),
    'run_monthly_ncf_sensitivity_analysis': ('engelberg.analysis', 'run_monthly_ncf_sensitivity_analysis'),
    'run_monte_carlo_analysis': ('engelberg.analysis', 'run_monte_carlo_analysis'),
    'run_monte_carlo_sensitivity_analysis': ('engelberg.analysis', 'run_monte_carlo_sensitivity_analysis'),
    'run_monte_carlo_simulation': ('engelberg.monte_carlo', 'run_monte_carlo_simulation'),
    'calculate_statistics': ('engelberg.monte_carlo', 'calculate_statistics'),
}


def __getattr__(name):
    """Resolve optional package exports lazily on first access."""
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module 'engelberg' has no attribute '{name}'")

    module_name, attr_name = _LAZY_EXPORTS[name]
    module = __import__(module_name, fromlist=[attr_name])
    value = getattr(module, attr_name)
    globals()[name] = value
    return value

__all__ = [
    # Constants
    'HORIZONS',
    # Core dataclasses
    'FinancingParams',
    'RentalParams',
    'ExpenseParams',
    'SeasonalParams',
    'BaseCaseConfig',
    # Configuration loaders
    'load_assumptions_from_json',
    'create_base_case_config',
    'get_projection_defaults',
    # Calculation functions
    'compute_annual_cash_flows',
    'compute_15_year_projection',
    'calculate_irrs_from_projection',
    'apply_sensitivity',
    # Export functions
    'export_base_case_to_json',
    'export_sensitivity_to_json',
    'export_monte_carlo_to_json',
    'export_monte_carlo_sensitivity_to_json',
    # Analysis functions
    'run_base_case_analysis',
    'run_sensitivity_analysis',
    'run_cash_on_cash_sensitivity_analysis',
    'run_monthly_ncf_sensitivity_analysis',
    'run_monte_carlo_analysis',
    'run_monte_carlo_sensitivity_analysis',
    # Monte Carlo functions
    'run_monte_carlo_simulation',
    'calculate_statistics',
]
