"""
Unit tests for core calculation functions: compute_annual_cash_flows, expense calculations, tax calculations
"""

import pytest
from engelberg.core import (
    compute_annual_cash_flows,
    BaseCaseConfig,
    FinancingParams,
    RentalParams,
    ExpenseParams,
    SeasonalParams
)
from tests.fixtures.test_configs import create_test_base_config
from tests.conftest import assert_approximately_equal


class TestComputeAnnualCashFlows:
    """Tests for compute_annual_cash_flows() function."""
    
    def test_revenue_calculation(self, minimal_config):
        """Test that revenue (gross_rental_income) is calculated correctly."""
        results = compute_annual_cash_flows(minimal_config)
        
        # Revenue should match rental.gross_rental_income
        expected_revenue = minimal_config.rental.gross_rental_income
        assert results['gross_rental_income'] == pytest.approx(expected_revenue, rel=1e-6)
        assert results['gross_rental_income'] > 0
    
    def test_property_management_cost_calculation(self, minimal_config):
        """Test property management cost calculation."""
        results = compute_annual_cash_flows(minimal_config)
        
        # Property management should be percentage of revenue AFTER platform fees AND cleaning fees
        # revenue_after_platform_and_cleaning = net_rental_income - cleaning_cost
        revenue_after_platform_and_cleaning = results['net_rental_income'] - results.get('cleaning_cost', 0.0)
        expected = revenue_after_platform_and_cleaning * minimal_config.expenses.property_management_fee_rate
        assert results['property_management_cost'] == pytest.approx(expected, rel=1e-6)
    
    def test_cleaning_cost_when_separate(self):
        """Test cleaning cost when separate from management fee."""
        config = create_test_base_config()
        # Ensure cleaning is separate (cleaning_cost_per_stay > 0)
        config.expenses.cleaning_cost_per_stay = 100.0
        
        results = compute_annual_cash_flows(config)
        
        # Cleaning cost should be calculated
        rented_nights = config.rental.rented_nights
        num_stays = rented_nights / config.expenses.average_length_of_stay
        expected_cleaning = num_stays * 100.0
        
        assert results['cleaning_cost'] == pytest.approx(expected_cleaning, rel=1e-6)
        assert results['cleaning_cost'] > 0
    
    def test_cleaning_cost_when_included_in_management(self):
        """Test that cleaning cost is 0 when included in management fee."""
        config = create_test_base_config()
        # Set cleaning_cost_per_stay to 0 (included in management)
        config.expenses.cleaning_cost_per_stay = 0.0
        
        results = compute_annual_cash_flows(config)
        
        # Cleaning cost should be 0
        assert results['cleaning_cost'] == 0.0
    
    def test_tourist_tax_calculation(self, minimal_config):
        """Test tourist tax calculation."""
        results = compute_annual_cash_flows(minimal_config)
        
        # Tourist tax = rented_nights * avg_guests_per_night * tax_per_person_per_night
        rented_nights = minimal_config.rental.rented_nights
        expected = rented_nights * minimal_config.expenses.avg_guests_per_night * minimal_config.expenses.tourist_tax_per_person_per_night
        
        assert results['tourist_tax'] == pytest.approx(expected, rel=1e-6)
    
    def test_insurance_expense(self, minimal_config):
        """Test insurance expense."""
        results = compute_annual_cash_flows(minimal_config)
        
        # Insurance should match expense parameter
        assert results['insurance'] == minimal_config.expenses.insurance_annual
    
    def test_maintenance_reserve_calculation(self, minimal_config):
        """Test maintenance reserve calculation."""
        results = compute_annual_cash_flows(minimal_config)
        
        # Maintenance reserve = property_value * maintenance_rate
        expected = minimal_config.expenses.property_value * minimal_config.expenses.maintenance_rate
        assert results['maintenance_reserve'] == pytest.approx(expected, rel=1e-6)
    
    def test_total_operating_expenses(self, minimal_config):
        """Test total operating expenses calculation."""
        results = compute_annual_cash_flows(minimal_config)
        
        # Sum of all operating expenses
        expected = (
            results['property_management_cost'] +
            results['cleaning_cost'] +
            results['tourist_tax'] +
            results['insurance'] +
            results['nubbing_costs'] +
            results['electricity_internet'] +
            results['maintenance_reserve']
        )
        
        assert results['total_operating_expenses'] == pytest.approx(expected, rel=1e-6)
    
    def test_noi_calculation(self, minimal_config):
        """Test Net Operating Income (NOI) calculation."""
        results = compute_annual_cash_flows(minimal_config)
        
        # NOI = Net Rental Income (after OTA fees) - Operating Expenses
        expected = results['net_rental_income'] - results['total_operating_expenses']
        assert results['net_operating_income'] == pytest.approx(expected, rel=1e-6)
    
    def test_debt_service_calculation(self, minimal_config):
        """Test debt service calculation."""
        results = compute_annual_cash_flows(minimal_config)
        
        # Debt service should match financing.annual_debt_service
        expected = minimal_config.financing.annual_debt_service
        assert results['debt_service'] == pytest.approx(expected, rel=1e-6)
    
    def test_net_cash_flow_calculation(self, minimal_config):
        """Test net cash flow calculation."""
        results = compute_annual_cash_flows(minimal_config)
        
        # Net cash flow = NOI - Debt Service
        expected = results['net_operating_income'] - results['debt_service']
        assert results['cash_flow_after_debt_service'] == pytest.approx(expected, rel=1e-6)
    
    def test_cash_flow_per_owner(self, minimal_config):
        """Test cash flow per owner calculation."""
        results = compute_annual_cash_flows(minimal_config)
        
        # Cash flow per owner = cash_flow_after_debt_service / num_owners
        expected = results['cash_flow_after_debt_service'] / minimal_config.financing.num_owners
        assert results['cash_flow_per_owner'] == pytest.approx(expected, rel=1e-6)
    
    def test_edge_case_zero_occupancy(self):
        """Test edge case: zero occupancy (no revenue)."""
        config = create_test_base_config()
        # Set all seasons to zero occupancy
        for season in config.rental.seasons:
            season.occupancy_rate = 0.0
        
        results = compute_annual_cash_flows(config)
        
        # Revenue should be 0
        assert results['gross_rental_income'] == 0.0
        # But expenses still exist
        assert results['total_operating_expenses'] > 0
        # Cash flow should be negative
        assert results['cash_flow_after_debt_service'] < 0
    
    def test_edge_case_zero_ltv(self):
        """Test edge case: zero LTV (no debt)."""
        config = create_test_base_config()
        config.financing.ltv = 0.0
        
        results = compute_annual_cash_flows(config)
        
        # Debt service should be 0
        assert results['debt_service'] == 0.0
        # Cash flow should equal NOI
        assert results['cash_flow_after_debt_service'] == pytest.approx(results['net_operating_income'], rel=1e-6)
    
    def test_all_expense_components_present(self, minimal_config):
        """Test that all expense components are present in results."""
        results = compute_annual_cash_flows(minimal_config)
        
        required_keys = [
            'property_management_cost',
            'cleaning_cost',
            'tourist_tax',
            'insurance',
            'nubbing_costs',
            'electricity_internet',
            'maintenance_reserve',
            'total_operating_expenses'
        ]
        
        for key in required_keys:
            assert key in results, f"Missing key: {key}"
            assert isinstance(results[key], (int, float)), f"Key {key} is not numeric"
    
    def test_all_revenue_components_present(self, minimal_config):
        """Test that all revenue components are present in results."""
        results = compute_annual_cash_flows(minimal_config)
        
        assert 'gross_rental_income' in results
        assert isinstance(results['gross_rental_income'], (int, float))
        assert results['gross_rental_income'] >= 0
    
    def test_all_cash_flow_components_present(self, minimal_config):
        """Test that all cash flow components are present in results."""
        results = compute_annual_cash_flows(minimal_config)
        
        required_keys = [
            'net_operating_income',
            'debt_service',
            'cash_flow_after_debt_service',
            'cash_flow_per_owner'
        ]
        
        for key in required_keys:
            assert key in results, f"Missing key: {key}"
            assert isinstance(results[key], (int, float)), f"Key {key} is not numeric"


