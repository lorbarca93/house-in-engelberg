"""
===============================================================================
ENGELBERG PROPERTY INVESTMENT - UNIFIED ANALYSIS SCRIPT
===============================================================================

OVERVIEW:
    This is the MAIN script for running all financial analyses. It combines
    base case analysis, Model Sensitivity analysis, and Monte Carlo simulation into
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

    2. MODEL SENSITIVITY ANALYSIS
       - Tests how Equity IRR and After-Tax Cash Flow per Person change when parameters vary
       - Creates dual tornado chart data (parameters ranked by impact for each metric)
       - 15 key parameters analyzed (appreciation, maintenance, interest rate, etc.)
       - Shows which assumptions matter most for both Year 1 cash flow and 15-year returns

    3. MONTE CARLO SIMULATION
       - Runs 1,000 probabilistic scenarios
       - Accounts for uncertainty in occupancy, rates, expenses
       - Calculates statistical distributions and probabilities
       - Shows risk profile of investment

OUTPUT:
    - JSON files: website/data/{case_name}_*.json
    - Console: Key metrics and results
    - Dashboard: Visualizations at website/index.html

===============================================================================
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any

# ===========================================================================
# SECTION 1: IMPORTS
# Import all necessary functions from the core simulation engine
# ===========================================================================

from engelberg.core import (
    # Constants
    HORIZONS,                        # Supported time horizons [5, 10, 15, ..., 40]
    # Configuration loaders
    create_base_case_config,        # Loads and validates assumptions from JSON
    get_projection_defaults,        # Gets inflation, appreciation, selling costs, etc.
    
    # Calculation functions
    compute_annual_cash_flows,      # Calculates Year 1 revenue, expenses, cash flow
    compute_15_year_projection,     # Projects N years with inflation/appreciation
    calculate_irrs_from_projection, # Calculates IRR, NPV, MOIC, payback period
    
    # Export functions
    export_base_case_to_json,       # Exports base case results to JSON
    export_sensitivity_to_json,     # Exports Model Sensitivity results to JSON
    export_monte_carlo_to_json,     # Exports Monte Carlo results to JSON
    export_monte_carlo_sensitivity_to_json,  # Exports MC Sensitivity results to JSON
    
    # Data structures
    BaseCaseConfig,                 # Main configuration object
    FinancingParams,                # Financing parameters
    LoanTranche,                    # Loan tranche structure
    RentalParams,                   # Rental income parameters
    ExpenseParams,                  # Operating expense parameters
    
    # Path resolution
    resolve_path,                   # Resolve paths relative to project root
    get_project_root,               # Get project root directory
    
    # Sensitivity functions
    apply_sensitivity                # Modify config with parameter changes
)

# Import Monte Carlo functions
from engelberg.monte_carlo import (
    run_monte_carlo_simulation,     # Runs probabilistic simulations
    calculate_statistics            # Calculates summary statistics from simulations
)


# ===========================================================================
# SECTION 2: HELPER FUNCTIONS
# Utility functions used across multiple analyses
# ===========================================================================

def extract_case_name(json_path: str) -> str:
    """
    Extract case name from assumptions file path.
    
    Examples:
        assumptions.json -> base_case
        assumptions_migros.json -> migros
        assumptions_3_owners.json -> 3_owners
    
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
        Path to saved file (relative to project root)
    """
    data_dir = resolve_path("website/data")
    os.makedirs(data_dir, exist_ok=True)
    output_path = os.path.join(data_dir, f"{case_name}_{analysis_type}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    # Return relative path for compatibility
    return f"website/data/{case_name}_{analysis_type}.json"


# ===========================================================================
# SECTION 3: BASE CASE ANALYSIS
# Calculates the core financial metrics for Year 1 and 15-year projection
# ===========================================================================

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
        - Gross Rental Income = Occupancy x Daily Rate x Available Nights
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
    
    # Step 2: Calculate Year 1 annual cash flows (account for ramp-up period)
    # This computes revenue, all expenses, NOI, debt service, and final cash flow
    ramp_up_months = proj_defaults.get('ramp_up_months', 0)
    renovation_downtime_months = proj_defaults.get('renovation_downtime_months', 0)
    renovation_frequency_years = proj_defaults.get('renovation_frequency_years', 0)
    operational_months_year1 = max(0, 12 - ramp_up_months)
    if renovation_frequency_years > 0 and renovation_downtime_months > 0 and 1 % renovation_frequency_years == 0:
        operational_months_year1 = max(0, operational_months_year1 - renovation_downtime_months)
    results = compute_annual_cash_flows(config, operational_months=operational_months_year1)
    
    # Year-1 KPIs (same for all horizons)
    kpis_year1 = {
        'cap_rate_pct': results.get('cap_rate_pct', 0),
        'cash_on_cash_return_pct': results.get('cash_on_cash_return_pct', 0),
        'debt_coverage_ratio': results.get('debt_coverage_ratio', 0),
        'operating_expense_ratio_pct': results.get('operating_expense_ratio_pct', 0),
        'blended_interest_rate': results.get('blended_interest_rate', config.financing.blended_interest_rate),
        'stress_overall_pass': results.get('stress_results', {}).get('overall_pass'),
    }
    
    def _irr_to_export(irr_results):
        """Build irr_results dict in same shape as export (for by_horizon)."""
        return {
            'equity_irr_with_sale_pct': irr_results.get('equity_irr_with_sale_pct', irr_results.get('irr_with_sale_pct', 0)),
            'equity_irr_without_sale_pct': irr_results.get('equity_irr_without_sale_pct', irr_results.get('irr_without_sale_pct', 0)),
            'project_irr_with_sale_pct': irr_results.get('project_irr_with_sale_pct', 0),
            'project_irr_without_sale_pct': irr_results.get('project_irr_without_sale_pct', 0),
            'sale_proceeds_per_owner': irr_results.get('sale_proceeds_per_owner', 0),
            'final_property_value': irr_results.get('final_property_value', 0),
            'final_loan_balance': irr_results.get('final_loan_balance', 0),
            'npv_at_5pct': irr_results.get('npv_at_5pct', 0),
            'moic': irr_results.get('moic', 0),
            'payback_period_years': irr_results.get('payback_period_years'),
            'gross_sale_price': irr_results.get('gross_sale_price', 0),
            'selling_costs': irr_results.get('selling_costs', 0),
            'capital_gains_tax': irr_results.get('capital_gains_tax', 0),
            'property_transfer_tax_sale': irr_results.get('property_transfer_tax_sale', 0),
            'net_sale_price': irr_results.get('net_sale_price', 0),
            'selling_costs_rate_pct': irr_results.get('selling_costs_rate_pct', 0),
            'capital_gains_tax_rate_pct': irr_results.get('capital_gains_tax_rate_pct', 0),
            'property_transfer_tax_sale_rate_pct': irr_results.get('property_transfer_tax_sale_rate_pct', 0),
        }
    
    # Step 3: Build by_horizon (projection + IRR + KPIs for each horizon)
    by_horizon = {}
    projection_15y = None
    irr_15y = None
    for horizon in HORIZONS:
        proj = compute_15_year_projection(
            config,
            start_year=proj_defaults['start_year'],
            inflation_rate=proj_defaults['inflation_rate'],
            property_appreciation_rate=proj_defaults['property_appreciation_rate'],
            projection_years=horizon,
            ramp_up_months=ramp_up_months,
            renovation_downtime_months=renovation_downtime_months,
            renovation_frequency_years=renovation_frequency_years
        )
        final_pv = proj[-1]['property_value']
        final_loan = proj[-1]['remaining_loan_balance']
        irr_out = calculate_irrs_from_projection(
            proj,
            config.financing.total_initial_investment_per_owner,
            final_pv,
            final_loan,
            config.financing.num_owners,
            config.financing.purchase_price,
            proj_defaults['selling_costs_rate'],
            proj_defaults['discount_rate'],
            proj_defaults.get('capital_gains_tax_rate', 0.02),
            proj_defaults.get('property_transfer_tax_sale_rate', 0.015)
        )
        by_horizon[str(horizon)] = {
            'projection': proj,
            'irr_results': _irr_to_export(irr_out),
            'kpis': kpis_year1
        }
        if horizon == 15:
            projection_15y = proj
            irr_15y = irr_out
    
    projection = projection_15y
    irr_results = irr_15y
    
    # Step 4: Display key results (15-year)
    if verbose:
        print(f"\n{'KEY METRICS':-^70}")
        print(f"  Cash Flow per Owner:         CHF {results['cash_flow_per_owner']:>15,.0f}")
        print(f"  Equity IRR (15Y):            {irr_results['equity_irr_with_sale_pct']:>19.2f}%")
        print(f"  Project IRR:                 {irr_results['project_irr_with_sale_pct']:>19.2f}%")
        print(f"  NPV @ 5%:                    CHF {irr_results['npv_at_5pct']:>15,.0f}")
        print(f"  MOIC:                        {irr_results['moic']:>19.2f}x")
    
    # Step 5: Export to JSON (top-level = 15-year; by_horizon = all horizons)
    json_data = export_base_case_to_json(config, results, projection, irr_results, by_horizon=by_horizon)
    output_path = save_json(json_data, case_name, 'base_case_analysis')
    
    if verbose:
        print(f"\n[+] JSON exported: {output_path}")
    
    return json_data


# ===========================================================================
# SECTION 4: MODEL SENSITIVITY ANALYSIS
# Model Sensitivity functions have been moved to engelberg.model_sensitivity
# Import them here for backward compatibility
# ===========================================================================

from engelberg.model_sensitivity import (
    run_sensitivity_analysis,
    run_cash_on_cash_sensitivity_analysis,
    run_monthly_ncf_sensitivity_analysis,
)

from engelberg.mc_sensitivity import (
    run_monte_carlo_sensitivity_analysis,
)

# ===========================================================================
# SECTION 5: MONTE CARLO SIMULATION
# Runs probabilistic simulations to assess risk and uncertainty
# ===========================================================================

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


# ===========================================================================
# SECTION 5B: LOAN STRUCTURE SENSITIVITY
# Compare KPI outcomes across alternative debt tranche structures
# ===========================================================================

def _clone_financing_with_tranches(
    base_financing: FinancingParams,
    loan_tranches: List[LoanTranche],
    saron_base_rate: float,
) -> FinancingParams:
    """Clone financing terms while replacing loan tranches."""
    return FinancingParams(
        purchase_price=base_financing.purchase_price,
        ltv=base_financing.ltv,
        interest_rate=base_financing.interest_rate,
        amortization_rate=base_financing.amortization_rate,
        num_owners=base_financing.num_owners,
        notary_fee_rate=base_financing.notary_fee_rate,
        legal_doc_fee_rate=base_financing.legal_doc_fee_rate,
        agency_fee_rate_buyer=base_financing.agency_fee_rate_buyer,
        inspection_chf=base_financing.inspection_chf,
        interior_designer_chf=base_financing.interior_designer_chf,
        furniture_chf=base_financing.furniture_chf,
        loan_tranches=loan_tranches,
        saron_base_rate=saron_base_rate,
        stress=base_financing.stress,
    )


def _extract_base_rate_anchors(financing: FinancingParams) -> Dict[str, float]:
    """
    Derive base rate anchors from configured tranches (or fallbacks).
    """
    saron_base = financing.effective_saron_base_rate
    default_short_fixed = financing.interest_rate + 0.0015
    default_long_fixed = financing.interest_rate + 0.0030
    default_saron_margin = max(0.0, financing.interest_rate - saron_base)

    fixed_tranches = sorted(
        [t for t in (financing.loan_tranches or []) if t.rate_type == "fixed"],
        key=lambda t: t.term_years or 0,
    )
    saron_tranches = [t for t in (financing.loan_tranches or []) if t.rate_type == "saron"]

    short_fixed_rate = (
        float(fixed_tranches[0].fixed_rate)
        if fixed_tranches and fixed_tranches[0].fixed_rate is not None
        else default_short_fixed
    )
    long_fixed_rate = (
        float(fixed_tranches[-1].fixed_rate)
        if fixed_tranches and fixed_tranches[-1].fixed_rate is not None
        else default_long_fixed
    )
    if long_fixed_rate < short_fixed_rate:
        long_fixed_rate = short_fixed_rate

    if saron_tranches:
        saron_margin = sum(float(t.saron_margin or 0.0) for t in saron_tranches) / len(saron_tranches)
    else:
        saron_margin = default_saron_margin if default_saron_margin > 0 else 0.009

    return {
        "saron_base_rate": saron_base,
        "saron_margin": saron_margin,
        "short_fixed_rate": short_fixed_rate,
        "long_fixed_rate": long_fixed_rate,
    }


def run_loan_structure_sensitivity_analysis(
    json_path: str,
    case_name: str,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Compare major KPIs across predefined loan structures:
    100% SARON, 100% fixed, staggered fixed, and mixed structures.
    """
    if verbose:
        print("\n" + "=" * 70)
        print("LOAN STRUCTURE SENSITIVITY")
        print("=" * 70)

    base_config = create_base_case_config(json_path)
    proj_defaults = get_projection_defaults(json_path)
    rate_anchors = _extract_base_rate_anchors(base_config.financing)
    num_owners = max(1, base_config.financing.num_owners)
    projection_years = int(proj_defaults.get("projection_years", 15))
    ramp_up_months = int(proj_defaults.get("ramp_up_months", 0))
    renovation_downtime_months = int(proj_defaults.get("renovation_downtime_months", 0))
    renovation_frequency_years = int(proj_defaults.get("renovation_frequency_years", 0))
    operational_months_year1 = max(0, 12 - ramp_up_months)
    if (
        renovation_frequency_years > 0
        and renovation_downtime_months > 0
        and (1 % renovation_frequency_years == 0)
    ):
        operational_months_year1 = max(0, operational_months_year1 - renovation_downtime_months)

    short_term = 7
    long_term = 10
    saron_base_rate = rate_anchors["saron_base_rate"]
    saron_margin = rate_anchors["saron_margin"]
    short_fixed_rate = rate_anchors["short_fixed_rate"]
    long_fixed_rate = rate_anchors["long_fixed_rate"]

    scenario_defs = [
        {
            "id": "saron_100",
            "name": "100% SARON",
            "description": "Fully floating-rate exposure with lowest initial fixed-rate lock-in.",
            "loan_tranches": [
                LoanTranche(
                    name="SARON",
                    share_of_loan=1.0,
                    rate_type="saron",
                    saron_margin=saron_margin,
                )
            ],
        },
        {
            "id": "fixed_100_10y",
            "name": "100% Fixed 10Y",
            "description": "Fully fixed rate for ten years with maximum payment stability.",
            "loan_tranches": [
                LoanTranche(
                    name="Fixed 10Y",
                    share_of_loan=1.0,
                    rate_type="fixed",
                    fixed_rate=long_fixed_rate,
                    term_years=long_term,
                )
            ],
        },
        {
            "id": "fixed_staggered_50_50",
            "name": "Staggered Fixed (50/50)",
            "description": "No SARON exposure, split between 5-7Y and 10Y fixed maturities.",
            "loan_tranches": [
                LoanTranche(
                    name="Fixed 5-7Y",
                    share_of_loan=0.5,
                    rate_type="fixed",
                    fixed_rate=short_fixed_rate,
                    term_years=short_term,
                ),
                LoanTranche(
                    name="Fixed 10Y",
                    share_of_loan=0.5,
                    rate_type="fixed",
                    fixed_rate=long_fixed_rate,
                    term_years=long_term,
                ),
            ],
        },
        {
            "id": "mixed_50_50",
            "name": "Mixed 50% SARON / 50% Fixed",
            "description": "Balanced floating/fixed split with staggered fixed maturities.",
            "loan_tranches": [
                LoanTranche(
                    name="SARON",
                    share_of_loan=0.5,
                    rate_type="saron",
                    saron_margin=saron_margin,
                ),
                LoanTranche(
                    name="Fixed 5-7Y",
                    share_of_loan=0.25,
                    rate_type="fixed",
                    fixed_rate=short_fixed_rate,
                    term_years=short_term,
                ),
                LoanTranche(
                    name="Fixed 10Y",
                    share_of_loan=0.25,
                    rate_type="fixed",
                    fixed_rate=long_fixed_rate,
                    term_years=long_term,
                ),
            ],
        },
        {
            "id": "mixed_60_40_laddered",
            "name": "Mixed 60% SARON / 40% Fixed Laddered",
            "description": "Recommended structure balancing current cash flow and rate-risk diversification.",
            "loan_tranches": [
                LoanTranche(
                    name="SARON",
                    share_of_loan=0.6,
                    rate_type="saron",
                    saron_margin=saron_margin,
                ),
                LoanTranche(
                    name="Fixed 5-7Y",
                    share_of_loan=0.25,
                    rate_type="fixed",
                    fixed_rate=short_fixed_rate,
                    term_years=short_term,
                ),
                LoanTranche(
                    name="Fixed 10Y",
                    share_of_loan=0.15,
                    rate_type="fixed",
                    fixed_rate=long_fixed_rate,
                    term_years=long_term,
                ),
            ],
        },
        {
            "id": "mixed_70_30",
            "name": "Mixed 70% SARON / 30% Fixed",
            "description": "Higher floating exposure to minimize base-case debt service.",
            "loan_tranches": [
                LoanTranche(
                    name="SARON",
                    share_of_loan=0.7,
                    rate_type="saron",
                    saron_margin=saron_margin,
                ),
                LoanTranche(
                    name="Fixed 5-7Y",
                    share_of_loan=0.2,
                    rate_type="fixed",
                    fixed_rate=short_fixed_rate,
                    term_years=short_term,
                ),
                LoanTranche(
                    name="Fixed 10Y",
                    share_of_loan=0.1,
                    rate_type="fixed",
                    fixed_rate=long_fixed_rate,
                    term_years=long_term,
                ),
            ],
        },
    ]

    scenario_results: List[Dict[str, Any]] = []
    for scenario in scenario_defs:
        scenario_financing = _clone_financing_with_tranches(
            base_financing=base_config.financing,
            loan_tranches=scenario["loan_tranches"],
            saron_base_rate=saron_base_rate,
        )
        scenario_config = BaseCaseConfig(
            financing=scenario_financing,
            rental=base_config.rental,
            expenses=base_config.expenses,
            projection=base_config.projection,
        )

        year1_results = compute_annual_cash_flows(
            scenario_config,
            operational_months=operational_months_year1,
        )
        projection = compute_15_year_projection(
            scenario_config,
            start_year=proj_defaults["start_year"],
            inflation_rate=proj_defaults["inflation_rate"],
            property_appreciation_rate=proj_defaults["property_appreciation_rate"],
            projection_years=projection_years,
            ramp_up_months=ramp_up_months,
            renovation_downtime_months=renovation_downtime_months,
            renovation_frequency_years=renovation_frequency_years,
        )
        irr_results = calculate_irrs_from_projection(
            projection=projection,
            initial_equity=scenario_financing.total_initial_investment_per_owner,
            final_property_value=projection[-1]["property_value"],
            final_loan_balance=projection[-1]["remaining_loan_balance"],
            num_owners=scenario_financing.num_owners,
            purchase_price=scenario_financing.purchase_price,
            selling_costs_rate=proj_defaults["selling_costs_rate"],
            discount_rate=proj_defaults["discount_rate"],
            capital_gains_tax_rate=proj_defaults.get("capital_gains_tax_rate", 0.02),
            property_transfer_tax_sale_rate=proj_defaults.get("property_transfer_tax_sale_rate", 0.015),
        )

        first_five = projection[: min(5, len(projection))]
        cumulative_cash_flow_after_tax_total = sum(
            float(row.get("after_tax_cash_flow_total", row.get("cash_flow_after_debt_service", 0.0)))
            for row in first_five
        )
        cumulative_amortization_total = sum(float(row.get("amortization_payment", 0.0)) for row in first_five)
        property_appreciation_total = (
            float(first_five[-1].get("property_value", 0.0)) - scenario_financing.purchase_price
            if first_five
            else 0.0
        )
        net_wealth_creation_total = (
            cumulative_cash_flow_after_tax_total
            + cumulative_amortization_total
            + property_appreciation_total
        )

        yearly_components: List[Dict[str, Any]] = []
        cumulative_wealth_per_owner = 0.0
        previous_property_value = scenario_financing.purchase_price
        for row in first_five:
            property_value = float(row.get("property_value", previous_property_value))
            annual_appreciation_per_owner = (property_value - previous_property_value) / num_owners
            after_tax_per_owner = float(
                row.get("after_tax_cash_flow_per_owner", row.get("cash_flow_per_owner", 0.0))
            )
            amortization_per_owner = float(row.get("amortization_payment", 0.0)) / num_owners
            net_wealth_delta_per_owner = (
                after_tax_per_owner + amortization_per_owner + annual_appreciation_per_owner
            )
            cumulative_wealth_per_owner += net_wealth_delta_per_owner
            yearly_components.append(
                {
                    "year": row.get("year"),
                    "year_number": row.get("year_number"),
                    "after_tax_cash_flow_per_owner": after_tax_per_owner,
                    "amortization_equity_per_owner": amortization_per_owner,
                    "appreciation_equity_per_owner": annual_appreciation_per_owner,
                    "net_wealth_delta_per_owner": net_wealth_delta_per_owner,
                    "cumulative_wealth_per_owner": cumulative_wealth_per_owner,
                    "equity_per_owner": (
                        (float(row.get("property_value", 0.0)) - float(row.get("remaining_loan_balance", 0.0)))
                        / num_owners
                    ),
                }
            )
            previous_property_value = property_value

        stress = year1_results.get("stress_results", {}) or {}
        stress_base = stress.get("base", {}) or {}
        stress_150 = stress.get("saron_150bps", {}) or {}
        stress_250 = stress.get("saron_250bps", {}) or {}
        has_saron_exposure = any(
            tranche.rate_type == "saron" for tranche in scenario["loan_tranches"]
        )
        base_dscr = float(stress_base.get("dscr", 0.0))
        dscr_150 = float(
            stress_150.get("dscr", base_dscr if not has_saron_exposure else 0.0)
        )
        dscr_250 = float(
            stress_250.get("dscr", base_dscr if not has_saron_exposure else 0.0)
        )

        scenario_results.append(
            {
                "id": scenario["id"],
                "name": scenario["name"],
                "description": scenario["description"],
                "loan_tranches": [
                    {
                        "name": t.name,
                        "share_of_loan": t.share_of_loan,
                        "rate_type": t.rate_type,
                        "fixed_rate": t.fixed_rate,
                        "saron_margin": t.saron_margin,
                        "term_years": t.term_years,
                    }
                    for t in scenario["loan_tranches"]
                ],
                "kpis": {
                    "blended_interest_rate": float(year1_results.get("blended_interest_rate", 0.0)),
                    "year1_debt_service": float(year1_results.get("debt_service", 0.0)),
                    "year1_interest_payment": float(year1_results.get("interest_payment", 0.0)),
                    "year1_amortization_payment": float(year1_results.get("amortization_payment", 0.0)),
                    "year1_after_tax_cash_flow_per_owner_monthly": float(
                        year1_results.get("after_tax_cash_flow_per_owner", 0.0)
                    )
                    / 12.0,
                    "year1_after_tax_cash_flow_total": float(
                        year1_results.get("after_tax_cash_flow_total", 0.0)
                    ),
                    "year1_dscr": float(year1_results.get("debt_coverage_ratio", 0.0)),
                    "equity_irr_with_sale_pct": float(irr_results.get("equity_irr_with_sale_pct", 0.0)),
                    "npv_at_5pct": float(irr_results.get("npv_at_5pct", 0.0)),
                    "moic": float(irr_results.get("moic", 0.0)),
                    "stress_overall_pass": bool(stress.get("overall_pass", False)),
                    "stress_dscr_base": base_dscr,
                    "stress_dscr_saron_150bps": dscr_150,
                    "stress_dscr_saron_250bps": dscr_250,
                    "has_saron_exposure": has_saron_exposure,
                },
                "equity_build_5y": {
                    "cash_flow_after_tax_total": cumulative_cash_flow_after_tax_total,
                    "cash_flow_after_tax_per_owner": cumulative_cash_flow_after_tax_total / num_owners,
                    "amortization_total": cumulative_amortization_total,
                    "amortization_per_owner": cumulative_amortization_total / num_owners,
                    "property_appreciation_total": property_appreciation_total,
                    "property_appreciation_per_owner": property_appreciation_total / num_owners,
                    "net_wealth_creation_total": net_wealth_creation_total,
                    "net_wealth_creation_per_owner": net_wealth_creation_total / num_owners,
                },
                "yearly_wealth_components_first5": yearly_components,
            }
        )

    ranking_by_irr = sorted(
        scenario_results,
        key=lambda s: s["kpis"]["equity_irr_with_sale_pct"],
        reverse=True,
    )
    ranking_by_cash = sorted(
        scenario_results,
        key=lambda s: s["kpis"]["year1_after_tax_cash_flow_per_owner_monthly"],
        reverse=True,
    )
    stress_passed = [s for s in ranking_by_irr if s["kpis"]["stress_overall_pass"]]
    recommended = stress_passed[0] if stress_passed else ranking_by_irr[0]

    out = {
        "analysis_type": "loan_structure_sensitivity",
        "case_name": case_name,
        "projection_years": projection_years,
        "assumptions": {
            "saron_base_rate": saron_base_rate,
            "saron_margin": saron_margin,
            "short_fixed_rate": short_fixed_rate,
            "long_fixed_rate": long_fixed_rate,
        },
        "stress_policy": {
            "base_dscr_min": float(proj_defaults.get("base_dscr_min", 1.20)),
            "saron_150_dscr_min": float(proj_defaults.get("saron_150_dscr_min", 1.05)),
            "saron_250_min_cash_flow": float(
                proj_defaults.get("saron_250_min_cash_flow", 0.0)
            ),
        },
        "recommended_scenario_id": recommended["id"],
        "ranking": {
            "by_equity_irr_desc": [s["id"] for s in ranking_by_irr],
            "by_monthly_cashflow_desc": [s["id"] for s in ranking_by_cash],
        },
        "scenarios": scenario_results,
    }

    output_path = save_json(out, case_name, "loan_structure_sensitivity")
    if verbose:
        print(f"  [+] JSON exported: {output_path}")
        print(f"  Recommended scenario: {recommended['name']} ({recommended['id']})")
    return out


