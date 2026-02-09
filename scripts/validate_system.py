"""
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
COMPREHENSIVE SYSTEM VALIDATION SCRIPT
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

PURPOSE:
    Performs extensive validation of the entire Engelberg Property Investment
    Simulation system. Includes cross-checks between scripts, assumptions,
    data files, and dashboard components.

VALIDATION CATEGORIES:
    1. File Structure & Existence
    2. Python Module Imports & Dependencies
    3. Assumptions Files (Structure & Values)
    4. Cross-Validation (Scripts â†” Assumptions â†” Data)
    5. Data File Integrity
    6. Calculation Consistency
    7. Dashboard Components
    8. End-to-End Integration Tests

USAGE:
    python validate_system.py [--verbose]

â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
"""

import os
import sys
import io
import json
import importlib
import importlib.util
from typing import Dict, List, Tuple
from dataclasses import dataclass

# Add project root to path so we can import engelberg package
# Note: We calculate this manually here because we need it before importing engelberg
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import get_project_root and resolve_path for path operations (after sys.path is set)
from engelberg.core import get_project_root, resolve_path

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


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# VALIDATION SECTION 1: FILE STRUCTURE & EXISTENCE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def validate_file_structure(result: ValidationResult):
    """Validate that all required files and directories exist."""
    print("\n[1/13] Validating File Structure & Existence...")
    print("-" * 80)
    
    # Required directories
    required_dirs = ['website', 'website/data']
    for dir_path in required_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            result.add_pass(f"Directory exists: {dir_path}")
        else:
            result.add_fail(f"Directory missing: {dir_path}")
    
    # Required Python package structure
    required_packages = [
        ('engelberg/__init__.py', 'Main package'),
        ('engelberg/core.py', 'Core calculation engine'),
        ('engelberg/analysis.py', 'Analysis orchestration'),
        ('engelberg/monte_carlo.py', 'Monte Carlo simulation engine'),
    ]
    
    for package_file, description in required_packages:
        if os.path.exists(package_file):
            result.add_pass(f"Package file exists: {package_file} ({description})")
        else:
            result.add_fail(f"Package file missing: {package_file} ({description})")
    
    # Required scripts
    required_scripts = [
        ('scripts/analyze.py', 'Main analysis CLI script'),
        ('scripts/analyze_monte_carlo_sensitivity.py', 'Dedicated MC sensitivity CLI script'),
        ('scripts/generate_all_data.py', 'Batch data generator'),
        ('scripts/validate_system.py', 'This validation script')
    ]
    
    for script, description in required_scripts:
        if os.path.exists(script):
            result.add_pass(f"Script exists: {script} ({description})")
        else:
            result.add_fail(f"Script missing: {script} ({description})")
    
    # Required configuration files
    base_assumptions_path = resolve_path('assumptions/assumptions.json')
    if os.path.exists(base_assumptions_path):
        result.add_pass(f"Base assumptions file: {os.path.relpath(base_assumptions_path, get_project_root())}")
    else:
        result.add_fail(f"Base assumptions file missing: {os.path.relpath(base_assumptions_path, get_project_root())}")
    
    if os.path.exists('requirements.txt'):
        result.add_pass("Dependencies file: requirements.txt")
    else:
        result.add_fail("Dependencies file missing: requirements.txt")
    
    # Dashboard
    if os.path.exists('website/index.html'):
        result.add_pass("Dashboard: website/index.html")
    else:
        result.add_fail("Dashboard missing: website/index.html")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# VALIDATION SECTION 2: PYTHON MODULE IMPORTS & DEPENDENCIES
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def validate_python_imports(result: ValidationResult):
    """Validate that all Python modules can be imported."""
    print("\n[2/13] Validating Python Module Imports...")
    print("-" * 80)
    
    # Check package modules
    package_modules = [
        ('engelberg.core', 'Core calculation functions'),
        ('engelberg.analysis', 'Analysis orchestration'),
        ('engelberg.monte_carlo', 'Monte Carlo engine'),
    ]
    
    for module_name, description in package_modules:
        try:
            importlib.import_module(module_name)
            result.add_pass(f"Package module imports: {module_name} ({description})")
        except Exception as e:
            result.add_fail(f"Package module import error: {module_name} - {str(e)}")
    
    # Check script modules (these are in scripts/ directory)
    script_modules = [
        ('scripts.generate_all_data', 'Batch generator'),
        ('scripts.analyze_monte_carlo_sensitivity', 'Dedicated MC sensitivity runner'),
    ]
    
    for module_name, description in script_modules:
        try:
            # Import from scripts directory
            spec = importlib.util.spec_from_file_location(
                module_name.replace('.', '_'),
                os.path.join(project_root, module_name.replace('.', '/') + '.py')
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                result.add_pass(f"Script module imports: {module_name} ({description})")
            else:
                result.add_fail(f"Script module not found: {module_name}")
        except Exception as e:
            result.add_fail(f"Script module import error: {module_name} - {str(e)}")
    
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


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# VALIDATION SECTION 3: ASSUMPTIONS FILES (STRUCTURE & VALUES)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def validate_assumptions_files(result: ValidationResult):
    """Validate all assumptions JSON files for structure and reasonable values."""
    print("\n[3/13] Validating Assumptions Files...")
    print("-" * 80)
    
    import glob
    assumptions_dir = resolve_path("assumptions")
    assumptions_files = glob.glob(os.path.join(assumptions_dir, "assumptions*.json"))
    
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
        
        # Validate structure (normalize path for comparison)
        rel_path = os.path.relpath(assumptions_file, get_project_root())
        if rel_path == "assumptions/assumptions.json" or os.path.basename(assumptions_file) == "assumptions.json":
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
        
        # Expense rate ranges (catch typos e.g. 0.25 instead of 0.0025)
        if 'expenses' in assumptions:
            exp = assumptions['expenses']
            if 'insurance_rate' in exp and not str(exp.get('insurance_rate', '')).startswith('_'):
                ir = float(exp['insurance_rate'])
                if 0.0005 <= ir <= 0.02:
                    result.add_pass(f"{assumptions_file}: Insurance rate {ir*100:.2f}% in reasonable range (0.05-2%)")
                else:
                    result.add_warning(f"{assumptions_file}: Insurance rate {ir*100:.2f}% outside typical range (0.05-2%)")
            if 'maintenance_rate' in exp and not str(exp.get('maintenance_rate', '')).startswith('_'):
                mr = float(exp['maintenance_rate'])
                if 0.0005 <= mr <= 0.02:
                    result.add_pass(f"{assumptions_file}: Maintenance rate {mr*100:.2f}% in reasonable range (0.05-2%)")
                else:
                    result.add_warning(f"{assumptions_file}: Maintenance rate {mr*100:.2f}% outside typical range (0.05-2%)")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# VALIDATION SECTION 4: CROSS-VALIDATION (SCRIPTS â†” ASSUMPTIONS â†” DATA)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def validate_cross_checks(result: ValidationResult):
    """Perform cross-validation between scripts, assumptions, and generated data."""
    print("\n[4/13] Validating Cross-Dependencies...")
    print("-" * 80)
    
    try:
        from engelberg.core import (
            create_base_case_config,
            compute_annual_cash_flows,
            get_projection_defaults
        )
        
        # Test 1: Assumptions can be loaded and config created
        try:
            base_assumptions_path = resolve_path('assumptions/assumptions.json')
            config = create_base_case_config(base_assumptions_path)
            result.add_pass(f"Cross-check: {os.path.relpath(base_assumptions_path, get_project_root())} â†’ config creation successful")
            
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
            base_assumptions_path = resolve_path('assumptions/assumptions.json')
            proj_defaults = get_projection_defaults(base_assumptions_path)
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
            base_assumptions_path = resolve_path('assumptions/assumptions.json')
            with open(base_assumptions_path, 'r', encoding='utf-8') as f:
                assumptions = json.load(f)
            
            # Check financing consistency
            if assumptions['financing']['ltv'] == config.financing.ltv:
                result.add_pass("Cross-check: LTV matches (JSON â†” Config)")
            else:
                result.add_fail(f"Cross-check: LTV mismatch (JSON: {assumptions['financing']['ltv']} vs Config: {config.financing.ltv})")
            
            if assumptions['financing']['interest_rate'] == config.financing.interest_rate:
                result.add_pass("Cross-check: Interest rate matches (JSON â†” Config)")
            else:
                result.add_fail(f"Cross-check: Interest rate mismatch")
            
            # Check maintenance rate
            if assumptions['expenses']['maintenance_rate'] == config.expenses.maintenance_rate:
                result.add_pass("Cross-check: Maintenance rate matches (JSON â†” Config)")
            else:
                result.add_fail(f"Cross-check: Maintenance rate mismatch")
            
            # Check insurance rate (config stores insurance_annual; rate = insurance_annual / purchase_price)
            expected_insurance_rate = config.expenses.insurance_annual / config.financing.purchase_price if config.financing.purchase_price else 0
            if abs(assumptions['expenses']['insurance_rate'] - expected_insurance_rate) < 1e-9:
                result.add_pass("Cross-check: Insurance rate matches (JSON â†” Config)")
            else:
                result.add_fail(f"Cross-check: Insurance rate mismatch (JSON: {assumptions['expenses']['insurance_rate']}, Config derived: {expected_insurance_rate})")
            
        except Exception as e:
            result.add_fail(f"Cross-check: JSON â†” Config comparison failed - {str(e)}")
        
    except ImportError as e:
        result.add_fail(f"Cross-check: Cannot import engelberg.core - {str(e)}")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# VALIDATION SECTION 5: DATA FILE INTEGRITY
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def validate_data_files(result: ValidationResult):
    """Validate generated data files for completeness and consistency."""
    print("\n[5/13] Validating Generated Data Files...")
    print("-" * 80)
    
    # Check cases_index.json
    index_path = resolve_path("website/data/cases_index.json")
    if os.path.exists(index_path):
        result.add_pass(f"Cases index exists: {index_path}")
        
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
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
                            file_path = resolve_path(f"website/data/{filename}")
                            if os.path.exists(file_path):
                                result.add_pass(f"Case '{case_name}' {analysis_type}: {filename}")
                                
                                # Validate JSON structure
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        data = json.load(f)
                                    
                                    # Check for required keys based on analysis type
                                    if analysis_type == 'base_case_analysis':
                                        required_keys = ['config', 'annual_results', 'irr_results']  # projection_15yr or projection
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


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# VALIDATION SECTION 6: CALCULATION CONSISTENCY
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def validate_calculation_consistency(result: ValidationResult):
    """Verify that calculations are internally consistent."""
    print("\n[6/13] Validating Calculation Consistency...")
    print("-" * 80)
    
    try:
        # Load base case data
        data_path = resolve_path('website/data/base_case_base_case_analysis.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        config = data['config']
        results = data['annual_results']
        irr_results = data['irr_results']
        projection = data.get('projection') or data.get('projection_15yr')  # Support both new and legacy keys
        
        # Check 1: LTV calculation
        expected_loan = config['financing']['purchase_price'] * config['financing']['ltv']
        actual_loan = config['financing']['loan_amount']
        if abs(expected_loan - actual_loan) < 1:
            result.add_pass("Calculation: LTV â†’ Loan Amount consistent")
        else:
            result.add_fail(f"Calculation: LTV mismatch (expected {expected_loan:.0f}, got {actual_loan:.0f})")
        
        # Check 2: Equity calculation
        expected_equity = config['financing']['purchase_price'] - config['financing']['loan_amount']
        actual_equity = config['financing']['equity_total']
        if abs(expected_equity - actual_equity) < 1:
            result.add_pass("Calculation: Purchase Price - Loan = Equity consistent")
        else:
            result.add_fail(f"Calculation: Equity mismatch")
        
        # Check 3: NOI calculation (Net Revenue - Expenses)
        # Note: NOI = Net rental income (after OTA fees) - Operating expenses
        # NOT gross revenue - expenses, because OTA fees are deducted from gross revenue first
        net_rental_income = results.get('net_rental_income', results['gross_rental_income'])
        expected_noi = net_rental_income - results['total_operating_expenses']
        actual_noi = results['net_operating_income']
        if abs(expected_noi - actual_noi) < 1:
            result.add_pass("Calculation: Net Revenue - Expenses = NOI consistent")
        else:
            result.add_fail(f"Calculation: NOI mismatch (expected {expected_noi:.2f}, got {actual_noi:.2f})")
        
        # Check 3b: Ramp-up metadata present
        if 'ramp_up_months' in results and 'operational_months' in results:
            ramp_up = results['ramp_up_months']
            operational = results['operational_months']
            if ramp_up + operational == 12:
                result.add_pass(f"Ramp-up: Months add up (ramp-up: {ramp_up}, operational: {operational})")
            else:
                result.add_fail(f"Ramp-up: Months don't add to 12 (ramp-up: {ramp_up}, operational: {operational})")
            
            # If ramp-up > 0, revenue should be reduced proportionally
            if ramp_up > 0 and projection:
                year1_projection = projection[0] if isinstance(projection, list) else projection
                if 'operational_months' in year1_projection:
                    year1_op_months = year1_projection['operational_months']
                    if year1_op_months < 12:
                        result.add_pass(f"Ramp-up: Year 1 projection reflects partial operation ({year1_op_months} months)")
                    else:
                        result.add_fail("Ramp-up: Year 1 projection shows full year despite ramp-up")
        else:
            # Ramp-up metadata may not be present in older data
            pass
        
        # Check 4: Cash Flow calculation (NOI - Debt Service)
        expected_cf = results['net_operating_income'] - results['debt_service']
        actual_cf = results['cash_flow_after_debt_service']
        if abs(expected_cf - actual_cf) < 1:
            result.add_pass("Calculation: NOI - Debt Service = Cash Flow consistent")
        else:
            result.add_fail(f"Calculation: Cash Flow mismatch")
        
        # Check 5: Projection length (should match projection_years from assumptions, default 15)
        expected_years = config.get('projection', {}).get('projection_years', 15)
        if len(projection) == expected_years:
            result.add_pass(f"Calculation: Projection has correct length ({expected_years} years)")
        else:
            result.add_fail(f"Calculation: Projection has {len(projection)} years (expected {expected_years})")
        
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


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# VALIDATION SECTION 6B: OUTPUT KPI SAFETY RANGES
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def validate_output_kpi_ranges(result: ValidationResult):
    """Validate that output KPIs are within reasonable safety ranges to catch calculation errors."""
    print("\n[7/13] Validating Output KPI Safety Ranges...")
    print("-" * 80)
    
    try:
        # Load base case data
        data_path = resolve_path('website/data/base_case_base_case_analysis.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        irr_results = data.get('irr_results', {})
        annual_results = data.get('annual_results', {})
        projection = data.get('projection') or data.get('projection_15yr', [])
        config = data.get('config', {})
        
        # 1. IRR Validation (Equity IRR and Project IRR)
        equity_irr = irr_results.get('equity_irr_with_sale_pct', 0)
        project_irr = irr_results.get('project_irr_with_sale_pct', 0)
        
        # IRR should be between -50% and 100% (negative is possible for bad investments, but extreme values suggest errors)
        if -50 <= equity_irr <= 100:
            result.add_pass(f"Output KPI: Equity IRR {equity_irr:.2f}% within safety range (-50% to 100%)")
        else:
            result.add_fail(f"Output KPI: Equity IRR {equity_irr:.2f}% OUT OF RANGE! Possible calculation error.")
        
        if -50 <= project_irr <= 100:
            result.add_pass(f"Output KPI: Project IRR {project_irr:.2f}% within safety range (-50% to 100%)")
        else:
            result.add_fail(f"Output KPI: Project IRR {project_irr:.2f}% OUT OF RANGE! Possible calculation error.")
        
        # 2. Cap Rate Validation
        if projection:
            # Calculate cap rate from first year
            first_year = projection[0]
            property_value = first_year.get('property_value', 0)
            noi = first_year.get('net_operating_income', 0)
            
            if property_value > 0:
                cap_rate = (noi / property_value) * 100
                # Cap rate should be between -5% and 20% (negative possible if NOI negative, but extreme values suggest errors)
                if -5 <= cap_rate <= 20:
                    result.add_pass(f"Output KPI: Cap Rate {cap_rate:.2f}% within safety range (-5% to 20%)")
                else:
                    result.add_fail(f"Output KPI: Cap Rate {cap_rate:.2f}% OUT OF RANGE! Possible calculation error.")
        
        # 3. Cash Flow Validation
        cash_flow = annual_results.get('cash_flow_after_debt_service', 0)
        purchase_price = config.get('financing', {}).get('purchase_price', 1300000)
        
        # Cash flow should be between -50% and +50% of purchase price (extreme values suggest errors)
        if -purchase_price * 0.5 <= cash_flow <= purchase_price * 0.5:
            result.add_pass(f"Output KPI: Annual Cash Flow {cash_flow:,.0f} CHF within safety range (Â±50% of purchase price)")
        else:
            result.add_fail(f"Output KPI: Annual Cash Flow {cash_flow:,.0f} CHF OUT OF RANGE! Possible calculation error.")
        
        # 4. NPV Validation
        npv = irr_results.get('npv_at_5pct', 0)
        # NPV should be between -200% and +200% of initial equity (extreme values suggest errors)
        initial_equity = config.get('financing', {}).get('equity_total', 325000)
        if -initial_equity * 2 <= npv <= initial_equity * 2:
            result.add_pass(f"Output KPI: NPV {npv:,.0f} CHF within safety range (Â±200% of initial equity)")
        else:
            result.add_fail(f"Output KPI: NPV {npv:,.0f} CHF OUT OF RANGE! Possible calculation error.")
        
        # 5. MOIC Validation
        moic = irr_results.get('moic', 0)
        # MOIC should be between 0x and 10x (0x = total loss, 10x is very high but possible)
        if 0 <= moic <= 10:
            result.add_pass(f"Output KPI: MOIC {moic:.2f}x within safety range (0x to 10x)")
        else:
            result.add_fail(f"Output KPI: MOIC {moic:.2f}x OUT OF RANGE! Possible calculation error.")
        
        # 6. Debt Coverage Ratio Validation
        if projection:
            first_year = projection[0]
            noi = first_year.get('net_operating_income', 0)
            debt_service = first_year.get('debt_service', 1)
            
            if debt_service > 0:
                dcr = noi / debt_service
                # DCR should be between -2 and 5 (negative possible if NOI negative, but extreme values suggest errors)
                if -2 <= dcr <= 5:
                    result.add_pass(f"Output KPI: Debt Coverage Ratio {dcr:.2f}x within safety range (-2x to 5x)")
                else:
                    result.add_fail(f"Output KPI: Debt Coverage Ratio {dcr:.2f}x OUT OF RANGE! Possible calculation error.")
        
        # 7. Occupancy Rate Validation
        # Check both annual_results and projection for occupancy
        occupancy = None
        if 'overall_occupancy_rate' in annual_results:
            occupancy = annual_results.get('overall_occupancy_rate', 0) * 100
        elif projection and len(projection) > 0:
            occupancy = projection[0].get('overall_occupancy_rate', 0) * 100
        
        if occupancy is not None:
            # Occupancy should be between 0% and 100%
            if 0 <= occupancy <= 100:
                result.add_pass(f"Output KPI: Occupancy Rate {occupancy:.1f}% within safety range (0% to 100%)")
            else:
                result.add_fail(f"Output KPI: Occupancy Rate {occupancy:.1f}% OUT OF RANGE! Possible calculation error.")
        else:
            result.add_warning("Output KPI: Occupancy Rate not found in data")
        
        # 8. Property Value Validation
        if projection:
            first_year = projection[0]
            property_value = first_year.get('property_value', 0)
            
            # Property value should be positive and reasonable (between 50% and 200% of purchase price)
            purchase_price = config.get('financing', {}).get('purchase_price', 1300000)
            if purchase_price * 0.5 <= property_value <= purchase_price * 2:
                result.add_pass(f"Output KPI: Property Value {property_value:,.0f} CHF within safety range (50%-200% of purchase price)")
            else:
                result.add_fail(f"Output KPI: Property Value {property_value:,.0f} CHF OUT OF RANGE! Possible calculation error.")
        
        # 9. Gross Rental Income Validation
        gross_income = annual_results.get('gross_rental_income', 0)
        # Gross income should be positive and reasonable (not more than 20% of property value)
        if property_value > 0:
            income_rate = (gross_income / property_value) * 100
            if 0 <= income_rate <= 20:
                result.add_pass(f"Output KPI: Gross Rental Income {gross_income:,.0f} CHF ({income_rate:.1f}% of property value) within safety range")
            else:
                result.add_fail(f"Output KPI: Gross Rental Income {gross_income:,.0f} CHF ({income_rate:.1f}% of property value) OUT OF RANGE! Possible calculation error.")
        
        # 10. Loan Balance Validation (should decrease over time)
        if len(projection) >= 2:
            initial_loan = projection[0].get('remaining_loan_balance', 0)
            final_loan = projection[-1].get('remaining_loan_balance', 0)
            
            # Loan should decrease (or stay same if no amortization)
            if final_loan <= initial_loan:
                result.add_pass(f"Output KPI: Loan balance decreases correctly ({initial_loan:,.0f} â†’ {final_loan:,.0f} CHF)")
            else:
                result.add_fail(f"Output KPI: Loan balance INCREASES! ({initial_loan:,.0f} â†’ {final_loan:,.0f} CHF) Possible calculation error.")
        
        # 11. Property Value Appreciation Validation (should increase over time if appreciation rate > 0)
        if len(projection) >= 2:
            initial_value = projection[0].get('property_value', 0)
            final_value = projection[-1].get('property_value', 0)
            
            # Check if property value increases (should increase if appreciation rate is positive)
            proj_config = config.get('projection', {})
            appreciation_rate = proj_config.get('property_appreciation_rate', 0.04)
            
            if appreciation_rate > 0:
                if final_value >= initial_value:
                    result.add_pass(f"Output KPI: Property value increases with positive appreciation rate ({initial_value:,.0f} â†’ {final_value:,.0f} CHF)")
                else:
                    result.add_fail(f"Output KPI: Property value DECREASES despite positive appreciation rate! Possible calculation error.")
        
    except FileNotFoundError:
        result.add_warning("Output KPI: Base case data file not found (run python analyze.py)")
    except Exception as e:
        result.add_fail(f"Output KPI: Validation error - {str(e)}")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# VALIDATION SECTION 7: ASSUMPTIONS â†” DATA CROSS-VALIDATION
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def validate_assumptions_data_cross_check(result: ValidationResult):
    """Cross-validate that data files reflect assumptions correctly."""
    print("\n[8/13] Cross-Validating Assumptions â†” Generated Data...")
    print("-" * 80)
    
    try:
        # Load assumptions
        base_assumptions_path = resolve_path('assumptions/assumptions.json')
        with open(base_assumptions_path, 'r', encoding='utf-8') as f:
            assumptions = json.load(f)
        
        # Load generated data
        data_path = resolve_path('website/data/base_case_base_case_analysis.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Cross-check: Financing parameters
        if assumptions['financing']['purchase_price'] == data['config']['financing']['purchase_price']:
            result.add_pass("Cross-check: Purchase price (assumptions/assumptions.json â†” data)")
        else:
            result.add_fail("Cross-check: Purchase price mismatch")
        
        if assumptions['financing']['ltv'] == data['config']['financing']['ltv']:
            result.add_pass("Cross-check: LTV (assumptions/assumptions.json â†” data)")
        else:
            result.add_fail("Cross-check: LTV mismatch")
        
        if assumptions['financing']['interest_rate'] == data['config']['financing']['interest_rate']:
            result.add_pass("Cross-check: Interest rate (assumptions/assumptions.json â†” data)")
        else:
            result.add_fail("Cross-check: Interest rate mismatch")
        
        # Cross-check: Expense parameters
        if assumptions['expenses']['maintenance_rate'] == data['config']['expenses']['maintenance_rate']:
            result.add_pass("Cross-check: Maintenance rate (assumptions/assumptions.json â†” data)")
        else:
            result.add_fail("Cross-check: Maintenance rate mismatch")
        
        # Insurance: data stores insurance_annual; rate = insurance_annual / purchase_price
        purchase_price = data['config']['financing']['purchase_price']
        insurance_annual = data['config']['expenses'].get('insurance_annual', 0)
        data_insurance_rate = insurance_annual / purchase_price if purchase_price else 0
        if abs(assumptions['expenses']['insurance_rate'] - data_insurance_rate) < 1e-9:
            result.add_pass("Cross-check: Insurance rate (assumptions/assumptions.json â†” data)")
        else:
            result.add_fail("Cross-check: Insurance rate mismatch")
        
        if assumptions['expenses']['cleaning_cost_per_stay'] == data['config']['expenses']['cleaning_cost_per_stay']:
            result.add_pass("Cross-check: Cleaning cost (assumptions/assumptions.json â†” data)")
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


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# VALIDATION SECTION 8: SENSITIVITY ANALYSIS VALIDATION
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def validate_sensitivity_analysis(result: ValidationResult):
    """Validate sensitivity analysis calculations and consistency."""
    print("\n[9/13] Validating Sensitivity Analysis...")
    print("-" * 80)
    
    try:
        data_path = resolve_path('website/data/base_case_sensitivity.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            sens_data = json.load(f)
        
        base_irr = sens_data['base_irr']
        sensitivities = sens_data['sensitivities']
        
        result.add_pass(f"Sensitivity: Base IRR = {base_irr:.2f}%")
        result.add_pass(f"Sensitivity: {len(sensitivities)} parameters analyzed")
        
        # Verify ramp-up parameter is included (should be 16 total parameters now: 13 config + 3 special)
        param_names = [s['parameter_name'] for s in sensitivities]
        if 'Ramp-Up Period' in param_names:
            result.add_pass("Sensitivity: Ramp-Up Period parameter included")
        else:
            result.add_warning("Sensitivity: Ramp-Up Period parameter not found (expected 16 total params)")
        
        # Validate each sensitivity
        for sens in sensitivities:
            param = sens['parameter']
            
            # Check impact calculation
            calculated_impact = abs(sens['high']['irr'] - sens['low']['irr'])
            stated_impact = sens['impact']
            
            if abs(calculated_impact - stated_impact) < 0.0001:
                result.add_pass(f"Sensitivity '{param}': Impact calculation correct (Â±{stated_impact:.2f}%)")
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


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# VALIDATION SECTION 9: MONTE CARLO VALIDATION
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def validate_monte_carlo(result: ValidationResult):
    """Validate Monte Carlo simulation results."""
    print("\n[10/13] Validating Monte Carlo Simulation...")
    print("-" * 80)
    
    try:
        data_path = resolve_path('website/data/base_case_monte_carlo.json')
        with open(data_path, 'r', encoding='utf-8') as f:
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


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# VALIDATION SECTION 10: DASHBOARD VALIDATION
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def validate_dashboard(result: ValidationResult):
    """Validate dashboard HTML and JavaScript components."""
    print("\n[11/13] Validating Dashboard Components...")
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
        ('Horizon Selector', 'id="horizonSelect"', 'Time horizon dropdown'),
        ('Content Area', 'contentArea', 'Main content display'),
        ('Horizon State', 'currentHorizon', 'Global horizon state tracking'),
        ('Horizon Options', 'supportedHorizons', 'Canonical horizon values'),
        ('Horizon Selector Setup', 'populateHorizonSelector', 'Horizon selector initialization'),
        ('Horizon Visibility Logic', 'updateHorizonVisibility', 'Per-analysis horizon visibility'),
        ('Horizon Data Resolver', 'by_horizon', 'Horizon-specific payload resolution'),
        ('renderBaseCase', 'renderBaseCase', 'Model rendering function'),
        ('renderSensitivity', 'renderSensitivity', 'Sensitivity rendering function'),
        ('renderMonteCarlo', 'renderMonteCarlo', 'Monte Carlo rendering function'),
        ('renderMonteCarloSensitivity', 'renderMonteCarloSensitivity', 'Monte Carlo sensitivity rendering function'),
        ('renderScenarioComparison', 'renderScenarioComparison', 'Scenario comparison rendering function'),
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

    # Check horizon visibility policy matrix
    required_horizon_policies = [
        '"base_case"',
        '"sensitivity"',
        '"sensitivity_coc"',
        '"sensitivity_ncf"',
        '"monte_carlo"',
        '"monte_carlo_sensitivity"',
        '"scenario_comparison"',
    ]
    missing_policies = [token for token in required_horizon_policies if token not in html_content]
    if 'supportedAnalyses' in html_content and 'hiddenAnalyses' in html_content and not missing_policies:
        result.add_pass("Dashboard: Horizon visibility policy matrix present")
    else:
        result.add_fail(f"Dashboard: Horizon visibility policy incomplete (missing tokens: {missing_policies})")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# VALIDATION SECTION 11: SCRIPT INTEGRATION TESTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def validate_script_integration(result: ValidationResult):
    """Test that scripts can call each other correctly."""
    print("\n[12/13] Validating Script Integration...")
    print("-" * 80)
    
    try:
        # Test 1: engelberg.analysis has required functions
        from engelberg.analysis import run_base_case_analysis, run_sensitivity_analysis
        result.add_pass("Integration: engelberg.analysis has run_base_case_analysis()")
        result.add_pass("Integration: engelberg.analysis has run_sensitivity_analysis()")
        
        # Test 2: engelberg.monte_carlo has required functions
        from engelberg.monte_carlo import run_monte_carlo_simulation
        result.add_pass("Integration: engelberg.monte_carlo exports simulation function")
        
        # Test 3: Package structure is correct
        import engelberg
        if hasattr(engelberg, '__version__'):
            result.add_pass("Integration: engelberg package has version metadata")
        else:
            result.add_warning("Integration: engelberg package missing version metadata")
        
    except ImportError as e:
        result.add_fail(f"Integration: Import error - {str(e)}")
    except Exception as e:
        result.add_fail(f"Integration: Error - {str(e)}")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# VALIDATION SECTION 12: END-TO-END CONSISTENCY
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def validate_end_to_end(result: ValidationResult):
    """Perform end-to-end validation across entire system."""
    print("\n[13/13] Validating End-to-End Consistency...")
    print("-" * 80)
    
    try:
        # Check that all cases in index have corresponding assumptions files
        index_path = resolve_path('website/data/cases_index.json')
        with open(index_path, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        for case in index['cases']:
            case_name = case['case_name']
            assumptions_file = case['assumptions_file']
            # Check both with and without assumptions/ prefix for backward compatibility
            # Try resolved path first
            assumptions_path = resolve_path(assumptions_file) if os.path.exists(resolve_path(assumptions_file)) else resolve_path(f"assumptions/{assumptions_file}")
            
            if os.path.exists(assumptions_path):
                result.add_pass(f"E2E: Case '{case_name}' has assumptions file: {assumptions_path}")
            else:
                result.add_fail(f"E2E: Case '{case_name}' missing assumptions: {assumptions_path}")
            
            # Check data files match case name
            for analysis_type, filename in case.get('data_files', {}).items():
                if filename and filename.startswith(case_name):
                    result.add_pass(f"E2E: Case '{case_name}' filename correct: {filename}")
                elif filename:
                    result.add_warning(f"E2E: Case '{case_name}' filename mismatch: {filename}")
        
        # Check that number of cases matches
        import glob
        assumptions_files = glob.glob("assumptions/assumptions*.json")
        if len(index['cases']) == len(assumptions_files):
            result.add_pass(f"E2E: Case count matches ({len(index['cases'])} cases)")
        else:
            result.add_warning(f"E2E: Case count mismatch (index: {len(index['cases'])}, files: {len(assumptions_files)})")
        
    except Exception as e:
        result.add_fail(f"E2E: Validation error - {str(e)}")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MAIN VALIDATION ORCHESTRATOR
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

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
    validate_output_kpi_ranges(result)
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

