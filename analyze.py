"""
═══════════════════════════════════════════════════════════════════════════════
ENGELBERG PROPERTY INVESTMENT - UNIFIED ANALYSIS SCRIPT
═══════════════════════════════════════════════════════════════════════════════

OVERVIEW:
    This is the MAIN script for running all financial analyses. It combines
    base case analysis, sensitivity analysis, and Monte Carlo simulation into
    a single, easy-to-use tool.

PURPOSE:
    Run financial analyses for the Engelberg vacation property investment.
    Analyzes different ownership scenarios and financing options.

USAGE:
    python run_analysis.py [assumptions_file] [options]
    
    Examples:
        python run_analysis.py                           # All analyses, base case
        python run_analysis.py assumptions_migros.json   # All analyses, Migros
        python run_analysis.py --analysis base           # Only base case
        python run_analysis.py --analysis sensitivity    # Only sensitivity
        python run_analysis.py --analysis monte_carlo    # Only Monte Carlo
        python run_analysis.py --quiet                   # Minimal output

WHAT IT DOES:
    1. BASE CASE ANALYSIS
       - Calculates annual cash flows (revenue, expenses, debt service)
       - Projects 15 years with inflation and appreciation
       - Calculates IRR, NPV, MOIC, payback period
       - Exports to JSON for dashboard

    2. SENSITIVITY ANALYSIS
       - Tests how Project IRR changes when parameters vary
       - Creates tornado chart data (parameters ranked by impact)
       - 8 key parameters analyzed (appreciation, maintenance, etc.)
       - Shows which assumptions matter most

    3. MONTE CARLO SIMULATION
       - Runs 1,000 probabilistic scenarios
       - Accounts for uncertainty in occupancy, rates, expenses
       - Calculates statistical distributions and probabilities
       - Shows risk profile of investment

OUTPUT:
    - JSON files: website/data/{case_name}_*.json
    - Console: Key metrics and results
    - Dashboard: Visualizations at website/index.html

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Callable
from dataclasses import replace

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: IMPORTS
# Import all necessary functions from the core simulation engine
# ═══════════════════════════════════════════════════════════════════════════

from core_engine import (
    # Configuration loaders
    create_base_case_config,        # Loads and validates assumptions from JSON
    get_projection_defaults,        # Gets inflation, appreciation, selling costs, etc.
    
    # Calculation functions
    compute_annual_cash_flows,      # Calculates Year 1 revenue, expenses, cash flow
    compute_15_year_projection,     # Projects 15 years with inflation/appreciation
    calculate_irrs_from_projection, # Calculates IRR, NPV, MOIC, payback period
    
    # Export functions
    export_base_case_to_json,       # Exports base case results to JSON
    export_sensitivity_to_json,     # Exports sensitivity results to JSON
    export_monte_carlo_to_json,     # Exports Monte Carlo results to JSON
    
    # Data structures
    BaseCaseConfig,                 # Main configuration object
    FinancingParams,                # Financing parameters
    RentalParams,                   # Rental income parameters
    ExpenseParams                   # Operating expense parameters
)

# Import Monte Carlo functions
from monte_carlo_engine import (
    run_monte_carlo_simulation,     # Runs probabilistic simulations
    calculate_statistics            # Calculates summary statistics from simulations
)


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: HELPER FUNCTIONS
# Utility functions used across multiple analyses
# ═══════════════════════════════════════════════════════════════════════════

def extract_case_name(json_path: str) -> str:
    """
    Extract case name from assumptions file path.
    
    Examples:
        assumptions.json → base_case
        assumptions_migros.json → migros
        assumptions_3_owners.json → 3_owners
    
    Args:
        json_path: Path to assumptions JSON file
    
    Returns:
        Case name string
    """
    basename = os.path.basename(json_path)
    
    if basename == "assumptions.json":
        return "base_case"
    elif basename.startswith("assumptions_") and basename.endswith(".json"):
        # Remove "assumptions_" prefix and ".json" suffix
        return basename[12:-5]
    else:
        return "base_case"


def save_json(data: Dict, case_name: str, analysis_type: str) -> str:
    """
    Save analysis results to JSON file.
    
    Args:
        data: Dictionary with analysis results
        case_name: Name of the case (e.g., 'base_case', 'migros')
        analysis_type: Type of analysis (e.g., 'base_case_analysis', 'sensitivity')
    
    Returns:
        Path to saved file
    """
    os.makedirs("website/data", exist_ok=True)
    output_path = f"website/data/{case_name}_{analysis_type}.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    return output_path


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: BASE CASE ANALYSIS
# Calculates the core financial metrics for Year 1 and 15-year projection
# ═══════════════════════════════════════════════════════════════════════════

def run_base_case_analysis(json_path: str, case_name: str, verbose: bool = True) -> Dict:
    """
    Run base case financial analysis.
    
    WHAT IT DOES:
        1. Loads all assumptions from JSON file
        2. Calculates Year 1 cash flows (revenue, expenses, debt service)
        3. Projects 15 years forward with inflation and appreciation
        4. Calculates IRR, NPV, MOIC, and payback period
        5. Exports results to JSON for dashboard
    
    KEY CALCULATIONS:
        - Gross Rental Income = Occupancy × Daily Rate × Available Nights
        - Net Operating Income = Revenue - Operating Expenses
        - Cash Flow = NOI - Debt Service (interest + amortization)
        - IRR = Discount rate where NPV of all cash flows = 0
    
    Args:
        json_path: Path to assumptions JSON file
        case_name: Name of the case (for file naming)
        verbose: Whether to print detailed output
    
    Returns:
        Dictionary with complete analysis results
    """
    if verbose:
        print("\n" + "=" * 70)
        print("BASE CASE ANALYSIS")
        print("=" * 70)
    
    # Step 1: Load configuration from JSON
    config = create_base_case_config(json_path)
    proj_defaults = get_projection_defaults(json_path)
    
    # Step 2: Calculate Year 1 annual cash flows
    # This computes revenue, all expenses, NOI, debt service, and final cash flow
    results = compute_annual_cash_flows(config)
    
    # Step 3: Project 15 years forward
    # Applies inflation to revenue/expenses and appreciation to property value
    projection = compute_15_year_projection(
        config,
        start_year=proj_defaults['start_year'],
        inflation_rate=proj_defaults['inflation_rate'],
        property_appreciation_rate=proj_defaults['property_appreciation_rate']
    )
    
    # Step 4: Calculate return metrics
    # IRR, NPV, MOIC, payback period - includes selling costs at year 15
    final_property_value = projection[-1]['property_value']
    final_loan_balance = projection[-1]['remaining_loan_balance']
    
    irr_results = calculate_irrs_from_projection(
        projection,
        results['equity_per_owner'],
        final_property_value,
        final_loan_balance,
        config.financing.num_owners,
        config.financing.purchase_price,
        proj_defaults['selling_costs_rate'],
        proj_defaults['discount_rate']
    )
    
    # Step 5: Display key results
    if verbose:
        print(f"\n{'KEY METRICS':-^70}")
        print(f"  Cash Flow per Owner:         CHF {results['cash_flow_per_owner']:>15,.0f}")
        print(f"  Equity IRR (15Y):            {irr_results['equity_irr_with_sale_pct']:>19.2f}%")
        print(f"  Project IRR:                 {irr_results['project_irr_with_sale_pct']:>19.2f}%")
        print(f"  NPV @ 5%:                    CHF {irr_results['npv_at_5pct']:>15,.0f}")
        print(f"  MOIC:                        {irr_results['moic']:>19.2f}x")
    
    # Step 6: Export to JSON
    json_data = export_base_case_to_json(config, results, projection, irr_results)
    output_path = save_json(json_data, case_name, 'base_case_analysis')
    
    if verbose:
        print(f"\n[+] JSON exported: {output_path}")
    
    return json_data


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: SENSITIVITY ANALYSIS
# Tests how Equity IRR changes when key parameters vary (tornado chart)
# ═══════════════════════════════════════════════════════════════════════════

def calculate_equity_irr(config: BaseCaseConfig, json_path: str, 
                         property_appreciation_rate: float = None) -> float:
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
    
    Returns:
        Equity IRR as percentage (e.g., 4.5 means 4.5%)
    """
    # Load projection parameters
    proj_defaults = get_projection_defaults(json_path)
    appreciation_rate = property_appreciation_rate if property_appreciation_rate is not None else proj_defaults['property_appreciation_rate']
    
    # Calculate results
    results = compute_annual_cash_flows(config)
    projection = compute_15_year_projection(
        config,
        start_year=proj_defaults['start_year'],
        inflation_rate=proj_defaults['inflation_rate'],
        property_appreciation_rate=appreciation_rate
    )
    
    # Get IRR
    irr_results = calculate_irrs_from_projection(
        projection,
        results['equity_per_owner'],
        projection[-1]['property_value'],
        projection[-1]['remaining_loan_balance'],
        config.financing.num_owners,
        config.financing.purchase_price,
        proj_defaults['selling_costs_rate'],
        proj_defaults['discount_rate']
    )
    
    return irr_results['equity_irr_with_sale_pct']


