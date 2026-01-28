"""
Unit tests for 15-year projection calculations: inflation, appreciation, loan balance reduction
"""

import pytest
from engelberg.core import (
    compute_15_year_projection,
    compute_annual_cash_flows
)
from tests.fixtures.test_configs import create_test_base_config
from tests.conftest import assert_approximately_equal


class TestCompute15YearProjection:
    """Tests for compute_15_year_projection() function."""
    
    def test_year_1_matches_annual_cash_flows(self, minimal_config):
        """Test that Year 1 matches compute_annual_cash_flows() result."""
        annual_results = compute_annual_cash_flows(minimal_config)
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        # Year 1 should match annual cash flows
        year_1 = projection[0]
        assert year_1['year'] == 2026
        assert year_1['gross_rental_income'] == pytest.approx(annual_results['gross_rental_income'], rel=1e-6)
        assert year_1['net_operating_income'] == pytest.approx(annual_results['net_operating_income'], rel=1e-6)
        assert year_1['cash_flow_per_owner'] == pytest.approx(annual_results['cash_flow_per_owner'], rel=1e-6)
    
    def test_inflation_application_to_revenue(self, minimal_config):
        """Test that inflation is applied to revenue over time."""
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.02,  # 2% inflation
            property_appreciation_rate=0.025
        )
        
        year_1_revenue = projection[0]['gross_rental_income']
        year_5_revenue = projection[4]['gross_rental_income']
        year_10_revenue = projection[9]['gross_rental_income']
        
        # Revenue should increase with inflation
        # Year 5: (1.02)^4 ≈ 1.0824
        expected_year_5 = year_1_revenue * (1.02 ** 4)
        assert year_5_revenue == pytest.approx(expected_year_5, rel=0.01)
        
        # Year 10: (1.02)^9 ≈ 1.195
        expected_year_10 = year_1_revenue * (1.02 ** 9)
        assert year_10_revenue == pytest.approx(expected_year_10, rel=0.01)
    
    def test_inflation_application_to_expenses(self, minimal_config):
        """Test that inflation is applied to operating expenses."""
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.02,
            property_appreciation_rate=0.025
        )
        
        year_1_expenses = projection[0]['total_operating_expenses']
        year_5_expenses = projection[4]['total_operating_expenses']
        
        # Expenses should increase with inflation
        expected_year_5 = year_1_expenses * (1.02 ** 4)
        assert year_5_expenses == pytest.approx(expected_year_5, rel=0.01)
    
    def test_property_appreciation_calculation(self, minimal_config):
        """Test property appreciation calculation."""
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025  # 2.5% appreciation
        )
        
        initial_value = minimal_config.financing.purchase_price
        year_1_value = projection[0]['property_value']
        year_5_value = projection[4]['property_value']
        year_15_value = projection[14]['property_value']
        
        # Year 1: no appreciation yet (or first year appreciation)
        # Year 5: (1.025)^4 ≈ 1.1038
        expected_year_5 = initial_value * (1.025 ** 4)
        assert year_5_value == pytest.approx(expected_year_5, rel=0.01)
        
        # Year 15: (1.025)^14 ≈ 1.416
        expected_year_15 = initial_value * (1.025 ** 14)
        assert year_15_value == pytest.approx(expected_year_15, rel=0.01)
    
    def test_loan_balance_reduction(self, minimal_config):
        """Test loan balance reduction due to amortization."""
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        initial_loan = minimal_config.financing.loan_amount
        year_1_balance = projection[0]['remaining_loan_balance']
        year_5_balance = projection[4]['remaining_loan_balance']
        year_15_balance = projection[14]['remaining_loan_balance']
        
        # Year 1: loan should be initial - first year amortization
        annual_amort = minimal_config.financing.annual_amortization
        expected_year_1 = initial_loan - annual_amort
        assert year_1_balance == pytest.approx(expected_year_1, rel=1e-6)
        
        # Loan balance should decrease over time
        assert year_5_balance < year_1_balance
        assert year_15_balance < year_5_balance
        
        # Year 15: should be initial - (15 * annual_amort)
        expected_year_15 = initial_loan - (15 * annual_amort)
        assert year_15_balance == pytest.approx(expected_year_15, rel=1e-6)
    
    def test_interest_calculation_on_declining_balance(self, minimal_config):
        """Test interest calculation on declining loan balance."""
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        interest_rate = minimal_config.financing.interest_rate
        initial_loan = minimal_config.financing.loan_amount
        
        # Year 1: Interest calculated on initial loan balance (at start of year)
        year_1_interest = projection[0]['interest_payment']
        expected_year_1_interest = initial_loan * interest_rate
        assert year_1_interest == pytest.approx(expected_year_1_interest, rel=1e-6)
        
        # Year 2: Interest calculated on remaining balance from year 1 (end of year 1 = start of year 2)
        year_1_end_balance = projection[0]['remaining_loan_balance']
        year_2_interest = projection[1]['interest_payment']
        expected_year_2_interest = year_1_end_balance * interest_rate
        assert year_2_interest == pytest.approx(expected_year_2_interest, rel=1e-6)
        
        # Year 5: Interest calculated on remaining balance from year 4
        year_4_end_balance = projection[3]['remaining_loan_balance']
        year_5_interest = projection[4]['interest_payment']
        expected_year_5_interest = year_4_end_balance * interest_rate
        assert year_5_interest == pytest.approx(expected_year_5_interest, rel=1e-6)
        
        # Interest should decrease as loan balance decreases
        assert year_5_interest < year_1_interest
    
    def test_cumulative_cash_flow_tracking(self, minimal_config):
        """Test cumulative cash flow tracking."""
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        # Cumulative cash flow should accumulate over time
        year_1_cumulative = projection[0]['cumulative_cash_flow_per_owner']
        year_5_cumulative = projection[4]['cumulative_cash_flow_per_owner']
        year_10_cumulative = projection[9]['cumulative_cash_flow_per_owner']
        
        # Year 1 cumulative should equal Year 1 cash flow
        year_1_cf = projection[0]['cash_flow_per_owner']
        assert year_1_cumulative == pytest.approx(year_1_cf, rel=1e-6)
        
        # Cumulative should increase (or decrease if negative) over time
        # Calculate manually to verify
        manual_cumulative = sum(projection[i]['cash_flow_per_owner'] for i in range(5))
        assert year_5_cumulative == pytest.approx(manual_cumulative, rel=1e-6)
    
    def test_final_year_property_value(self, minimal_config):
        """Test final year property value."""
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        initial_value = minimal_config.financing.purchase_price
        final_value = projection[14]['property_value']
        
        # Should appreciate over 15 years
        expected = initial_value * (1.025 ** 14)
        assert final_value == pytest.approx(expected, rel=0.01)
    
    def test_final_year_loan_balance(self, minimal_config):
        """Test final year loan balance."""
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        initial_loan = minimal_config.financing.loan_amount
        annual_amort = minimal_config.financing.annual_amortization
        final_balance = projection[14]['remaining_loan_balance']
        
        # Should be initial - (15 * annual_amort)
        expected = initial_loan - (15 * annual_amort)
        assert final_balance == pytest.approx(expected, rel=1e-6)
    
    def test_edge_case_zero_inflation(self, minimal_config):
        """Test edge case: zero inflation."""
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.0,
            property_appreciation_rate=0.025
        )
        
        year_1_revenue = projection[0]['gross_rental_income']
        year_15_revenue = projection[14]['gross_rental_income']
        
        # Revenue should remain constant (no inflation)
        assert year_15_revenue == pytest.approx(year_1_revenue, rel=1e-6)
    
    def test_edge_case_zero_appreciation(self, minimal_config):
        """Test edge case: zero property appreciation."""
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.0
        )
        
        initial_value = minimal_config.financing.purchase_price
        final_value = projection[14]['property_value']
        
        # Property value should remain constant
        assert final_value == pytest.approx(initial_value, rel=1e-6)
    
    def test_edge_case_zero_amortization(self):
        """Test edge case: zero amortization (interest-only loan)."""
        config = create_test_base_config(amortization_rate=0.0)
        
        projection = compute_15_year_projection(
            config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        initial_loan = config.financing.loan_amount
        year_1_balance = projection[0]['remaining_loan_balance']
        year_15_balance = projection[14]['remaining_loan_balance']
        
        # Loan balance should remain constant (no amortization)
        assert year_1_balance == pytest.approx(initial_loan, rel=1e-6)
        assert year_15_balance == pytest.approx(initial_loan, rel=1e-6)
    
    def test_projection_has_15_years(self, minimal_config):
        """Test that projection has exactly 15 years."""
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        assert len(projection) == 15
        assert projection[0]['year'] == 2026
        assert projection[14]['year'] == 2040
    
    def test_all_required_fields_present(self, minimal_config):
        """Test that all required fields are present in projection."""
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        required_fields = [
            'year',
            'gross_rental_income',
            'total_operating_expenses',
            'net_operating_income',
            'interest_payment',
            'amortization_payment',
            'debt_service',
            'cash_flow_per_owner',
            'cumulative_cash_flow_per_owner',
            'remaining_loan_balance',
            'property_value'
        ]
        
        for year_data in projection:
            for field in required_fields:
                assert field in year_data, f"Missing field: {field} in year {year_data['year']}"
                assert isinstance(year_data[field], (int, float)), \
                    f"Field {field} is not numeric in year {year_data['year']}"
    
    def test_variable_length_of_stay_in_projection(self, minimal_config):
        """Test that cleaning cost correctly accounts for variable length of stay."""
        # Base case with default length of stay
        base_projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        # Projection with longer average stay (fewer stays = less cleaning)
        long_stay_projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025,
            average_length_of_stay=3.0  # Longer stays
        )
        
        # Get base rented nights and cleaning cost
        base_rented_nights = base_projection[0]['rented_nights']
        base_cleaning = base_projection[0]['total_operating_expenses'] - (
            base_projection[0].get('property_management_cost', 0) +
            base_projection[0].get('tourist_tax', 0) +
            base_projection[0].get('insurance', 0) +
            base_projection[0].get('nubbing_costs', 0) +
            base_projection[0].get('electricity_internet', 0) +
            base_projection[0].get('maintenance_reserve', 0)
        )
        
        # With longer stays, same rented_nights but fewer stays
        # Cleaning cost should be lower
        long_stay_cleaning = long_stay_projection[0]['total_operating_expenses'] - (
            long_stay_projection[0].get('property_management_cost', 0) +
            long_stay_projection[0].get('tourist_tax', 0) +
            long_stay_projection[0].get('insurance', 0) +
            long_stay_projection[0].get('nubbing_costs', 0) +
            long_stay_projection[0].get('electricity_internet', 0) +
            long_stay_projection[0].get('maintenance_reserve', 0)
        )
        
        # Longer stays = fewer stays = less cleaning cost (if cleaning_cost_per_stay > 0)
        if minimal_config.expenses.cleaning_cost_per_stay > 0:
            assert long_stay_cleaning < base_cleaning
    
    def test_variable_avg_guests_in_projection(self, minimal_config):
        """Test that tourist tax correctly accounts for variable avg_guests."""
        # Base case
        base_projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        # Projection with more guests (higher tourist tax)
        more_guests_projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025,
            avg_guests_per_night=3.0  # More guests
        )
        
        # Tourist tax should be higher with more guests
        base_tourist_tax = base_projection[0].get('tourist_tax', 0)
        more_guests_tourist_tax = more_guests_projection[0].get('tourist_tax', 0)
        
        # More guests = higher tourist tax (assuming same rented_nights)
        if base_tourist_tax > 0:
            assert more_guests_tourist_tax > base_tourist_tax
    
    def test_rented_nights_in_projection(self, minimal_config):
        """Test that rented_nights is calculated and included in projection."""
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.02,
            property_appreciation_rate=0.025
        )
        
        # Year 1 should have base rented_nights
        year_1_rented = projection[0]['rented_nights']
        assert year_1_rented > 0
        
        # Year 2 should have inflated rented_nights (if no market shock)
        year_2_rented = projection[1]['rented_nights']
        # With 2% inflation, year 2 should be approximately year 1 × 1.02
        expected_year_2 = year_1_rented * 1.02
        assert year_2_rented == pytest.approx(expected_year_2, rel=0.01)
        
        # All years should have rented_nights
        for year_data in projection:
            assert 'rented_nights' in year_data
            assert year_data['rented_nights'] >= 0
