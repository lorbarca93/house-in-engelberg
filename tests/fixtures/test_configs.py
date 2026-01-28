"""
Factory functions for creating test configurations
"""

from engelberg.core import (
    BaseCaseConfig,
    FinancingParams,
    RentalParams,
    ExpenseParams,
    SeasonalParams
)


def create_test_financing_params(
    purchase_price=1000000.0,
    ltv=0.75,
    interest_rate=0.01,
    amortization_rate=0.01,
    num_owners=2
):
    """Create FinancingParams with test defaults."""
    return FinancingParams(
        purchase_price=purchase_price,
        ltv=ltv,
        interest_rate=interest_rate,
        amortization_rate=amortization_rate,
        num_owners=num_owners
    )


def create_test_rental_params(
    owner_nights_per_person=5,
    num_owners=2,
    occupancy_rate=0.65,
    average_daily_rate=200.0,
    days_per_year=365,
    with_seasons=True
):
    """Create RentalParams with test defaults."""
    if with_seasons:
        winter_season = SeasonalParams(
            name="Winter",
            months=[12, 1, 2, 3],
            occupancy_rate=0.75,
            average_daily_rate=250.0,
            nights_in_season=120 - 4
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
        
        return RentalParams(
            owner_nights_per_person=owner_nights_per_person,
            num_owners=num_owners,
            occupancy_rate=occupancy_rate,
            average_daily_rate=average_daily_rate,
            days_per_year=days_per_year,
            seasons=[winter_season, summer_season, offpeak_season]
        )
    else:
        return RentalParams(
            owner_nights_per_person=owner_nights_per_person,
            num_owners=num_owners,
            occupancy_rate=occupancy_rate,
            average_daily_rate=average_daily_rate,
            days_per_year=days_per_year,
            seasons=None
        )


def create_test_expense_params(
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
):
    """Create ExpenseParams with test defaults."""
    return ExpenseParams(
        property_management_fee_rate=property_management_fee_rate,
        cleaning_cost_per_stay=cleaning_cost_per_stay,
        average_length_of_stay=average_length_of_stay,
        tourist_tax_per_person_per_night=tourist_tax_per_person_per_night,
        avg_guests_per_night=avg_guests_per_night,
        insurance_annual=insurance_annual,
        nubbing_costs_annual=nubbing_costs_annual,
        electricity_internet_annual=electricity_internet_annual,
        maintenance_rate=maintenance_rate,
        property_value=property_value
    )


def create_test_base_config(
    purchase_price=1000000.0,
    ltv=0.75,
    interest_rate=0.01,
    amortization_rate=0.01,
    num_owners=2,
    with_seasons=True
):
    """Create complete BaseCaseConfig with test defaults."""
    financing = create_test_financing_params(
        purchase_price=purchase_price,
        ltv=ltv,
        interest_rate=interest_rate,
        amortization_rate=amortization_rate,
        num_owners=num_owners
    )
    
    rental = create_test_rental_params(
        num_owners=num_owners,
        with_seasons=with_seasons
    )
    
    expenses = create_test_expense_params(
        property_value=purchase_price
    )
    
    return BaseCaseConfig(
        financing=financing,
        rental=rental,
        expenses=expenses
    )
