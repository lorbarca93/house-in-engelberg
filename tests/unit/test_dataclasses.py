"""
Unit tests for data classes: FinancingParams, RentalParams, ExpenseParams, SeasonalParams
"""

import pytest
from engelberg.core import (
    FinancingParams,
    RentalParams,
    ExpenseParams,
    SeasonalParams
)
from tests.fixtures.test_configs import (
    create_test_financing_params,
    create_test_rental_params,
    create_test_expense_params
)


class TestFinancingParams:
    """Tests for FinancingParams dataclass."""
    
    def test_loan_amount_calculation(self):
        """Test loan_amount property calculation."""
        financing = FinancingParams(
            purchase_price=1000000.0,
            ltv=0.75,
            interest_rate=0.01,
            amortization_rate=0.01,
            num_owners=2
        )
        assert financing.loan_amount == 750000.0
    
    def test_equity_total_calculation(self):
        """Test equity_total property calculation."""
        financing = FinancingParams(
            purchase_price=1000000.0,
            ltv=0.75,
            interest_rate=0.01,
            amortization_rate=0.01,
            num_owners=2
        )
        assert financing.equity_total == 250000.0
    
    def test_equity_per_owner_calculation(self):
        """Test equity_per_owner property calculation."""
        financing = FinancingParams(
            purchase_price=1000000.0,
            ltv=0.75,
            interest_rate=0.01,
            amortization_rate=0.01,
            num_owners=4
        )
        assert financing.equity_per_owner == 62500.0  # 250000 / 4
    
    def test_annual_interest_calculation(self):
        """Test annual_interest property calculation."""
        financing = FinancingParams(
            purchase_price=1000000.0,
            ltv=0.75,
            interest_rate=0.02,  # 2%
            amortization_rate=0.01,
            num_owners=2
        )
        assert financing.annual_interest == 15000.0  # 750000 * 0.02
    
    def test_annual_amortization_calculation(self):
        """Test annual_amortization property calculation."""
        financing = FinancingParams(
            purchase_price=1000000.0,
            ltv=0.75,
            interest_rate=0.01,
            amortization_rate=0.01,  # 1%
            num_owners=2
        )
        assert financing.annual_amortization == 7500.0  # 750000 * 0.01
    
    def test_annual_debt_service_calculation(self):
        """Test annual_debt_service property calculation."""
        financing = FinancingParams(
            purchase_price=1000000.0,
            ltv=0.75,
            interest_rate=0.02,
            amortization_rate=0.01,
            num_owners=2
        )
        expected = 15000.0 + 7500.0  # interest + amortization
        assert financing.annual_debt_service == expected
    
    def test_edge_case_ltv_zero(self):
        """Test edge case: LTV = 0 (100% equity)."""
        financing = FinancingParams(
            purchase_price=1000000.0,
            ltv=0.0,
            interest_rate=0.01,
            amortization_rate=0.01,
            num_owners=2
        )
        assert financing.loan_amount == 0.0
        assert financing.equity_total == 1000000.0
        assert financing.annual_interest == 0.0
        assert financing.annual_amortization == 0.0
    
    def test_edge_case_ltv_one(self):
        """Test edge case: LTV = 1.0 (100% loan)."""
        financing = FinancingParams(
            purchase_price=1000000.0,
            ltv=1.0,
            interest_rate=0.01,
            amortization_rate=0.01,
            num_owners=2
        )
        assert financing.loan_amount == 1000000.0
        assert financing.equity_total == 0.0
        assert financing.equity_per_owner == 0.0
    
    def test_edge_case_one_owner(self):
        """Test edge case: num_owners = 1."""
        financing = FinancingParams(
            purchase_price=1000000.0,
            ltv=0.75,
            interest_rate=0.01,
            amortization_rate=0.01,
            num_owners=1
        )
        assert financing.equity_per_owner == 250000.0


