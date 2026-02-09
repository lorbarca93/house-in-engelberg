"""
Pytest configuration and shared fixtures for Engelberg Property Investment tests
"""

import os
import pytest
import json
import tempfile
from pathlib import Path
from engelberg.core import (
    BaseCaseConfig,
    FinancingParams,
    RentalParams,
    ExpenseParams,
    SeasonalParams,
    create_base_case_config
)


@pytest.fixture
def sample_assumptions_path():
    """Path to sample assumptions file for testing."""
    return os.path.join(os.path.dirname(__file__), 'fixtures', 'sample_assumptions.json')


@pytest.fixture
def temp_output_dir():
    """Temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def minimal_config():
    """Minimal valid BaseCaseConfig for testing."""
    financing = FinancingParams(
        purchase_price=1000000.0,
        ltv=0.75,
        interest_rate=0.01,
        amortization_rate=0.01,
        num_owners=2
    )
    
    # Simple seasonal structure for testing
    winter_season = SeasonalParams(
        name="Winter",
        months=[12, 1, 2, 3],
        occupancy_rate=0.75,
        average_daily_rate=250.0,
        nights_in_season=120 - 4  # 4 months * 30 days - 4 owner nights
    )
    
    summer_season = SeasonalParams(
        name="Summer",
        months=[6, 7, 8, 9],
        occupancy_rate=0.70,
        average_daily_rate=200.0,
        nights_in_season=120 - 4
    )
    
    offpeak_season = SeasonalParams(
        name="Off-Peak",
        months=[4, 5, 10, 11],
        occupancy_rate=0.50,
        average_daily_rate=150.0,
        nights_in_season=120 - 4
    )
    
    rental = RentalParams(
        owner_nights_per_person=5,
        num_owners=2,
        occupancy_rate=0.65,  # Legacy, not used when seasons provided
        average_daily_rate=200.0,  # Legacy, not used when seasons provided
        days_per_year=365,
        seasons=[winter_season, summer_season, offpeak_season]
    )
    
    expenses = ExpenseParams(
        property_management_fee_rate=0.20,
        cleaning_cost_per_stay=100.0,
        average_length_of_stay=1.7,
        tourist_tax_per_person_per_night=3.0,
        avg_guests_per_night=2.0,
        insurance_annual=4000.0,  # 0.4% of 1M
        nubbing_costs_annual=2000.0,
        electricity_internet_annual=1000.0,
        maintenance_rate=0.005,
        property_value=1000000.0,
        vat_rate_on_gross_rental=0.0
    )
    
    return BaseCaseConfig(
        financing=financing,
        rental=rental,
        expenses=expenses
    )


@pytest.fixture
def base_config(sample_assumptions_path):
    """Base case configuration loaded from sample assumptions."""
    return create_base_case_config(sample_assumptions_path)


def assert_approximately_equal(actual, expected, tolerance_percent=0.01, tolerance_abs=None):
    """
    Assert that two financial values are approximately equal.
    
    Args:
        actual: Actual value
        expected: Expected value
        tolerance_percent: Percentage tolerance (default 0.01%)
        tolerance_abs: Absolute tolerance (overrides percentage if provided)
    """
    if tolerance_abs is None:
        tolerance_abs = abs(expected) * (tolerance_percent / 100.0)
        # Minimum absolute tolerance of 0.01 for very small values
        tolerance_abs = max(tolerance_abs, 0.01)
    
    assert abs(actual - expected) <= tolerance_abs, \
        f"Values not approximately equal: {actual} vs {expected} (tolerance: {tolerance_abs})"


def load_test_assumptions(json_path):
    """Load assumptions from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)