class TestExpenseCalculations:
    """Tests for individual expense calculation methods."""
    
    def test_property_management_fee_calculation(self):
        """Test property management fee calculation."""
        expenses = ExpenseParams(
            property_management_fee_rate=0.25,
            cleaning_cost_per_stay=100.0,
            average_length_of_stay=1.7,
            tourist_tax_per_person_per_night=3.0,
            avg_guests_per_night=2.0,
            insurance_annual=4000.0,
            nubbing_costs_annual=2000.0,
            electricity_internet_annual=1000.0,
            maintenance_rate=0.005,
            property_value=1000000.0
        )
        
        gross_rental_income = 50000.0
        expected = 50000.0 * 0.25  # 12500.0
        assert expenses.property_management_cost(gross_rental_income) == expected
    
    def test_cleaning_cost_method(self):
        """Test cleaning_cost() method."""
        expenses = ExpenseParams(
            property_management_fee_rate=0.20,
            cleaning_cost_per_stay=80.0,
            average_length_of_stay=2.0,
            tourist_tax_per_person_per_night=3.0,
            avg_guests_per_night=2.0,
            insurance_annual=4000.0,
            nubbing_costs_annual=2000.0,
            electricity_internet_annual=1000.0,
            maintenance_rate=0.005,
            property_value=1000000.0
        )
        
        rented_nights = 200.0
        num_stays = 200.0 / 2.0  # 100 stays
        expected = 100.0 * 80.0  # 8000.0
        
        assert expenses.cleaning_cost(rented_nights) == pytest.approx(expected, rel=1e-6)
    
    def test_tourist_tax_method(self):
        """Test tourist_tax() method."""
        expenses = ExpenseParams(
            property_management_fee_rate=0.20,
            cleaning_cost_per_stay=100.0,
            average_length_of_stay=1.7,
            tourist_tax_per_person_per_night=3.5,
            avg_guests_per_night=2.5,
            insurance_annual=4000.0,
            nubbing_costs_annual=2000.0,
            electricity_internet_annual=1000.0,
            maintenance_rate=0.005,
            property_value=1000000.0
        )
        
        rented_nights = 150.0
        expected = 150.0 * 2.5 * 3.5  # 1312.5
        assert expenses.tourist_tax(rented_nights) == pytest.approx(expected, rel=1e-6)
    
    def test_maintenance_reserve_property(self):
        """Test maintenance_reserve property."""
        expenses = ExpenseParams(
            property_management_fee_rate=0.20,
            cleaning_cost_per_stay=100.0,
            average_length_of_stay=1.7,
            tourist_tax_per_person_per_night=3.0,
            avg_guests_per_night=2.0,
            insurance_annual=4000.0,
            nubbing_costs_annual=2000.0,
            electricity_internet_annual=1000.0,
            maintenance_rate=0.01,  # 1%
            property_value=1200000.0
        )
        
        expected = 1200000.0 * 0.01  # 12000.0
        assert expenses.maintenance_reserve == expected


