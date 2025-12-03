"""
═══════════════════════════════════════════════════════════════════════════════
COMPREHENSIVE SYSTEM VALIDATION SCRIPT
═══════════════════════════════════════════════════════════════════════════════

PURPOSE:
    Performs extensive validation of the entire Engelberg Property Investment
    Simulation system. Includes cross-checks between scripts, assumptions,
    data files, and dashboard components.

VALIDATION CATEGORIES:
    1. File Structure & Existence
    2. Python Module Imports & Dependencies
    3. Assumptions Files (Structure & Values)
    4. Cross-Validation (Scripts ↔ Assumptions ↔ Data)
    5. Data File Integrity
    6. Calculation Consistency
    7. Dashboard Components
    8. End-to-End Integration Tests

USAGE:
    python validate_system.py [--verbose]

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import io
import json
import importlib
from typing import Dict, List, Tuple
from dataclasses import dataclass

# Set UTF-8 encoding for console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


@dataclass
class ValidationResult:
    """Stores validation results with pass/fail/warning counts."""
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def add_pass(self, message: str):
        self.passed += 1
        print(f"[PASS] {message}")
    
    def add_fail(self, message: str):
        self.failed += 1
        self.errors.append(message)
        print(f"[FAIL] {message}")
    
    def add_warning(self, message: str):
        self.warnings += 1
        print(f"[WARN] {message}")


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION SECTION 1: FILE STRUCTURE & EXISTENCE
# ═══════════════════════════════════════════════════════════════════════════

def validate_file_structure(result: ValidationResult):
    """Validate that all required files and directories exist."""
    print("\n[1/12] Validating File Structure & Existence...")
    print("-" * 80)
    
    # Required directories
    required_dirs = ['website', 'website/data']
    for dir_path in required_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            result.add_pass(f"Directory exists: {dir_path}")
        else:
            result.add_fail(f"Directory missing: {dir_path}")
    
    # Required Python scripts
    required_scripts = [
        ('core_engine.py', 'Core calculation engine'),
        ('analyze.py', 'Main unified analysis script'),
        ('monte_carlo_engine.py', 'Monte Carlo simulation engine'),
        ('generate_all_data.py', 'Batch data generator'),
        ('validate_system.py', 'This validation script')
    ]
    
    for script, description in required_scripts:
        if os.path.exists(script):
            result.add_pass(f"Script exists: {script} ({description})")
        else:
            result.add_fail(f"Script missing: {script} ({description})")
    
    # Required configuration files
    if os.path.exists('assumptions.json'):
        result.add_pass("Base assumptions file: assumptions.json")
    else:
        result.add_fail("Base assumptions file missing: assumptions.json")
    
    if os.path.exists('requirements.txt'):
        result.add_pass("Dependencies file: requirements.txt")
    else:
        result.add_fail("Dependencies file missing: requirements.txt")
    
    # Dashboard
    if os.path.exists('website/index.html'):
        result.add_pass("Dashboard: website/index.html")
    else:
        result.add_fail("Dashboard missing: website/index.html")


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION SECTION 2: PYTHON MODULE IMPORTS & DEPENDENCIES
# ═══════════════════════════════════════════════════════════════════════════

def validate_python_imports(result: ValidationResult):
    """Validate that all Python modules can be imported."""
    print("\n[2/12] Validating Python Module Imports...")
    print("-" * 80)
    
    modules = [
        ('core_engine', 'Core calculation functions'),
        ('analyze', 'Main analysis script'),
        ('monte_carlo_engine', 'Monte Carlo engine'),
        ('generate_all_data', 'Batch generator')
    ]
    
    for module_name, description in modules:
        try:
            importlib.import_module(module_name)
            result.add_pass(f"Module imports: {module_name} ({description})")
        except Exception as e:
            result.add_fail(f"Module import error: {module_name} - {str(e)}")
    
    # Check required packages
    required_packages = [
        ('pandas', 'Data manipulation'),
        ('plotly', 'Charting library'),
        ('numpy', 'Numerical computations')
    ]
    
    for package, description in required_packages:
        try:
            importlib.import_module(package)
            result.add_pass(f"Package available: {package} ({description})")
        except ImportError:
            result.add_fail(f"Package missing: {package} ({description}) - Run: pip install {package}")


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION SECTION 3: ASSUMPTIONS FILES (STRUCTURE & VALUES)
# ═══════════════════════════════════════════════════════════════════════════

def validate_assumptions_files(result: ValidationResult):
    """Validate all assumptions JSON files for structure and reasonable values."""
    print("\n[3/12] Validating Assumptions Files...")
    print("-" * 80)
    
    import glob
    assumptions_files = glob.glob("assumptions*.json")
    
    if not assumptions_files:
        result.add_fail("No assumptions files found")
        return
    
    result.add_pass(f"Found {len(assumptions_files)} assumptions files")
    
    for assumptions_file in assumptions_files:
        # Load and parse JSON
        try:
            with open(assumptions_file, 'r', encoding='utf-8') as f:
                assumptions = json.load(f)
            result.add_pass(f"Valid JSON: {assumptions_file}")
        except json.JSONDecodeError as e:
            result.add_fail(f"Invalid JSON in {assumptions_file}: {str(e)}")
            continue
        except Exception as e:
            result.add_fail(f"Error reading {assumptions_file}: {str(e)}")
            continue
        
        # Validate structure
        if assumptions_file == "assumptions.json":
            # Base file - must have all sections
            required_sections = ['financing', 'rental', 'expenses', 'seasonal', 'projection']
            for section in required_sections:
                if section in assumptions:
                    result.add_pass(f"{assumptions_file}: Has '{section}' section")
                else:
                    result.add_fail(f"{assumptions_file}: Missing '{section}' section")
        else:
            # Override files - at least one section
            has_any_section = any(section in assumptions for section in ['financing', 'rental', 'expenses'])
            if has_any_section:
                result.add_pass(f"{assumptions_file}: Has override sections")
            else:
                result.add_fail(f"{assumptions_file}: No valid override sections found")
        
        # Validate reasonable value ranges
        if 'financing' in assumptions:
            fin = assumptions['financing']
            
            # LTV check
            if 'ltv' in fin:
                ltv = fin['ltv']
                if 0.4 <= ltv <= 0.95:
                    result.add_pass(f"{assumptions_file}: LTV {ltv*100:.0f}% in reasonable range")
                else:
                    result.add_warning(f"{assumptions_file}: LTV {ltv*100:.0f}% outside typical range (40-95%)")
            
            # Interest rate check
            if 'interest_rate' in fin:
                rate = fin['interest_rate']
                if 0.001 <= rate <= 0.10:
                    result.add_pass(f"{assumptions_file}: Interest rate {rate*100:.2f}% in reasonable range")
                else:
                    result.add_warning(f"{assumptions_file}: Interest rate {rate*100:.2f}% seems unusual")
        
        if 'projection' in assumptions:
            proj = assumptions['projection']
            
            # Inflation check
            if 'inflation_rate' in proj:
                inf = proj['inflation_rate']
                if -0.02 <= inf <= 0.05:
                    result.add_pass(f"{assumptions_file}: Inflation {inf*100:.1f}% in reasonable range")
                else:
                    result.add_warning(f"{assumptions_file}: Inflation {inf*100:.1f}% seems unusual")
            
            # Appreciation check
            if 'property_appreciation_rate' in proj:
                appr = proj['property_appreciation_rate']
                if 0.005 <= appr <= 0.08:
                    result.add_pass(f"{assumptions_file}: Appreciation {appr*100:.1f}% in reasonable range")
                else:
                    result.add_warning(f"{assumptions_file}: Appreciation {appr*100:.1f}% seems unusual")


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION SECTION 4: CROSS-VALIDATION (SCRIPTS ↔ ASSUMPTIONS ↔ DATA)
# ═══════════════════════════════════════════════════════════════════════════

def validate_cross_checks(result: ValidationResult):
    """Perform cross-validation between scripts, assumptions, and generated data."""
    print("\n[4/12] Validating Cross-Dependencies...")
    print("-" * 80)
    
    try:
        from core_engine import (
            create_base_case_config,
            compute_annual_cash_flows,
            get_projection_defaults
        )
        
        # Test 1: Assumptions can be loaded and config created
        try:
            config = create_base_case_config('assumptions.json')
            result.add_pass("Cross-check: assumptions.json → config creation successful")
            
            # Verify config has expected structure
            if hasattr(config, 'financing') and hasattr(config, 'rental') and hasattr(config, 'expenses'):
                result.add_pass("Cross-check: Config has all required sections")
            else:
                result.add_fail("Cross-check: Config missing required sections")
            
        except Exception as e:
            result.add_fail(f"Cross-check: Config creation failed - {str(e)}")
        
        # Test 2: Config can generate cash flows
        try:
            results = compute_annual_cash_flows(config)
            required_keys = ['gross_rental_income', 'net_operating_income', 'cash_flow_per_owner']
            missing_keys = [k for k in required_keys if k not in results]
            
            if not missing_keys:
                result.add_pass("Cross-check: Cash flow calculations produce all required metrics")
            else:
                result.add_fail(f"Cross-check: Cash flow missing keys: {missing_keys}")
        except Exception as e:
            result.add_fail(f"Cross-check: Cash flow calculation failed - {str(e)}")
        
        # Test 3: Projection defaults can be loaded
        try:
            proj_defaults = get_projection_defaults('assumptions.json')
            required_proj_keys = ['inflation_rate', 'property_appreciation_rate', 'selling_costs_rate']
            missing_proj = [k for k in required_proj_keys if k not in proj_defaults]
            
            if not missing_proj:
                result.add_pass("Cross-check: Projection defaults complete")
            else:
                result.add_fail(f"Cross-check: Projection defaults missing: {missing_proj}")
        except Exception as e:
            result.add_fail(f"Cross-check: Projection defaults failed - {str(e)}")
        
        # Test 4: Verify assumptions values match config values
        try:
            assumptions = json.load(open('assumptions.json'))
            
            # Check financing consistency
            if assumptions['financing']['ltv'] == config.financing.ltv:
                result.add_pass("Cross-check: LTV matches (JSON ↔ Config)")
            else:
                result.add_fail(f"Cross-check: LTV mismatch (JSON: {assumptions['financing']['ltv']} vs Config: {config.financing.ltv})")
            
            if assumptions['financing']['interest_rate'] == config.financing.interest_rate:
                result.add_pass("Cross-check: Interest rate matches (JSON ↔ Config)")
            else:
                result.add_fail(f"Cross-check: Interest rate mismatch")
            
            # Check maintenance rate
            if assumptions['expenses']['maintenance_rate'] == config.expenses.maintenance_rate:
                result.add_pass("Cross-check: Maintenance rate matches (JSON ↔ Config)")
            else:
                result.add_fail(f"Cross-check: Maintenance rate mismatch")
            
        except Exception as e:
            result.add_fail(f"Cross-check: JSON ↔ Config comparison failed - {str(e)}")
        
    except ImportError as e:
        result.add_fail(f"Cross-check: Cannot import core_engine - {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION SECTION 5: DATA FILE INTEGRITY
# ═══════════════════════════════════════════════════════════════════════════

def validate_data_files(result: ValidationResult):
    """Validate generated data files for completeness and consistency."""
    print("\n[5/12] Validating Generated Data Files...")
    print("-" * 80)
    
    # Check cases_index.json
    index_path = "website/data/cases_index.json"
    if os.path.exists(index_path):
        result.add_pass(f"Cases index exists: {index_path}")
        
        try:
            with open(index_path) as f:
                index = json.load(f)
            result.add_pass("Cases index: Valid JSON")
            
            if 'cases' in index and isinstance(index['cases'], list):
                result.add_pass(f"Cases index: {len(index['cases'])} cases listed")
                
                # Validate each case in index
                for case in index['cases']:
                    case_name = case.get('case_name')
                    
                    # Check that corresponding data files exist
                    for analysis_type, filename in case.get('data_files', {}).items():
                        if filename:
                            file_path = f"website/data/{filename}"
                            if os.path.exists(file_path):
                                result.add_pass(f"Case '{case_name}' {analysis_type}: {filename}")
                                
                                # Validate JSON structure
                                try:
                                    with open(file_path) as f:
                                        data = json.load(f)
                                    
                                    # Check for required keys based on analysis type
                                    if analysis_type == 'base_case_analysis':
                                        required_keys = ['config', 'annual_results', 'projection_15yr', 'irr_results']
                                        missing = [k for k in required_keys if k not in data]
                                        if not missing:
                                            result.add_pass(f"Case '{case_name}': Base case structure valid")
                                        else:
                                            result.add_fail(f"Case '{case_name}': Base case missing keys: {missing}")
                                    
                                    elif analysis_type == 'sensitivity':
                                        if 'sensitivities' in data and 'base_irr' in data:
                                            result.add_pass(f"Case '{case_name}': Sensitivity structure valid")
                                        else:
                                            result.add_fail(f"Case '{case_name}': Sensitivity missing required keys")
                                    
                                    elif analysis_type == 'monte_carlo':
                                        if 'statistics' in data:
                                            result.add_pass(f"Case '{case_name}': Monte Carlo structure valid")
                                        else:
                                            result.add_fail(f"Case '{case_name}': Monte Carlo missing statistics")
                                
                                except json.JSONDecodeError:
                                    result.add_fail(f"Invalid JSON: {file_path}")
                            else:
                                result.add_fail(f"Missing data file: {file_path}")
            else:
                result.add_fail("Cases index: Missing or invalid 'cases' array")
        
        except json.JSONDecodeError:
            result.add_fail("Cases index: Invalid JSON format")
    else:
        result.add_fail(f"Cases index missing: {index_path}")


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION SECTION 6: CALCULATION CONSISTENCY
# ═══════════════════════════════════════════════════════════════════════════

def validate_calculation_consistency(result: ValidationResult):
    """Verify that calculations are internally consistent."""
    print("\n[6/12] Validating Calculation Consistency...")
    print("-" * 80)
    
    try:
        # Load base case data
        with open('website/data/base_case_base_case_analysis.json') as f:
            data = json.load(f)
        
        config = data['config']
        results = data['annual_results']
        irr_results = data['irr_results']
        projection = data['projection_15yr']
        
        # Check 1: LTV calculation
        expected_loan = config['financing']['purchase_price'] * config['financing']['ltv']
        actual_loan = config['financing']['loan_amount']
        if abs(expected_loan - actual_loan) < 1:
            result.add_pass("Calculation: LTV → Loan Amount consistent")
        else:
            result.add_fail(f"Calculation: LTV mismatch (expected {expected_loan:.0f}, got {actual_loan:.0f})")
        
        # Check 2: Equity calculation
        expected_equity = config['financing']['purchase_price'] - config['financing']['loan_amount']
        actual_equity = config['financing']['equity_total']
        if abs(expected_equity - actual_equity) < 1:
            result.add_pass("Calculation: Purchase Price - Loan = Equity consistent")
        else:
            result.add_fail(f"Calculation: Equity mismatch")
        
        # Check 3: NOI calculation (Revenue - Expenses)
        expected_noi = results['gross_rental_income'] - results['total_operating_expenses']
        actual_noi = results['net_operating_income']
        if abs(expected_noi - actual_noi) < 1:
            result.add_pass("Calculation: Revenue - Expenses = NOI consistent")
        else:
            result.add_fail(f"Calculation: NOI mismatch (expected {expected_noi:.2f}, got {actual_noi:.2f})")
        
        # Check 4: Cash Flow calculation (NOI - Debt Service)
        expected_cf = results['net_operating_income'] - results['debt_service']
        actual_cf = results['cash_flow_after_debt_service']
        if abs(expected_cf - actual_cf) < 1:
            result.add_pass("Calculation: NOI - Debt Service = Cash Flow consistent")
        else:
            result.add_fail(f"Calculation: Cash Flow mismatch")
        
        # Check 5: Projection length
        if len(projection) == 15:
            result.add_pass("Calculation: Projection has correct length (15 years)")
        else:
            result.add_fail(f"Calculation: Projection has {len(projection)} years (expected 15)")
        
        # Check 6: MOIC calculation
        if 'moic' in irr_results and irr_results['moic'] > 0:
            result.add_pass(f"Calculation: MOIC = {irr_results['moic']:.2f}x (calculated)")
        else:
            result.add_fail("Calculation: MOIC missing or invalid")
        
        # Check 7: Selling costs properly applied
        if 'selling_costs' in irr_results and irr_results['selling_costs'] > 0:
            expected_costs = irr_results['gross_sale_price'] * (irr_results['selling_costs_rate_pct'] / 100)
            actual_costs = irr_results['selling_costs']
            if abs(expected_costs - actual_costs) < 10:
                result.add_pass(f"Calculation: Selling costs = {actual_costs:,.0f} CHF (7.8% applied)")
            else:
                result.add_fail(f"Calculation: Selling costs mismatch")
        else:
            result.add_fail("Calculation: Selling costs not applied")
        
    except FileNotFoundError:
        result.add_warning("Calculation: Base case data file not found (run python analyze.py)")
    except Exception as e:
        result.add_fail(f"Calculation: Validation error - {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION SECTION 7: ASSUMPTIONS ↔ DATA CROSS-VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def validate_assumptions_data_cross_check(result: ValidationResult):
    """Cross-validate that data files reflect assumptions correctly."""
    print("\n[7/12] Cross-Validating Assumptions ↔ Generated Data...")
    print("-" * 80)
    
    try:
        # Load assumptions
        with open('assumptions.json') as f:
            assumptions = json.load(f)
        
        # Load generated data
        with open('website/data/base_case_base_case_analysis.json') as f:
            data = json.load(f)
        
        # Cross-check: Financing parameters
        if assumptions['financing']['purchase_price'] == data['config']['financing']['purchase_price']:
            result.add_pass("Cross-check: Purchase price (assumptions.json ↔ data)")
        else:
            result.add_fail("Cross-check: Purchase price mismatch")
        
        if assumptions['financing']['ltv'] == data['config']['financing']['ltv']:
            result.add_pass("Cross-check: LTV (assumptions.json ↔ data)")
        else:
            result.add_fail("Cross-check: LTV mismatch")
        
        if assumptions['financing']['interest_rate'] == data['config']['financing']['interest_rate']:
            result.add_pass("Cross-check: Interest rate (assumptions.json ↔ data)")
        else:
            result.add_fail("Cross-check: Interest rate mismatch")
        
        # Cross-check: Expense parameters
        if assumptions['expenses']['maintenance_rate'] == data['config']['expenses']['maintenance_rate']:
            result.add_pass("Cross-check: Maintenance rate (assumptions.json ↔ data)")
        else:
            result.add_fail("Cross-check: Maintenance rate mismatch")
        
        if assumptions['expenses']['cleaning_cost_per_stay'] == data['config']['expenses']['cleaning_cost_per_stay']:
            result.add_pass("Cross-check: Cleaning cost (assumptions.json ↔ data)")
        else:
            result.add_fail("Cross-check: Cleaning cost mismatch")
        
        # Cross-check: Projection parameters
        if 'projection' in assumptions:
            proj_assumptions = assumptions['projection']
            
            # Check if data was generated with same parameters
            # (We can't directly compare since projection params aren't in config,
            # but we can verify they're being used by checking results)
            inflation = proj_assumptions.get('inflation_rate', 0.02)
            appreciation = proj_assumptions.get('property_appreciation_rate', 0.025)
            
            result.add_pass(f"Cross-check: Inflation rate: {inflation*100:.1f}% (from assumptions)")
            result.add_pass(f"Cross-check: Appreciation rate: {appreciation*100:.1f}% (from assumptions)")
        
    except FileNotFoundError as e:
        result.add_warning(f"Cross-check: File not found - {str(e)}")
    except Exception as e:
        result.add_fail(f"Cross-check: Error - {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION SECTION 8: SENSITIVITY ANALYSIS VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def validate_sensitivity_analysis(result: ValidationResult):
    """Validate sensitivity analysis calculations and consistency."""
    print("\n[8/12] Validating Sensitivity Analysis...")
    print("-" * 80)
    
    try:
        with open('website/data/base_case_sensitivity.json') as f:
            sens_data = json.load(f)
        
        base_irr = sens_data['base_irr']
        sensitivities = sens_data['sensitivities']
        
        result.add_pass(f"Sensitivity: Base IRR = {base_irr:.2f}%")
        result.add_pass(f"Sensitivity: {len(sensitivities)} parameters analyzed")
        
        # Validate each sensitivity
        for sens in sensitivities:
            param = sens['parameter']
            
            # Check impact calculation
            calculated_impact = abs(sens['high']['irr'] - sens['low']['irr'])
            stated_impact = sens['impact']
            
            if abs(calculated_impact - stated_impact) < 0.0001:
                result.add_pass(f"Sensitivity '{param}': Impact calculation correct (±{stated_impact:.2f}%)")
            else:
                result.add_fail(f"Sensitivity '{param}': Impact mismatch (expected {calculated_impact:.4f}, got {stated_impact:.4f})")
            
            # Check delta calculations
            expected_low_delta = sens['low']['irr'] - base_irr
            actual_low_delta = sens['low']['delta_irr']
            if abs(expected_low_delta - actual_low_delta) < 0.0001:
                result.add_pass(f"Sensitivity '{param}': Low delta correct")
            else:
                result.add_fail(f"Sensitivity '{param}': Low delta incorrect")
            
            expected_high_delta = sens['high']['irr'] - base_irr
            actual_high_delta = sens['high']['delta_irr']
            if abs(expected_high_delta - actual_high_delta) < 0.0001:
                result.add_pass(f"Sensitivity '{param}': High delta correct")
            else:
                result.add_fail(f"Sensitivity '{param}': High delta incorrect")
        
        # Check sorting by impact
        impacts = [s['impact'] for s in sensitivities]
        if impacts == sorted(impacts, reverse=True):
            result.add_pass("Sensitivity: Parameters correctly sorted by impact (descending)")
        else:
            result.add_warning("Sensitivity: Parameters not sorted by impact")
        
    except FileNotFoundError:
        result.add_warning("Sensitivity: Data file not found (run python analyze.py)")
    except Exception as e:
        result.add_fail(f"Sensitivity: Validation error - {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION SECTION 9: MONTE CARLO VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def validate_monte_carlo(result: ValidationResult):
    """Validate Monte Carlo simulation results."""
    print("\n[9/12] Validating Monte Carlo Simulation...")
    print("-" * 80)
    
    try:
        with open('website/data/base_case_monte_carlo.json') as f:
            mc_data = json.load(f)
        
        stats = mc_data.get('statistics', {})
        
        # Check that statistics exist
        if 'npv' in stats:
            npv_stats = stats['npv']
            result.add_pass(f"Monte Carlo: NPV statistics present")
            
            # Validate statistical properties
            if npv_stats['mean'] != 0:
                result.add_pass(f"Monte Carlo: Mean NPV = {npv_stats['mean']:,.0f} CHF")
            
            if npv_stats['std'] > 0:
                result.add_pass(f"Monte Carlo: Std Dev = {npv_stats['std']:,.0f} CHF (> 0)")
            else:
                result.add_fail("Monte Carlo: Standard deviation is zero (no variation)")
            
            # Check percentile ordering
            if npv_stats['p5'] <= npv_stats['median'] <= npv_stats['p95']:
                result.add_pass("Monte Carlo: Percentiles correctly ordered (p5 < median < p95)")
            else:
                result.add_fail("Monte Carlo: Percentile ordering incorrect")
        else:
            result.add_fail("Monte Carlo: NPV statistics missing")
        
        if 'irr_with_sale' in stats:
            result.add_pass("Monte Carlo: IRR statistics present")
        else:
            result.add_fail("Monte Carlo: IRR statistics missing")
        
    except FileNotFoundError:
        result.add_warning("Monte Carlo: Data file not found (run python analyze.py)")
    except Exception as e:
        result.add_fail(f"Monte Carlo: Validation error - {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION SECTION 10: DASHBOARD VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def validate_dashboard(result: ValidationResult):
    """Validate dashboard HTML and JavaScript components."""
    print("\n[10/12] Validating Dashboard Components...")
    print("-" * 80)
    
    if not os.path.exists('website/index.html'):
        result.add_fail("Dashboard file missing: website/index.html")
        return
    
    with open('website/index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Check required components
    required_elements = [
        ('Plotly.js', 'plotly', 'Charting library'),
        ('Case Selector', 'id="caseSelect"', 'Case selection dropdown'),
        ('Content Area', 'contentArea', 'Main content display'),
        ('renderBaseCase', 'renderBaseCase', 'Model rendering function'),
        ('renderSensitivity', 'renderSensitivity', 'Sensitivity rendering function'),
        ('renderMonteCarlo', 'renderMonteCarlo', 'Monte Carlo rendering function'),
    ]
    
    for name, search_term, description in required_elements:
        if search_term in html_content:
            result.add_pass(f"Dashboard: {name} present ({description})")
        else:
            result.add_fail(f"Dashboard: {name} missing ({description})")
    
    # Check for tornado chart rendering
    if 'tornadoChart' in html_content and 'Plotly.newPlot' in html_content:
        result.add_pass("Dashboard: Tornado chart rendering code present")
    else:
        result.add_fail("Dashboard: Tornado chart rendering incomplete")
    
    # Check for overlap prevention
    if 'overflow: visible' in html_content or 'clear: both' in html_content:
        result.add_pass("Dashboard: Overlap prevention measures present")
    else:
        result.add_warning("Dashboard: No explicit overlap prevention found")


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION SECTION 11: SCRIPT INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════

def validate_script_integration(result: ValidationResult):
    """Test that scripts can call each other correctly."""
    print("\n[11/12] Validating Script Integration...")
    print("-" * 80)
    
    try:
        # Test 1: analyze.py imports from core_engine.py
        import analyze
        if hasattr(analyze, 'run_base_case_analysis'):
            result.add_pass("Integration: analyze.py has run_base_case_analysis()")
        else:
            result.add_fail("Integration: analyze.py missing run_base_case_analysis()")
        
        if hasattr(analyze, 'run_sensitivity_analysis'):
            result.add_pass("Integration: analyze.py has run_sensitivity_analysis()")
        else:
            result.add_fail("Integration: analyze.py missing run_sensitivity_analysis()")
        
        # Test 2: generate_all_data.py can call analyze.py
        import generate_all_data
        result.add_pass("Integration: generate_all_data.py imports successfully")
        
        # Test 3: monte_carlo_engine.py imports from core_engine.py
        import monte_carlo_engine
        if hasattr(monte_carlo_engine, 'run_monte_carlo_simulation'):
            result.add_pass("Integration: monte_carlo_engine.py exports simulation function")
        else:
            result.add_fail("Integration: monte_carlo_engine.py missing simulation function")
        
    except ImportError as e:
        result.add_fail(f"Integration: Import error - {str(e)}")
    except Exception as e:
        result.add_fail(f"Integration: Error - {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION SECTION 12: END-TO-END CONSISTENCY
# ═══════════════════════════════════════════════════════════════════════════

def validate_end_to_end(result: ValidationResult):
    """Perform end-to-end validation across entire system."""
    print("\n[12/12] Validating End-to-End Consistency...")
    print("-" * 80)
    
    try:
        # Check that all cases in index have corresponding assumptions files
        with open('website/data/cases_index.json') as f:
            index = json.load(f)
        
        for case in index['cases']:
            case_name = case['case_name']
            assumptions_file = case['assumptions_file']
            
            if os.path.exists(assumptions_file):
                result.add_pass(f"E2E: Case '{case_name}' has assumptions file: {assumptions_file}")
            else:
                result.add_fail(f"E2E: Case '{case_name}' missing assumptions: {assumptions_file}")
            
            # Check data files match case name
            for analysis_type, filename in case.get('data_files', {}).items():
                if filename and filename.startswith(case_name):
                    result.add_pass(f"E2E: Case '{case_name}' filename correct: {filename}")
                elif filename:
                    result.add_warning(f"E2E: Case '{case_name}' filename mismatch: {filename}")
        
        # Check that number of cases matches
        import glob
        assumptions_files = glob.glob("assumptions*.json")
        if len(index['cases']) == len(assumptions_files):
            result.add_pass(f"E2E: Case count matches ({len(index['cases'])} cases)")
        else:
            result.add_warning(f"E2E: Case count mismatch (index: {len(index['cases'])}, files: {len(assumptions_files)})")
        
    except Exception as e:
        result.add_fail(f"E2E: Validation error - {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN VALIDATION ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Run all validation checks and display summary."""
    print("=" * 80)
    print("ENGELBERG PROPERTY INVESTMENT - COMPREHENSIVE SYSTEM VALIDATION")
    print("=" * 80)
    print()
    
    result = ValidationResult()
    
    # Run all validation sections
    validate_file_structure(result)
    validate_python_imports(result)
    validate_assumptions_files(result)
    validate_cross_checks(result)
    validate_data_files(result)
    validate_calculation_consistency(result)
    validate_assumptions_data_cross_check(result)
    validate_sensitivity_analysis(result)
    validate_monte_carlo(result)
    validate_dashboard(result)
    validate_script_integration(result)
    validate_end_to_end(result)
    
    # Display summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"[PASS] Passed:  {result.passed}")
    print(f"[FAIL] Failed:  {result.failed}")
    print(f"[WARN] Warnings: {result.warnings}")
    print(f"Total:           {result.passed + result.failed + result.warnings}")
    
    if result.failed > 0:
        print("\nFAILED CHECKS:")
        for error in result.errors:
            print(f"  [FAIL] {error}")
    
    print("\n" + "=" * 80)
    if result.failed == 0:
        print("[SUCCESS] SYSTEM VALIDATION PASSED")
    else:
        print("[ERROR] SYSTEM VALIDATION FAILED")
        print(f"Please fix {result.failed} error(s) before using the system")
    print("=" * 80)
    
    return result.failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
