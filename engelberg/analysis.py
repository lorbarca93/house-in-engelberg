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
from typing import Dict

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
    operational_months_year1 = 12 - ramp_up_months
    results = compute_annual_cash_flows(config, operational_months=operational_months_year1)
    
    # Year-1 KPIs (same for all horizons)
    kpis_year1 = {
        'cap_rate_pct': results.get('cap_rate_pct', 0),
        'cash_on_cash_return_pct': results.get('cash_on_cash_return_pct', 0),
        'debt_coverage_ratio': results.get('debt_coverage_ratio', 0),
        'operating_expense_ratio_pct': results.get('operating_expense_ratio_pct', 0)
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
            'net_sale_price': irr_results.get('net_sale_price', 0),
            'selling_costs_rate_pct': irr_results.get('selling_costs_rate_pct', 0)
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
            ramp_up_months=ramp_up_months
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
            proj_defaults['discount_rate']
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
# SECTION 6: MAIN PROGRAM
# Command-line interface and orchestration
# ===========================================================================

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
        choices=['all', 'base', 'sensitivity', 'monte_carlo', 'monte_carlo_sensitivity'],
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