class TestTaxCalculations:
    """Tests for tax calculations in compute_annual_cash_flows()."""
    
    def test_tax_savings_calculation(self, minimal_config):
        """Test that tax savings are calculated correctly as interest × 30%."""
        results = compute_annual_cash_flows(minimal_config)
        
        # Tax savings should be interest payment × 30%
        expected_tax_savings_total = results['interest_payment'] * 0.30
        assert results['tax_savings_total'] == pytest.approx(expected_tax_savings_total, rel=1e-6)
        assert results['tax_savings_total'] > 0
    
    def test_tax_savings_per_owner(self, minimal_config):
        """Test that tax savings per owner is calculated correctly."""
        results = compute_annual_cash_flows(minimal_config)
        
        # Tax savings per owner should be total savings / num_owners
        expected_per_owner = results['tax_savings_total'] / minimal_config.financing.num_owners
        assert results['tax_savings_per_owner'] == pytest.approx(expected_per_owner, rel=1e-6)
    
    def test_taxable_income_calculation(self, minimal_config):
        """Test that taxable income = NOI - interest (only interest deductible)."""
        results = compute_annual_cash_flows(minimal_config)
        
        # Taxable income should be NOI minus interest (principal not deductible)
        expected_taxable = results['net_operating_income'] - results['interest_payment']
        assert results['taxable_income'] == pytest.approx(expected_taxable, rel=1e-6)
    
    def test_tax_liability_calculation(self, minimal_config):
        """Test that tax liability = max(0, taxable_income) × 30%."""
        results = compute_annual_cash_flows(minimal_config)
        
        # Tax liability should be taxable income × 30% (if positive)
        expected_liability = max(0.0, results['taxable_income']) * 0.30
        assert results['tax_liability'] == pytest.approx(expected_liability, rel=1e-6)
        assert results['tax_liability'] >= 0
    
    def test_after_tax_cash_flow_calculation(self, minimal_config):
        """Test that after-tax cash flow = pre-tax + tax savings."""
        results = compute_annual_cash_flows(minimal_config)
        
        # After-tax cash flow should be pre-tax + tax savings
        expected_after_tax_total = results['cash_flow_after_debt_service'] + results['tax_savings_total']
        expected_after_tax_per_owner = results['cash_flow_per_owner'] + results['tax_savings_per_owner']
        
        assert results['after_tax_cash_flow_total'] == pytest.approx(expected_after_tax_total, rel=1e-6)
        assert results['after_tax_cash_flow_per_owner'] == pytest.approx(expected_after_tax_per_owner, rel=1e-6)
    
    def test_tax_liability_zero_when_negative_taxable_income(self):
        """Test that tax liability is 0 when taxable income is negative."""
        config = create_test_base_config()
        # Create scenario with negative taxable income (high expenses, low revenue)
        # Set very high interest rate to make interest payment large
        config.financing.interest_rate = 0.10  # 10% interest
        # Set low occupancy to reduce revenue
        for season in config.rental.seasons:
            season.occupancy_rate = 0.1  # 10% occupancy
        
        results = compute_annual_cash_flows(config)
        
        # If taxable income is negative, tax liability should be 0
        if results['taxable_income'] < 0:
            assert results['tax_liability'] == 0.0
        # Tax savings should still be calculated (interest × 30%)
        assert results['tax_savings_total'] == pytest.approx(results['interest_payment'] * 0.30, rel=1e-6)
    
    def test_principal_not_tax_deductible(self, minimal_config):
        """Test that principal repayment is NOT included in tax calculations."""
        results = compute_annual_cash_flows(minimal_config)
        
        # Taxable income should only subtract interest, not principal
        # If principal were deductible, taxable income would be NOI - interest - principal
        # But it should be NOI - interest only
        expected_taxable = results['net_operating_income'] - results['interest_payment']
        assert results['taxable_income'] == pytest.approx(expected_taxable, rel=1e-6)
        
        # Verify principal is NOT in the calculation
        # If principal were deductible, taxable would be lower
        taxable_with_principal = results['net_operating_income'] - results['interest_payment'] - results['amortization_payment']
        assert results['taxable_income'] > taxable_with_principal  # Should be higher (principal not deducted)