def calculate_cash_on_cash(config: BaseCaseConfig, json_path: str, 
                           property_appreciation_rate: float = None) -> float:
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
    # Calculate Year 1 results
    results = compute_annual_cash_flows(config)
    
    # Cash-on-Cash = Annual Cash Flow per Owner / Equity per Owner * 100
    equity_per_owner = results['equity_per_owner']
    annual_cash_flow_per_owner = results['cash_flow_per_owner']
    
    if equity_per_owner == 0:
        return 0.0
    
    cash_on_cash_pct = (annual_cash_flow_per_owner / equity_per_owner) * 100
    
    return cash_on_cash_pct


def calculate_monthly_ncf(config: BaseCaseConfig, json_path: str, 
                          property_appreciation_rate: float = None) -> float:
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
    # Calculate Year 1 results
    results = compute_annual_cash_flows(config)
    
    # Monthly cash flow = Annual cash flow per owner / 12
    annual_cash_flow_per_owner = results['cash_flow_per_owner']
    monthly_ncf = annual_cash_flow_per_owner / 12
    
    return monthly_ncf


def create_sensitivity_result(param_name: str, base_value: float, 
                              low_value: float, high_value: float,
                              base_irr: float, low_irr: float, high_irr: float,
                              range_pct: float) -> Dict:
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
    
    Returns:
        Dictionary with sensitivity results
    """
    return {
        'parameter': param_name,
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


def test_parameter_sensitivity(base_config: BaseCaseConfig, json_path: str,
                               param_name: str, base_value: float,
                               low_value: float, high_value: float,
                               modify_config: Callable, range_pct: float) -> Dict:
    """
    Test sensitivity of a single parameter.
    
    WORKFLOW:
        1. Calculate base case Project IRR
        2. Modify parameter to low value → calculate new IRR
        3. Modify parameter to high value → calculate new IRR
        4. Return results showing impact
    
    Args:
        base_config: Base case configuration
        json_path: Path to assumptions file
        param_name: Name of parameter (for display)
        base_value: Base case value
        low_value: Low scenario value
        high_value: High scenario value
        modify_config: Function that modifies config with new value
        range_pct: Percentage range being tested
    
    Returns:
        Dictionary with sensitivity results
    """
    # Calculate IRRs for base, low, and high scenarios
    base_irr = calculate_equity_irr(base_config, json_path)
    
    low_config = modify_config(base_config, low_value)
    low_irr = calculate_equity_irr(low_config, json_path)
    
    high_config = modify_config(base_config, high_value)
    high_irr = calculate_equity_irr(high_config, json_path)
    
    # Package results
    return create_sensitivity_result(
        param_name, base_value, low_value, high_value,
        base_irr, low_irr, high_irr, range_pct
    )


def run_sensitivity_analysis(json_path: str, case_name: str, verbose: bool = True) -> Dict:
    """
    Run sensitivity analysis on Equity IRR for 15 key parameters.
    
    PARAMETERS TESTED:
        1. Property Appreciation Rate (±1%) - Usually most impactful
        2. Maintenance Reserve Rate (±0.5%)
        3. Property Management Fee (±5%)
        4. Purchase Price (±10%)
        5. Occupancy Rate (±10%)
        6. Average Daily Rate (±20%)
        7. Interest Rate (±1%)
        8. LTV - Loan to Value (±10%)
        9. Inflation Rate (±0.5%) - NEW!
        10. Amortization Rate (0% to 2%) - NEW!
        11. Cleaning Cost per Stay (±30%) - NEW!
        12. Average Length of Stay (±30%) - NEW!
        13. Insurance Rate (0.3% to 0.5%) - NEW!
        14. Winter Season Occupancy (±15%) - NEW!
        15. Selling Costs Rate (±2%) - NEW!
    
    METHODOLOGY:
        - Vary each parameter while holding others constant
        - Calculate resulting Equity IRR
        - Rank by impact (for tornado chart)
        - Export ranked results
    
    Args:
        json_path: Path to assumptions JSON file
        case_name: Name of the case
        verbose: Whether to print detailed output
    
    Returns:
        Dictionary with all sensitivity results
    """
    if verbose:
        print("\n" + "=" * 70)
        print("SENSITIVITY ANALYSIS")
        print("=" * 70)
    
    # Load base configuration
    base_config = create_base_case_config(json_path)
    base_irr = calculate_equity_irr(base_config, json_path)
    
    if verbose:
        print(f"  Base Case Equity IRR: {base_irr:.2f}%")
    
    sensitivities = []
    
    # ───────────────────────────────────────────────────────────────────────
    # Test 1: Property Appreciation Rate (±1%)
    # ───────────────────────────────────────────────────────────────────────
    # Property appreciation is typically the most impactful parameter because
    # it directly affects terminal value (sale price at year 15)
    
    proj_defaults = get_projection_defaults(json_path)
    base_appr = proj_defaults['property_appreciation_rate']
    low_appr = 0.015  # 1.5%
    high_appr = 0.035  # 3.5%
    
    base_irr_appr = calculate_equity_irr(base_config, json_path, base_appr)
    low_irr_appr = calculate_equity_irr(base_config, json_path, low_appr)
    high_irr_appr = calculate_equity_irr(base_config, json_path, high_appr)
    
    sensitivities.append(create_sensitivity_result(
        'Property Appreciation Rate', base_appr, low_appr, high_appr,
        base_irr_appr, low_irr_appr, high_irr_appr, 40
    ))
    
    # ───────────────────────────────────────────────────────────────────────
    # Test 2: Maintenance Reserve Rate (±0.5%)
    # ───────────────────────────────────────────────────────────────────────
    # Maintenance is a large annual expense (0.7% of CHF 1.3M = CHF 9,100/year)
    # Testing 0.2% to 1.2% range
    
    base_maint = base_config.expenses.maintenance_rate
    sensitivities.append(test_parameter_sensitivity(
        base_config, json_path,
        'Maintenance Reserve Rate', base_maint,
        base_maint - 0.005, base_maint + 0.005,
        lambda cfg, val: replace(cfg, expenses=replace(cfg.expenses, maintenance_rate=val)),
        100
    ))
    
    # ───────────────────────────────────────────────────────────────────────
    # Test 3: Property Management Fee (±5%)
    # ───────────────────────────────────────────────────────────────────────
    # Management fee is 20% of gross revenue (can range 15-25%)
    
    base_mgmt = base_config.expenses.property_management_fee_rate
    sensitivities.append(test_parameter_sensitivity(
        base_config, json_path,
        'Property Management Fee', base_mgmt,
        base_mgmt - 0.05, base_mgmt + 0.05,
        lambda cfg, val: replace(cfg, expenses=replace(cfg.expenses, property_management_fee_rate=val)),
        50
    ))
    
    # ───────────────────────────────────────────────────────────────────────
    # Test 4: Purchase Price (±10%)
    # ───────────────────────────────────────────────────────────────────────
    # Tests sensitivity to negotiation and market timing
    
    base_price = base_config.financing.purchase_price
    sensitivities.append(test_parameter_sensitivity(
        base_config, json_path,
        'Purchase Price', base_price,
        base_price * 0.90, base_price * 1.10,
        lambda cfg, val: replace(cfg, financing=replace(cfg.financing, purchase_price=val)),
        20
    ))
    
    # ───────────────────────────────────────────────────────────────────────
    # Test 5: Occupancy Rate (±10%)
    # ───────────────────────────────────────────────────────────────────────
    # Tests impact of better/worse rental performance
    # NOTE: Must modify seasonal occupancy rates, not just the legacy field
    
    base_occ = base_config.rental.occupancy_rate
    def modify_occupancy(cfg, multiplier):
        new_seasons = []
        for season in cfg.rental.seasons:
            new_season = replace(season, occupancy_rate=season.occupancy_rate * multiplier)
            new_seasons.append(new_season)
        return replace(cfg, rental=replace(cfg.rental, seasons=new_seasons, occupancy_rate=base_occ * multiplier))
    
    sensitivities.append(test_parameter_sensitivity(
        base_config, json_path,
        'Occupancy Rate', base_occ,
        base_occ * 0.90, base_occ * 1.10,
        lambda cfg, val: modify_occupancy(cfg, val / base_occ),
        20
    ))
    
    # ───────────────────────────────────────────────────────────────────────
    # Test 6: Average Daily Rate (±20%)
    # ───────────────────────────────────────────────────────────────────────
    # Tests pricing strategy impact
    # NOTE: Must modify seasonal rates, not just the legacy field
    
    base_rate = base_config.rental.average_daily_rate
    def modify_daily_rate(cfg, multiplier):
        new_seasons = []
        for season in cfg.rental.seasons:
            new_season = replace(season, average_daily_rate=season.average_daily_rate * multiplier)
            new_seasons.append(new_season)
        return replace(cfg, rental=replace(cfg.rental, seasons=new_seasons, average_daily_rate=base_rate * multiplier))
    
    sensitivities.append(test_parameter_sensitivity(
        base_config, json_path,
        'Average Daily Rate', base_rate,
        base_rate * 0.80, base_rate * 1.20,
        lambda cfg, val: modify_daily_rate(cfg, val / base_rate),
        40
    ))
    
    # ───────────────────────────────────────────────────────────────────────
    # Test 7: Interest Rate (±1%)
    # ───────────────────────────────────────────────────────────────────────
    # Tests refinancing risk or different financing options
    
    base_int = base_config.financing.interest_rate
    sensitivities.append(test_parameter_sensitivity(
        base_config, json_path,
        'Interest Rate', base_int,
        base_int - 0.01, base_int + 0.01,
        lambda cfg, val: replace(cfg, financing=replace(cfg.financing, interest_rate=val)),
        154
    ))
    
    # ───────────────────────────────────────────────────────────────────────
    # Test 8: LTV - Loan to Value (±10%)
    # ───────────────────────────────────────────────────────────────────────
    # Tests different leverage scenarios
    
    base_ltv = base_config.financing.ltv
    sensitivities.append(test_parameter_sensitivity(
        base_config, json_path,
        'Loan-to-Value (LTV)', base_ltv,
        base_ltv * 0.90, min(base_ltv * 1.10, 0.95),
        lambda cfg, val: replace(cfg, financing=replace(cfg.financing, ltv=val)),
        20
    ))
    
    # ───────────────────────────────────────────────────────────────────────
    # Test 9: Inflation Rate (±0.5%)
    # ───────────────────────────────────────────────────────────────────────
    # Tests impact of different inflation scenarios on revenue and expenses
    # Inflation affects both revenue growth and expense growth over 15 years
    
    base_inflation = proj_defaults['inflation_rate']
    # For inflation, we need a special approach since it's a projection parameter
    def test_inflation_sensitivity(base_cfg, inflation_rate):
        results = compute_annual_cash_flows(base_cfg)
        projection = compute_15_year_projection(
            base_cfg,
            start_year=proj_defaults['start_year'],
            inflation_rate=inflation_rate,  # VARIED
            property_appreciation_rate=proj_defaults['property_appreciation_rate']
        )
        irr_results = calculate_irrs_from_projection(
            projection,
            results['equity_per_owner'],
            projection[-1]['property_value'],
            projection[-1]['remaining_loan_balance'],
            base_cfg.financing.num_owners,
            base_cfg.financing.purchase_price,
            proj_defaults['selling_costs_rate'],
            proj_defaults['discount_rate']
        )
        return irr_results['equity_irr_with_sale_pct']
    
    low_inflation = base_inflation - 0.005
    high_inflation = base_inflation + 0.005
    base_irr_inflation = test_inflation_sensitivity(base_config, base_inflation)
    low_irr_inflation = test_inflation_sensitivity(base_config, low_inflation)
    high_irr_inflation = test_inflation_sensitivity(base_config, high_inflation)
    
    sensitivities.append(create_sensitivity_result(
        'Inflation Rate', base_inflation, low_inflation, high_inflation,
        base_irr_inflation, low_irr_inflation, high_irr_inflation, 100
    ))
    
    # ───────────────────────────────────────────────────────────────────────
    # Test 10: Amortization Rate (0% to 2%)
    # ───────────────────────────────────────────────────────────────────────
    # Tests interest-only (0%) vs aggressive paydown (2%)
    # Lower amortization = better cash flow but more debt at exit
    
    base_amort = base_config.financing.amortization_rate
    sensitivities.append(test_parameter_sensitivity(
        base_config, json_path,
        'Amortization Rate', base_amort,
        0.0, 0.02,
        lambda cfg, val: replace(cfg, financing=replace(cfg.financing, amortization_rate=val)),
        200
    ))
    
    # ───────────────────────────────────────────────────────────────────────
    # Test 11: Cleaning Cost per Stay (±30%)
    # ───────────────────────────────────────────────────────────────────────
    # Tests negotiating power with cleaning services
    # With ~130 turnovers/year, this is a meaningful expense
    
    base_clean = base_config.expenses.cleaning_cost_per_stay
    sensitivities.append(test_parameter_sensitivity(
        base_config, json_path,
        'Cleaning Cost per Stay', base_clean,
        base_clean * 0.70, base_clean * 1.30,
        lambda cfg, val: replace(cfg, expenses=replace(cfg.expenses, cleaning_cost_per_stay=val)),
        60
    ))
    
    # ───────────────────────────────────────────────────────────────────────
    # Test 12: Average Length of Stay (±30%)
    # ───────────────────────────────────────────────────────────────────────
    # Tests impact of marketing to encourage longer stays
    # Longer stays = fewer turnovers = lower cleaning costs
    
    base_los = base_config.expenses.average_length_of_stay
    sensitivities.append(test_parameter_sensitivity(
        base_config, json_path,
        'Average Length of Stay', base_los,
        base_los * 0.70, base_los * 1.30,
        lambda cfg, val: replace(cfg, expenses=replace(cfg.expenses, average_length_of_stay=val)),
        60
    ))
    
    # ───────────────────────────────────────────────────────────────────────
    # Test 13: Insurance Rate (±25%)
    # ───────────────────────────────────────────────────────────────────────
    # Tests shopping around for better insurance rates
    # Range: 0.3% to 0.5% of property value
    
    base_insurance_rate = 0.004  # Current rate from assumptions
    def modify_insurance(cfg, new_rate):
        new_insurance = cfg.financing.purchase_price * new_rate
        return replace(cfg, expenses=replace(cfg.expenses, insurance_annual=new_insurance))
    
    low_insurance_rate = 0.003
    high_insurance_rate = 0.005
    sensitivities.append(test_parameter_sensitivity(
        base_config, json_path,
        'Insurance Rate', base_insurance_rate,
        low_insurance_rate, high_insurance_rate,
        lambda cfg, val: modify_insurance(cfg, val),
        50
    ))
    
    # ───────────────────────────────────────────────────────────────────────
    # Test 14: Seasonal Occupancy Spread (Winter Season ±15%)
    # ───────────────────────────────────────────────────────────────────────
    # Tests targeted marketing to boost high-season occupancy
    # Winter is the premium season (ski season)
    
    winter_season = [s for s in base_config.rental.seasons if s.name == "Winter Peak (Ski Season)"][0]
    base_winter_occ = winter_season.occupancy_rate
    
    def modify_winter_occupancy(cfg, new_occ_rate):
        new_seasons = []
        for season in cfg.rental.seasons:
            if season.name == "Winter Peak (Ski Season)":
                new_season = replace(season, occupancy_rate=new_occ_rate)
            else:
                new_season = season
            new_seasons.append(new_season)
        return replace(cfg, rental=replace(cfg.rental, seasons=new_seasons))
    
    sensitivities.append(test_parameter_sensitivity(
        base_config, json_path,
        'Winter Season Occupancy', base_winter_occ,
        base_winter_occ * 0.85, min(base_winter_occ * 1.15, 0.95),
        lambda cfg, val: modify_winter_occupancy(cfg, val),
        30
    ))
    
    # ───────────────────────────────────────────────────────────────────────
    # Test 15: Selling Costs Rate (±2%)
    # ───────────────────────────────────────────────────────────────────────
    # Tests impact of transaction costs at sale (broker, notary, transfer tax)
    
    base_selling_rate = proj_defaults['selling_costs_rate']
    # Special approach for selling costs since it affects IRR calculation
    def test_selling_costs_irr(base_cfg, selling_rate):
        results = compute_annual_cash_flows(base_cfg)
        projection = compute_15_year_projection(
            base_cfg,
            start_year=proj_defaults['start_year'],
            inflation_rate=proj_defaults['inflation_rate'],
            property_appreciation_rate=proj_defaults['property_appreciation_rate']
        )
        irr_results = calculate_irrs_from_projection(
            projection,
            results['equity_per_owner'],
            projection[-1]['property_value'],
            projection[-1]['remaining_loan_balance'],
            base_cfg.financing.num_owners,
            base_cfg.financing.purchase_price,
            selling_rate,  # VARIED
            proj_defaults['discount_rate']
        )
        return irr_results['equity_irr_with_sale_pct']
    
    low_selling = max(base_selling_rate - 0.02, 0.05)
    high_selling = base_selling_rate + 0.02
    base_irr_selling = test_selling_costs_irr(base_config, base_selling_rate)
    low_irr_selling = test_selling_costs_irr(base_config, low_selling)
    high_irr_selling = test_selling_costs_irr(base_config, high_selling)
    
    sensitivities.append(create_sensitivity_result(
        'Selling Costs Rate', base_selling_rate, low_selling, high_selling,
        base_irr_selling, low_irr_selling, high_irr_selling, 26
    ))
    
    # Sort by impact (most impactful first - for tornado chart)
    sensitivities.sort(key=lambda x: x['impact'], reverse=True)
    
    if verbose:
        print(f"\n  Top 5 impactful parameters:")
        for i, sens in enumerate(sensitivities[:5], 1):
            print(f"    {i}. {sens['parameter']:<35} Impact: ±{sens['impact']:.2f}%")
    
    # Package and export results
    output_data = {
        'base_irr': base_irr,
        'sensitivities': sensitivities,
        'sorted_by': 'impact',
        'analysis_type': 'tornado_chart',
        'metric': 'Project IRR'
    }
    
    output_path = save_json(output_data, case_name, 'sensitivity')
    
    if verbose:
        print(f"\n[+] JSON exported: {output_path}")
    
    return output_data


def run_cash_on_cash_sensitivity_analysis(json_path: str, case_name: str, verbose: bool = True) -> Dict:
    """
    Run sensitivity analysis on Cash-on-Cash return for all 15 parameters.
    
    Cash-on-Cash = Year 1 Annual Cash Flow / Initial Equity Investment
    
    This shows how much cash yield you get in the first year relative
    to your equity investment. Unlike IRR, this doesn't consider:
    - Property appreciation
    - Time value of money
    - Multi-year cash flows
    
    It's a simple "what's my cash yield?" metric that's easy to understand
    and compare to other investments like bonds or dividend stocks.
    
    PARAMETERS TESTED: Same 14 as Equity IRR sensitivity
    
    Args:
        json_path: Path to assumptions JSON file
        case_name: Name of the case
        verbose: Whether to print detailed output
    
    Returns:
        Dictionary with all sensitivity results
    """
    if verbose:
        print("\n" + "=" * 70)
        print("CASH-ON-CASH SENSITIVITY ANALYSIS")
        print("=" * 70)
    
    # Load base configuration
    base_config = create_base_case_config(json_path)
    base_coc = calculate_cash_on_cash(base_config, json_path)
    
    if verbose:
        print(f"  Base Case Cash-on-Cash: {base_coc:.2f}%")
    
    sensitivities = []
    proj_defaults = get_projection_defaults(json_path)
    
    # Use the same test helper but with calculate_cash_on_cash instead
    def test_coc_parameter(base_cfg, param_name, base_val, low_val, high_val, modify_fn, range_pct):
        base_coc = calculate_cash_on_cash(base_cfg, json_path)
        low_cfg = modify_fn(base_cfg, low_val)
        low_coc = calculate_cash_on_cash(low_cfg, json_path)
        high_cfg = modify_fn(base_cfg, high_val)
        high_coc = calculate_cash_on_cash(high_cfg, json_path)
        return create_sensitivity_result(
            param_name, base_val, low_val, high_val,
            base_coc, low_coc, high_coc, range_pct
        )
    
    # Test all 14 parameters (same as Equity IRR sensitivity)
    
    # 1. Property Appreciation (doesn't affect Year 1 CoC, but include for consistency)
    base_appr = proj_defaults['property_appreciation_rate']
    sensitivities.append(create_sensitivity_result(
        'Property Appreciation Rate', base_appr, 0.015, 0.035,
        base_coc, base_coc, base_coc, 40  # No impact on Year 1 cash
    ))
    
    # 2. Maintenance Reserve Rate
    base_maint = base_config.expenses.maintenance_rate
    sensitivities.append(test_coc_parameter(
        base_config, 'Maintenance Reserve Rate', base_maint,
        base_maint - 0.005, base_maint + 0.005,
        lambda cfg, val: replace(cfg, expenses=replace(cfg.expenses, maintenance_rate=val)),
        100
    ))
    
    # 3. Property Management Fee
    base_mgmt = base_config.expenses.property_management_fee_rate
    sensitivities.append(test_coc_parameter(
        base_config, 'Property Management Fee', base_mgmt,
        base_mgmt - 0.05, base_mgmt + 0.05,
        lambda cfg, val: replace(cfg, expenses=replace(cfg.expenses, property_management_fee_rate=val)),
        50
    ))
    
    # 4. Purchase Price
    base_price = base_config.financing.purchase_price
    sensitivities.append(test_coc_parameter(
        base_config, 'Purchase Price', base_price,
        base_price * 0.90, base_price * 1.10,
        lambda cfg, val: replace(cfg, financing=replace(cfg.financing, purchase_price=val)),
        20
    ))
    
    # 5. Occupancy Rate (modify seasonal data)
    base_occ = base_config.rental.occupancy_rate
    def modify_occupancy(cfg, multiplier):
        new_seasons = []
        for season in cfg.rental.seasons:
            new_season = replace(season, occupancy_rate=season.occupancy_rate * multiplier)
            new_seasons.append(new_season)
        return replace(cfg, rental=replace(cfg.rental, seasons=new_seasons, occupancy_rate=base_occ * multiplier))
    
    sensitivities.append(test_coc_parameter(
        base_config, 'Occupancy Rate', base_occ,
        base_occ * 0.90, base_occ * 1.10,
        lambda cfg, val: modify_occupancy(cfg, val / base_occ),
        20
    ))
    
    # 6. Average Daily Rate (modify seasonal data)
    base_rate = base_config.rental.average_daily_rate
    def modify_daily_rate(cfg, multiplier):
        new_seasons = []
        for season in cfg.rental.seasons:
            new_season = replace(season, average_daily_rate=season.average_daily_rate * multiplier)
            new_seasons.append(new_season)
        return replace(cfg, rental=replace(cfg.rental, seasons=new_seasons, average_daily_rate=base_rate * multiplier))
    
    sensitivities.append(test_coc_parameter(
        base_config, 'Average Daily Rate', base_rate,
        base_rate * 0.80, base_rate * 1.20,
        lambda cfg, val: modify_daily_rate(cfg, val / base_rate),
        40
    ))
    
    # 7. Interest Rate
    base_int = base_config.financing.interest_rate
    sensitivities.append(test_coc_parameter(
        base_config, 'Interest Rate', base_int,
        base_int - 0.01, base_int + 0.01,
        lambda cfg, val: replace(cfg, financing=replace(cfg.financing, interest_rate=val)),
        154
    ))
    
    # 8. LTV
    base_ltv = base_config.financing.ltv
    sensitivities.append(test_coc_parameter(
        base_config, 'Loan-to-Value (LTV)', base_ltv,
        base_ltv * 0.90, min(base_ltv * 1.10, 0.95),
        lambda cfg, val: replace(cfg, financing=replace(cfg.financing, ltv=val)),
        20
    ))
    
    # 9. Inflation Rate (doesn't affect Year 1, but include for consistency)
    base_inflation = proj_defaults['inflation_rate']
    sensitivities.append(create_sensitivity_result(
        'Inflation Rate', base_inflation, base_inflation - 0.005, base_inflation + 0.005,
        base_coc, base_coc, base_coc, 100  # No impact on Year 1 cash
    ))
    
    # 10. Amortization Rate
    base_amort = base_config.financing.amortization_rate
    sensitivities.append(test_coc_parameter(
        base_config, 'Amortization Rate', base_amort,
        0.0, 0.02,
        lambda cfg, val: replace(cfg, financing=replace(cfg.financing, amortization_rate=val)),
        200
    ))
    
    # 11. Cleaning Cost per Stay
    base_clean = base_config.expenses.cleaning_cost_per_stay
    sensitivities.append(test_coc_parameter(
        base_config, 'Cleaning Cost per Stay', base_clean,
        base_clean * 0.70, base_clean * 1.30,
        lambda cfg, val: replace(cfg, expenses=replace(cfg.expenses, cleaning_cost_per_stay=val)),
        60
    ))
    
    # 12. Average Length of Stay
    base_los = base_config.expenses.average_length_of_stay
    sensitivities.append(test_coc_parameter(
        base_config, 'Average Length of Stay', base_los,
        base_los * 0.70, base_los * 1.30,
        lambda cfg, val: replace(cfg, expenses=replace(cfg.expenses, average_length_of_stay=val)),
        60
    ))
    
    # 13. Insurance Rate
    def modify_insurance(cfg, new_rate):
        new_insurance = cfg.financing.purchase_price * new_rate
        return replace(cfg, expenses=replace(cfg.expenses, insurance_annual=new_insurance))
    
    sensitivities.append(test_coc_parameter(
        base_config, 'Insurance Rate', 0.004,
        0.003, 0.005,
        lambda cfg, val: modify_insurance(cfg, val),
        50
    ))
    
    # 14. Winter Season Occupancy
    winter_season = [s for s in base_config.rental.seasons if s.name == "Winter Peak (Ski Season)"][0]
    base_winter_occ = winter_season.occupancy_rate
    
    def modify_winter_occupancy(cfg, new_occ_rate):
        new_seasons = []
        for season in cfg.rental.seasons:
            if season.name == "Winter Peak (Ski Season)":
                new_season = replace(season, occupancy_rate=new_occ_rate)
            else:
                new_season = season
            new_seasons.append(new_season)
        return replace(cfg, rental=replace(cfg.rental, seasons=new_seasons))
    
    sensitivities.append(test_coc_parameter(
        base_config, 'Winter Season Occupancy', base_winter_occ,
        base_winter_occ * 0.85, min(base_winter_occ * 1.15, 0.95),
        lambda cfg, val: modify_winter_occupancy(cfg, val),
        30
    ))
    
    # 15. Selling Costs Rate (doesn't affect Year 1 CoC, but include for consistency)
    base_selling_rate = proj_defaults['selling_costs_rate']
    sensitivities.append(create_sensitivity_result(
        'Selling Costs Rate', base_selling_rate, 
        max(base_selling_rate - 0.02, 0.05), base_selling_rate + 0.02,
        base_coc, base_coc, base_coc, 26  # No impact on Year 1 cash
    ))
    
    # Sort by impact
    sensitivities.sort(key=lambda x: x['impact'], reverse=True)
    
    if verbose:
        print(f"\n  Top 5 impactful parameters:")
        for i, sens in enumerate(sensitivities[:5], 1):
            print(f"    {i}. {sens['parameter']:<35} Impact: ±{sens['impact']:.2f}%")
    
    # Package and export results
    output_data = {
        'base_coc': base_coc,
        'sensitivities': sensitivities,
        'sorted_by': 'impact',
        'analysis_type': 'tornado_chart',
        'metric': 'Cash-on-Cash'
    }
    
    output_path = save_json(output_data, case_name, 'sensitivity_coc')
    
    if verbose:
        print(f"\n[+] JSON exported: {output_path}")
    
    return output_data


def run_monthly_ncf_sensitivity_analysis(json_path: str, case_name: str, verbose: bool = True) -> Dict:
    """
    Run sensitivity analysis on Monthly Net Cash Flow per Owner.
    
    Monthly NCF = Annual Cash Flow per Owner / 12
    
    This shows how much cash each owner receives (or pays!) each month.
    This is the most practical metric for understanding actual cash position.
    
    Unlike IRR (which considers appreciation) or CoC (which shows annual %),
    this shows the actual CHF amount hitting your bank account monthly.
    
    PARAMETERS TESTED: Same 15 as other sensitivity analyses
    
    Note: Some parameters (appreciation, selling costs) don't affect monthly
    cash flow since they only impact the exit at Year 15.
    
    Args:
        json_path: Path to assumptions JSON file
        case_name: Name of the case
        verbose: Whether to print detailed output
    
    Returns:
        Dictionary with all sensitivity results
    """
    if verbose:
        print("\n" + "=" * 70)
        print("MONTHLY NET CASH FLOW SENSITIVITY ANALYSIS")
        print("=" * 70)
    
    # Load base configuration
    base_config = create_base_case_config(json_path)
    base_ncf = calculate_monthly_ncf(base_config, json_path)
    
    if verbose:
        print(f"  Base Case Monthly NCF: CHF {base_ncf:.0f}")
    
    sensitivities = []
    proj_defaults = get_projection_defaults(json_path)
    
    # Helper to test NCF sensitivity
    def test_ncf_parameter(base_cfg, param_name, base_val, low_val, high_val, modify_fn, range_pct):
        base_ncf = calculate_monthly_ncf(base_cfg, json_path)
        low_cfg = modify_fn(base_cfg, low_val)
        low_ncf = calculate_monthly_ncf(low_cfg, json_path)
        high_cfg = modify_fn(base_cfg, high_val)
        high_ncf = calculate_monthly_ncf(high_cfg, json_path)
        return create_sensitivity_result(
            param_name, base_val, low_val, high_val,
            base_ncf, low_ncf, high_ncf, range_pct
        )
    
    # Test all 15 parameters
    
    # 1. Property Appreciation (NO IMPACT on monthly cash flow - only affects exit)
    base_appr = proj_defaults['property_appreciation_rate']
    sensitivities.append(create_sensitivity_result(
        'Property Appreciation Rate', base_appr, 0.015, 0.035,
        base_ncf, base_ncf, base_ncf, 40  # No impact
    ))
    
    # 2. Maintenance Reserve Rate
    base_maint = base_config.expenses.maintenance_rate
    sensitivities.append(test_ncf_parameter(
        base_config, 'Maintenance Reserve Rate', base_maint,
        base_maint - 0.0025, base_maint + 0.0025,
        lambda cfg, val: replace(cfg, expenses=replace(cfg.expenses, maintenance_rate=val)),
        100
    ))
    
    # 3. Property Management Fee
    base_mgmt = base_config.expenses.property_management_fee_rate
    sensitivities.append(test_ncf_parameter(
        base_config, 'Management Fee Rate', base_mgmt,
        base_mgmt - 0.02, base_mgmt + 0.02,
        lambda cfg, val: replace(cfg, expenses=replace(cfg.expenses, property_management_fee_rate=val)),
        20
    ))
    
    # 4. Purchase Price
    base_price = base_config.financing.purchase_price
    sensitivities.append(test_ncf_parameter(
        base_config, 'Purchase Price', base_price,
        base_price * 0.85, base_price * 1.15,
        lambda cfg, val: replace(cfg, financing=replace(cfg.financing, purchase_price=val)),
        30
    ))
    
    # 5. Interest Rate - MAJOR IMPACT on monthly payments
    base_rate = base_config.financing.interest_rate
    sensitivities.append(test_ncf_parameter(
        base_config, 'Interest Rate', base_rate,
        base_rate - 0.01, base_rate + 0.01,
        lambda cfg, val: replace(cfg, financing=replace(cfg.financing, interest_rate=val)),
        150
    ))
    
    # 6. Loan-to-Value (LTV)
    base_ltv = base_config.financing.ltv
    sensitivities.append(test_ncf_parameter(
        base_config, 'Loan-to-Value (LTV)', base_ltv,
        base_ltv * 0.9, base_ltv * 1.1,
        lambda cfg, val: replace(cfg, financing=replace(cfg.financing, ltv=val)),
        20
    ))
    
    # 7. Average Daily Rate (ADR)
    def modify_adr(cfg, new_adr_multiplier):
        new_seasons = []
        for season in cfg.rental.seasons:
            new_seasons.append(replace(season, average_daily_rate=season.average_daily_rate * new_adr_multiplier))
        return replace(cfg, rental=replace(cfg.rental, seasons=new_seasons))
    
    base_adr = sum(s.average_daily_rate for s in base_config.rental.seasons) / len(base_config.rental.seasons)
    low_ncf = calculate_monthly_ncf(modify_adr(base_config, 0.85), json_path)
    high_ncf = calculate_monthly_ncf(modify_adr(base_config, 1.15), json_path)
    sensitivities.append(create_sensitivity_result(
        'Average Daily Rate', base_adr, base_adr * 0.85, base_adr * 1.15,
        base_ncf, low_ncf, high_ncf, 30
    ))
    
    # 8. Occupancy Rate
    def modify_occupancy(cfg, new_occ_multiplier):
        new_seasons = []
        for season in cfg.rental.seasons:
            new_seasons.append(replace(season, occupancy_rate=min(0.95, season.occupancy_rate * new_occ_multiplier)))
        return replace(cfg, rental=replace(cfg.rental, seasons=new_seasons))
    
    base_occ = sum(s.occupancy_rate for s in base_config.rental.seasons) / len(base_config.rental.seasons)
    low_ncf = calculate_monthly_ncf(modify_occupancy(base_config, 0.85), json_path)
    high_ncf = calculate_monthly_ncf(modify_occupancy(base_config, 1.15), json_path)
    sensitivities.append(create_sensitivity_result(
        'Occupancy Rate', base_occ, base_occ * 0.85, min(0.95, base_occ * 1.15),
        base_ncf, low_ncf, high_ncf, 30
    ))
    
    # 9. Inflation Rate (minimal monthly impact - mostly long-term)
    base_infl = proj_defaults['inflation_rate']
    sensitivities.append(create_sensitivity_result(
        'Inflation Rate', base_infl, 0.005, 0.015,
        base_ncf, base_ncf, base_ncf, 100  # No Year 1 impact
    ))
    
    # 10. Amortization Rate - MAJOR IMPACT (principal paydown)
    base_amort = base_config.financing.amortization_rate
    sensitivities.append(test_ncf_parameter(
        base_config, 'Amortization Rate', base_amort,
        0.0, 0.02,  # 0% (interest-only) to 2%
        lambda cfg, val: replace(cfg, financing=replace(cfg.financing, amortization_rate=val)),
        200
    ))
    
    # 11. Cleaning Cost per Stay
    base_cleaning = base_config.expenses.cleaning_cost_per_stay
    sensitivities.append(test_ncf_parameter(
        base_config, 'Cleaning Cost per Stay', base_cleaning,
        base_cleaning * 0.7, base_cleaning * 1.3,
        lambda cfg, val: replace(cfg, expenses=replace(cfg.expenses, cleaning_cost_per_stay=val)),
        60
    ))
    
    # 12. Average Length of Stay (in ExpenseParams, affects cleaning frequency)
    base_length = base_config.expenses.average_length_of_stay
    sensitivities.append(test_ncf_parameter(
        base_config, 'Average Length of Stay', base_length,
        base_length * 0.7, base_length * 1.3,
        lambda cfg, val: replace(cfg, expenses=replace(cfg.expenses, average_length_of_stay=val)),
        60
    ))
    
    # 13. Insurance (annual amount, derived from rate)
    base_ins = base_config.expenses.insurance_annual
    purchase_price = base_config.financing.purchase_price
    base_ins_rate = base_ins / purchase_price if purchase_price > 0 else 0.004
    # Test ±0.1% insurance rate
    low_ins = purchase_price * 0.003   # 0.3% rate
    high_ins = purchase_price * 0.005  # 0.5% rate
    sensitivities.append(test_ncf_parameter(
        base_config, 'Insurance Rate', base_ins_rate,
        0.003, 0.005,
        lambda cfg, val: replace(cfg, expenses=replace(cfg.expenses, insurance_annual=purchase_price * val)),
        50
    ))
    
    # 14. Winter Season Occupancy
    def modify_winter_occupancy(cfg, new_winter_occ):
        new_seasons = []
        for season in cfg.rental.seasons:
            if season.name == 'Winter':
                new_seasons.append(replace(season, occupancy_rate=new_winter_occ))
            else:
                new_seasons.append(season)
        return replace(cfg, rental=replace(cfg.rental, seasons=new_seasons))
    
    base_winter_occ = next((s.occupancy_rate for s in base_config.rental.seasons if s.name == 'Winter'), 0.75)
    sensitivities.append(test_ncf_parameter(
        base_config, 'Winter Season Occupancy', base_winter_occ,
        base_winter_occ * 0.85, min(0.95, base_winter_occ * 1.15),
        modify_winter_occupancy,
        30
    ))
    
    # 15. Selling Costs Rate (NO IMPACT on monthly cash - only at exit)
    base_sell = proj_defaults['selling_costs_rate']
    sensitivities.append(create_sensitivity_result(
        'Selling Costs Rate', base_sell, 0.058, 0.098,
        base_ncf, base_ncf, base_ncf, 50  # No impact on monthly
    ))
    
    # Sort by impact (highest first)
    sensitivities.sort(key=lambda x: x['impact'], reverse=True)
    
    if verbose:
        print(f"\n  Top 5 impactful parameters:")
        for i, sens in enumerate(sensitivities[:5], 1):
            print(f"    {i}. {sens['parameter']:<35} Impact: ±CHF {sens['impact']:.0f}")
    
    # Prepare output
    output_data = {
        'case_name': case_name,
        'base_ncf': base_ncf,
        'sensitivities': sensitivities,
        'sorted_by': 'impact',
        'analysis_type': 'tornado_chart',
        'metric': 'Monthly NCF'
    }
    
    output_path = save_json(output_data, case_name, 'sensitivity_ncf')
    
    if verbose:
        print(f"\n[+] JSON exported: {output_path}")
    
    return output_data


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: MONTE CARLO SIMULATION
# Runs probabilistic simulations to assess risk and uncertainty
# ═══════════════════════════════════════════════════════════════════════════

def run_monte_carlo_analysis(json_path: str, case_name: str, 
                             n_simulations: int = 1000, verbose: bool = True) -> Dict:
    """
    Run Monte Carlo simulation to assess investment risk.
    
    WHAT IT DOES:
        - Runs N simulations (default 1,000)
        - Each simulation randomly varies:
          * Occupancy rates (by season)
          * Daily rates (by season)
          * Operating expenses
        - Calculates NPV and IRR for each simulation
        - Computes statistics (mean, median, percentiles)
    
    WHY IT'S USEFUL:
        Shows the range of possible outcomes and their probabilities.
        Helps understand investment risk beyond just the base case.
    
    FEATURES:
        - Correlations: Related variables move together
        - Seasonality: Winter and summer vary differently
        - Expense variation: Realistic cost uncertainty
    
    Args:
        json_path: Path to assumptions JSON file
        case_name: Name of the case
        n_simulations: Number of simulations to run
        verbose: Whether to print output
    
    Returns:
        Dictionary with simulation results
    """
    if verbose:
        print("\n" + "=" * 70)
        print("MONTE CARLO SIMULATION")
        print("=" * 70)
        print(f"  Running {n_simulations} simulations...")
    
    # Load configuration
    config = create_base_case_config(json_path)
    
    # Run simulations
    # This returns a DataFrame with one row per simulation
    df = run_monte_carlo_simulation(config, num_simulations=n_simulations)
    
    # Calculate summary statistics
    stats = calculate_statistics(df)
    
    if verbose:
        print(f"\n{'SIMULATION RESULTS':-^70}")
        print(f"  Mean NPV:                    CHF {stats['npv']['mean']:>15,.0f}")
        print(f"  Median NPV:                  CHF {stats['npv']['median']:>15,.0f}")
        print(f"  Std Dev:                     CHF {stats['npv']['std']:>15,.0f}")
    
    # Export results
    json_data = export_monte_carlo_to_json(df, stats)
    output_path = save_json(json_data, case_name, 'monte_carlo')
    
    if verbose:
        print(f"\n[+] JSON exported: {output_path}")
    
    return json_data


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: MAIN PROGRAM
# Command-line interface and orchestration
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """
    Main function - orchestrates all analyses based on command-line arguments.
    
    COMMAND-LINE OPTIONS:
        assumptions_file: Which scenario to analyze (default: assumptions.json)
        --analysis: Which analysis to run (base, sensitivity, monte_carlo, all)
        --simulations: Number of Monte Carlo simulations (default: 1000)
        --quiet: Suppress detailed output
    
    WORKFLOW:
        1. Parse command-line arguments
        2. Extract case name from file path
        3. Run requested analyses
        4. Display summary
    """
    # ───────────────────────────────────────────────────────────────────────
    # Parse Command-Line Arguments
    # ───────────────────────────────────────────────────────────────────────
    
    parser = argparse.ArgumentParser(
        description='Run Engelberg property investment analyses',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_analysis.py                        # All analyses for base case
  python run_analysis.py assumptions_migros.json # All analyses for Migros
  python run_analysis.py --analysis base         # Only base case
  python run_analysis.py --analysis sensitivity  # Only sensitivity
  python run_analysis.py --simulations 5000      # 5,000 Monte Carlo sims
  python run_analysis.py --quiet                 # Minimal output
        """
    )
    
    parser.add_argument(
        'assumptions_file', 
        nargs='?', 
        default='assumptions.json',
        help='Path to assumptions JSON file (default: assumptions.json)'
    )
    
    parser.add_argument(
        '--analysis', '-a',
        choices=['all', 'base', 'sensitivity', 'monte_carlo'],
        default='all',
        help='Which analysis to run (default: all)'
    )
    
    parser.add_argument(
        '--simulations', '-n',
        type=int,
        default=1000,
        help='Number of Monte Carlo simulations (default: 1000)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress detailed output'
    )
    
    args = parser.parse_args()
    
    # ───────────────────────────────────────────────────────────────────────
    # Setup and Validation
    # ───────────────────────────────────────────────────────────────────────
    
    json_path = args.assumptions_file
    case_name = extract_case_name(json_path)
    verbose = not args.quiet
    
    # Check if assumptions file exists
    if not os.path.exists(json_path):
        print(f"❌ ERROR: Assumptions file not found: {json_path}")
        print(f"\nAvailable files:")
        import glob
        for f in glob.glob("assumptions*.json"):
            print(f"  • {f}")
        sys.exit(1)
    
    # ───────────────────────────────────────────────────────────────────────
    # Display Header
    # ───────────────────────────────────────────────────────────────────────
    
    if verbose:
        print("═" * 70)
        print("ENGELBERG PROPERTY INVESTMENT - UNIFIED ANALYSIS")
        print("═" * 70)
        print(f"\nCase: {case_name}")
        print(f"Assumptions File: {json_path}")
        print(f"Analysis Type: {args.analysis}")
        print()
    
    # ───────────────────────────────────────────────────────────────────────
    # Run Requested Analyses
    # ───────────────────────────────────────────────────────────────────────
    
    try:
        results = {}
        
        # Base Case Analysis
        if args.analysis in ['all', 'base']:
            results['base_case'] = run_base_case_analysis(json_path, case_name, verbose)
        
        # Sensitivity Analysis (Equity IRR)
        if args.analysis in ['all', 'sensitivity']:
            results['sensitivity'] = run_sensitivity_analysis(json_path, case_name, verbose)
            # Also run Cash-on-Cash sensitivity
            results['sensitivity_coc'] = run_cash_on_cash_sensitivity_analysis(json_path, case_name, verbose)
            # Also run Monthly NCF sensitivity
            results['sensitivity_ncf'] = run_monthly_ncf_sensitivity_analysis(json_path, case_name, verbose)
        
        # Monte Carlo Simulation
        if args.analysis in ['all', 'monte_carlo']:
            results['monte_carlo'] = run_monte_carlo_analysis(
                json_path, case_name, args.simulations, verbose
            )
        
        # ───────────────────────────────────────────────────────────────────
        # Display Summary
        # ───────────────────────────────────────────────────────────────────
        
        if verbose:
            print("\n" + "═" * 70)
            print("✅ ANALYSIS COMPLETE")
            print("═" * 70)
            print(f"\nGenerated files in website/data/:")
            for analysis_type in results.keys():
                filename = f"{case_name}_{analysis_type}.json"
                # Adjust filename for base_case_analysis
                if analysis_type == 'base_case':
                    filename = f"{case_name}_base_case_analysis.json"
                print(f"  • {filename}")
            print(f"\n📊 View results: website/index.html")
            print()
        
        return results
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# SCRIPT ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """
    Entry point when script is run directly.
    
    This allows the script to be:
    1. Run directly: python run_analysis.py
    2. Imported as module: from run_analysis import run_base_case_analysis
    """
    main()
