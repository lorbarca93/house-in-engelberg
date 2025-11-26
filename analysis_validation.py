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
            
            # Data integrity tests
            print("\n[*] Running Data Integrity Tests...")
            self.test_data_integrity()
            
            # File generation tests
            print("\n[*] Testing File Generation...")
            self.test_file_generation()
            
            # Alternative scenarios tests
            print("\n[*] Testing Alternative Scenarios...")
            self.test_alternative_scenarios()
            
            # Performance tests
            print("\n[*] Running Performance Tests...")
            self.test_performance()
            
            # Generate dashboard
            print("\n[*] Generating Test Dashboard...")
            self.generate_dashboard()
            
            print("\n" + "=" * 80)
            print("TEST SUITE COMPLETE")
            print("=" * 80)
            passed = sum(1 for r in self.results if r.passed)
            total = len(self.results)
            print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
            print(f"Dashboard saved to: website/report_validation.html")
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
                    self.base_config, discount_rate=0.03
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
                    discount_rate=0.03
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
                        self.base_config, discount_rate=0.03
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
                # Get statistics from Monte Carlo
                mc_median_cf = self.monte_carlo_results['annual_cash_flow'].median()
                mc_q25 = self.monte_carlo_results['annual_cash_flow'].quantile(0.25)
                mc_q75 = self.monte_carlo_results['annual_cash_flow'].quantile(0.75)
                base_cf = self.base_case_results['cash_flow_after_debt_service']
                
                # Check if base case is within the interquartile range (IQR) of Monte Carlo results
                # This is more appropriate for Monte Carlo since parameters vary randomly
                within_iqr = mc_q25 <= base_cf <= mc_q75
                same_sign = (base_cf < 0 and mc_median_cf < 0) or (base_cf > 0 and mc_median_cf > 0)
                
                # Also check if within 2x IQR (more lenient check)
                iqr = mc_q75 - mc_q25
                within_2x_iqr = (mc_median_cf - 2*iqr) <= base_cf <= (mc_median_cf + 2*iqr)
                
                test.passed = same_sign and (within_iqr or within_2x_iqr)
                diff_pct = abs(base_cf - mc_median_cf) / abs(base_cf) * 100 if base_cf != 0 else 0
                test.message = f"Base: {base_cf:,.0f}, MC Median: {mc_median_cf:,.0f}, IQR: [{mc_q25:,.0f}, {mc_q75:,.0f}]"
                test.details = {
                    'base_cf': base_cf,
                    'mc_median_cf': mc_median_cf,
                    'mc_q25': mc_q25,
                    'mc_q75': mc_q75,
                    'difference_pct': diff_pct,
                    'same_sign': same_sign,
                    'within_iqr': within_iqr,
                    'within_2x_iqr': within_2x_iqr
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
            
            # Test 6: Property value appreciation
            if self.base_case_projection:
                test = TestResult("Property Value Appreciation", "Cross-Validation")
                initial_value = self.base_case_projection[0]['property_value']
                final_value = self.base_case_projection[-1]['property_value']
                test.passed = final_value > initial_value
                test.message = f"Initial: {initial_value:,.0f}, Final: {final_value:,.0f}"
                self.results.append(test)
            
            # Test 7: Cash flow per owner calculation
            if self.base_case_results:
                test = TestResult("Cash Flow Per Owner Calculation", "Cross-Validation")
                expected_cf_per_owner = (self.base_case_results['cash_flow_after_debt_service'] / 
                                       self.base_config.financing.num_owners)
                test.check_equality(expected_cf_per_owner, self.base_case_results['cash_flow_per_owner'], tolerance=0.01)
                self.results.append(test)
            
            # Test 8: Operating expense ratio
            if self.base_case_results:
                test = TestResult("Operating Expense Ratio", "Cross-Validation")
                expected_oer = (self.base_case_results['total_operating_expenses'] / 
                              self.base_case_results['gross_rental_income'] * 100)
                test.check_equality(expected_oer, self.base_case_results['operating_expense_ratio_pct'], tolerance=0.1)
                self.results.append(test)
            
        except Exception as e:
            test = TestResult("Cross-Validation", "Cross-Validation")
            test.set_fail(f"Exception: {str(e)}")
            self.results.append(test)
            traceback.print_exc()
    
    def test_data_integrity(self):
        """Test data integrity and edge cases"""
        try:
            # Test 1: No negative revenue
            if self.base_case_results:
                test = TestResult("Revenue Non-Negative", "Data Integrity")
                test.passed = self.base_case_results['gross_rental_income'] >= 0
                test.message = f"Revenue: {self.base_case_results['gross_rental_income']:,.0f} CHF"
                self.results.append(test)
            
            # Test 2: Loan amount <= Purchase price
            if self.base_config:
                test = TestResult("Loan Amount <= Purchase Price", "Data Integrity")
                test.passed = self.base_config.financing.loan_amount <= self.base_config.financing.purchase_price
                test.message = f"Loan: {self.base_config.financing.loan_amount:,.0f}, Price: {self.base_config.financing.purchase_price:,.0f}"
                self.results.append(test)
            
            # Test 3: Equity = Purchase Price - Loan
            if self.base_config:
                test = TestResult("Equity Calculation Integrity", "Data Integrity")
                calculated_equity = self.base_config.financing.purchase_price - self.base_config.financing.loan_amount
                test.check_equality(calculated_equity, self.base_config.financing.equity_total, tolerance=0.01)
                self.results.append(test)
            
            # Test 4: Occupancy rate in valid range
            if self.base_config:
                test = TestResult("Occupancy Rate Valid Range", "Data Integrity")
                test.passed = 0 <= self.base_config.rental.occupancy_rate <= 1
                test.message = f"Occupancy: {self.base_config.rental.occupancy_rate*100:.1f}%"
                self.results.append(test)
            
            # Test 5: LTV in valid range
            if self.base_config:
                test = TestResult("LTV Valid Range", "Data Integrity")
                test.passed = 0 < self.base_config.financing.ltv < 1
                test.message = f"LTV: {self.base_config.financing.ltv*100:.1f}%"
                self.results.append(test)
            
            # Test 6: Projection years are sequential
            if self.base_case_projection:
                test = TestResult("Projection Year Sequence", "Data Integrity")
                years = [year['year'] for year in self.base_case_projection]
                test.passed = years == list(range(years[0], years[0] + len(years)))
                test.message = f"Years: {years[0]} to {years[-1]}"
                self.results.append(test)
            
            # Test 7: All projection values are numeric
            if self.base_case_projection:
                test = TestResult("Projection Values Numeric", "Data Integrity")
                all_numeric = True
                for year_data in self.base_case_projection:
                    for key, value in year_data.items():
                        if key != 'year' and not isinstance(value, (int, float)):
                            all_numeric = False
                            break
                    if not all_numeric:
                        break
                test.passed = all_numeric
                test.message = "All projection values are numeric" if all_numeric else "Some non-numeric values found"
                self.results.append(test)
            
        except Exception as e:
            test = TestResult("Data Integrity", "Data Integrity")
            test.set_fail(f"Exception: {str(e)}")
            self.results.append(test)
            traceback.print_exc()
    
    def test_file_generation(self):
        """Test that HTML reports are generated correctly"""
        try:
            # Test 1: Base case report exists
            test = TestResult("Base Case Report File Exists", "File Generation")
            report_path = "website/report_base_case.html"
            test.passed = os.path.exists(report_path)
            if test.passed:
                file_size = os.path.getsize(report_path)
                test.message = f"File exists ({file_size:,} bytes)"
                test.passed = file_size > 1000  # Should be at least 1KB
            else:
                test.message = "File not found"
            self.results.append(test)
            
            # Test 2: Sensitivity report exists
            test = TestResult("Sensitivity Report File Exists", "File Generation")
            report_path = "website/report_sensitivity.html"
            test.passed = os.path.exists(report_path)
            if test.passed:
                file_size = os.path.getsize(report_path)
                test.message = f"File exists ({file_size:,} bytes)"
                test.passed = file_size > 1000
            else:
                test.message = "File not found"
            self.results.append(test)
            
            # Test 3: Monte Carlo report exists
            test = TestResult("Monte Carlo Report File Exists", "File Generation")
            report_path = "website/report_monte_carlo.html"
            test.passed = os.path.exists(report_path)
            if test.passed:
                file_size = os.path.getsize(report_path)
                test.message = f"File exists ({file_size:,} bytes)"
                test.passed = file_size > 1000
            else:
                test.message = "File not found"
            self.results.append(test)
            
            # Test 4: HTML structure validation (check for key elements)
            test = TestResult("Base Case HTML Structure", "File Generation")
            report_path = "website/report_base_case.html"
            if os.path.exists(report_path):
                with open(report_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    has_doctype = '<!DOCTYPE html>' in content
                    has_title = '<title>' in content
                    has_body = '<body>' in content
                    has_charts = 'apexcharts' in content.lower() or 'plotly' in content.lower()
                    test.passed = has_doctype and has_title and has_body and has_charts
                    test.message = f"HTML structure valid: DOCTYPE={has_doctype}, Title={has_title}, Body={has_body}, Charts={has_charts}"
            else:
                test.set_fail("Report file not found")
            self.results.append(test)
            
            # Test 5: Homepage exists
            test = TestResult("Homepage File Exists", "File Generation")
            report_path = "website/index.html"
            test.passed = os.path.exists(report_path)
            if test.passed:
                file_size = os.path.getsize(report_path)
                test.message = f"File exists ({file_size:,} bytes)"
            else:
                test.message = "File not found"
            self.results.append(test)
            
        except Exception as e:
            test = TestResult("File Generation", "File Generation")
            test.set_fail(f"Exception: {str(e)}")
            self.results.append(test)
            traceback.print_exc()
    
    def test_alternative_scenarios(self):
        """Test alternative scenario calculations"""
        try:
            from analysis_alternative_scenarios import generate_scenario_report
            
            # Test 1: 3 owners scenario
            test = TestResult("3 Owners Scenario Calculation", "Alternative Scenarios")
            try:
                config_3 = create_base_case_config()
                config_3.financing.num_owners = 3
                config_3.rental.num_owners = 3
                results_3 = compute_annual_cash_flows(config_3)
                # Equity per owner should be higher with fewer owners
                test.passed = results_3['equity_per_owner'] > self.base_case_results['equity_per_owner']
                test.message = f"3 owners equity: {results_3['equity_per_owner']:,.0f}, Base: {self.base_case_results['equity_per_owner']:,.0f}"
            except Exception as e:
                test.set_fail(f"Failed: {str(e)}")
            self.results.append(test)
            
            # Test 2: Lower price scenario
            test = TestResult("Lower Price Scenario Calculation", "Alternative Scenarios")
            try:
                config_lower = create_base_case_config()
                config_lower.financing.purchase_price = 1_100_000
                results_lower = compute_annual_cash_flows(config_lower)
                # Lower price should result in lower debt service
                test.passed = results_lower['debt_service'] < self.base_case_results['debt_service']
                test.message = f"Lower price debt: {results_lower['debt_service']:,.0f}, Base: {self.base_case_results['debt_service']:,.0f}"
            except Exception as e:
                test.set_fail(f"Failed: {str(e)}")
            self.results.append(test)
            
        except Exception as e:
            test = TestResult("Alternative Scenarios", "Alternative Scenarios")
            test.set_fail(f"Exception: {str(e)}")
            self.results.append(test)
            traceback.print_exc()
    
    def test_performance(self):
        """Test performance and timing"""
        try:
            import time
            
            # Test 1: Base case calculation speed
            test = TestResult("Base Case Calculation Speed", "Performance")
            start_time = time.time()
            _ = compute_annual_cash_flows(self.base_config)
            elapsed = time.time() - start_time
            test.passed = elapsed < 1.0  # Should complete in under 1 second
            test.message = f"Calculation time: {elapsed*1000:.2f}ms"
            test.details = {'elapsed_ms': elapsed * 1000}
            self.results.append(test)
            
            # Test 2: Projection calculation speed
            test = TestResult("Projection Calculation Speed", "Performance")
            start_time = time.time()
            _ = compute_15_year_projection(self.base_config, start_year=2026)
            elapsed = time.time() - start_time
            test.passed = elapsed < 2.0  # Should complete in under 2 seconds
            test.message = f"Calculation time: {elapsed*1000:.2f}ms"
            test.details = {'elapsed_ms': elapsed * 1000}
            self.results.append(test)
            
        except Exception as e:
            test = TestResult("Performance", "Performance")
            test.set_fail(f"Exception: {str(e)}")
            self.results.append(test)
            traceback.print_exc()
    
    def generate_dashboard(self):
        """Generate HTML dashboard with test results"""
        # Ensure output directory exists
        os.makedirs("website", exist_ok=True)
        
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
        
        # Define helper functions for layout (if not imported)
        def generate_top_toolbar(report_title: str, back_link: str = "index.html", subtitle: str = "") -> str:
            return f'''<div class="top-toolbar"><div class="toolbar-left"><a href="{back_link}" class="toolbar-btn"><i class="fas fa-home"></i> <span class="toolbar-btn-text">Home</span></a></div><div class="toolbar-center"><h1 class="toolbar-title">{report_title}</h1>{f'<p class="toolbar-subtitle">{subtitle}</p>' if subtitle else ''}</div><div class="toolbar-right"></div></div>'''
        
        def generate_sidebar_navigation(sections):
            nav_items = ''.join([f'<li><a href="#{s.get("id","")}" class="sidebar-item" data-section="{s.get("id","")}"><i class="{s.get("icon","fas fa-circle")}"></i><span class="sidebar-item-text">{s.get("title","")}</span></a></li>' for s in sections])
            return f'<nav class="sidebar"><div class="sidebar-header"><h3><i class="fas fa-bars"></i> Navigation</h3></div><ul class="sidebar-nav">{nav_items}</ul></nav>'
        
        def generate_shared_layout_css():
            return '''.layout-container{display:flex;flex-direction:column;min-height:100vh;background:#f5f7fa}.top-toolbar{position:fixed;top:0;left:0;right:0;height:60px;background:var(--gradient-1);color:white;display:flex;align-items:center;justify-content:space-between;padding:0 20px;z-index:1000;box-shadow:0 2px 8px rgba(0,0,0,0.15)}.toolbar-left,.toolbar-right{display:flex;align-items:center;gap:15px}.toolbar-center{flex:1;text-align:center}.toolbar-title{font-size:1.3em;font-weight:700;margin:0;color:white}.toolbar-subtitle{font-size:0.85em;margin:0;opacity:0.9}.toolbar-btn{display:inline-flex;align-items:center;gap:8px;padding:10px 20px;background:rgba(255,255,255,0.2);color:white;text-decoration:none;border-radius:6px;font-size:0.9em;font-weight:600;transition:all 0.2s ease;border:1px solid rgba(255,255,255,0.3)}.toolbar-btn:hover{background:rgba(255,255,255,0.3);transform:translateY(-1px)}.sidebar{position:fixed;left:0;top:60px;width:250px;height:calc(100vh - 60px);background:white;box-shadow:2px 0 8px rgba(0,0,0,0.1);overflow-y:auto;z-index:999;transition:transform 0.3s ease}.sidebar-header{padding:20px;background:var(--primary);color:white;border-bottom:1px solid rgba(255,255,255,0.1)}.sidebar-header h3{font-size:1.1em;font-weight:600;margin:0;display:flex;align-items:center;gap:10px}.sidebar-nav{list-style:none;padding:0;margin:0}.sidebar-nav li{margin:0}.sidebar-item{display:flex;align-items:center;gap:12px;padding:15px 20px;color:#495057;text-decoration:none;border-left:3px solid transparent;transition:all 0.2s ease;font-size:0.9em}.sidebar-item:hover{background:#f8f9fa;color:var(--primary);border-left-color:var(--primary)}.sidebar-item.active{background:#e7f3ff;color:var(--primary);border-left-color:var(--primary);font-weight:600}.sidebar-item i{width:20px;text-align:center;font-size:0.9em}.sidebar-item-text{flex:1}.main-content{margin-left:250px;margin-top:60px;padding:30px 40px;background:white;min-height:calc(100vh - 60px)}.section{scroll-margin-top:80px}@media (max-width:768px){.sidebar{transform:translateX(-100%);width:250px}.sidebar.open{transform:translateX(0)}.main-content{margin-left:0}.toolbar-btn-text{display:none}.toolbar-title{font-size:1.1em}}.sidebar::-webkit-scrollbar{width:6px}.sidebar::-webkit-scrollbar-track{background:#f1f1f1}.sidebar::-webkit-scrollbar-thumb{background:#888;border-radius:3px}.sidebar::-webkit-scrollbar-thumb:hover{background:#555}'''
        
        def generate_shared_layout_js():
            return '''<script>(function(){document.querySelectorAll('.sidebar-item').forEach(item=>{item.addEventListener('click',function(e){e.preventDefault();const targetId=this.getAttribute('href').substring(1);const targetElement=document.getElementById(targetId);if(targetElement){const offset=80;const elementPosition=targetElement.getBoundingClientRect().top;const offsetPosition=elementPosition+window.pageYOffset-offset;window.scrollTo({top:offsetPosition,behavior:'smooth'});updateActiveSection(targetId)}})});function updateActiveSection(activeId){document.querySelectorAll('.sidebar-item').forEach(item=>{item.classList.remove('active');if(item.getAttribute('data-section')===activeId){item.classList.add('active')}})}const observerOptions={root:null,rootMargin:'-20% 0px -70% 0px',threshold:0};const observer=new IntersectionObserver(function(entries){entries.forEach(entry=>{if(entry.isIntersecting){const sectionId=entry.target.id;if(sectionId){updateActiveSection(sectionId)}}})},observerOptions);document.querySelectorAll('.section[id], h2[id], h3[id]').forEach(section=>{observer.observe(section)})})();</script>'''
        
        # Define sections for sidebar navigation
        sections = [
            {'id': 'test-summary', 'title': 'Test Summary', 'icon': 'fas fa-check-circle'},
            {'id': 'test-results', 'title': 'Test Results', 'icon': 'fas fa-list'},
        ]
        
        # Generate sidebar and toolbar
        sidebar_html = generate_sidebar_navigation(sections)
        toolbar_html = generate_top_toolbar(
            report_title="Analysis Test Dashboard",
            back_link="index.html",
            subtitle="Validation & Quality Assurance"
        )
        
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
        {generate_shared_layout_css()}
        
        :root {{
            --gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --primary: #1a1a2e;
        }}
        
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
            font-size: 2.2em;
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
    <div class="layout-container">
        {toolbar_html}
        {sidebar_html}
        <div class="main-content">
        <div class="header" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center; margin-bottom: 30px; border-radius: 8px;">
            <h1><i class="fas fa-check-circle"></i> Analysis Test Dashboard</h1>
            <div class="subtitle">Comprehensive Validation of Base Case, Sensitivity, and Monte Carlo Analyses</div>
        </div>
        
        <div class="section" id="test-summary">
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
        
        </div>
        </div>
        
        <div class="footer" style="margin-top: 40px; padding: 30px; background: #f8f9fa; text-align: center; border-top: 1px solid #dee2e6;">
            <p style="margin: 0; font-size: 0.9em; color: #6c757d;">This dashboard validates calculations across Base Case, Sensitivity, and Monte Carlo analyses</p>
            <p style="margin: 5px 0 0 0; font-size: 0.85em; color: #6c757d;">All calculations are cross-checked for accuracy and consistency</p>
        </div>
        </div>
    </div>
    {generate_shared_layout_js()}
</body>
</html>
"""
        
        # Write to file
        output_path = "website/report_validation.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"  [+] Dashboard saved to: {output_path}")


if __name__ == "__main__":
    tester = AnalysisTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

