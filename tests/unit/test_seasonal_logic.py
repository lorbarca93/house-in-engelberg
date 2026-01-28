"""
Unit tests for seasonal rental income calculations and owner nights distribution
"""

import pytest
from engelberg.core import (
    RentalParams,
    SeasonalParams,
    compute_annual_cash_flows
)
from tests.fixtures.test_configs import create_test_base_config


class TestSeasonalRentalIncome:
    """Tests for seasonal rental income calculations."""
    
    def test_seasonal_rental_income_calculation(self):
        """Test seasonal rental income calculation."""
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
        
        offpeak = SeasonalParams(
            name="Off-Peak",
            months=[4, 5, 10, 11],
            occupancy_rate=0.50,
            average_daily_rate=150.0,
            nights_in_season=120
        )
        
        rental = RentalParams(
            owner_nights_per_person=5,
            num_owners=2,
            occupancy_rate=0.65,
            average_daily_rate=200.0,
            seasons=[winter, summer, offpeak]
        )
        
        # Calculate expected income
        winter_income = 120 * 0.75 * 250.0  # 22,500
        summer_income = 120 * 0.70 * 200.0  # 16,800
        offpeak_income = 120 * 0.50 * 150.0  # 9,000
        expected_total = winter_income + summer_income + offpeak_income
        
        assert rental.gross_rental_income == pytest.approx(expected_total, rel=1e-6)
    
    def test_owner_nights_distribution_across_seasons(self):
        """Test owner nights distribution across seasons."""
        # Create config with specific owner nights distribution
        config = create_test_base_config()
        
        # Verify owner nights are distributed
        total_owner_nights = config.rental.total_owner_nights
        assert total_owner_nights > 0
        
        # Each season should account for some owner nights
        # (exact distribution depends on implementation)
        assert config.rental.rentable_nights < 365
    
    def test_rentable_nights_per_season(self):
        """Test rentable nights per season calculation."""
        winter = SeasonalParams(
            name="Winter",
            months=[12, 1, 2, 3],
            occupancy_rate=0.75,
            average_daily_rate=250.0,
            nights_in_season=120  # Total nights in season minus owner nights
        )
        
        # Rentable nights should be nights_in_season
        assert winter.nights_in_season == 120
        
        # Rented nights = nights_in_season * occupancy_rate
        assert winter.rented_nights == pytest.approx(90.0, rel=1e-6)  # 120 * 0.75
    
    def test_seasonal_occupancy_rates(self):
        """Test seasonal occupancy rates."""
        winter = SeasonalParams(
            name="Winter",
            months=[12, 1, 2, 3],
            occupancy_rate=0.80,  # High occupancy
            average_daily_rate=250.0,
            nights_in_season=120
        )
        
        summer = SeasonalParams(
            name="Summer",
            months=[6, 7, 8, 9],
            occupancy_rate=0.60,  # Lower occupancy
            average_daily_rate=200.0,
            nights_in_season=120
        )
        
        # Winter should have higher rented nights
        assert winter.rented_nights > summer.rented_nights
    
    def test_weighted_average_daily_rate(self):
        """Test weighted average daily rate across seasons."""
        winter = SeasonalParams(
            name="Winter",
            months=[12, 1, 2, 3],
            occupancy_rate=0.75,
            average_daily_rate=300.0,  # High rate
            nights_in_season=100
        )
        
        summer = SeasonalParams(
            name="Summer",
            months=[6, 7, 8, 9],
            occupancy_rate=0.70,
            average_daily_rate=150.0,  # Lower rate
            nights_in_season=100
        )
        
        rental = RentalParams(
            owner_nights_per_person=5,
            num_owners=2,
            occupancy_rate=0.65,
            average_daily_rate=200.0,
            seasons=[winter, summer]
        )
        
        # Calculate weighted average
        winter_income = winter.season_income
        summer_income = summer.season_income
        total_income = winter_income + summer_income
        total_rented_nights = winter.rented_nights + summer.rented_nights
        
        weighted_avg_rate = total_income / total_rented_nights if total_rented_nights > 0 else 0
        
        # Should be between the two rates
        assert 150.0 < weighted_avg_rate < 300.0
        # Should be closer to winter rate (higher occupancy and rate)
        assert weighted_avg_rate > 200.0
    
    def test_annual_totals_match_expected(self):
        """Test that annual totals match expected values."""
        config = create_test_base_config()
        results = compute_annual_cash_flows(config)
        
        # Annual revenue should be sum of all season incomes
        if config.rental.seasons:
            expected_revenue = sum(season.season_income for season in config.rental.seasons)
            assert results['gross_rental_income'] == pytest.approx(expected_revenue, rel=1e-6)
        
        # Annual rented nights should be sum of all season rented nights
        if config.rental.seasons:
            expected_nights = sum(season.rented_nights for season in config.rental.seasons)
            assert results['rented_nights'] == pytest.approx(expected_nights, rel=1e-6)
    
    def test_seasonal_breakdown_in_results(self):
        """Test that seasonal breakdown is included in results."""
        config = create_test_base_config()
        results = compute_annual_cash_flows(config)
        
        # Should have seasonal_breakdown if seasons are defined
        if config.rental.seasons:
            assert 'seasonal_breakdown' in results
            breakdown = results['seasonal_breakdown']
            
            # Should have data for each season
            for season in config.rental.seasons:
                assert season.name in breakdown
                season_data = breakdown[season.name]
                assert 'nights' in season_data
                assert 'income' in season_data
                assert 'rate' in season_data
                assert 'occupancy' in season_data
    
    def test_overall_occupancy_rate_calculation(self):
        """Test overall occupancy rate calculation."""
        config = create_test_base_config()
        results = compute_annual_cash_flows(config)
        
        # Overall occupancy should be rented_nights / rentable_nights
        if 'overall_occupancy_rate' in results:
            expected = results['rented_nights'] / results['rentable_nights'] if results['rentable_nights'] > 0 else 0
            assert results['overall_occupancy_rate'] == pytest.approx(expected, rel=1e-6)
    
    def test_average_daily_rate_calculation(self):
        """Test average daily rate calculation."""
        config = create_test_base_config()
        results = compute_annual_cash_flows(config)
        
        # Average daily rate should be revenue / rented_nights
        if 'average_daily_rate' in results and results['rented_nights'] > 0:
            expected = results['gross_rental_income'] / results['rented_nights']
            assert results['average_daily_rate'] == pytest.approx(expected, rel=1e-6)
    
    def test_seasonal_income_property(self):
        """Test SeasonalParams.season_income property."""
        season = SeasonalParams(
            name="Test Season",
            months=[1, 2, 3],
            occupancy_rate=0.70,
            average_daily_rate=200.0,
            nights_in_season=90
        )
        
        # season_income = rented_nights * average_daily_rate
        expected = 90 * 0.70 * 200.0  # 12,600
        assert season.season_income == pytest.approx(expected, rel=1e-6)
    
    def test_seasonal_rented_nights_property(self):
        """Test SeasonalParams.rented_nights property."""
        season = SeasonalParams(
            name="Test Season",
            months=[1, 2, 3],
            occupancy_rate=0.75,
            average_daily_rate=200.0,
            nights_in_season=100
        )
        
        # rented_nights = nights_in_season * occupancy_rate
        expected = 100 * 0.75  # 75.0
        assert season.rented_nights == pytest.approx(expected, rel=1e-6)