# ===========================================================================
# SECTION 6: MAIN PROGRAM
# Command-line interface and orchestration
# ===========================================================================

def main():
    """
    Main function - orchestrates all analyses based on command-line arguments.
    
    COMMAND-LINE OPTIONS:
        assumptions_file: Which scenario to analyze (default: assumptions.json)
        --analysis: Which analysis to run (base, sensitivity, monte_carlo, loan_structure_sensitivity, all)
        --simulations: Number of Monte Carlo simulations (default: 1000)
        --quiet: Suppress detailed output
    
    WORKFLOW:
        1. Parse command-line arguments
        2. Extract case name from file path
        3. Run requested analyses
        4. Display summary
    """
    # -----------------------------------------------------------------------
    # Parse Command-Line Arguments
    # -----------------------------------------------------------------------
    
    parser = argparse.ArgumentParser(
        description='Run Engelberg property investment analyses',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
        python run_analysis.py                        # All analyses for base case
        python run_analysis.py assumptions_migros.json # All analyses for Migros
        python run_analysis.py --analysis base         # Only base case
        python run_analysis.py --analysis sensitivity  # Only Model Sensitivity
        python run_analysis.py --analysis monte_carlo_sensitivity  # Only MC Sensitivity
        python run_analysis.py --analysis loan_structure_sensitivity  # Loan structure scenarios
        python run_analysis.py --simulations 5000      # 5,000 Monte Carlo sims
        python run_analysis.py --quiet                 # Minimal output
        """
    )
    
    parser.add_argument(
        'assumptions_file', 
        nargs='?', 
        default='assumptions/assumptions.json',
        help='Path to assumptions JSON file (default: assumptions/assumptions.json). Can be relative to project root or in assumptions/ directory.'
    )
    
    parser.add_argument(
        '--analysis', '-a',
        choices=['all', 'base', 'sensitivity', 'monte_carlo', 'monte_carlo_sensitivity', 'loan_structure_sensitivity'],
        default='all',
        help='Which analysis to run (default: all). monte_carlo_sensitivity runs Monte Carlo for each parameter value.'
    )
    
    parser.add_argument(
        '--simulations', '-n',
        type=int,
        default=10000,
        help='Number of Monte Carlo simulations (default: 10,000 for better accuracy)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress detailed output'
    )
    
    args = parser.parse_args()
    
    # -----------------------------------------------------------------------
    # Setup and Validation
    # -----------------------------------------------------------------------
    
    # Resolve assumptions file path
    json_path = args.assumptions_file
    original_path = json_path
    
    # Try to find the file in common locations
    if not os.path.isabs(json_path):
        # Try resolved path first (relative to project root)
        resolved_path = resolve_path(json_path)
        if os.path.exists(resolved_path):
            json_path = resolved_path
        # Try in assumptions/ directory
        elif os.path.exists(resolve_path(f"assumptions/{json_path}")):
            json_path = resolve_path(f"assumptions/{json_path}")
        # Try just the filename in assumptions/ directory (if path contains directory separators)
        elif os.path.basename(json_path) != json_path:
            # Already tried with full path, try just filename
            filename_only = os.path.basename(json_path)
            assumptions_path = resolve_path(f"assumptions/{filename_only}")
            if os.path.exists(assumptions_path):
                json_path = assumptions_path
        # Try original path (might be relative to current dir)
        elif not os.path.exists(json_path):
            # File not found - show helpful error
            print(f"ERROR: Assumptions file not found: {original_path}")
            print(f"\nSearched locations:")
            print(f"  - {resolve_path(original_path)}")
            print(f"  - {resolve_path(f'assumptions/{original_path}')}")
            if os.path.basename(original_path) != original_path:
                print(f"  - {resolve_path(f'assumptions/{os.path.basename(original_path)}')}")
            print(f"  - {os.path.abspath(original_path)}")
            print(f"\nAvailable files in assumptions/ directory:")
            import glob
            assumptions_dir = resolve_path("assumptions")
            if os.path.exists(assumptions_dir):
                for f in glob.glob(os.path.join(assumptions_dir, "*.json")):
                    print(f"  - {os.path.relpath(f, get_project_root())}")
            sys.exit(1)
    
    # Normalize to absolute path
    json_path = os.path.abspath(json_path)
    case_name = extract_case_name(json_path)
    verbose = not args.quiet
    
    # -----------------------------------------------------------------------
    # Display Header
    # -----------------------------------------------------------------------
    
    if verbose:
        print("=" * 70)
        print("ENGELBERG PROPERTY INVESTMENT - UNIFIED ANALYSIS")
        print("=" * 70)
        print(f"\nCase: {case_name}")
        print(f"Assumptions File: {json_path}")
        print(f"Analysis Type: {args.analysis}")
        print()
    
    # -----------------------------------------------------------------------
    # Run Requested Analyses
    # -----------------------------------------------------------------------
    
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
        
        # Monte Carlo Sensitivity Analysis
        if args.analysis in ['all', 'monte_carlo_sensitivity']:
            # Use 1000 simulations per value with LHS (equivalent accuracy to 2000 with random sampling)
            # Total will be 5 params x 10 values x 1000 sims = 50,000 simulations
            sensitivity_sims = 1000
            results['monte_carlo_sensitivity'] = run_monte_carlo_sensitivity_analysis(
                json_path, case_name, sensitivity_sims, verbose
            )

        # Loan Structure Sensitivity
        if args.analysis in ['all', 'loan_structure_sensitivity']:
            results['loan_structure_sensitivity'] = run_loan_structure_sensitivity_analysis(
                json_path, case_name, verbose
            )
        
        # -------------------------------------------------------------------
        # Display Summary
        # -------------------------------------------------------------------
        
        if verbose:
            print("\n" + "=" * 70)
            print("ANALYSIS COMPLETE")
            print("=" * 70)
            print(f"\nGenerated files in website/data/:")
            for analysis_type in results.keys():
                filename = f"{case_name}_{analysis_type}.json"
                # Adjust filename for base_case_analysis
                if analysis_type == 'base_case':
                    filename = f"{case_name}_base_case_analysis.json"
                elif analysis_type == 'monte_carlo_sensitivity':
                    filename = f"{case_name}_monte_carlo_sensitivity.json"
                print(f"  * {filename}")
            print(f"\nChart View results: website/index.html")
            print()
        
        return results
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# ===========================================================================
# SCRIPT ENTRY POINT
# ===========================================================================

if __name__ == "__main__":
    """
    Entry point when script is run directly.
    Calls main() function to run analyses based on command-line arguments.
    """
    main()
