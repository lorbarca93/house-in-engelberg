"""
Model Sensitivity Analysis Module

This module provides deterministic sensitivity analysis for the Engelberg property investment model.
It tests how key financial metrics (Equity IRR, Cash-on-Cash, Monthly NCF) change when parameters vary.

Model Sensitivity uses deterministic calculations (no randomness) to show the direct impact
of parameter changes on financial outcomes.
"""

import os
import json
from typing import Dict, List, Callable, Tuple, Optional
from dataclasses import replace

from engelberg.core import (
    HORIZONS,
    create_base_case_config,
    get_projection_defaults,
    compute_annual_cash_flows,
    compute_15_year_projection,
    calculate_irrs_from_projection,
    apply_sensitivity,
    resolve_path,
    BaseCaseConfig,
)

from engelberg.model_sensitivity_ranges import (
    MODEL_SENSITIVITY_PARAMETER_CONFIG,
    MODEL_SENSITIVITY_SPECIAL_FACTORS,
)


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def save_json(data: Dict, case_name: str, analysis_type: str) -> str:
    """
    Save analysis results to JSON file.
    
    Args:
        data: Dictionary with analysis results
        case_name: Name of the case (e.g., 'base_case', 'migros')
        analysis_type: Type of analysis (e.g., 'base_case_analysis', 'sensitivity')
    
    Returns:
        Path to saved file (relative to project root)
    """
    data_dir = resolve_path("website/data")
    os.makedirs(data_dir, exist_ok=True)
    output_path = os.path.join(data_dir, f"{case_name}_{analysis_type}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    # Return relative path for compatibility
    return f"website/data/{case_name}_{analysis_type}.json"


def create_sensitivity_result(param_name: str, base_value: float, 
                              low_value: float, high_value: float,
                              base_irr: float, low_irr: float, high_irr: float,
                              range_pct: float,
                              base_atcf: float = None, low_atcf: float = None, high_atcf: float = None) -> Dict:
    """
    Package sensitivity results into standard format.
    
    Args:
        param_name: Name of parameter being tested
        base_value: Base case value
        low_value: Low scenario value
        high_value: High scenario value
        base_irr: Base case IRR
        low_irr: IRR with low value
        high_irr: IRR with high value
        range_pct: Percentage range tested
        base_atcf: Base case after-tax cash flow per person (optional)
        low_atcf: After-tax cash flow per person with low value (optional)
        high_atcf: After-tax cash flow per person with high value (optional)
    
    Returns:
        Dictionary with sensitivity results
    """
    result = {
        'parameter': param_name,
        'parameter_name': param_name,
        'base_value': base_value,
        'base_irr': base_irr,
        'low': {
            'value': low_value,
            'irr': low_irr,
            'delta_irr': low_irr - base_irr,
            'delta_pct': ((low_irr - base_irr) / base_irr * 100) if base_irr != 0 else 0
        },
        'high': {
            'value': high_value,
            'irr': high_irr,
            'delta_irr': high_irr - base_irr,
            'delta_pct': ((high_irr - base_irr) / base_irr * 100) if base_irr != 0 else 0
        },
        'range_pct': range_pct,
        'impact': abs(high_irr - low_irr)
    }
    
    # Add after-tax cash flow per person if provided
    if base_atcf is not None and low_atcf is not None and high_atcf is not None:
        result['base_atcf'] = base_atcf
        result['low']['atcf'] = low_atcf
        result['low']['delta_atcf'] = low_atcf - base_atcf
        result['high']['atcf'] = high_atcf
        result['high']['delta_atcf'] = high_atcf - base_atcf
        result['impact_atcf'] = abs(high_atcf - low_atcf)
    
    return result


def scale_low_high(base_value: float, low_factor: float, high_factor: float,
                   clamp_min: float = None, clamp_max: float = None) -> Tuple[float, float]:
    """
    Scale sensitivity ranges from the case-specific base value using fixed multipliers.
    Preserves the original relative swing (derived from legacy absolute deltas) while
    adapting to each case. Applies optional bounds to keep values sensible.
    """
    low = base_value * low_factor
    high = base_value * high_factor

    if clamp_min is not None:
        low = max(low, clamp_min)
        high = max(high, clamp_min)

    if clamp_max is not None:
        low = min(low, clamp_max)
        high = min(high, clamp_max)

    return low, high


# ═══════════════════════════════════════════════════════════════════════════
# EXPLICIT CONFIG MODIFIER FUNCTIONS
# These functions replace error-prone lambda functions with explicit, testable
# functions that use apply_sensitivity() where possible.
# ═══════════════════════════════════════════════════════════════════════════

def modify_maintenance_rate(cfg: BaseCaseConfig, value: float) -> BaseCaseConfig:
    """
    Modify maintenance reserve rate in the configuration.
    
    Args:
        cfg: Base configuration
        value: New maintenance rate (as decimal, e.g., 0.005 for 0.5%)
    
    Returns:
        Modified configuration with new maintenance rate
    """
    # Clamp to reasonable bounds
    value = max(0.0, value)  # Cannot be negative
    return apply_sensitivity(cfg, maintenance_rate=value)


def modify_cleaning_cost(cfg: BaseCaseConfig, value: float) -> BaseCaseConfig:
    """
    Modify cleaning cost per stay in the configuration.
    
    Args:
        cfg: Base configuration
        value: New cleaning cost per stay (in CHF)
    
    Returns:
        Modified configuration with new cleaning cost
    """
    # Clamp to reasonable bounds
    value = max(0.0, value)  # Cannot be negative
    return apply_sensitivity(cfg, cleaning_cost_per_stay=value)


def modify_length_of_stay(cfg: BaseCaseConfig, value: float) -> BaseCaseConfig:
    """
    Modify average length of stay in the configuration.
    
    Args:
        cfg: Base configuration
        value: New average length of stay (in nights)
    
    Returns:
        Modified configuration with new length of stay
    """
    # Clamp to reasonable bounds (must be positive)
    value = max(0.1, value)  # Minimum 0.1 nights
    return apply_sensitivity(cfg, average_length_of_stay=value)


def modify_insurance_rate(cfg: BaseCaseConfig, value: float) -> BaseCaseConfig:
    """
    Modify insurance rate (as % of purchase price) in the configuration.
    
    Args:
        cfg: Base configuration
        value: New insurance rate (as decimal, e.g., 0.004 for 0.4%)
    
    Returns:
        Modified configuration with new insurance rate
    """
    # Clamp to reasonable bounds
    value = max(0.0, value)  # Cannot be negative
    return apply_sensitivity(cfg, insurance_rate=value)


def modify_ltv(cfg: BaseCaseConfig, value: float) -> BaseCaseConfig:
    """
    Modify loan-to-value ratio in the configuration.
    
    Args:
        cfg: Base configuration
        value: New LTV ratio (as decimal, e.g., 0.75 for 75%)
    
    Returns:
        Modified configuration with new LTV
    """
    # Clamp to reasonable bounds (typically 0-95%)
    value = max(0.0, min(0.95, value))
    return apply_sensitivity(cfg, ltv=value)


def modify_winter_occupancy(cfg: BaseCaseConfig, value: float) -> BaseCaseConfig:
    """
    Modify winter season occupancy rate in the configuration.
    
    This is a special case that modifies a specific season rather than
    the overall occupancy rate.
    
    Args:
        cfg: Base configuration
        value: New winter occupancy rate (as decimal, e.g., 0.75 for 75%)
    
    Returns:
        Modified configuration with new winter occupancy
    """
    # Clamp to reasonable bounds
    value = max(0.0, min(0.95, value))
    
    # Find and modify the winter season
    if not cfg.rental.seasons:
        # If no seasons, fall back to modifying overall occupancy
        return apply_sensitivity(cfg, occupancy=value)
    
    new_seasons = []
    for season in cfg.rental.seasons:
        if season.name == "Winter Peak (Ski Season)":
            new_season = replace(season, occupancy_rate=value)
        else:
            new_season = season
        new_seasons.append(new_season)
    
    new_rental = replace(cfg.rental, seasons=new_seasons)
    return replace(cfg, rental=new_rental)


def modify_ramp_up_months(cfg: BaseCaseConfig, value: float, json_path: str) -> BaseCaseConfig:
    """
    Modify ramp-up period (pre-operational months) in the projection defaults.
    
    This function modifies how many months the property is in ramp-up (pre-operational)
    before starting short-term rental operations. During ramp-up: no revenue, but
    debt service, insurance, Nebenkosten, and minimal utilities are paid.
    
    Args:
        cfg: Base configuration
        value: New ramp-up period in months (will be rounded to integer)
        json_path: Path to assumptions file (needed to reload projection defaults)
    
    Returns:
        Modified configuration - ramp_up_months will be passed to projection functions
    """
    # Clamp to reasonable bounds (0-18 months)
    value = max(0, min(18, int(round(value))))
    
    # Since ramp_up_months is a projection parameter (not config parameter),
    # we need to store it for later use in compute_15_year_projection
    # For now, return config unchanged - ramp_up_months will be passed separately to projection functions
    # This is handled in the unified sensitivity loop
    return cfg


# ═══════════════════════════════════════════════════════════════════════════
# METRIC CALCULATORS
# Functions that calculate specific financial metrics for sensitivity analysis
# ═══════════════════════════════════════════════════════════════════════════

def calculate_equity_irr(config: BaseCaseConfig, json_path: str,
                         property_appreciation_rate: float = None, 
                         projection_years: Optional[int] = None,
                         ramp_up_months: Optional[int] = None) -> float:
    """
    Calculate Equity IRR (levered) for any configuration.
    
    This is the core metric we analyze in sensitivity analysis.
    Equity IRR shows the actual return to investors considering
    financing (debt), which makes it sensitive to all parameters:
    occupancy, rates, interest rates, LTV, etc.
    
    Args:
        config: Configuration to test
        json_path: Path to assumptions (for projection defaults)
        property_appreciation_rate: Override appreciation rate (for sensitivity)
        projection_years: Horizon in years; if None, use proj_defaults['projection_years'] or 15
        ramp_up_months: Override ramp-up period; if None, use proj_defaults['ramp_up_months'] or 0
    
    Returns:
        Equity IRR as percentage (e.g., 4.5 means 4.5%)
    """
    # Load projection parameters
    proj_defaults = get_projection_defaults(json_path)
    appreciation_rate = property_appreciation_rate if property_appreciation_rate is not None else proj_defaults['property_appreciation_rate']
    years = projection_years if projection_years is not None else proj_defaults.get('projection_years', 15)
    ramp_up = ramp_up_months if ramp_up_months is not None else proj_defaults.get('ramp_up_months', 0)
    renovation_downtime_months = int(proj_defaults.get('renovation_downtime_months', 0))
    renovation_frequency_years = int(proj_defaults.get('renovation_frequency_years', 0))
    
    # Calculate results
    results = compute_annual_cash_flows(config)
    projection = compute_15_year_projection(
        config,
        start_year=proj_defaults['start_year'],
        inflation_rate=proj_defaults['inflation_rate'],
        property_appreciation_rate=appreciation_rate,
        projection_years=years,
        ramp_up_months=ramp_up,
        renovation_downtime_months=renovation_downtime_months,
        renovation_frequency_years=renovation_frequency_years
    )
    
    # Get IRR
    irr_results = calculate_irrs_from_projection(
        projection,
        config.financing.total_initial_investment_per_owner,  # Includes acquisition costs
        projection[-1]['property_value'],
        projection[-1]['remaining_loan_balance'],
        config.financing.num_owners,
        config.financing.purchase_price,
        proj_defaults['selling_costs_rate'],
        proj_defaults['discount_rate'],
        proj_defaults.get('capital_gains_tax_rate', 0.02),
        proj_defaults.get('property_transfer_tax_sale_rate', 0.015)
    )
    
    return irr_results['equity_irr_with_sale_pct']


def calculate_after_tax_cash_flow_per_person(
    config: BaseCaseConfig,
    json_path: str,
    property_appreciation_rate: float = None,
    ramp_up_months: Optional[int] = None,
    renovation_downtime_months: Optional[int] = None,
    renovation_frequency_years: Optional[int] = None,
) -> float:
    """
    Calculate after-tax cash flow per person (monthly) for any configuration.
    
    This is used in sensitivity analysis to show how monthly cash flow changes
    with parameter variations. Note that property appreciation rate does not
    affect Year 1 cash flow, so this parameter is included for API consistency
    but has no effect on the result.
    
    Args:
        config: Configuration to test
        json_path: Path to assumptions (for projection defaults)
        property_appreciation_rate: Override appreciation rate (for sensitivity)
        ramp_up_months: Override ramp-up period for Year 1 cash flow
        renovation_downtime_months: Override renovation downtime months
        renovation_frequency_years: Override renovation cycle frequency
    
    Returns:
        After-tax cash flow per person (monthly, in CHF)
    """
    # Load projection parameters
    proj_defaults = get_projection_defaults(json_path)
    appreciation_rate = (
        property_appreciation_rate
        if property_appreciation_rate is not None
        else proj_defaults["property_appreciation_rate"]
    )
    ramp_up = (
        int(ramp_up_months)
        if ramp_up_months is not None
        else int(proj_defaults.get("ramp_up_months", 0))
    )
    renovation_months = (
        int(renovation_downtime_months)
        if renovation_downtime_months is not None
        else int(proj_defaults.get("renovation_downtime_months", 0))
    )
    renovation_frequency = (
        int(renovation_frequency_years)
        if renovation_frequency_years is not None
        else int(proj_defaults.get("renovation_frequency_years", 0))
    )

    # If Year 1 has downtime (ramp-up or renovation), use projection Year 1.
    year1_has_renovation = renovation_frequency > 0 and renovation_months > 0 and (1 % renovation_frequency == 0)
    if ramp_up > 0 or year1_has_renovation:
        projection = compute_15_year_projection(
            config=config,
            start_year=2026,
            projection_years=1,
            inflation_rate=proj_defaults["inflation_rate"],
            property_appreciation_rate=appreciation_rate,
            ramp_up_months=ramp_up,
            renovation_downtime_months=renovation_months,
            renovation_frequency_years=renovation_frequency,
        )
        annual_cash_flow = projection[0].get("after_tax_cash_flow_per_owner", 0.0)
    else:
        results = compute_annual_cash_flows(config)
        annual_cash_flow = results.get("after_tax_cash_flow_per_owner", 0.0)

    # Return after-tax cash flow per owner (monthly = annual / 12)
    return annual_cash_flow / 12.0


def calculate_cash_on_cash(config: BaseCaseConfig, json_path: str, 
                           property_appreciation_rate: float = None,
                           projection_years: Optional[int] = None, **kwargs) -> float:
    """
    Calculate Cash-on-Cash return for any configuration.
    
    Cash-on-Cash = Annual Cash Flow / Initial Equity Investment
    
    This is a simple yield metric that shows the annual cash return
    as a percentage of the equity invested. Unlike IRR, it doesn't
    consider appreciation or time value of money - just Year 1 cash yield.
    
    Args:
        config: Configuration to test
        json_path: Path to assumptions (for projection defaults)
        property_appreciation_rate: Not used for CoC but kept for consistency
    
    Returns:
        Cash-on-Cash return as percentage (e.g., 5.5 means 5.5%)
    """
    proj_defaults = get_projection_defaults(json_path)
    ramp_up = int(kwargs.get('ramp_up_months', proj_defaults.get('ramp_up_months', 0)))
    renovation_months = int(kwargs.get('renovation_downtime_months', proj_defaults.get('renovation_downtime_months', 0)))
    renovation_frequency = int(kwargs.get('renovation_frequency_years', proj_defaults.get('renovation_frequency_years', 0)))

    year1_projection = compute_15_year_projection(
        config=config,
        start_year=proj_defaults.get('start_year', 2026),
        projection_years=1,
        inflation_rate=proj_defaults.get('inflation_rate', 0.01),
        property_appreciation_rate=proj_defaults.get('property_appreciation_rate', 0.025),
        ramp_up_months=ramp_up,
        renovation_downtime_months=renovation_months,
        renovation_frequency_years=renovation_frequency,
    )
    
    # Cash-on-Cash = Annual Cash Flow per Owner / Equity per Owner * 100
    equity_per_owner = config.financing.equity_per_owner
    annual_cash_flow_per_owner = year1_projection[0].get('cash_flow_per_owner', 0.0)
    
    if equity_per_owner == 0:
        return 0.0
    
    cash_on_cash_pct = (annual_cash_flow_per_owner / equity_per_owner) * 100
    
    return cash_on_cash_pct


def calculate_monthly_ncf(config: BaseCaseConfig, json_path: str, 
                          property_appreciation_rate: float = None,
                          projection_years: Optional[int] = None, **kwargs) -> float:
    """
    Calculate Monthly Net Cash Flow per Owner after taxes and debt service.
    
    This is the actual cash hitting each owner's bank account each month,
    after ALL expenses including mortgage payments (interest + principal).
    
    Monthly NCF = (Annual Cash Flow per Owner) / 12
    
    This is the most practical metric for owners who want to know:
    "How much cash will I receive/pay each month?"
    
    Args:
        config: Configuration to test
        json_path: Path to assumptions (for projection defaults)
        property_appreciation_rate: Not used but kept for consistency
    
    Returns:
        Monthly net cash flow per owner in CHF (can be negative!)
    """
    proj_defaults = get_projection_defaults(json_path)
    ramp_up = int(kwargs.get('ramp_up_months', proj_defaults.get('ramp_up_months', 0)))
    renovation_months = int(kwargs.get('renovation_downtime_months', proj_defaults.get('renovation_downtime_months', 0)))
    renovation_frequency = int(kwargs.get('renovation_frequency_years', proj_defaults.get('renovation_frequency_years', 0)))

    year1_projection = compute_15_year_projection(
        config=config,
        start_year=proj_defaults.get('start_year', 2026),
        projection_years=1,
        inflation_rate=proj_defaults.get('inflation_rate', 0.01),
        property_appreciation_rate=proj_defaults.get('property_appreciation_rate', 0.025),
        ramp_up_months=ramp_up,
        renovation_downtime_months=renovation_months,
        renovation_frequency_years=renovation_frequency,
    )

    # Monthly cash flow = Annual cash flow per owner / 12
    annual_cash_flow_per_owner = year1_projection[0].get('cash_flow_per_owner', 0.0)
    monthly_ncf = annual_cash_flow_per_owner / 12
    
    return monthly_ncf


# ═══════════════════════════════════════════════════════════════════════════
# UNIFIED SENSITIVITY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

def run_unified_sensitivity_analysis(
    json_path: str,
    case_name: str,
    metric_calculator: Callable,
    metric_name: str,
    verbose: bool = True,
    include_atcf: bool = False,
    projection_years: Optional[int] = None
) -> Dict:
    """
    Unified sensitivity analysis function that tests all parameters for any metric.
    
    This function eliminates code duplication by providing a single implementation
    that works for Equity IRR, Cash-on-Cash, Monthly NCF, and any other metric.
    
    Args:
        json_path: Path to assumptions JSON file
        case_name: Name of the case
        metric_calculator: Function that calculates the metric (e.g., calculate_equity_irr)
        metric_name: Name of the metric for display/export (e.g., "Equity IRR")
        verbose: Whether to print detailed output
        include_atcf: Whether to also calculate after-tax cash flow per person (for dual metrics)
        projection_years: Horizon in years for projection-based metrics; if None, use defaults (15)
    
    Returns:
        Dictionary with all sensitivity results
    """
    if verbose:
        print("\n" + "=" * 70)
        print(f"MODEL SENSITIVITY ANALYSIS - {metric_name.upper()}")
        print("=" * 70)
    
    # Load base configuration
    base_config = create_base_case_config(json_path)
    proj_defaults = get_projection_defaults(json_path)
    years = projection_years if projection_years is not None else proj_defaults.get('projection_years', 15)
    
    # Calculate base metric (pass projection_years for horizon; CoC/NCF accept via **kwargs)
    base_metric = metric_calculator(base_config, json_path, projection_years=years)
    base_atcf = None
    if include_atcf:
        base_atcf = calculate_after_tax_cash_flow_per_person(base_config, json_path)
    
    if verbose:
        print(f"  Base Case {metric_name}: {base_metric:.2f}")
        if include_atcf:
            print(f"  Base Case After-Tax Cash Flow per Person (monthly): CHF {base_atcf:,.2f}")
    
    sensitivities = []
    
    # Test all parameters from MODEL_SENSITIVITY_PARAMETER_CONFIG
    for param_key, param_config in MODEL_SENSITIVITY_PARAMETER_CONFIG.items():
        # Get base value
        base_value = param_config['get_base_value'](base_config)
        
        # Calculate low and high values
        low_value, high_value = scale_low_high(
            base_value,
            param_config['low_factor'],
            param_config['high_factor'],
            param_config['clamp_min'],
            param_config['clamp_max']
        )
        
        # Handle special cases
        if param_key == 'winter_occupancy':
            modifier = modify_winter_occupancy
        elif param_key == 'ramp_up_months':
            # Ramp-up is a projection parameter, not config - handle specially
            modifier = None  # No config modification needed
        else:
            modifier = param_config['modifier']
        
        # Calculate metrics for base, low, and high
        base_metric_val = base_metric
        try:
            if param_key == 'ramp_up_months':
                # For ramp-up, pass as parameter to metric calculator
                low_metric_val = metric_calculator(base_config, json_path, projection_years=years, ramp_up_months=int(low_value))
                high_metric_val = metric_calculator(base_config, json_path, projection_years=years, ramp_up_months=int(high_value))
                low_config = base_config  # No config change
                high_config = base_config
            else:
                low_config = modifier(base_config, low_value)
                low_metric_val = metric_calculator(low_config, json_path, projection_years=years)
                high_config = modifier(base_config, high_value)
                high_metric_val = metric_calculator(high_config, json_path, projection_years=years)
        except Exception as e:
            if verbose:
                print(f"  Warning: Error testing {param_config['parameter_name']}: {e}")
            # Skip this parameter if there's an error
            continue
        
        # Calculate ATCF if needed
        low_atcf_val = None
        high_atcf_val = None
        if include_atcf:
            try:
                if param_key == 'ramp_up_months':
                    # For ramp-up, pass as parameter to ATCF calculator
                    low_atcf_val = calculate_after_tax_cash_flow_per_person(base_config, json_path, ramp_up_months=int(low_value))
                    high_atcf_val = calculate_after_tax_cash_flow_per_person(base_config, json_path, ramp_up_months=int(high_value))
                else:
                    low_atcf_val = calculate_after_tax_cash_flow_per_person(low_config, json_path)
                    high_atcf_val = calculate_after_tax_cash_flow_per_person(high_config, json_path)
            except (ValueError, KeyError, TypeError) as e:
                # If ATCF calculation fails (missing data, invalid config), use base value
                print(f"Warning: ATCF calculation failed for {param_config['parameter_name']}: {e}")
                low_atcf_val = base_atcf
                high_atcf_val = base_atcf
        
        # Package results
        result = create_sensitivity_result(
            param_config['parameter_name'],
            base_value,
            low_value,
            high_value,
            base_metric_val,
            low_metric_val,
            high_metric_val,
            param_config['range_pct'],
            base_atcf,
            low_atcf_val,
            high_atcf_val
        )
        sensitivities.append(result)
    
    # Handle special parameters (projection parameters, not config parameters)
    # These require special handling because they affect projection calculations, not config
    
    # 1. Property Appreciation Rate
    base_appr = proj_defaults['property_appreciation_rate']
    low_appr, high_appr = scale_low_high(
        base_appr,
        MODEL_SENSITIVITY_SPECIAL_FACTORS['property_appreciation'][0],
        MODEL_SENSITIVITY_SPECIAL_FACTORS['property_appreciation'][1],
        clamp_min=0.0,
        clamp_max=1.0
    )
    
    # For metrics that use projection (like IRR), test with different appreciation rates
    # For Year 1 metrics (like CoC, NCF), appreciation has no effect
    if metric_name in ['Equity IRR', 'Project IRR']:
        base_irr_appr = calculate_equity_irr(base_config, json_path, base_appr, projection_years=years)
        low_irr_appr = calculate_equity_irr(base_config, json_path, low_appr, projection_years=years)
        high_irr_appr = calculate_equity_irr(base_config, json_path, high_appr, projection_years=years)
        
        # ATCF doesn't change with appreciation (Year 1 metric)
        base_atcf_appr = base_atcf if include_atcf else None
        low_atcf_appr = base_atcf if include_atcf else None
        high_atcf_appr = base_atcf if include_atcf else None
        
        sensitivities.append(create_sensitivity_result(
            'Property Appreciation Rate',
            base_appr,
            low_appr,
            high_appr,
            base_irr_appr,
            low_irr_appr,
            high_irr_appr,
            40,
            base_atcf_appr,
            low_atcf_appr,
            high_atcf_appr
        ))
    else:
        # Year 1 metrics: appreciation has no effect
        sensitivities.append(create_sensitivity_result(
            'Property Appreciation Rate',
            base_appr,
            low_appr,
            high_appr,
            base_metric,
            base_metric,
            base_metric,
            40,
            base_atcf,
            base_atcf if include_atcf else None,
            base_atcf if include_atcf else None
        ))
    
    # 2. Inflation Rate
    base_inflation = proj_defaults['inflation_rate']
    low_inflation, high_inflation = scale_low_high(
        base_inflation,
        MODEL_SENSITIVITY_SPECIAL_FACTORS['inflation'][0],
        MODEL_SENSITIVITY_SPECIAL_FACTORS['inflation'][1],
        clamp_min=0.0
    )
    
    if metric_name in ['Equity IRR', 'Project IRR']:
        # Test inflation sensitivity for IRR (affects projection)
        def test_inflation_sensitivity(base_cfg, inflation_rate, ramp_up_months):
            compute_annual_cash_flows(base_cfg)
            projection = compute_15_year_projection(
                base_cfg,
                start_year=proj_defaults['start_year'],
                inflation_rate=inflation_rate,
                property_appreciation_rate=proj_defaults['property_appreciation_rate'],
                projection_years=years,
                ramp_up_months=ramp_up_months,
                renovation_downtime_months=proj_defaults.get('renovation_downtime_months', 0),
                renovation_frequency_years=proj_defaults.get('renovation_frequency_years', 0)
            )
            irr_results = calculate_irrs_from_projection(
                projection,
                base_cfg.financing.total_initial_investment_per_owner,
                projection[-1]['property_value'],
                projection[-1]['remaining_loan_balance'],
                base_cfg.financing.num_owners,
                base_cfg.financing.purchase_price,
                proj_defaults['selling_costs_rate'],
                proj_defaults['discount_rate'],
                proj_defaults.get('capital_gains_tax_rate', 0.02),
                proj_defaults.get('property_transfer_tax_sale_rate', 0.015)
            )
            return irr_results['equity_irr_with_sale_pct']
        
        ramp_up = proj_defaults.get('ramp_up_months', 0)
        base_irr_inflation = base_metric
        low_irr_inflation = test_inflation_sensitivity(base_config, low_inflation, ramp_up)
        high_irr_inflation = test_inflation_sensitivity(base_config, high_inflation, ramp_up)
        
        sensitivities.append(create_sensitivity_result(
            'Inflation Rate',
            base_inflation,
            low_inflation,
            high_inflation,
            base_irr_inflation,
            low_irr_inflation,
            high_irr_inflation,
            100
        ))
    else:
        # Year 1 metrics: inflation has minimal/no effect
        sensitivities.append(create_sensitivity_result(
            'Inflation Rate',
            base_inflation,
            low_inflation,
            high_inflation,
            base_metric,
            base_metric,
            base_metric,
            100
        ))
    
    # 3. Selling Costs Rate
    base_selling_rate = proj_defaults['selling_costs_rate']
    low_selling, high_selling = scale_low_high(
        base_selling_rate,
        MODEL_SENSITIVITY_SPECIAL_FACTORS['selling_costs'][0],
        MODEL_SENSITIVITY_SPECIAL_FACTORS['selling_costs'][1],
        clamp_min=0.05
    )
    
    if metric_name in ['Equity IRR', 'Project IRR']:
        # Test selling costs sensitivity for IRR (affects exit value)
        def test_selling_costs_irr(base_cfg, selling_rate, ramp_up_months):
            compute_annual_cash_flows(base_cfg)
            projection = compute_15_year_projection(
                base_cfg,
                start_year=proj_defaults['start_year'],
                inflation_rate=proj_defaults['inflation_rate'],
                property_appreciation_rate=proj_defaults['property_appreciation_rate'],
                projection_years=years,
                ramp_up_months=ramp_up_months,
                renovation_downtime_months=proj_defaults.get('renovation_downtime_months', 0),
                renovation_frequency_years=proj_defaults.get('renovation_frequency_years', 0)
            )
            irr_results = calculate_irrs_from_projection(
                projection,
                base_cfg.financing.total_initial_investment_per_owner,
                projection[-1]['property_value'],
                projection[-1]['remaining_loan_balance'],
                base_cfg.financing.num_owners,
                base_cfg.financing.purchase_price,
                selling_rate,
                proj_defaults['discount_rate'],
                proj_defaults.get('capital_gains_tax_rate', 0.02),
                proj_defaults.get('property_transfer_tax_sale_rate', 0.015)
            )
            return irr_results['equity_irr_with_sale_pct']
        
        ramp_up = proj_defaults.get('ramp_up_months', 0)
        base_irr_selling = base_metric
        low_irr_selling = test_selling_costs_irr(base_config, low_selling, ramp_up)
        high_irr_selling = test_selling_costs_irr(base_config, high_selling, ramp_up)
        
        # Selling costs don't affect Year 1 cash flow
        base_atcf_selling = base_atcf if include_atcf else None
        low_atcf_selling = base_atcf if include_atcf else None
        high_atcf_selling = base_atcf if include_atcf else None
        
        sensitivities.append(create_sensitivity_result(
            'Selling Costs Rate',
            base_selling_rate,
            low_selling,
            high_selling,
            base_irr_selling,
            low_irr_selling,
            high_irr_selling,
            26,
            base_atcf_selling,
            low_atcf_selling,
            high_atcf_selling
        ))
    else:
        # Year 1 metrics: selling costs have no effect
        sensitivities.append(create_sensitivity_result(
            'Selling Costs Rate',
            base_selling_rate,
            low_selling,
            high_selling,
            base_metric,
            base_metric,
            base_metric,
            26
        ))
    
    # Sort by impact (most impactful first - for tornado chart)
    sensitivities.sort(key=lambda x: x['impact'], reverse=True)
    
    if verbose:
        print(f"\n  Top 5 impactful parameters:")
        for i, sens in enumerate(sensitivities[:5], 1):
            print(f"    {i}. {sens['parameter']:<35} Impact: ±{sens['impact']:.2f}")
    
    # Package and export results
    # Handle different metric name formats for backward compatibility
    if metric_name == 'Equity IRR':
        output_data = {
            'base_irr': base_metric,
            'sensitivities': sensitivities,
            'sorted_by': 'impact',
            'analysis_type': 'tornado_chart',
            'metric': 'Project IRR'
        }
        if include_atcf:
            output_data['base_atcf'] = base_atcf
    elif metric_name == 'Cash-on-Cash':
        output_data = {
            'base_coc': base_metric,
            'sensitivities': sensitivities,
            'sorted_by': 'impact',
            'analysis_type': 'tornado_chart',
            'metric': 'Cash-on-Cash'
        }
    elif metric_name == 'Monthly NCF':
        output_data = {
            'base_ncf': base_metric,
            'sensitivities': sensitivities,
            'sorted_by': 'impact',
            'analysis_type': 'tornado_chart',
            'metric': 'Monthly NCF'
        }
    else:
        # Generic format
        output_data = {
            f'base_{metric_name.lower().replace(" ", "_")}': base_metric,
            'sensitivities': sensitivities,
            'sorted_by': 'impact',
            'analysis_type': 'tornado_chart',
            'metric': metric_name
        }
    
    return output_data


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API - MAIN SENSITIVITY ANALYSIS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def run_sensitivity_analysis(json_path: str, case_name: str, verbose: bool = True) -> Dict:
    """
    Run Model Sensitivity analysis on Equity IRR and After-Tax Cash Flow per Person for 15 key parameters.
    
    This analysis produces data for TWO tornado charts:
    1. After-Tax Cash Flow per Person (Year 1 cash flow impact)
    2. Equity IRR (per-horizon return impact)
    
    Runs sensitivity for each horizon in HORIZONS and stores results in by_horizon; top-level
    sensitivities are the 15-year run for backward compatibility.
    
    Args:
        json_path: Path to assumptions JSON file
        case_name: Name of the case
        verbose: Whether to print detailed output
    
    Returns:
        Dictionary with all sensitivity results including:
        - base_irr: Base case Equity IRR (15Y)
        - base_atcf: Base case After-Tax Cash Flow per Person
        - sensitivities: List of parameter sensitivity results (15Y)
        - by_horizon: { "5": {...}, "10": {...}, ..., "40": {...} } with sensitivities per horizon
    """
    by_horizon = {}
    output_data_15 = None
    for horizon in HORIZONS:
        out = run_unified_sensitivity_analysis(
            json_path=json_path,
            case_name=case_name,
            metric_calculator=calculate_equity_irr,
            metric_name='Equity IRR',
            verbose=verbose if horizon == 15 else False,
            include_atcf=True,
            projection_years=horizon
        )
        by_horizon[str(horizon)] = {
            'sensitivities': out.get('sensitivities', []),
            'base_irr': out.get('base_irr'),
            'base_atcf': out.get('base_atcf'),
        }
        if horizon == 15:
            output_data_15 = out
    output_data = output_data_15
    output_data['by_horizon'] = by_horizon
    
    # Export to JSON (unified function doesn't export, we do it here for backward compatibility)
    output_path = save_json(output_data, case_name, 'sensitivity')
    
    if verbose:
        print(f"\n[+] JSON exported: {output_path}")
    
    return output_data


def run_cash_on_cash_sensitivity_analysis(json_path: str, case_name: str, verbose: bool = True) -> Dict:
    """
    Run Model Sensitivity analysis on Cash-on-Cash return for all 15 parameters.
    
    Cash-on-Cash = Year 1 Annual Cash Flow / Initial Equity Investment
    
    This shows how much cash yield you get in the first year relative
    to your equity investment. Unlike IRR, this doesn't consider:
    - Property appreciation
    - Time value of money
    - Multi-year cash flows
    
    It's a simple "what's my cash yield?" metric that's easy to understand
    and compare to other investments like bonds or dividend stocks.
    
    This function is now a thin wrapper around run_unified_sensitivity_analysis().
    
    Args:
        json_path: Path to assumptions JSON file
        case_name: Name of the case
        verbose: Whether to print detailed output
    
    Returns:
        Dictionary with all sensitivity results
    """
    # Use unified function with Cash-on-Cash metric (Year 1 metric; same result for all horizons)
    output_data = run_unified_sensitivity_analysis(
        json_path=json_path,
        case_name=case_name,
        metric_calculator=calculate_cash_on_cash,
        metric_name='Cash-on-Cash',
        verbose=verbose,
        include_atcf=False
    )
    # Duplicate same result under each horizon for uniform UI (by_horizon[horizon]).
    # CoC is a Year-1 metric and does not vary by time horizon; the UI hides the horizon
    # bar for this view and shows a note that the metric is Year 1 only.
    output_data['by_horizon'] = {str(h): {'sensitivities': output_data.get('sensitivities', []), 'base_coc': output_data.get('base_coc')} for h in HORIZONS}
    
    # Export to JSON (unified function doesn't export, we do it here for backward compatibility)
    output_path = save_json(output_data, case_name, 'sensitivity_coc')
    
    if verbose:
        print(f"\n[+] JSON exported: {output_path}")
    
    return output_data


def run_monthly_ncf_sensitivity_analysis(json_path: str, case_name: str, verbose: bool = True) -> Dict:
    """
    Run Model Sensitivity analysis on Monthly Net Cash Flow per Owner.
    
    Monthly NCF = Annual Cash Flow per Owner / 12
    
    This shows how much cash each owner receives (or pays!) each month.
    This is the most practical metric for understanding actual cash position.
    
    Unlike IRR (which considers appreciation) or CoC (which shows annual %),
    this shows the actual CHF amount hitting your bank account monthly.
    
    This function is now a thin wrapper around run_unified_sensitivity_analysis().
    
    Args:
        json_path: Path to assumptions JSON file
        case_name: Name of the case
        verbose: Whether to print detailed output
    
    Returns:
        Dictionary with all sensitivity results
    """
    # Use unified function with Monthly NCF metric (Year 1 metric; same result for all horizons)
    output_data = run_unified_sensitivity_analysis(
        json_path=json_path,
        case_name=case_name,
        metric_calculator=calculate_monthly_ncf,
        metric_name='Monthly NCF',
        verbose=verbose,
        include_atcf=False
    )
    # Duplicate same result under each horizon for uniform UI (by_horizon[horizon]).
    # Monthly NCF is a Year-1 metric and does not vary by time horizon; the UI hides the
    # horizon bar for this view and shows a note that the metric is Year 1 only.
    output_data['by_horizon'] = {str(h): {'sensitivities': output_data.get('sensitivities', []), 'base_ncf': output_data.get('base_ncf')} for h in HORIZONS}
    
    # Export to JSON (unified function doesn't export, we do it here for backward compatibility)
    output_path = save_json(output_data, case_name, 'sensitivity_ncf')
    
    if verbose:
        print(f"\n[+] JSON exported: {output_path}")
    
    return output_data
