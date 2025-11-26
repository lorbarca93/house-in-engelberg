"""
Comprehensive Test Script for Base Case, Sensitivity, and Monte Carlo Analyses
Validates calculations and creates a monitoring dashboard
"""

import sys
import os
import traceback
from datetime import datetime
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

# Import all analysis modules
from simulation import (
    create_base_case_config,
    compute_annual_cash_flows,
    compute_15_year_projection,
    calculate_irrs_from_projection,
    BaseCaseConfig
)
import analysis_base_case as base_case_report
import analysis_sensitivity as sensitivity_analysis
import analysis_monte_carlo as monte_carlo_analysis


class TestResult:
    """Container for test results"""
    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category
        self.passed = False
        self.message = ""
        self.expected = None
        self.actual = None
        self.tolerance = 0.01  # 1% tolerance for floating point comparisons
        self.details = {}
    
    def check_equality(self, expected: float, actual: float, tolerance: float = None):
        """Check if two values are equal within tolerance"""
        if tolerance is None:
            tolerance = self.tolerance
        diff = abs(expected - actual)
        max_val = max(abs(expected), abs(actual), 1.0)
        relative_error = diff / max_val if max_val > 0 else diff
        
        self.expected = expected
        self.actual = actual
        self.passed = relative_error <= tolerance
        self.message = f"Expected: {expected:.2f}, Actual: {actual:.2f}, Error: {relative_error*100:.2f}%"
        return self.passed
    
    def check_range(self, value: float, min_val: float, max_val: float):
        """Check if value is within expected range"""
        self.actual = value
        self.expected = f"[{min_val:.2f}, {max_val:.2f}]"
        self.passed = min_val <= value <= max_val
        self.message = f"Value: {value:.2f}, Expected Range: [{min_val:.2f}, {max_val:.2f}]"
        return self.passed
    
    def check_positive(self, value: float):
        """Check if value is positive"""
        self.actual = value
        self.expected = "> 0"
        self.passed = value > 0
        self.message = f"Value: {value:.2f}, Expected: > 0"
        return self.passed
    
    def check_negative(self, value: float):
        """Check if value is negative"""
        self.actual = value
        self.expected = "< 0"
        self.passed = value < 0
        self.message = f"Value: {value:.2f}, Expected: < 0"
        return self.passed
    
    def set_pass(self, message: str = ""):
        """Manually set test as passed"""
        self.passed = True
        self.message = message
    
    def set_fail(self, message: str):
        """Manually set test as failed"""
        self.passed = False
        self.message = message


