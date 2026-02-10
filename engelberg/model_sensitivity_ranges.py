"""
Model Sensitivity Parameter Ranges Configuration

This module defines all parameter ranges, clamps, and modifiers for Model Sensitivity analysis.
Model Sensitivity tests how deterministic metrics (Equity IRR, Cash-on-Cash, Monthly NCF)
change when parameters vary.

CONFIG PARAMETERS (16):
- maintenance_rate, management_fee, purchase_price, occupancy, average_daily_rate
- interest_rate, ltv, amortization, cleaning_cost, length_of_stay
- insurance_rate, winter_occupancy, ramp_up_months
- saron_share, fixed_10y_share, saron_margin

SPECIAL PARAMETERS (3):
- property_appreciation: Projection parameter (affects IRR only)
- inflation: Projection parameter (affects IRR only)
- selling_costs: Projection parameter (affects IRR only)

The modifier functions are defined in engelberg.model_sensitivity and imported here
to avoid circular dependencies. Simple modifiers use lambdas that call apply_sensitivity directly.
"""

from engelberg.core import apply_sensitivity

# Import modifier functions from model_sensitivity (will be defined there)
# We'll import them at the bottom of model_sensitivity.py to avoid circular imports
# For now, we'll use lambdas that call apply_sensitivity with validation