class TestRentalParams:
    """Tests for RentalParams dataclass."""
    
    def test_total_owner_nights_calculation(self):
        """Test total_owner_nights property."""
        rental = RentalParams(
            owner_nights_per_person=5,
            num_owners=4,
            occupancy_rate=0.65,
            average_daily_rate=200.0
        )
        assert rental.total_owner_nights == 20  # 5 * 4
    
    def test_rentable_nights_calculation(self):
        """Test rentable_nights property."""
        rental = RentalParams(
            owner_nights_per_person=5,
            num_owners=4,
            occupancy_rate=0.65,
            average_daily_rate=200.0,
            days_per_year=365
        )
        assert rental.rentable_nights == 345  # 365 - 20
    
    def test_rented_nights_legacy_mode(self):
        """Test rented_nights with legacy mode (no seasons)."""
        rental = RentalParams(
            owner_nights_per_person=5,
            num_owners=4,
            occupancy_rate=0.65,
            average_daily_rate=200.0,
            days_per_year=365,
            seasons=None
        )
        expected = 345 * 0.65  # rentable_nights * occupancy_rate
        assert rental.rented_nights == pytest.approx(expected, rel=1e-6)
    
    def test_rented_nights_seasonal_mode(self):
        """Test rented_nights with seasonal mode."""
        winter = SeasonalParams(
            name="Winter",
            months=[12, 1, 2, 3],
            occupancy_rate=0.75,
            average_daily_rate=250.0,
            nights_in_season=120
        )
        summer = SeasonalParams(
            name="Summer",
            months=[6, 7, 8, 9],
            occupancy_rate=0.70,
            average_daily_rate=200.0,
            nights_in_season=120
        )
        
        rental = RentalParams(
            owner_nights_per_person=5,
            num_owners=2,
            occupancy_rate=0.65,
            average_daily_rate=200.0,
            seasons=[winter, summer]
        )
        
        expected = (120 * 0.75) + (120 * 0.70)  # sum of season.rented_nights
        assert rental.rented_nights == pytest.approx(expected, rel=1e-6)
    
    def test_gross_rental_income_legacy_mode(self):
        """Test gross_rental_income with legacy mode."""
        rental = RentalParams(
            owner_nights_per_person=5,
            num_owners=4,
            occupancy_rate=0.65,
            average_daily_rate=200.0,
            days_per_year=365,
            seasons=None
        )
        expected = 345 * 0.65 * 200.0  # rented_nights * average_daily_rate
        assert rental.gross_rental_income == pytest.approx(expected, rel=1e-6)
    
    def test_gross_rental_income_seasonal_mode(self):
        """Test gross_rental_income with seasonal mode."""
        winter = SeasonalParams(
            name="Winter",
            months=[12, 1, 2, 3],
            occupancy_rate=0.75,
            average_daily_rate=250.0,
            nights_in_season=120
        )
        summer = SeasonalParams(
            name="Summer",
            months=[6, 7, 8, 9],
            occupancy_rate=0.70,
            average_daily_rate=200.0,
            nights_in_season=120
        )
        
        rental = RentalParams(
            owner_nights_per_person=5,
            num_owners=2,
            occupancy_rate=0.65,
            average_daily_rate=200.0,
            seasons=[winter, summer]
        )
        
        expected = (120 * 0.75 * 250.0) + (120 * 0.70 * 200.0)
        assert rental.gross_rental_income == pytest.approx(expected, rel=1e-6)
    
    def test_get_seasonal_breakdown_with_seasons(self):
        """Test get_seasonal_breakdown() with seasons."""
        winter = SeasonalParams(
            name="Winter",
            months=[12, 1, 2, 3],
            occupancy_rate=0.75,
            average_daily_rate=250.0,
            nights_in_season=120
        )
        
        rental = RentalParams(
            owner_nights_per_person=5,
            num_owners=2,
            occupancy_rate=0.65,
            average_daily_rate=200.0,
            seasons=[winter]
        )
        
        breakdown = rental.get_seasonal_breakdown()
        assert 'Winter' in breakdown
        assert breakdown['Winter']['nights'] == pytest.approx(90.0, rel=1e-6)  # 120 * 0.75
        assert breakdown['Winter']['income'] == pytest.approx(22500.0, rel=1e-6)  # 90 * 250
    
    def test_get_seasonal_breakdown_without_seasons(self):
        """Test get_seasonal_breakdown() without seasons (legacy mode)."""
        rental = RentalParams(
            owner_nights_per_person=5,
            num_owners=4,
            occupancy_rate=0.65,
            average_daily_rate=200.0,
            days_per_year=365,
            seasons=None
        )
        
        breakdown = rental.get_seasonal_breakdown()
        assert 'Annual' in breakdown
        assert breakdown['Annual']['occupancy'] == 0.65


class TestExpenseParams:
    """Tests for ExpenseParams dataclass."""
    
    def test_property_management_cost(self):
        """Test property_management_cost() method."""
        expenses = ExpenseParams(
            property_management_fee_rate=0.20,
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
        expected = 50000.0 * 0.20  # 20% of revenue
        assert expenses.property_management_cost(gross_rental_income) == expected
    
    def test_cleaning_cost_calculation(self):
        """Test cleaning_cost() calculation."""
        expenses = ExpenseParams(
            property_management_fee_rate=0.20,
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
        
        rented_nights = 170.0
        num_stays = 170.0 / 1.7  # 100 stays
        expected = num_stays * 100.0  # 100 stays * 100 CHF
        
        assert expenses.cleaning_cost(rented_nights) == pytest.approx(expected, rel=1e-6)
    
    def test_tourist_tax_calculation(self):
        """Test tourist_tax() calculation."""
        expenses = ExpenseParams(
            property_management_fee_rate=0.20,
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
        
        rented_nights = 200.0
        expected = 200.0 * 2.0 * 3.0  # nights * guests * tax_per_person_per_night
        assert expenses.tourist_tax(rented_nights) == expected
    
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
            maintenance_rate=0.005,  # 0.5%
            property_value=1000000.0
        )
        
        expected = 1000000.0 * 0.005  # 5000.0
        assert expenses.maintenance_reserve == expected


class TestSeasonalParams:
    """Tests for SeasonalParams dataclass."""
    
    def test_rented_nights_property(self):
        """Test rented_nights property."""
        season = SeasonalParams(
            name="Winter",
            months=[12, 1, 2, 3],
            occupancy_rate=0.75,
            average_daily_rate=250.0,
            nights_in_season=120
        )
        
        expected = 120 * 0.75  # 90.0
        assert season.rented_nights == expected
    
    def test_season_income_property(self):
        """Test season_income property."""
        season = SeasonalParams(
            name="Winter",
            months=[12, 1, 2, 3],
            occupancy_rate=0.75,
            average_daily_rate=250.0,
            nights_in_season=120
        )
        
        expected = 90.0 * 250.0  # rented_nights * average_daily_rate
        assert season.season_income == expected