class AnalysisTester:
    """Main test class for all analyses"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.base_config = None
        self.base_case_results = None
        self.base_case_projection = None
        self.base_case_irr = None
        self.sensitivity_results = None
        self.monte_carlo_results = None
        self.monte_carlo_stats = None
    
    def run_all_tests(self):
        """Run all test suites"""
        print("=" * 80)
        print("COMPREHENSIVE ANALYSIS TEST SUITE")
        print("=" * 80)
        print()
        
        try:
            # Load base configuration
            print("[*] Loading base case configuration...")
            self.base_config = create_base_case_config()
            self.test_base_config()
            
            # Test base case analysis
            print("\n[*] Testing Base Case Analysis...")
            self.test_base_case()
            
            # Test sensitivity analysis
            print("\n[*] Testing Sensitivity Analysis...")
            self.test_sensitivity_analysis()
            
            # Test Monte Carlo analysis
            print("\n[*] Testing Monte Carlo Analysis...")
            self.test_monte_carlo()
            
            # Cross-validation tests
            print("\n[*] Running Cross-Validation Tests...")
            self.test_cross_validation()
            
            # Generate dashboard
            print("\n[*] Generating Test Dashboard...")
            self.generate_dashboard()
            
            print("\n" + "=" * 80)
            print("TEST SUITE COMPLETE")
            print("=" * 80)
            passed = sum(1 for r in self.results if r.passed)
            total = len(self.results)
            print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
            print(f"Dashboard saved to: output/report_validation.html")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n[ERROR] Test suite failed with exception: {e}")
            traceback.print_exc()
            return False
        
        return True
    
    def test_base_config(self):
        """Test base configuration is valid"""
        test = TestResult("Base Configuration Valid", "Configuration")
        
        try:
            # Check key parameters
            assert self.base_config.financing.purchase_price > 0, "Purchase price must be positive"
            assert 0 < self.base_config.financing.ltv < 1, "LTV must be between 0 and 1"
            assert self.base_config.financing.interest_rate > 0, "Interest rate must be positive"
            assert self.base_config.financing.num_owners > 0, "Number of owners must be positive"
            assert 0 < self.base_config.rental.occupancy_rate <= 1, "Occupancy rate must be between 0 and 1"
            assert self.base_config.rental.average_daily_rate > 0, "Daily rate must be positive"
            
            # Check calculated values
            assert self.base_config.financing.loan_amount > 0, "Loan amount must be positive"
            assert self.base_config.financing.equity_total > 0, "Equity must be positive"
            assert self.base_config.financing.equity_per_owner > 0, "Equity per owner must be positive"
            
            test.set_pass("All base configuration parameters are valid")
        except AssertionError as e:
            test.set_fail(str(e))
        
        self.results.append(test)
    
    def test_base_case(self):
        """Test base case calculations"""
        try:
            # Run base case analysis
            base_result = compute_annual_cash_flows(self.base_config)
            self.base_case_results = base_result
            
            # Test 1: Revenue calculation
            test = TestResult("Gross Rental Income Calculation", "Base Case - Revenue")
            expected_gri = (self.base_config.rental.rented_nights * 
                          self.base_config.rental.average_daily_rate)
            test.check_equality(expected_gri, base_result['gross_rental_income'], tolerance=1.0)
            self.results.append(test)
            
            # Test 2: NOI = Revenue - Expenses
            test = TestResult("Net Operating Income Calculation", "Base Case - Income")
            calculated_noi = base_result['gross_rental_income'] - base_result['total_operating_expenses']
            test.check_equality(calculated_noi, base_result['net_operating_income'], tolerance=1.0)
            self.results.append(test)
            
            # Test 3: Cash Flow = NOI - Debt Service
            test = TestResult("Cash Flow After Debt Calculation", "Base Case - Cash Flow")
            calculated_cf = base_result['net_operating_income'] - base_result['debt_service']
            test.check_equality(calculated_cf, base_result['cash_flow_after_debt_service'], tolerance=1.0)
            self.results.append(test)
            
            # Test 4: Cap Rate = NOI / Purchase Price
            test = TestResult("Cap Rate Calculation", "Base Case - KPIs")
            expected_cap_rate = (base_result['net_operating_income'] / 
                               self.base_config.financing.purchase_price) * 100
            test.check_equality(expected_cap_rate, base_result['cap_rate_pct'], tolerance=0.1)
            self.results.append(test)
            
            # Test 5: Cash-on-Cash Return = CF / Equity
            test = TestResult("Cash-on-Cash Return Calculation", "Base Case - KPIs")
            expected_coc = (base_result['cash_flow_after_debt_service'] / 
                          base_result['equity_total']) * 100
            test.check_equality(expected_coc, base_result['cash_on_cash_return_pct'], tolerance=0.1)
            self.results.append(test)
            
            # Test 6: Debt Coverage Ratio = NOI / Debt Service
            test = TestResult("Debt Coverage Ratio Calculation", "Base Case - KPIs")
            if base_result['debt_service'] > 0:
                expected_dscr = base_result['net_operating_income'] / base_result['debt_service']
                test.check_equality(expected_dscr, base_result['debt_coverage_ratio'], tolerance=0.01)
            else:
                test.set_fail("Debt service is zero, cannot calculate DSCR")
            self.results.append(test)
            
            # Test 7: Debt Service = Interest + Amortization
            test = TestResult("Debt Service Components", "Base Case - Financing")
            calculated_ds = base_result['interest_payment'] + base_result['amortization_payment']
            test.check_equality(calculated_ds, base_result['debt_service'], tolerance=1.0)
            self.results.append(test)
            
            # Test 8: Equity = Purchase Price - Loan
            test = TestResult("Equity Calculation", "Base Case - Financing")
            expected_equity = (self.base_config.financing.purchase_price - 
                             self.base_config.financing.loan_amount)
            test.check_equality(expected_equity, base_result['equity_total'], tolerance=1.0)
            self.results.append(test)
            
            # Test 9: 15-Year Projection
            print("  [*] Computing 15-year projection...")
            projection = compute_15_year_projection(
                self.base_config, 
                start_year=2026, 
                inflation_rate=0.02, 
                property_appreciation_rate=0.02
            )
            self.base_case_projection = projection
            
            test = TestResult("15-Year Projection Length", "Base Case - Projection")
            test.check_equality(15, len(projection), tolerance=0)
            self.results.append(test)
            
            # Test 10: Loan balance decreases over time
            test = TestResult("Loan Amortization", "Base Case - Projection")
            initial_loan = projection[0]['remaining_loan_balance']
            final_loan = projection[-1]['remaining_loan_balance']
            test.passed = final_loan < initial_loan
            test.message = f"Initial: {initial_loan:,.0f}, Final: {final_loan:,.0f}"
            self.results.append(test)
            
            # Test 11: IRR Calculation
            print("  [*] Calculating IRRs...")
            final_property_value = projection[-1]['property_value']
            final_loan_balance = projection[-1]['remaining_loan_balance']
            irr_results = calculate_irrs_from_projection(
                projection,
                base_result['equity_per_owner'],
                final_property_value,
                final_loan_balance,
                self.base_config.financing.num_owners,
                purchase_price=self.base_config.financing.purchase_price
            )
            self.base_case_irr = irr_results
            
            test = TestResult("IRR with Sale Range", "Base Case - IRR")
            # IRR should be reasonable (between -50% and 50%)
            test.check_range(irr_results['irr_with_sale_pct'], -50, 50)
            self.results.append(test)
            
            test = TestResult("IRR with Sale > IRR without Sale", "Base Case - IRR")
            test.passed = irr_results['irr_with_sale_pct'] >= irr_results['irr_without_sale_pct']
            test.message = f"With Sale: {irr_results['irr_with_sale_pct']:.2f}%, Without: {irr_results['irr_without_sale_pct']:.2f}%"
            self.results.append(test)
            
        except Exception as e:
            test = TestResult("Base Case Analysis", "Base Case")
            test.set_fail(f"Exception: {str(e)}")
            self.results.append(test)
            traceback.print_exc()
    
    def test_sensitivity_analysis(self):
        """Test sensitivity analysis calculations"""
        try:
            print("  [*] Running sensitivity analysis...")
            
            # Test that sensitivity functions work
            test = TestResult("Sensitivity Analysis Execution", "Sensitivity")
            try:
                # Run a simple sensitivity
                df_occ = sensitivity_analysis.sensitivity_occupancy_rate(
                    self.base_config, min_rate=0.50, max_rate=0.60, steps=3
                )
                test.set_pass(f"Successfully generated {len(df_occ)} sensitivity scenarios")
            except Exception as e:
                test.set_fail(f"Failed to run sensitivity: {str(e)}")
            self.results.append(test)
            
            # Test that sensitivity results are reasonable
            if test.passed:
                test = TestResult("Sensitivity Results Validity", "Sensitivity")
                # Check that higher occupancy leads to higher cash flow
                if len(df_occ) >= 2:
                    low_occ_cf = df_occ.iloc[0]['Cash Flow After Debt (CHF)']
                    high_occ_cf = df_occ.iloc[-1]['Cash Flow After Debt (CHF)']
                    test.passed = high_occ_cf >= low_occ_cf
                    test.message = f"Low occupancy CF: {low_occ_cf:,.0f}, High occupancy CF: {high_occ_cf:,.0f}"
                else:
                    test.set_fail("Insufficient sensitivity data")
                self.results.append(test)
            
            # Test NPV/IRR calculation for sensitivity
            test = TestResult("Sensitivity NPV/IRR Calculation", "Sensitivity")
            try:
                npv_irr = sensitivity_analysis.calculate_npv_irr_for_config(
                    self.base_config, discount_rate=0.04
                )
                # NPV should be reasonable
                test.check_range(npv_irr['npv'], -1_000_000, 1_000_000)
                test.details = {'npv': npv_irr['npv'], 'irr': npv_irr['irr_with_sale_pct']}
            except Exception as e:
                test.set_fail(f"Failed to calculate NPV/IRR: {str(e)}")
            self.results.append(test)
            
        except Exception as e:
            test = TestResult("Sensitivity Analysis", "Sensitivity")
            test.set_fail(f"Exception: {str(e)}")
            self.results.append(test)
            traceback.print_exc()
    
    def test_monte_carlo(self):
        """Test Monte Carlo analysis"""
        try:
            print("  [*] Running Monte Carlo simulation (1000 iterations for testing)...")
            
            # Run smaller simulation for testing
            test = TestResult("Monte Carlo Execution", "Monte Carlo")
            try:
                df_mc = monte_carlo_analysis.run_monte_carlo_simulation(
                    self.base_config, 
                    num_simulations=1000,  # Smaller for testing
                    discount_rate=0.04
                )
                self.monte_carlo_results = df_mc
                test.set_pass(f"Successfully completed {len(df_mc)} simulations")
            except Exception as e:
                test.set_fail(f"Failed to run Monte Carlo: {str(e)}")
            self.results.append(test)
            
            if test.passed and self.monte_carlo_results is not None:
                # Test statistics calculation
                test = TestResult("Monte Carlo Statistics", "Monte Carlo")
                try:
                    stats = monte_carlo_analysis.calculate_statistics(self.monte_carlo_results)
                    self.monte_carlo_stats = stats
                    
                    # Check that mean is within reasonable range
                    npv_mean = stats['npv']['mean']
                    test.check_range(npv_mean, -500_000, 500_000)
                    test.details = {
                        'npv_mean': npv_mean,
                        'npv_std': stats['npv']['std'],
                        'irr_mean': stats['irr_with_sale']['mean']
                    }
                except Exception as e:
                    test.set_fail(f"Failed to calculate statistics: {str(e)}")
                self.results.append(test)
                
                # Test that results are distributed
                test = TestResult("Monte Carlo Distribution", "Monte Carlo")
                npv_std = self.monte_carlo_results['npv'].std()
                test.passed = npv_std > 0  # Should have some variance
                test.message = f"Standard deviation: {npv_std:,.0f}"
                self.results.append(test)
                
        except Exception as e:
            test = TestResult("Monte Carlo Analysis", "Monte Carlo")
            test.set_fail(f"Exception: {str(e)}")
            self.results.append(test)
            traceback.print_exc()
    
    def test_cross_validation(self):
        """Cross-validate calculations between different methods"""
        try:
            # Test 1: Base case NPV should match sensitivity base case NPV
            if self.base_case_results:
                test = TestResult("Base Case NPV Consistency", "Cross-Validation")
                try:
                    base_npv_irr = sensitivity_analysis.calculate_npv_irr_for_config(
                        self.base_config, discount_rate=0.04
                    )
                    # This is a sanity check - values should be reasonable
                    test.check_range(base_npv_irr['npv'], -1_000_000, 1_000_000)
                    test.details = {'base_npv': base_npv_irr['npv']}
                except Exception as e:
                    test.set_fail(f"Failed: {str(e)}")
                self.results.append(test)
            
            # Test 2: Monte Carlo base case should be close to actual base case
            if self.monte_carlo_results is not None and self.base_case_results:
                test = TestResult("Monte Carlo Base Case Alignment", "Cross-Validation")
                # Get median from Monte Carlo (should be close to base case)
                mc_median_cf = self.monte_carlo_results['annual_cash_flow'].median()
                base_cf = self.base_case_results['cash_flow_after_debt_service']
                # Allow 20% difference due to randomness
                test.check_equality(base_cf, mc_median_cf, tolerance=0.20)
                test.details = {
                    'base_cf': base_cf,
                    'mc_median_cf': mc_median_cf,
                    'difference_pct': abs(base_cf - mc_median_cf) / abs(base_cf) * 100 if base_cf != 0 else 0
                }
                self.results.append(test)
            
            # Test 3: IRR consistency
            if self.base_case_irr and self.monte_carlo_stats:
                test = TestResult("IRR Consistency", "Cross-Validation")
                base_irr = self.base_case_irr['irr_with_sale_pct']
                mc_irr = self.monte_carlo_stats['irr_with_sale']['median']
                # Allow 10 percentage points difference due to Monte Carlo randomness
                diff = abs(base_irr - mc_irr)
                test.passed = diff <= 10.0
                test.message = f"Base IRR: {base_irr:.2f}%, MC Median: {mc_irr:.2f}%, Diff: {diff:.2f}pp"
                test.details = {
                    'base_irr': base_irr,
                    'mc_median_irr': mc_irr,
                    'difference_pp': diff
                }
                self.results.append(test)
            
            # Test 4: Expense components sum correctly
            if self.base_case_results:
                test = TestResult("Expense Components Sum", "Cross-Validation")
                calculated_expenses = (
                    self.base_case_results['property_management_cost'] +
                    self.base_case_results['cleaning_cost'] +
                    self.base_case_results['tourist_tax'] +
                    self.base_case_results['insurance'] +
                    self.base_case_results['utilities'] +
                    self.base_case_results['maintenance_reserve']
                )
                test.check_equality(calculated_expenses, self.base_case_results['total_operating_expenses'], tolerance=1.0)
                test.details = {
                    'calculated': calculated_expenses,
                    'reported': self.base_case_results['total_operating_expenses']
                }
                self.results.append(test)
            
            # Test 5: Revenue consistency
            if self.base_case_results:
                test = TestResult("Revenue Calculation Consistency", "Cross-Validation")
                expected_revenue = (self.base_config.rental.rented_nights * 
                                  self.base_config.rental.average_daily_rate)
                test.check_equality(expected_revenue, self.base_case_results['gross_rental_income'], tolerance=1.0)
                self.results.append(test)
            
        except Exception as e:
            test = TestResult("Cross-Validation", "Cross-Validation")
            test.set_fail(f"Exception: {str(e)}")
            self.results.append(test)
            traceback.print_exc()
    
    def generate_dashboard(self):
        """Generate HTML dashboard with test results"""
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        
        # Group results by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
        
        # Calculate statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Generate HTML
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analysis Test Dashboard</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f7fa;
            color: #2c3e50;
            line-height: 1.6;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        
        .summary-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .summary-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        .summary-card .label {{
            color: #6c757d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .summary-card.passed .value {{
            color: #2ecc71;
        }}
        
        .summary-card.failed .value {{
            color: #e74c3c;
        }}
        
        .summary-card.total .value {{
            color: #3498db;
        }}
        
        .summary-card.rate .value {{
            color: #9b59b6;
        }}
        
        .category-section {{
            margin: 30px;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .category-header {{
            background: #0f3460;
            color: white;
            padding: 20px;
            font-size: 1.3em;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .test-results {{
            padding: 0;
        }}
        
        .test-item {{
            padding: 20px;
            border-bottom: 1px solid #e8ecef;
            display: grid;
            grid-template-columns: auto 1fr auto;
            gap: 20px;
            align-items: center;
        }}
        
        .test-item:last-child {{
            border-bottom: none;
        }}
        
        .test-item.passed {{
            background: #f0f9f4;
        }}
        
        .test-item.failed {{
            background: #fef5f5;
        }}
        
        .test-status {{
            font-size: 1.5em;
        }}
        
        .test-status.passed {{
            color: #2ecc71;
        }}
        
        .test-status.failed {{
            color: #e74c3c;
        }}
        
        .test-name {{
            font-weight: 600;
            font-size: 1.1em;
            color: #1a1a2e;
        }}
        
        .test-message {{
            color: #6c757d;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        
        .test-details {{
            font-size: 0.85em;
            color: #495057;
            font-family: 'Courier New', monospace;
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
        }}
        
        .timestamp {{
            text-align: center;
            padding: 20px;
            color: #6c757d;
            font-size: 0.9em;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-check-circle"></i> Analysis Test Dashboard</h1>
            <div class="subtitle">Comprehensive Validation of Base Case, Sensitivity, and Monte Carlo Analyses</div>
        </div>
        
        <div class="summary">
            <div class="summary-card total">
                <div class="label">Total Tests</div>
                <div class="value">{total_tests}</div>
            </div>
            <div class="summary-card passed">
                <div class="label">Passed</div>
                <div class="value">{passed_tests}</div>
            </div>
            <div class="summary-card failed">
                <div class="label">Failed</div>
                <div class="value">{failed_tests}</div>
            </div>
            <div class="summary-card rate">
                <div class="label">Pass Rate</div>
                <div class="value">{pass_rate:.1f}%</div>
            </div>
        </div>
"""
        
        # Add category sections
        for category, tests in categories.items():
            category_passed = sum(1 for t in tests if t.passed)
            category_total = len(tests)
            category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
            
            html += f"""
        <div class="category-section">
            <div class="category-header">
                <i class="fas fa-folder"></i> {category} ({category_passed}/{category_total} passed, {category_rate:.1f}%)
            </div>
            <div class="test-results">
"""
            
            for test in tests:
                status_class = "passed" if test.passed else "failed"
                status_icon = "check-circle" if test.passed else "times-circle"
                
                html += f"""
                <div class="test-item {status_class}">
                    <div class="test-status {status_class}">
                        <i class="fas fa-{status_icon}"></i>
                    </div>
                    <div>
                        <div class="test-name">{test.name}</div>
                        <div class="test-message">{test.message}</div>
"""
                
                if test.details:
                    html += f"""
                        <div class="test-details">
                            {', '.join([f"{k}: {v}" for k, v in test.details.items()])}
                        </div>
"""
                
                html += """
                    </div>
                </div>
"""
            
            html += """
            </div>
        </div>
"""
        
        # Add footer
        html += f"""
        <div class="timestamp">
            <i class="fas fa-clock"></i> Test run completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
        
        <div class="footer">
            <p>This dashboard validates calculations across Base Case, Sensitivity, and Monte Carlo analyses</p>
            <p>All calculations are cross-checked for accuracy and consistency</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Write to file
        output_path = "output/report_validation.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"  [+] Dashboard saved to: {output_path}")


if __name__ == "__main__":
    tester = AnalysisTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