MODEL_SENSITIVITY_PARAMETER_CONFIG = {
    'maintenance_rate': {
        'parameter_name': 'Maintenance Reserve Rate',
        'get_base_value': lambda cfg: cfg.expenses.maintenance_rate,
        'low_factor': 0.0,
        'high_factor': 2.0,
        'clamp_min': 0.0,
        'clamp_max': None,
        'modifier': lambda cfg, val: apply_sensitivity(cfg, maintenance_rate=max(0.0, val)),
        'affects_year1': True,
        'affects_exit': False,
        'range_pct': 100
    },
    'management_fee': {
        'parameter_name': 'Property Management Fee',
        'get_base_value': lambda cfg: cfg.expenses.property_management_fee_rate,
        'low_factor': 0.75,
        'high_factor': 1.25,
        'clamp_min': 0.0,
        'clamp_max': 1.0,
        'modifier': lambda cfg, val: apply_sensitivity(cfg, management_fee=val),
        'affects_year1': True,
        'affects_exit': False,
        'range_pct': 50
    },
    'purchase_price': {
        'parameter_name': 'Purchase Price',
        'get_base_value': lambda cfg: cfg.financing.purchase_price,
        'low_factor': 0.90,
        'high_factor': 1.10,
        'clamp_min': None,
        'clamp_max': None,
        'modifier': lambda cfg, val: apply_sensitivity(cfg, purchase_price=val),
        'affects_year1': True,
        'affects_exit': True,
        'range_pct': 20
    },
    'occupancy': {
        'parameter_name': 'Occupancy Rate',
        'get_base_value': lambda cfg: cfg.rental.occupancy_rate,
        'low_factor': 0.90,
        'high_factor': 1.10,
        'clamp_min': 0.0,
        'clamp_max': 1.0,
        'modifier': lambda cfg, val: apply_sensitivity(cfg, occupancy=val),
        'affects_year1': True,
        'affects_exit': False,
        'range_pct': 20
    },
    'average_daily_rate': {
        'parameter_name': 'Average Daily Rate',
        'get_base_value': lambda cfg: cfg.rental.average_daily_rate,
        'low_factor': 0.80,
        'high_factor': 1.20,
        'clamp_min': 0.0,
        'clamp_max': None,
        'modifier': lambda cfg, val: apply_sensitivity(cfg, daily_rate=val),
        'affects_year1': True,
        'affects_exit': False,
        'range_pct': 40
    },
    'interest_rate': {
        'parameter_name': 'Interest Rate',
        'get_base_value': lambda cfg: cfg.financing.interest_rate,
        'low_factor': 0.230769,  # ±1% on 1.3% base
        'high_factor': 1.769231,
        'clamp_min': 0.0,
        'clamp_max': None,
        'modifier': lambda cfg, val: apply_sensitivity(cfg, interest_rate=val),
        'affects_year1': True,
        'affects_exit': False,
        'range_pct': 154
    },
    'saron_share': {
        'parameter_name': 'SARON Share',
        'get_base_value': lambda cfg: sum(
            t.share_of_loan for t in (cfg.financing.loan_tranches or []) if t.rate_type == 'saron'
        ),
        'low_factor': 0.67,
        'high_factor': 1.17,
        'clamp_min': 0.30,
        'clamp_max': 0.80,
        'modifier': lambda cfg, val: apply_sensitivity(cfg, saron_share=val),
        'affects_year1': True,
        'affects_exit': False,
        'range_pct': 50
    },
    'fixed_10y_share': {
        'parameter_name': 'Fixed 10Y Share',
        'get_base_value': lambda cfg: max(
            (
                t.share_of_loan
                for t in (cfg.financing.loan_tranches or [])
                if t.rate_type == 'fixed'
            ),
            default=0.0,
        ),
        'low_factor': 0.67,
        'high_factor': 1.33,
        'clamp_min': 0.05,
        'clamp_max': 0.50,
        'modifier': lambda cfg, val: apply_sensitivity(cfg, fixed_10y_share=val),
        'affects_year1': True,
        'affects_exit': False,
        'range_pct': 66
    },
    'saron_margin': {
        'parameter_name': 'SARON Margin',
        'get_base_value': lambda cfg: next(
            (
                t.saron_margin
                for t in (cfg.financing.loan_tranches or [])
                if t.rate_type == 'saron'
            ),
            0.009,
        ),
        'low_factor': 0.75,
        'high_factor': 1.25,
        'clamp_min': 0.0,
        'clamp_max': None,
        'modifier': lambda cfg, val: apply_sensitivity(cfg, saron_margin=val),
        'affects_year1': True,
        'affects_exit': False,
        'range_pct': 50
    },
    'ltv': {
        'parameter_name': 'Loan-to-Value (LTV)',
        'get_base_value': lambda cfg: cfg.financing.ltv,
        'low_factor': 0.90,
        'high_factor': 1.10,
        'clamp_min': 0.0,
        'clamp_max': 0.95,
        'modifier': lambda cfg, val: apply_sensitivity(cfg, ltv=max(0.0, min(0.95, val))),
        'affects_year1': True,
        'affects_exit': True,
        'range_pct': 20
    },
    'amortization': {
        'parameter_name': 'Amortization Rate',
        'get_base_value': lambda cfg: cfg.financing.amortization_rate,
        'low_factor': 0.0,
        'high_factor': 2.0,
        'clamp_min': 0.0,
        'clamp_max': None,
        'modifier': lambda cfg, val: apply_sensitivity(cfg, amortization_rate=val),
        'affects_year1': True,
        'affects_exit': True,
        'range_pct': 200
    },
    'cleaning_cost': {
        'parameter_name': 'Cleaning Cost per Stay',
        'get_base_value': lambda cfg: cfg.expenses.cleaning_cost_per_stay,
        'low_factor': 0.70,
        'high_factor': 1.30,
        'clamp_min': 0.0,
        'clamp_max': None,
        'modifier': lambda cfg, val: apply_sensitivity(cfg, cleaning_cost_per_stay=max(0.0, val)),
        'affects_year1': True,
        'affects_exit': False,
        'range_pct': 60
    },
    'length_of_stay': {
        'parameter_name': 'Average Length of Stay',
        'get_base_value': lambda cfg: cfg.expenses.average_length_of_stay,
        'low_factor': 0.70,
        'high_factor': 1.30,
        'clamp_min': 0.1,
        'clamp_max': None,
        'modifier': lambda cfg, val: apply_sensitivity(cfg, average_length_of_stay=max(0.1, val)),
        'affects_year1': True,
        'affects_exit': False,
        'range_pct': 60
    },
    'insurance_rate': {
        'parameter_name': 'Insurance Rate',
        'get_base_value': lambda cfg: cfg.expenses.insurance_annual / cfg.financing.purchase_price if cfg.financing.purchase_price > 0 else 0.004,
        'low_factor': 0.75,
        'high_factor': 1.25,
        'clamp_min': 0.0,
        'clamp_max': None,
        'modifier': lambda cfg, val: apply_sensitivity(cfg, insurance_rate=max(0.0, val)),
        'affects_year1': True,
        'affects_exit': False,
        'range_pct': 50
    },
    'winter_occupancy': {
        'parameter_name': 'Winter Season Occupancy',
        'get_base_value': lambda cfg: next((s.occupancy_rate for s in cfg.rental.seasons if s.name == "Winter Peak (Ski Season)"), cfg.rental.occupancy_rate) if cfg.rental.seasons else cfg.rental.occupancy_rate,
        'low_factor': 0.85,
        'high_factor': 1.15,
        'clamp_min': 0.0,
        'clamp_max': 0.95,
        'modifier': lambda cfg, val: apply_sensitivity(cfg, occupancy=max(0.0, min(0.95, val))),  # Will be overridden in model_sensitivity.py
        'affects_year1': True,
        'affects_exit': False,
        'range_pct': 30
    },
    'ramp_up_months': {
        'parameter_name': 'Ramp-Up Period',
        'get_base_value': lambda cfg: cfg.projection.ramp_up_months if getattr(cfg, 'projection', None) else 3,
        'low_factor': 0.43,   # 3 months (7 × 0.43 ≈ 3)
        'high_factor': 1.71,  # 12 months (7 × 1.71 ≈ 12)
        'clamp_min': 0,
        'clamp_max': 18,
        'modifier': 'modify_ramp_up_months',  # Special handling in sensitivity loop
        'affects_year1': True,
        'affects_exit': False,
        'range_pct': 171,
        'requires_json_path': True  # Special flag: modifier needs json_path parameter
    },
}

# Special parameters that affect projection calculations (not config parameters)
MODEL_SENSITIVITY_SPECIAL_FACTORS = {
    'property_appreciation': (0.6, 1.4),          # 1.5%–3.5% on 2.5% base
    'inflation': (0.50, 1.50),                    # ±0.5% on 1.0% base
    'selling_costs': (0.743589, 1.256410)         # 5.8%–9.8% on 7.8% base
}
