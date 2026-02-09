"""
MC Sensitivity Parameter Ranges Configuration

This module defines parameter ranges for Monte Carlo-based sensitivity analysis.
MC Sensitivity tests how NPV > 0 probability changes with different parameter values
by running Monte Carlo simulations for each parameter value.

PARAMETERS (6):
- amortization_rate: 0% to 2x base (clamped to 0-2%)
- interest_rate: 0.5x to 2x base (clamped to 0.5%-5%)
- purchase_price: ±20% of base
- occupancy: ±20% of base (clamped to 0-100%)
- daily_rate: ±30% of base
- ramp_up_months: 4-10 months (triangular with mode at 7)

Each parameter is tested with 10 evenly spaced values across its range.
"""

MC_SENSITIVITY_PARAMETER_CONFIG = {
    'amortization_rate': {
        'parameter_name': 'Amortization Rate',
        'get_base_value': lambda cfg: cfg.financing.amortization_rate,
        'min_factor': 0.0,
        'max_factor': 2.0,
        'clamp_min': 0.0,
        'clamp_max': 0.02,
        'num_points': 10
    },
    'interest_rate': {
        'parameter_name': 'Interest Rate',
        'get_base_value': lambda cfg: cfg.financing.interest_rate,
        'min_factor': 0.5,
        'max_factor': 2.0,
        'clamp_min': 0.005,
        'clamp_max': 0.05,
        'num_points': 10
    },
    'purchase_price': {
        'parameter_name': 'Purchase Price',
        'get_base_value': lambda cfg: cfg.financing.purchase_price,
        'min_factor': 0.8,
        'max_factor': 1.2,
        'clamp_min': None,
        'clamp_max': None,
        'num_points': 10
    },
    'occupancy': {
        'parameter_name': 'Occupancy Rate',
        'get_base_value': lambda cfg: cfg.rental.occupancy_rate,
        'min_factor': 0.8,
        'max_factor': 1.2,
        'clamp_min': 0.0,
        'clamp_max': 1.0,
        'num_points': 10
    },
    'daily_rate': {
        'parameter_name': 'Price per Night',
        'get_base_value': lambda cfg: cfg.rental.average_daily_rate,
        'min_factor': 0.7,
        'max_factor': 1.3,
        'clamp_min': None,
        'clamp_max': None,
        'num_points': 10
    },
    'ramp_up_months': {
        'parameter_name': 'Ramp-Up Period',
        'get_base_value': lambda cfg: 7,  # Default 7 months
        'min_factor': 0.57,   # 4 months (7 × 0.57 ≈ 4)
        'max_factor': 1.43,   # 10 months (7 × 1.43 ≈ 10)
        'clamp_min': 3,
        'clamp_max': 12,
        'num_points': 10
    },
}
