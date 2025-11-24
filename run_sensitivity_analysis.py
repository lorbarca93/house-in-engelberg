"""
Sensitivity Analysis Script for Engelberg Property Investment
Analyzes various scenarios and generates comprehensive Excel and HTML reports
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from simulation import (
    create_base_case_config,
    compute_annual_cash_flows,
    compute_15_year_projection,
    calculate_irrs_from_projection,
    apply_sensitivity,
    BaseCaseConfig,
    FinancingParams,
    RentalParams,
    ExpenseParams
)
from datetime import datetime
from typing import Dict, List, Tuple


def sensitivity_occupancy_rate(base_config: BaseCaseConfig, min_rate: float = 0.30, max_rate: float = 0.70, steps: int = 9) -> pd.DataFrame:
    """Analyze sensitivity to occupancy rate (30% to 70%)."""
    results = []
    rates = np.linspace(min_rate, max_rate, steps)
    
    for rate in rates:
        config = apply_sensitivity(base_config, occupancy=rate)
        result = compute_annual_cash_flows(config)
        results.append({
            'Occupancy Rate (%)': rate * 100,
            'Gross Rental Income (CHF)': result['gross_rental_income'],
            'Net Operating Income (CHF)': result['net_operating_income'],
            'Cash Flow After Debt (CHF)': result['cash_flow_after_debt_service'],
            'Cash Flow per Owner (CHF)': result['cash_flow_per_owner'],
            'Debt Coverage Ratio': result['debt_coverage_ratio'],
            'Cap Rate (%)': result['cap_rate_pct'],
        })
    
    return pd.DataFrame(results)


def sensitivity_daily_rate(base_config: BaseCaseConfig, min_rate: float = 200, max_rate: float = 400, steps: int = 9) -> pd.DataFrame:
    """Analyze sensitivity to average daily rate (200 to 400 CHF)."""
    results = []
    rates = np.linspace(min_rate, max_rate, steps)
    
    for rate in rates:
        config = apply_sensitivity(base_config, daily_rate=rate)
        result = compute_annual_cash_flows(config)
        results.append({
            'Average Daily Rate (CHF)': rate,
            'Gross Rental Income (CHF)': result['gross_rental_income'],
            'Net Operating Income (CHF)': result['net_operating_income'],
            'Cash Flow After Debt (CHF)': result['cash_flow_after_debt_service'],
            'Cash Flow per Owner (CHF)': result['cash_flow_per_owner'],
            'Debt Coverage Ratio': result['debt_coverage_ratio'],
            'Cap Rate (%)': result['cap_rate_pct'],
        })
    
    return pd.DataFrame(results)


def sensitivity_owner_nights(base_config: BaseCaseConfig, min_nights: int = 0, max_nights: int = 150, steps: int = 16) -> pd.DataFrame:
    """Analyze sensitivity to number of owner nights (0 to 150)."""
    results = []
    nights_range = np.linspace(min_nights, max_nights, steps, dtype=int)
    
    for total_nights in nights_range:
        nights_per_person = total_nights / base_config.financing.num_owners if base_config.financing.num_owners > 0 else 0
        
        new_rental = RentalParams(
            owner_nights_per_person=int(nights_per_person),
            num_owners=base_config.rental.num_owners,
            occupancy_rate=base_config.rental.occupancy_rate,
            average_daily_rate=base_config.rental.average_daily_rate,
            days_per_year=base_config.rental.days_per_year
        )
        
        new_config = BaseCaseConfig(
            financing=base_config.financing,
            rental=new_rental,
            expenses=base_config.expenses
        )
        
        result = compute_annual_cash_flows(new_config)
        results.append({
            'Total Owner Nights': total_nights,
            'Owner Nights per Person': int(nights_per_person),
            'Rentable Nights': result['rentable_nights'],
            'Gross Rental Income (CHF)': result['gross_rental_income'],
            'Net Operating Income (CHF)': result['net_operating_income'],
            'Cash Flow After Debt (CHF)': result['cash_flow_after_debt_service'],
            'Cash Flow per Owner (CHF)': result['cash_flow_per_owner'],
        })
    
    return pd.DataFrame(results)


def sensitivity_seasonality(base_config: BaseCaseConfig) -> pd.DataFrame:
    """Analyze seasonality with winter peaks and summer lows."""
    # Define monthly multipliers (winter high, summer low)
    # Engelberg: Peak in Dec-Feb, low in May-Jun
    monthly_multipliers = {
        1: 1.4,   # January - peak
        2: 1.3,   # February - peak
        3: 1.1,   # March
        4: 0.9,   # April
        5: 0.7,   # May - low
        6: 0.7,   # June - low
        7: 0.9,   # July
        8: 1.0,   # August
        9: 1.0,   # September
        10: 1.1,  # October
        11: 1.2,  # November
        12: 1.4,  # December - peak
    }
    
    # Normalize to ensure annual average is 1.0
    total_multiplier = sum(monthly_multipliers.values())
    normalized_multipliers = {k: v * 12 / total_multiplier for k, v in monthly_multipliers.items()}
    
    results = []
    base_result = compute_annual_cash_flows(base_config)
    base_monthly_income = base_result['gross_rental_income'] / 12
    
    for month, multiplier in normalized_multipliers.items():
        monthly_income = base_monthly_income * multiplier
        # Adjust expenses proportionally (some are fixed, some variable)
        variable_expenses = base_result['property_management_cost'] + base_result['tourist_tax']
        fixed_expenses = base_result['insurance'] + base_result['utilities'] + base_result['maintenance_reserve']
        
        monthly_variable = variable_expenses / 12 * multiplier
        monthly_fixed = fixed_expenses / 12
        monthly_expenses = monthly_variable + monthly_fixed
        monthly_noi = monthly_income - monthly_expenses
        
        results.append({
            'Month': month,
            'Month Name': datetime(2026, month, 1).strftime('%B'),
            'Seasonality Multiplier': multiplier,
            'Monthly Gross Income (CHF)': monthly_income,
            'Monthly Operating Expenses (CHF)': monthly_expenses,
            'Monthly NOI (CHF)': monthly_noi,
        })
    
    return pd.DataFrame(results)


def sensitivity_platform_mix(base_config: BaseCaseConfig) -> pd.DataFrame:
    """Analyze mix of Airbnb vs Booking.com revenue."""
    # Assumptions: Airbnb typically has higher fees but better rates
    # Booking.com has lower fees but potentially lower rates
    results = []
    
    for airbnb_share in np.linspace(0, 1, 11):  # 0% to 100% Airbnb
        booking_share = 1 - airbnb_share
        
        # Airbnb: 3% platform fee, potentially 5% higher rates
        # Booking.com: 15% commission, potentially 5% lower rates
        airbnb_rate_multiplier = 1.05
        booking_rate_multiplier = 0.95
        
        # Weighted average rate
        avg_rate = (
            base_config.rental.average_daily_rate * airbnb_share * airbnb_rate_multiplier +
            base_config.rental.average_daily_rate * booking_share * booking_rate_multiplier
        )
        
        # Calculate gross income
        rented_nights = base_config.rental.rented_nights
        gross_income_airbnb = rented_nights * airbnb_share * base_config.rental.average_daily_rate * airbnb_rate_multiplier * 0.97
        gross_income_booking = rented_nights * booking_share * base_config.rental.average_daily_rate * booking_rate_multiplier * 0.85
        total_gross_income = gross_income_airbnb + gross_income_booking
        
        # Recalculate with new income
        config = apply_sensitivity(base_config, daily_rate=avg_rate)
        result = compute_annual_cash_flows(config)
        
        # Override with platform-adjusted income (net of platform fees)
        result['gross_rental_income'] = total_gross_income
        # Recalculate expenses based on new income
        result['property_management_cost'] = base_config.expenses.property_management_cost(total_gross_income)
        # Tourist tax is based on rented nights, which hasn't changed
        # Other expenses remain the same
        result['total_operating_expenses'] = (
            result['property_management_cost'] +
            result['tourist_tax'] +
            result['insurance'] +
            result['utilities'] +
            result['maintenance_reserve']
        )
        result['net_operating_income'] = total_gross_income - result['total_operating_expenses']
        result['cash_flow_after_debt_service'] = result['net_operating_income'] - result['debt_service']
        result['cash_flow_per_owner'] = result['cash_flow_after_debt_service'] / base_config.financing.num_owners
        
        results.append({
            'Airbnb Share (%)': airbnb_share * 100,
            'Booking.com Share (%)': booking_share * 100,
            'Effective Daily Rate (CHF)': avg_rate,
            'Gross Rental Income (CHF)': total_gross_income,
            'Net Operating Income (CHF)': result['net_operating_income'],
            'Cash Flow After Debt (CHF)': result['cash_flow_after_debt_service'],
            'Cash Flow per Owner (CHF)': result['cash_flow_per_owner'],
        })
    
    return pd.DataFrame(results)


def sensitivity_cleaning_pass_through(base_config: BaseCaseConfig) -> pd.DataFrame:
    """Analyze cleaning fee pass-through vs cost borne by owners."""
    results = []
    
    # Base case: cleaning included in 30% management fee
    base_result = compute_annual_cash_flows(base_config)
    
    # Scenario 1: Current (cleaning in management fee)
    results.append({
        'Scenario': 'Cleaning in Management Fee (30%)',
        'Management Fee Rate (%)': 30.0,
        'Cleaning Cost per Stay (CHF)': 0,
        'Cleaning Cost Annual (CHF)': 0,
        'Gross Rental Income (CHF)': base_result['gross_rental_income'],
        'Management Fee (CHF)': base_result['property_management_cost'],
        'Total Operating Expenses (CHF)': base_result['total_operating_expenses'],
        'Cash Flow After Debt (CHF)': base_result['cash_flow_after_debt_service'],
    })
    
    # Scenario 2: Cleaning pass-through to guests
    cleaning_per_stay = 100.0
    num_stays = base_config.rental.rented_nights / base_config.expenses.average_length_of_stay
    cleaning_annual = num_stays * cleaning_per_stay
    
    # Reduce management fee to 25% (no cleaning)
    new_expenses = ExpenseParams(
        property_management_fee_rate=0.25,
        cleaning_cost_per_stay=0.0,  # Passed to guests
        average_length_of_stay=base_config.expenses.average_length_of_stay,
        tourist_tax_per_person_per_night=base_config.expenses.tourist_tax_per_person_per_night,
        avg_guests_per_night=base_config.expenses.avg_guests_per_night,
        insurance_annual=base_config.expenses.insurance_annual,
        utilities_annual=base_config.expenses.utilities_annual,
        maintenance_rate=base_config.expenses.maintenance_rate,
        property_value=base_config.expenses.property_value
    )
    
    new_config = BaseCaseConfig(
        financing=base_config.financing,
        rental=base_config.rental,
        expenses=new_expenses
    )
    
    result_pass_through = compute_annual_cash_flows(new_config)
    # Add cleaning revenue to gross income
    result_pass_through['gross_rental_income'] += cleaning_annual
    result_pass_through['property_management_cost'] = new_expenses.property_management_cost(result_pass_through['gross_rental_income'])
    result_pass_through['total_operating_expenses'] = (
        result_pass_through['property_management_cost'] +
        result_pass_through['tourist_tax'] +
        result_pass_through['insurance'] +
        result_pass_through['utilities'] +
        result_pass_through['maintenance_reserve']
    )
    result_pass_through['net_operating_income'] = result_pass_through['gross_rental_income'] - result_pass_through['total_operating_expenses']
    result_pass_through['cash_flow_after_debt_service'] = result_pass_through['net_operating_income'] - result_pass_through['debt_service']
    
    results.append({
        'Scenario': 'Cleaning Pass-Through to Guests',
        'Management Fee Rate (%)': 25.0,
        'Cleaning Cost per Stay (CHF)': cleaning_per_stay,
        'Cleaning Cost Annual (CHF)': cleaning_annual,
        'Gross Rental Income (CHF)': result_pass_through['gross_rental_income'],
        'Management Fee (CHF)': result_pass_through['property_management_cost'],
        'Total Operating Expenses (CHF)': result_pass_through['total_operating_expenses'],
        'Cash Flow After Debt (CHF)': result_pass_through['cash_flow_after_debt_service'],
    })
    
    # Scenario 3: Owners bear cleaning cost
    result_owners_bear = compute_annual_cash_flows(new_config)
    result_owners_bear['cleaning_cost'] = cleaning_annual
    result_owners_bear['total_operating_expenses'] += cleaning_annual
    result_owners_bear['net_operating_income'] = result_owners_bear['gross_rental_income'] - result_owners_bear['total_operating_expenses']
    result_owners_bear['cash_flow_after_debt_service'] = result_owners_bear['net_operating_income'] - result_owners_bear['debt_service']
    
    results.append({
        'Scenario': 'Cleaning Cost Borne by Owners',
        'Management Fee Rate (%)': 25.0,
        'Cleaning Cost per Stay (CHF)': cleaning_per_stay,
        'Cleaning Cost Annual (CHF)': cleaning_annual,
        'Gross Rental Income (CHF)': result_owners_bear['gross_rental_income'],
        'Management Fee (CHF)': result_owners_bear['property_management_cost'],
        'Total Operating Expenses (CHF)': result_owners_bear['total_operating_expenses'],
        'Cash Flow After Debt (CHF)': result_owners_bear['cash_flow_after_debt_service'],
    })
    
    return pd.DataFrame(results)


def sensitivity_property_management_fee(base_config: BaseCaseConfig, min_rate: float = 0.20, max_rate: float = 0.35, steps: int = 16) -> pd.DataFrame:
    """Analyze sensitivity to property management fee (20% to 35%)."""
    results = []
    rates = np.linspace(min_rate, max_rate, steps)
    
    for rate in rates:
        new_expenses = ExpenseParams(
            property_management_fee_rate=rate,
            cleaning_cost_per_stay=0.0,  # Included in fee
            average_length_of_stay=base_config.expenses.average_length_of_stay,
            tourist_tax_per_person_per_night=base_config.expenses.tourist_tax_per_person_per_night,
            avg_guests_per_night=base_config.expenses.avg_guests_per_night,
            insurance_annual=base_config.expenses.insurance_annual,
            utilities_annual=base_config.expenses.utilities_annual,
            maintenance_rate=base_config.expenses.maintenance_rate,
            property_value=base_config.expenses.property_value
        )
        
        new_config = BaseCaseConfig(
            financing=base_config.financing,
            rental=base_config.rental,
            expenses=new_expenses
        )
        
        result = compute_annual_cash_flows(new_config)
        results.append({
            'Management Fee Rate (%)': rate * 100,
            'Management Fee (CHF)': result['property_management_cost'],
            'Total Operating Expenses (CHF)': result['total_operating_expenses'],
            'Net Operating Income (CHF)': result['net_operating_income'],
            'Cash Flow After Debt (CHF)': result['cash_flow_after_debt_service'],
            'Cash Flow per Owner (CHF)': result['cash_flow_per_owner'],
        })
    
    return pd.DataFrame(results)


def sensitivity_cleaning_cost(base_config: BaseCaseConfig, min_cost: float = 50, max_cost: float = 200, steps: int = 16) -> pd.DataFrame:
    """Analyze sensitivity to cleaning cost per turnover."""
    results = []
    costs = np.linspace(min_cost, max_cost, steps)
    
    for cost in costs:
        # Assume cleaning is separate (not in management fee)
        new_expenses = ExpenseParams(
            property_management_fee_rate=0.25,  # Reduced since cleaning separate
            cleaning_cost_per_stay=cost,
            average_length_of_stay=base_config.expenses.average_length_of_stay,
            tourist_tax_per_person_per_night=base_config.expenses.tourist_tax_per_person_per_night,
            avg_guests_per_night=base_config.expenses.avg_guests_per_night,
            insurance_annual=base_config.expenses.insurance_annual,
            utilities_annual=base_config.expenses.utilities_annual,
            maintenance_rate=base_config.expenses.maintenance_rate,
            property_value=base_config.expenses.property_value
        )
        
        new_config = BaseCaseConfig(
            financing=base_config.financing,
            rental=base_config.rental,
            expenses=new_expenses
        )
        
        result = compute_annual_cash_flows(new_config)
        results.append({
            'Cleaning Cost per Stay (CHF)': cost,
            'Annual Cleaning Cost (CHF)': result['cleaning_cost'],
            'Total Operating Expenses (CHF)': result['total_operating_expenses'],
            'Net Operating Income (CHF)': result['net_operating_income'],
            'Cash Flow After Debt (CHF)': result['cash_flow_after_debt_service'],
            'Cash Flow per Owner (CHF)': result['cash_flow_per_owner'],
        })
    
    return pd.DataFrame(results)


def sensitivity_utilities(base_config: BaseCaseConfig, min_utilities: float = 2000, max_utilities: float = 4000, steps: int = 9) -> pd.DataFrame:
    """Analyze sensitivity to utilities cost (2000 to 4000 CHF)."""
    results = []
    utilities_range = np.linspace(min_utilities, max_utilities, steps)
    
    for utilities in utilities_range:
        new_expenses = ExpenseParams(
            property_management_fee_rate=base_config.expenses.property_management_fee_rate,
            cleaning_cost_per_stay=base_config.expenses.cleaning_cost_per_stay,
            average_length_of_stay=base_config.expenses.average_length_of_stay,
            tourist_tax_per_person_per_night=base_config.expenses.tourist_tax_per_person_per_night,
            avg_guests_per_night=base_config.expenses.avg_guests_per_night,
            insurance_annual=base_config.expenses.insurance_annual,
            utilities_annual=utilities,
            maintenance_rate=base_config.expenses.maintenance_rate,
            property_value=base_config.expenses.property_value
        )
        
        new_config = BaseCaseConfig(
            financing=base_config.financing,
            rental=base_config.rental,
            expenses=new_expenses
        )
        
        result = compute_annual_cash_flows(new_config)
        results.append({
            'Utilities Annual (CHF)': utilities,
            'Total Operating Expenses (CHF)': result['total_operating_expenses'],
            'Net Operating Income (CHF)': result['net_operating_income'],
            'Cash Flow After Debt (CHF)': result['cash_flow_after_debt_service'],
            'Cash Flow per Owner (CHF)': result['cash_flow_per_owner'],
        })
    
    return pd.DataFrame(results)


def sensitivity_maintenance_reserve(base_config: BaseCaseConfig, min_rate: float = 0.005, max_rate: float = 0.02, steps: int = 16) -> pd.DataFrame:
    """Analyze sensitivity to maintenance reserve (0.5% to 2% of property value)."""
    results = []
    rates = np.linspace(min_rate, max_rate, steps)
    
    for rate in rates:
        new_expenses = ExpenseParams(
            property_management_fee_rate=base_config.expenses.property_management_fee_rate,
            cleaning_cost_per_stay=base_config.expenses.cleaning_cost_per_stay,
            average_length_of_stay=base_config.expenses.average_length_of_stay,
            tourist_tax_per_person_per_night=base_config.expenses.tourist_tax_per_person_per_night,
            avg_guests_per_night=base_config.expenses.avg_guests_per_night,
            insurance_annual=base_config.expenses.insurance_annual,
            utilities_annual=base_config.expenses.utilities_annual,
            maintenance_rate=rate,
            property_value=base_config.expenses.property_value
        )
        
        new_config = BaseCaseConfig(
            financing=base_config.financing,
            rental=base_config.rental,
            expenses=new_expenses
        )
        
        result = compute_annual_cash_flows(new_config)
        results.append({
            'Maintenance Rate (%)': rate * 100,
            'Maintenance Reserve (CHF)': result['maintenance_reserve'],
            'Total Operating Expenses (CHF)': result['total_operating_expenses'],
            'Net Operating Income (CHF)': result['net_operating_income'],
            'Cash Flow After Debt (CHF)': result['cash_flow_after_debt_service'],
            'Cash Flow per Owner (CHF)': result['cash_flow_per_owner'],
        })
    
    return pd.DataFrame(results)


def sensitivity_capex_events(base_config: BaseCaseConfig) -> pd.DataFrame:
    """Analyze impact of special one-off CAPEX events."""
    base_result = compute_annual_cash_flows(base_config)
    
    capex_events = [
        {'name': 'Roof Replacement', 'year': 5, 'cost': 50000, 'description': 'Complete roof replacement'},
        {'name': 'Heating System', 'year': 8, 'cost': 35000, 'description': 'New heating system installation'},
        {'name': 'Major Renovation', 'year': 12, 'cost': 80000, 'description': 'Kitchen and bathroom renovation'},
    ]
    
    results = []
    base_annual_cf = base_result['cash_flow_after_debt_service']
    
    # Base case (no CAPEX)
    results.append({
        'Year': 'Base (No CAPEX)',
        'CAPEX Event': 'None',
        'CAPEX Cost (CHF)': 0,
        'Annual Cash Flow (CHF)': base_annual_cf,
        'Cash Flow After Debt (CHF)': base_annual_cf,  # Added for consistency with other sensitivities
        '15-Year Total Cash Flow (CHF)': base_annual_cf * 15,
        '15-Year Net Cash Flow (CHF)': base_annual_cf * 15,
    })
    
    # Each CAPEX event
    # Note: CAPEX reduces cash flow in the year it occurs, but annual cash flow shown is average
    for event in capex_events:
        # Average annual impact (CAPEX spread over 15 years for comparison)
        annual_capex_impact = event['cost'] / 15
        avg_annual_cf = base_annual_cf - annual_capex_impact
        total_15yr = base_annual_cf * 15 - event['cost']
        
        results.append({
            'Year': event['year'],
            'CAPEX Event': event['name'],
            'CAPEX Cost (CHF)': event['cost'],
            'Annual Cash Flow (CHF)': avg_annual_cf,
            'Cash Flow After Debt (CHF)': avg_annual_cf,  # Added for consistency
            '15-Year Total Cash Flow (CHF)': base_annual_cf * 15,
            '15-Year Net Cash Flow (CHF)': total_15yr,
        })
    
    # All events combined
    total_capex = sum(e['cost'] for e in capex_events)
    annual_capex_impact = total_capex / 15
    avg_annual_cf = base_annual_cf - annual_capex_impact
    total_15yr = base_annual_cf * 15 - total_capex
    
    results.append({
        'Year': 'All Events',
        'CAPEX Event': 'Roof + Heating + Renovation',
        'CAPEX Cost (CHF)': total_capex,
        'Annual Cash Flow (CHF)': avg_annual_cf,
        'Cash Flow After Debt (CHF)': avg_annual_cf,  # Added for consistency
        '15-Year Total Cash Flow (CHF)': base_annual_cf * 15,
        '15-Year Net Cash Flow (CHF)': total_15yr,
    })
    
    return pd.DataFrame(results)


def sensitivity_interest_rate(base_config: BaseCaseConfig, min_rate: float = 0.012, max_rate: float = 0.035, steps: int = 24) -> pd.DataFrame:
    """Analyze sensitivity to mortgage interest rate (1.2% to 3.5%)."""
    results = []
    rates = np.linspace(min_rate, max_rate, steps)
    
    for rate in rates:
        config = apply_sensitivity(base_config, interest_rate=rate)
        result = compute_annual_cash_flows(config)
        results.append({
            'Interest Rate (%)': rate * 100,
            'Interest Payment (CHF)': result['interest_payment'],
            'Total Debt Service (CHF)': result['debt_service'],
            'Net Operating Income (CHF)': result['net_operating_income'],
            'Cash Flow After Debt (CHF)': result['cash_flow_after_debt_service'],
            'Cash Flow per Owner (CHF)': result['cash_flow_per_owner'],
            'Debt Coverage Ratio': result['debt_coverage_ratio'],
        })
    
    return pd.DataFrame(results)


def sensitivity_variable_interest_rate(base_config: BaseCaseConfig) -> pd.DataFrame:
    """
    Analyze sensitivity to variable interest rate risk.
    Simulates different interest rate scenarios over 15 years.
    """
    results = []
    
    # Base case interest rate
    base_rate = base_config.financing.interest_rate
    
    # Scenarios: interest rate changes over time
    scenarios = [
        {
            'name': 'Base Case (Fixed)',
            'description': 'Interest rate remains constant at base rate',
            'rate_path': [base_rate] * 15
        },
        {
            'name': 'Gradual Increase',
            'description': 'Interest rate increases by 0.5% per year for 3 years, then stabilizes',
            'rate_path': [base_rate + 0.005 * min(i, 3) for i in range(15)]
        },
        {
            'name': 'Rapid Increase',
            'description': 'Interest rate increases by 1% per year for 2 years, then stabilizes',
            'rate_path': [base_rate + 0.01 * min(i, 2) for i in range(15)]
        },
        {
            'name': 'Volatile (Up-Down)',
            'description': 'Interest rate fluctuates: +1% first 3 years, -0.5% next 3, +0.5% last 9',
            'rate_path': [base_rate + 0.01] * 3 + [base_rate + 0.005] * 3 + [base_rate + 0.01] * 9
        },
        {
            'name': 'High Volatility',
            'description': 'Interest rate swings: +1.5% first 2 years, -1% next 2, +2% last 11',
            'rate_path': [base_rate + 0.015] * 2 + [base_rate + 0.005] * 2 + [base_rate + 0.02] * 11
        },
        {
            'name': 'Worst Case',
            'description': 'Interest rate increases to 5% and stays there',
            'rate_path': [0.05] * 15
        }
    ]
    
    for scenario in scenarios:
        # Calculate average annual cash flow over 15 years with variable rates
        # We'll use a simplified approach: calculate year-by-year and average
        from simulation import compute_15_year_projection
        
        # Create a modified config for each year (simplified: use average rate)
        avg_rate = np.mean(scenario['rate_path'])
        modified_config = apply_sensitivity(base_config, interest_rate=avg_rate)
        
        # Calculate 15-year projection
        projection = compute_15_year_projection(
            modified_config, 
            start_year=2026, 
            inflation_rate=0.02, 
            property_appreciation_rate=0.02
        )
        
        # Calculate average annual cash flow
        avg_annual_cf = np.mean([year['cash_flow_after_debt_service'] for year in projection])
        avg_annual_cf_per_owner = avg_annual_cf / base_config.financing.num_owners
        
        # Calculate total cash flow over 15 years
        total_cf = sum([year['cash_flow_after_debt_service'] for year in projection])
        total_cf_per_owner = total_cf / base_config.financing.num_owners
        
        # Calculate average interest rate
        avg_interest_rate = np.mean(scenario['rate_path']) * 100
        max_interest_rate = max(scenario['rate_path']) * 100
        
        results.append({
            'Scenario': scenario['name'],
            'Description': scenario['description'],
            'Average Interest Rate (%)': avg_interest_rate,
            'Peak Interest Rate (%)': max_interest_rate,
            'Average Annual Cash Flow (CHF)': avg_annual_cf,
            'Average Annual Cash Flow per Owner (CHF)': avg_annual_cf_per_owner,
            '15-Year Total Cash Flow (CHF)': total_cf,
            '15-Year Total Cash Flow per Owner (CHF)': total_cf_per_owner,
            'Cash Flow After Debt (CHF)': avg_annual_cf,  # For consistency with other sensitivities
        })
    
    return pd.DataFrame(results)


def sensitivity_amortization_rate(base_config: BaseCaseConfig, min_rate: float = 0.01, max_rate: float = 0.02, steps: int = 11) -> pd.DataFrame:
    """Analyze sensitivity to amortization rate (1% to 2%)."""
    results = []
    rates = np.linspace(min_rate, max_rate, steps)
    
    for rate in rates:
        new_financing = FinancingParams(
            purchase_price=base_config.financing.purchase_price,
            ltv=base_config.financing.ltv,
            interest_rate=base_config.financing.interest_rate,
            amortization_rate=rate,
            num_owners=base_config.financing.num_owners
        )
        
        new_config = BaseCaseConfig(
            financing=new_financing,
            rental=base_config.rental,
            expenses=base_config.expenses
        )
        
        result = compute_annual_cash_flows(new_config)
        results.append({
            'Amortization Rate (%)': rate * 100,
            'Amortization Payment (CHF)': result['amortization_payment'],
            'Total Debt Service (CHF)': result['debt_service'],
            'Cash Flow After Debt (CHF)': result['cash_flow_after_debt_service'],
            'Cash Flow per Owner (CHF)': result['cash_flow_per_owner'],
            '15-Year Loan Reduction (CHF)': result['amortization_payment'] * 15,
        })
    
    return pd.DataFrame(results)


def sensitivity_ltv(base_config: BaseCaseConfig, min_ltv: float = 0.60, max_ltv: float = 0.80, steps: int = 21) -> pd.DataFrame:
    """Analyze sensitivity to loan-to-value ratio (60% to 80%)."""
    results = []
    ltv_range = np.linspace(min_ltv, max_ltv, steps)
    
    for ltv in ltv_range:
        new_financing = FinancingParams(
            purchase_price=base_config.financing.purchase_price,
            ltv=ltv,
            interest_rate=base_config.financing.interest_rate,
            amortization_rate=base_config.financing.amortization_rate,
            num_owners=base_config.financing.num_owners
        )
        
        new_config = BaseCaseConfig(
            financing=new_financing,
            rental=base_config.rental,
            expenses=base_config.expenses
        )
        
        result = compute_annual_cash_flows(new_config)
        results.append({
            'Loan-to-Value (%)': ltv * 100,
            'Loan Amount (CHF)': result['loan_amount'],
            'Equity Total (CHF)': result['equity_total'],
            'Equity per Owner (CHF)': result['equity_per_owner'],
            'Debt Service (CHF)': result['debt_service'],
            'Cash Flow After Debt (CHF)': result['cash_flow_after_debt_service'],
            'Cash Flow per Owner (CHF)': result['cash_flow_per_owner'],
            'Cash-on-Cash Return (%)': result['cash_on_cash_return_pct'],
        })
    
    return pd.DataFrame(results)


def sensitivity_mortgage_type(base_config: BaseCaseConfig) -> pd.DataFrame:
    """Analyze interest-only vs amortizing mortgage."""
    results = []
    
    # Amortizing mortgage (base case)
    base_result = compute_annual_cash_flows(base_config)
    results.append({
        'Mortgage Type': 'Amortizing (1% per year)',
        'Interest Payment (CHF)': base_result['interest_payment'],
        'Amortization Payment (CHF)': base_result['amortization_payment'],
        'Total Debt Service (CHF)': base_result['debt_service'],
        'Cash Flow After Debt (CHF)': base_result['cash_flow_after_debt_service'],
        'Loan Balance After 15 Years (CHF)': base_config.financing.loan_amount - (base_result['amortization_payment'] * 15),
        'Total Equity Build (CHF)': base_result['amortization_payment'] * 15,
    })
    
    # Interest-only mortgage
    interest_only_payment = base_config.financing.loan_amount * base_config.financing.interest_rate
    cash_flow_io = base_result['net_operating_income'] - interest_only_payment
    
    results.append({
        'Mortgage Type': 'Interest-Only',
        'Interest Payment (CHF)': interest_only_payment,
        'Amortization Payment (CHF)': 0,
        'Total Debt Service (CHF)': interest_only_payment,
        'Cash Flow After Debt (CHF)': cash_flow_io,
        'Loan Balance After 15 Years (CHF)': base_config.financing.loan_amount,
        'Total Equity Build (CHF)': 0,
    })
    
    return pd.DataFrame(results)


def calculate_npv_irr_for_config(config: BaseCaseConfig, discount_rate: float = 0.04) -> Dict[str, float]:
    """
    Calculate NPV and IRR for a given configuration.
    
    Args:
        config: BaseCaseConfig to analyze
        discount_rate: Discount rate for NPV calculation (default 4%)
    
    Returns:
        Dictionary with NPV and IRR metrics
    """
    # Get initial equity per owner (calculate once, reuse)
    initial_result = compute_annual_cash_flows(config)
    initial_equity = initial_result['equity_per_owner']
    
    # Calculate 15-year projection
    projection = compute_15_year_projection(config, start_year=2026, inflation_rate=0.02, property_appreciation_rate=0.02)
    
    # Get final values
    final_property_value = projection[-1]['property_value']
    final_loan_balance = projection[-1]['remaining_loan_balance']
    
    # Calculate IRRs
    irr_results = calculate_irrs_from_projection(
        projection,
        initial_equity,
        final_property_value,
        final_loan_balance,
        config.financing.num_owners,
        purchase_price=config.financing.purchase_price
    )
    
    # Calculate NPV (using IRR with sale)
    cash_flows = [year['cash_flow_per_owner'] for year in projection]
    sale_proceeds_per_owner = (final_property_value - final_loan_balance) / config.financing.num_owners
    
    # NPV calculation
    # Initial investment is at time 0 (negative cash flow)
    npv = -initial_equity
    # Cash flows occur at end of each year (years 1-15)
    for i, cf in enumerate(cash_flows):
        npv += cf / ((1 + discount_rate) ** (i + 1))
    # Sale proceeds occur at end of year 15 (same as last cash flow)
    npv += sale_proceeds_per_owner / ((1 + discount_rate) ** len(cash_flows))
    
    return {
        'npv': npv,
        'irr_with_sale_pct': irr_results['irr_with_sale_pct'],
        'irr_without_sale_pct': irr_results['irr_without_sale_pct'],
        'initial_equity': initial_equity,
        'total_cash_flow': sum(cash_flows),
        'sale_proceeds': sale_proceeds_per_owner
    }


def calculate_sensitivity_metrics(all_sensitivities: Dict[str, pd.DataFrame], base_config: BaseCaseConfig) -> Dict[str, Dict[str, float]]:
    """
    Calculate NPV and IRR impact for each sensitivity by comparing best/worst scenarios to base case.
    For each sensitivity, calculates the actual NPV/IRR for best and worst case scenarios.
    
    Returns:
        Dictionary with base case metrics and sensitivity impacts (with both positive and negative impacts)
    """
    discount_rate = 0.04  # 4% discount rate for NPV
    
    # Calculate base case metrics
    print("  [*] Calculating base case NPV and IRR...")
    base_metrics = calculate_npv_irr_for_config(base_config, discount_rate)
    
    # Calculate impact for each sensitivity
    sensitivity_impacts = {}
    
    for sens_name, df in all_sensitivities.items():
        if 'Cash Flow After Debt (CHF)' not in df.columns:
            continue
            
        print(f"  [*] Calculating impact for {sens_name}...")
        
        # Find best and worst case rows
        best_idx = df['Cash Flow After Debt (CHF)'].idxmax()
        worst_idx = df['Cash Flow After Debt (CHF)'].idxmin()
        
        # Get parameter values for best/worst cases
        param_col = df.columns[0]  # First column is the parameter being varied
        best_param_val = df.loc[best_idx, param_col]
        worst_param_val = df.loc[worst_idx, param_col]
        
        # Create configs for best and worst cases
        # Map sensitivity name to parameter type
        best_config = None
        worst_config = None
        
        if sens_name == 'Occupancy Rate':
            # Convert percentage to decimal if needed
            best_occ = best_param_val / 100.0 if best_param_val > 1.0 else best_param_val
            worst_occ = worst_param_val / 100.0 if worst_param_val > 1.0 else worst_param_val
            best_config = apply_sensitivity(base_config, occupancy=best_occ)
            worst_config = apply_sensitivity(base_config, occupancy=worst_occ)
        elif sens_name == 'Daily Rate':
            best_config = apply_sensitivity(base_config, daily_rate=best_param_val)
            worst_config = apply_sensitivity(base_config, daily_rate=worst_param_val)
        elif sens_name == 'Interest Rate':
            # Convert percentage to decimal if needed
            best_int = best_param_val / 100.0 if best_param_val > 1.0 else best_param_val
            worst_int = worst_param_val / 100.0 if worst_param_val > 1.0 else worst_param_val
            best_config = apply_sensitivity(base_config, interest_rate=best_int)
            worst_config = apply_sensitivity(base_config, interest_rate=worst_int)
        elif sens_name == 'Management Fee':
            # Convert percentage to decimal if needed
            best_mgmt = best_param_val / 100.0 if best_param_val > 1.0 else best_param_val
            worst_mgmt = worst_param_val / 100.0 if worst_param_val > 1.0 else worst_param_val
            best_config = apply_sensitivity(base_config, management_fee=best_mgmt)
            worst_config = apply_sensitivity(base_config, management_fee=worst_mgmt)
        else:
            # For other sensitivities, use simplified approximation
            best_cf = df.loc[best_idx, 'Cash Flow After Debt (CHF)']
            worst_cf = df.loc[worst_idx, 'Cash Flow After Debt (CHF)']
            base_cf = compute_annual_cash_flows(base_config)['cash_flow_after_debt_service']
            
            best_impact = best_cf - base_cf
            worst_impact = worst_cf - base_cf
            
            # NPV of annual impact over 15 years (simplified)
            npv_best_impact = sum(best_impact / ((1 + discount_rate) ** (i + 1)) for i in range(15))
            npv_worst_impact = sum(worst_impact / ((1 + discount_rate) ** (i + 1)) for i in range(15))
            
            # IRR impact approximation
            irr_best_impact = (best_impact / abs(base_cf)) * base_metrics['irr_with_sale_pct'] * 0.3 if base_cf != 0 else 0
            irr_worst_impact = (worst_impact / abs(base_cf)) * base_metrics['irr_with_sale_pct'] * 0.3 if base_cf != 0 else 0
            
            sensitivity_impacts[sens_name] = {
                'npv_best_impact': npv_best_impact,
                'npv_worst_impact': npv_worst_impact,
                'irr_best_impact': irr_best_impact,
                'irr_worst_impact': irr_worst_impact,
                'best_cf': best_cf,
                'worst_cf': worst_cf
            }
            continue
        
        # Calculate actual NPV and IRR for best and worst configs
        if best_config and worst_config:
            best_metrics = calculate_npv_irr_for_config(best_config, discount_rate)
            worst_metrics = calculate_npv_irr_for_config(worst_config, discount_rate)
            
            # Calculate impacts relative to base case
            npv_best_impact = best_metrics['npv'] - base_metrics['npv']
            npv_worst_impact = worst_metrics['npv'] - base_metrics['npv']
            
            irr_best_impact = best_metrics['irr_with_sale_pct'] - base_metrics['irr_with_sale_pct']
            irr_worst_impact = worst_metrics['irr_with_sale_pct'] - base_metrics['irr_with_sale_pct']
            
            sensitivity_impacts[sens_name] = {
                'npv_best_impact': npv_best_impact,
                'npv_worst_impact': npv_worst_impact,
                'irr_best_impact': irr_best_impact,
                'irr_worst_impact': irr_worst_impact,
                'best_cf': df.loc[best_idx, 'Cash Flow After Debt (CHF)'],
                'worst_cf': df.loc[worst_idx, 'Cash Flow After Debt (CHF)']
            }
    
    return {
        'base_case': base_metrics,
        'sensitivities': sensitivity_impacts
    }


def generate_sensitivity_impact_table(cash_on_cash_data, npv_data, irr_data, sensitivities, sensitivity_info) -> str:
    """
    Generate a comprehensive table showing all sensitivity impacts (IRR, NPV, Cash-on-Cash).
    """
    # Create a dictionary to collect all sensitivity data
    all_sens_data = {}
    
    # Collect all sensitivity names
    all_sens_names = set()
    all_sens_names.update([name for name, _ in cash_on_cash_data])
    all_sens_names.update([name for name, _, _ in npv_data])
    all_sens_names.update([name for name, _, _ in irr_data])
    
    # Build comprehensive data for each sensitivity
    for sens_name in all_sens_names:
        sens_entry = {
            'name': sens_name,
            'range_min': '',
            'range_max': '',
            'range_base': '',
            'description': '',
            'coc_worst': None,
            'coc_best': None,
            'npv_worst': None,
            'npv_best': None,
            'irr_worst': None,
            'irr_best': None
        }
        
        # Get range and description
        if sens_name in sensitivity_info:
            info = sensitivity_info[sens_name]
            sens_entry['range_min'] = info.get('min', 'N/A')
            sens_entry['range_max'] = info.get('max', 'N/A')
            sens_entry['range_base'] = info.get('base', 'N/A')
            sens_entry['description'] = info.get('what_it_evaluates', '')
        
        # Get Cash-on-Cash data
        coc_entry = next((data for name, data in cash_on_cash_data if name == sens_name), None)
        if coc_entry:
            sens_entry['coc_worst'] = coc_entry.get('worst_impact', 0)
            sens_entry['coc_best'] = coc_entry.get('best_impact', 0)
        
        # Get NPV data
        npv_entry = next((data for name, data, _ in npv_data if name == sens_name), None)
        if npv_entry:
            sens_entry['npv_worst'] = npv_entry.get('npv_worst_impact', 0)
            sens_entry['npv_best'] = npv_entry.get('npv_best_impact', 0)
        
        # Get IRR data
        irr_entry = next((data for name, data, _ in irr_data if name == sens_name), None)
        if irr_entry:
            sens_entry['irr_worst'] = irr_entry.get('irr_worst_impact', 0)
            sens_entry['irr_best'] = irr_entry.get('irr_best_impact', 0)
        
        all_sens_data[sens_name] = sens_entry
    
    # Sort by maximum absolute NPV impact
    sorted_sens = sorted(all_sens_data.values(), 
                        key=lambda x: max(abs(x['npv_worst'] or 0), abs(x['npv_best'] or 0)), 
                        reverse=True)
    
    # Generate table HTML
    table_html = '''
    <div style="margin-top: 30px; padding: 25px; background: #f8f9fa; border-radius: 12px; border-left: 4px solid #0f3460;">
        <h4 style="color: #0f3460; margin-bottom: 20px; font-size: 1.3em; font-weight: 600;">Comprehensive Sensitivity Impact Table</h4>
        <p style="margin-bottom: 20px; color: #495057; line-height: 1.7;">
            This table shows the impact of each sensitivity factor on three key metrics: 
            <strong>Cash-on-Cash (Unlevered)</strong>, <strong>NPV</strong>, and <strong>IRR</strong>. 
            Values show the impact relative to the base case (worst case = negative impact, best case = positive impact).
        </p>
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <thead>
                    <tr style="background: linear-gradient(135deg, #0f3460 0%, #1a1a2e 100%); color: white;">
                        <th style="padding: 15px; text-align: left; font-weight: 600; border-right: 1px solid rgba(255,255,255,0.2);">Sensitivity Factor</th>
                        <th style="padding: 15px; text-align: left; font-weight: 600; border-right: 1px solid rgba(255,255,255,0.2);">Range Tested</th>
                        <th style="padding: 15px; text-align: center; font-weight: 600; border-right: 1px solid rgba(255,255,255,0.2);" colspan="2">Cash-on-Cash Impact (%)</th>
                        <th style="padding: 15px; text-align: center; font-weight: 600; border-right: 1px solid rgba(255,255,255,0.2);" colspan="2">NPV Impact (CHF)</th>
                        <th style="padding: 15px; text-align: center; font-weight: 600;" colspan="2">IRR Impact (%)</th>
                    </tr>
                    <tr style="background: #e8ecef; color: #495057;">
                        <th style="padding: 10px 15px; border-right: 1px solid #dee2e6;"></th>
                        <th style="padding: 10px 15px; border-right: 1px solid #dee2e6;"></th>
                        <th style="padding: 10px 15px; text-align: center; border-right: 1px solid #dee2e6; font-size: 0.9em; font-weight: 500;">Worst</th>
                        <th style="padding: 10px 15px; text-align: center; border-right: 1px solid #dee2e6; font-size: 0.9em; font-weight: 500;">Best</th>
                        <th style="padding: 10px 15px; text-align: center; border-right: 1px solid #dee2e6; font-size: 0.9em; font-weight: 500;">Worst</th>
                        <th style="padding: 10px 15px; text-align: center; border-right: 1px solid #dee2e6; font-size: 0.9em; font-weight: 500;">Best</th>
                        <th style="padding: 10px 15px; text-align: center; border-right: 1px solid #dee2e6; font-size: 0.9em; font-weight: 500;">Worst</th>
                        <th style="padding: 10px 15px; text-align: center; font-size: 0.9em; font-weight: 500;">Best</th>
                    </tr>
                </thead>
                <tbody>
    '''
    
    for sens in sorted_sens:
        # Format range
        range_str = f"{sens['range_min']} to {sens['range_max']}<br><small style='color: #6c757d;'>(Base: {sens['range_base']})</small>"
        
        # Format Cash-on-Cash
        coc_worst_str = f"<span style='color: #e74c3c; font-weight: 600;'>{sens['coc_worst']:.2f}%</span>" if sens['coc_worst'] is not None else "<span style='color: #999;'>N/A</span>"
        coc_best_str = f"<span style='color: #2ecc71; font-weight: 600;'>{sens['coc_best']:.2f}%</span>" if sens['coc_best'] is not None else "<span style='color: #999;'>N/A</span>"
        
        # Format NPV
        npv_worst_str = f"<span style='color: #e74c3c; font-weight: 600;'>{sens['npv_worst']:,.0f}</span>" if sens['npv_worst'] is not None else "<span style='color: #999;'>N/A</span>"
        npv_best_str = f"<span style='color: #2ecc71; font-weight: 600;'>{sens['npv_best']:,.0f}</span>" if sens['npv_best'] is not None else "<span style='color: #999;'>N/A</span>"
        
        # Format IRR
        irr_worst_str = f"<span style='color: #e67e22; font-weight: 600;'>{sens['irr_worst']:.2f}%</span>" if sens['irr_worst'] is not None else "<span style='color: #999;'>N/A</span>"
        irr_best_str = f"<span style='color: #2ecc71; font-weight: 600;'>{sens['irr_best']:.2f}%</span>" if sens['irr_best'] is not None else "<span style='color: #999;'>N/A</span>"
        
        table_html += f'''
                    <tr style="border-bottom: 1px solid #e8ecef;">
                        <td style="padding: 15px; font-weight: 600; color: #1a1a2e; border-right: 1px solid #e8ecef;">{sens['name']}</td>
                        <td style="padding: 15px; color: #495057; border-right: 1px solid #e8ecef; font-size: 0.9em;">{range_str}</td>
                        <td style="padding: 15px; text-align: center; border-right: 1px solid #e8ecef;">{coc_worst_str}</td>
                        <td style="padding: 15px; text-align: center; border-right: 1px solid #e8ecef;">{coc_best_str}</td>
                        <td style="padding: 15px; text-align: center; border-right: 1px solid #e8ecef;">{npv_worst_str}</td>
                        <td style="padding: 15px; text-align: center; border-right: 1px solid #e8ecef;">{npv_best_str}</td>
                        <td style="padding: 15px; text-align: center; border-right: 1px solid #e8ecef;">{irr_worst_str}</td>
                        <td style="padding: 15px; text-align: center;">{irr_best_str}</td>
                    </tr>
        '''
    
    table_html += '''
                </tbody>
            </table>
        </div>
    </div>
    '''
    
    return table_html


def get_sensitivity_ranges_and_descriptions() -> Dict[str, Dict[str, any]]:
    """
    Returns detailed information about each sensitivity including:
    - Min and max values tested
    - What the sensitivity evaluates
    - Base case value
    """
    return {
        'Occupancy Rate': {
            'min': '30%',
            'max': '70%',
            'base': '~50% (seasonal average)',
            'description': 'Occupancy rate measures the percentage of available nights that are actually rented. Higher occupancy means more revenue but also higher operating costs (cleaning, utilities). This sensitivity tests how the investment performs if occupancy ranges from a conservative 30% (low demand scenario) to an optimistic 70% (strong demand scenario).',
            'what_it_evaluates': 'Tests the impact of rental demand on cash flow and returns. Lower occupancy reduces revenue but also reduces variable costs like cleaning. Higher occupancy maximizes revenue potential.'
        },
        'Daily Rate': {
            'min': '200 CHF',
            'max': '400 CHF',
            'base': '~324 CHF (weighted seasonal average)',
            'description': 'Average daily rate (ADR) is the average price charged per night. This is a key revenue driver - small changes in daily rate can significantly impact annual cash flow. The sensitivity tests rates from 200 CHF (discounted pricing) to 400 CHF (premium pricing).',
            'what_it_evaluates': 'Evaluates pricing strategy impact. Higher rates increase revenue directly but may reduce occupancy. Lower rates may increase occupancy but reduce per-night profitability.'
        },
        'Owner Nights': {
            'min': '0 nights',
            'max': '150 nights',
            'base': '20 nights (5 per owner)',
            'description': 'Owner nights are nights when the property is used by owners rather than rented. More personal use means less rental income, but provides personal value. This sensitivity tests scenarios from 0 nights (fully rented) to 150 nights (significant personal use).',
            'what_it_evaluates': 'Measures the trade-off between personal use and rental income. More owner nights reduce rentable inventory but provide non-monetary value to owners.'
        },
        'Interest Rate': {
            'min': '1.2%',
            'max': '3.5%',
            'base': '1.3%',
            'description': 'Mortgage interest rate directly affects debt service payments. Higher rates increase monthly payments and reduce cash flow. This sensitivity tests rates from 1.2% (very favorable) to 3.5% (less favorable market conditions).',
            'what_it_evaluates': 'Assesses financing cost risk. Interest rate changes directly impact debt service and therefore cash flow after debt service. This is critical for understanding financing risk.'
        },
        'Variable Interest Rate': {
            'min': 'Base rate (1.3%)',
            'max': '5.0%',
            'base': '1.3% (fixed)',
            'description': 'Variable interest rate mortgages expose the investment to interest rate risk over time. Rates can increase or decrease, significantly impacting debt service. This sensitivity models different rate change scenarios over the 15-year investment period.',
            'what_it_evaluates': 'Evaluates the risk of variable rate mortgages where interest rates can change over time. Tests scenarios including gradual increases, rapid increases, volatility, and worst-case scenarios.'
        },
        'Management Fee': {
            'min': '20%',
            'max': '35%',
            'base': '20%',
            'description': 'Property management fee is a percentage of gross rental income paid to the management company. This fee covers property management services. Higher fees reduce net operating income. The sensitivity tests fees from 20% (competitive) to 35% (premium service).',
            'what_it_evaluates': 'Measures the impact of management cost on profitability. Management fees are a significant operating expense that directly reduces cash flow.'
        },
        'Cleaning Cost': {
            'min': '0 CHF',
            'max': '150 CHF per stay',
            'base': '80 CHF per stay',
            'description': 'Cleaning cost per stay is a variable expense that depends on occupancy. More stays mean more cleaning costs. This sensitivity tests cleaning costs from 0 CHF (if included in management fee) to 150 CHF per stay (premium cleaning service).',
            'what_it_evaluates': 'Evaluates the impact of variable cleaning costs on cash flow. Since cleaning costs scale with occupancy, this affects profitability especially at higher occupancy rates.'
        },
        'Utilities': {
            'min': '2,000 CHF',
            'max': '4,000 CHF',
            'base': '3,000 CHF',
            'description': 'Annual utilities cost includes electricity, water, heating, and other utilities. This is a fixed annual expense that varies with property usage and energy prices. The sensitivity tests costs from 2,000 CHF (efficient property) to 4,000 CHF (higher usage or energy costs).',
            'what_it_evaluates': 'Assesses the impact of utility costs on operating expenses. Higher utility costs reduce net operating income and cash flow.'
        },
        'Maintenance Reserve': {
            'min': '0.5%',
            'max': '2.0%',
            'base': '1.0%',
            'description': 'Maintenance reserve is set aside annually as a percentage of property value for future repairs and maintenance. Higher reserves provide more safety but reduce current cash flow. The sensitivity tests reserves from 0.5% (minimal) to 2.0% (conservative).',
            'what_it_evaluates': 'Measures the trade-off between current cash flow and future maintenance funding. Higher reserves reduce cash flow now but provide more funds for future repairs.'
        },
        'Loan-to-Value': {
            'min': '60%',
            'max': '80%',
            'base': '75%',
            'description': 'Loan-to-value (LTV) ratio determines how much of the purchase price is financed versus equity. Higher LTV means more debt (higher payments) but less initial equity required. The sensitivity tests LTV from 60% (more equity, less debt) to 80% (more debt, less equity).',
            'what_it_evaluates': 'Evaluates financing structure impact. Higher LTV increases debt service but reduces initial capital requirement. Lower LTV requires more upfront capital but reduces ongoing debt payments.'
        },
        'Amortization Rate': {
            'min': '1.0%',
            'max': '2.0%',
            'base': '1.0%',
            'description': 'Amortization rate determines how quickly the loan principal is paid down. Higher rates reduce cash flow (more principal payment) but build equity faster. The sensitivity tests rates from 1.0% (slower equity build) to 2.0% (faster equity build).',
            'what_it_evaluates': 'Measures the trade-off between cash flow and equity building. Higher amortization reduces cash flow but increases equity over time.'
        },
        'Platform Mix': {
            'min': '0% Airbnb',
            'max': '100% Airbnb',
            'base': 'Mixed (varies)',
            'description': 'Different booking platforms have different fee structures. Airbnb typically charges 3% host fee but allows higher rates, while Booking.com charges 15% commission. This sensitivity tests different mixes of Airbnb vs Booking.com.',
            'what_it_evaluates': 'Evaluates the impact of booking platform selection on net revenue. Platform fees directly affect the net income received from rentals.'
        },
        'Cleaning Pass-Through': {
            'min': 'Included in fee',
            'max': 'Passed to guests',
            'base': 'Separate cost (80 CHF)',
            'description': 'Cleaning costs can be handled three ways: included in management fee, passed through to guests, or borne by owners. Each approach has different cash flow implications. This sensitivity compares these three scenarios.',
            'what_it_evaluates': 'Measures how cleaning cost allocation affects cash flow. Passing costs to guests increases revenue, while including in management fee may reduce transparency.'
        },
        'Owner Nights': {
            'min': '0 nights',
            'max': '150 nights',
            'base': '20 nights (5 per owner)',
            'description': 'Owner nights reduce rentable inventory. More personal use means less rental income but provides personal value. This sensitivity tests scenarios from fully rented (0 owner nights) to significant personal use (150 nights).',
            'what_it_evaluates': 'Evaluates the trade-off between personal use and rental income. More owner nights reduce revenue but provide non-monetary value.'
        },
        'CAPEX Events': {
            'min': 'No CAPEX',
            'max': 'Multiple major events',
            'base': 'No CAPEX in base case',
            'description': 'Major capital expenditures (roof replacement, heating system, renovations) are one-time costs that significantly impact cash flow in specific years. This sensitivity models the impact of major CAPEX events occurring during the investment period.',
            'what_it_evaluates': 'Assesses the impact of major one-time expenses on cash flow. CAPEX events can significantly reduce cash flow in the year they occur but may improve property value or reduce future maintenance.'
        },
        'Mortgage Type': {
            'min': 'Interest-only',
            'max': 'Amortizing (1-2%)',
            'base': 'Amortizing (1%)',
            'description': 'Mortgage type affects debt service. Interest-only mortgages have lower payments but no equity build. Amortizing mortgages build equity but have higher payments. This sensitivity compares interest-only vs amortizing options.',
            'what_it_evaluates': 'Measures the trade-off between cash flow and equity building. Interest-only provides better cash flow but no principal reduction.'
        }
    }


def generate_summary_charts(metrics: Dict, base_config: BaseCaseConfig, all_sensitivities: Dict = None) -> str:
    """
    Generate tornado and waterfall charts for sensitivity analysis summary using Plotly.
    Tornado charts show BOTH positive and negative impacts (bidirectional).
    Includes a new tornado chart for yearly cash-on-cash (unlevered) efficiency.
    
    Returns:
        HTML string with all summary charts
    """
    base_metrics = metrics['base_case']
    sensitivities = metrics['sensitivities']
    
    # Calculate cash-on-cash (unlevered) for each sensitivity
    # This shows how much money needs to be put in or can be made per year
    cash_on_cash_data = []
    if all_sensitivities:
        base_result = compute_annual_cash_flows(base_config)
        base_noi = base_result['net_operating_income']  # Unlevered cash flow
        base_purchase_price = base_config.financing.purchase_price
        
        for sens_name, df in all_sensitivities.items():
            if 'Cash Flow After Debt (CHF)' not in df.columns:
                continue
            
            # Get best and worst NOI (unlevered cash flow)
            # We need to calculate NOI for each scenario
            best_idx = df['Cash Flow After Debt (CHF)'].idxmax()
            worst_idx = df['Cash Flow After Debt (CHF)'].idxmin()
            
            # For simplicity, use the cash flow after debt as proxy
            # But we want unlevered, so we need to add back debt service
            # Actually, let's calculate it properly
            best_cf_after_debt = df.loc[best_idx, 'Cash Flow After Debt (CHF)']
            worst_cf_after_debt = df.loc[worst_idx, 'Cash Flow After Debt (CHF)']
            
            # Get debt service from base case
            base_debt_service = base_result['debt_service']
            
            # Unlevered cash flow = cash flow after debt + debt service
            best_noi = best_cf_after_debt + base_debt_service
            worst_noi = worst_cf_after_debt + base_debt_service
            
            # Cash-on-cash (unlevered) = NOI / Purchase Price
            best_coc = (best_noi / base_purchase_price) * 100
            worst_coc = (worst_noi / base_purchase_price) * 100
            base_coc = (base_noi / base_purchase_price) * 100
            
            # Impact relative to base
            best_impact = best_coc - base_coc
            worst_impact = worst_coc - base_coc
            
            cash_on_cash_data.append((sens_name, {
                'best_impact': best_impact,
                'worst_impact': worst_impact,
                'best_coc': best_coc,
                'worst_coc': worst_coc,
                'base_coc': base_coc
            }))
    
    # Prepare data for tornado charts - calculate range for each sensitivity
    # Sort by maximum absolute impact (range)
    npv_data = []
    for name, data in sensitivities.items():
        range_npv = max(abs(data.get('npv_best_impact', 0)), abs(data.get('npv_worst_impact', 0)))
        npv_data.append((name, data, range_npv))
    
    irr_data = []
    for name, data in sensitivities.items():
        range_irr = max(abs(data.get('irr_best_impact', 0)), abs(data.get('irr_worst_impact', 0)))
        irr_data.append((name, data, range_irr))
    
    # Sort by range and take top 10
    npv_data = sorted(npv_data, key=lambda x: x[2], reverse=True)[:10]
    irr_data = sorted(irr_data, key=lambda x: x[2], reverse=True)[:10]
    cash_on_cash_data = sorted(cash_on_cash_data, key=lambda x: max(abs(x[1]['best_impact']), abs(x[1]['worst_impact'])), reverse=True)[:10]
    
    charts_html = []
    
    # 0. NEW: Tornado Chart for Cash-on-Cash (Unlevered) - FIRST CHART
    if cash_on_cash_data:
        coc_categories = [name for name, _ in cash_on_cash_data]
        coc_categories = coc_categories[::-1]
        
        coc_positive = [data['best_impact'] for _, data in cash_on_cash_data[::-1]]
        coc_negative = [data['worst_impact'] for _, data in cash_on_cash_data[::-1]]
        
        fig_tornado_coc = go.Figure()
        
        # Negative impact bar (extends left from zero)
        fig_tornado_coc.add_trace(go.Bar(
            y=coc_categories,
            x=coc_negative,
            orientation='h',
            name='Worst Case Impact',
            marker_color='#e74c3c',
            text=[f"{abs(v):.2f}%" if v < 0 else "" for v in coc_negative],
            textposition='outside',
            textfont=dict(color='#e74c3c', size=10),
            base=0
        ))
        
        # Positive impact bar (extends right from zero)
        fig_tornado_coc.add_trace(go.Bar(
            y=coc_categories,
            x=coc_positive,
            orientation='h',
            name='Best Case Impact',
            marker_color='#2ecc71',
            text=[f"{v:.2f}%" if v > 0 else "" for v in coc_positive],
            textposition='outside',
            textfont=dict(color='#2ecc71', size=10),
            base=0
        ))
        
        fig_tornado_coc.update_layout(
            title="Tornado Chart: Yearly Cash-on-Cash (Unlevered) Impact by Sensitivity Factor",
            xaxis_title="Cash-on-Cash Impact (% of Purchase Price)",
            yaxis_title="Sensitivity Factor",
            height=500,
            barmode='relative',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode='closest',
            xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='black', showgrid=True)
        )
        
        charts_html.append(f'<div class="chart-container"><h3 style="margin-bottom: 20px; color: var(--primary);">Annual Cash Requirement/Generation Analysis</h3><p style="margin-bottom: 20px; color: #555; line-height: 1.7;">This chart shows how much money you need to put in (negative, left side in red) or can make (positive, right side in green) per year as a percentage of the purchase price, for each sensitivity factor. This is the <strong>unlevered cash-on-cash return</strong>, showing the property\'s operating performance independent of financing. The chart helps you understand the worst-case scenario for annual cash requirements and the best-case scenario for cash generation.</p>{fig_tornado_coc.to_html(include_plotlyjs="cdn", div_id="tornadoCOC")}</div>')
    
    # 1. Tornado Chart for NPV - BIDIRECTIONAL
    # For tornado chart, we want bars extending from zero (negative left, positive right)
    npv_categories = [name for name, _, _ in npv_data]
    # Reverse for display (top to bottom)
    npv_categories = npv_categories[::-1]
    
    # Get best (positive) and worst (negative) impacts
    npv_positive = [data.get('npv_best_impact', 0) for _, data, _ in npv_data[::-1]]
    npv_negative = [data.get('npv_worst_impact', 0) for _, data, _ in npv_data[::-1]]
    
    fig_tornado_npv = go.Figure()
    
    # Negative impact bar (extends left from zero)
    fig_tornado_npv.add_trace(go.Bar(
        y=npv_categories,
        x=npv_negative,
        orientation='h',
        name='Worst Case Impact',
        marker_color='#e74c3c',
        text=[f"{abs(v):,.0f}" if v < 0 else "" for v in npv_negative],
        textposition='outside',
        textfont=dict(color='#e74c3c', size=10),
        base=0  # Bars start from zero
    ))
    
    # Positive impact bar (extends right from zero)
    fig_tornado_npv.add_trace(go.Bar(
        y=npv_categories,
        x=npv_positive,
        orientation='h',
        name='Best Case Impact',
        marker_color='#2ecc71',
        text=[f"{v:,.0f}" if v > 0 else "" for v in npv_positive],
        textposition='outside',
        textfont=dict(color='#2ecc71', size=10),
        base=0  # Bars start from zero
    ))
    
    fig_tornado_npv.update_layout(
        title="Tornado Chart: NPV Impact Range by Sensitivity Factor",
        xaxis_title="NPV Impact (CHF)",
        yaxis_title="Sensitivity Factor",
        height=500,
        barmode='relative',  # Relative mode for tornado chart (bars extend from zero)
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='closest',
        xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='black', showgrid=True)
    )
    
    charts_html.append(f'<div class="chart-container"><h3 style="margin-bottom: 20px; color: var(--primary);">NPV Impact Analysis</h3><p style="margin-bottom: 20px; color: #555; line-height: 1.7;">This tornado chart shows how each sensitivity factor impacts the Net Present Value (NPV) of the investment over 15 years. NPV represents the total discounted value of all future cash flows. Red bars (left) show negative impact (reduces NPV), green bars (right) show positive impact (increases NPV). The longer the bar, the greater the impact.</p>{fig_tornado_npv.to_html(include_plotlyjs="cdn", div_id="tornadoNPV")}</div>')
    
    # 2. Tornado Chart for IRR - BIDIRECTIONAL
    irr_categories = [name for name, _, _ in irr_data]
    irr_categories = irr_categories[::-1]
    
    irr_positive = [data.get('irr_best_impact', 0) for _, data, _ in irr_data[::-1]]
    irr_negative = [data.get('irr_worst_impact', 0) for _, data, _ in irr_data[::-1]]
    
    fig_tornado_irr = go.Figure()
    
    # Negative impact bar (extends left from zero)
    fig_tornado_irr.add_trace(go.Bar(
        y=irr_categories,
        x=irr_negative,
        orientation='h',
        name='Worst Case Impact',
        marker_color='#e67e22',
        text=[f"{abs(v):.2f}%" if v < 0 else "" for v in irr_negative],
        textposition='outside',
        textfont=dict(color='#e67e22', size=10),
        base=0  # Bars start from zero
    ))
    
    # Positive impact bar (extends right from zero)
    fig_tornado_irr.add_trace(go.Bar(
        y=irr_categories,
        x=irr_positive,
        orientation='h',
        name='Best Case Impact',
        marker_color='#2ecc71',
        text=[f"{v:.2f}%" if v > 0 else "" for v in irr_positive],
        textposition='outside',
        textfont=dict(color='#2ecc71', size=10),
        base=0  # Bars start from zero
    ))
    
    fig_tornado_irr.update_layout(
        title="Tornado Chart: IRR Impact Range by Sensitivity Factor",
        xaxis_title="IRR Impact (%)",
        yaxis_title="Sensitivity Factor",
        height=500,
        barmode='relative',  # Relative mode for tornado chart (bars extend from zero)
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='closest',
        xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='black', showgrid=True)
    )
    
    charts_html.append(f'<div class="chart-container"><h3 style="margin-bottom: 20px; color: var(--primary);">IRR Impact Analysis</h3><p style="margin-bottom: 20px; color: #555; line-height: 1.7;">This tornado chart shows how each sensitivity factor impacts the Internal Rate of Return (IRR) of the investment. IRR is the annualized return percentage, including both operating cash flows and the property sale at the end of 15 years. Higher IRR means better returns. Red bars (left) show scenarios that reduce IRR, green bars (right) show scenarios that increase IRR.</p>{fig_tornado_irr.to_html(include_plotlyjs=False, div_id="tornadoIRR")}</div>')
    
    # Generate comprehensive sensitivity impact table
    sensitivity_info = get_sensitivity_ranges_and_descriptions()
    sensitivity_table_html = generate_sensitivity_impact_table(
        cash_on_cash_data, 
        npv_data, 
        irr_data, 
        sensitivities, 
        sensitivity_info
    )
    
    # Add the table after all tornado charts
    charts_html.append(f'<div class="chart-container" style="margin-top: 40px;"><h3 style="margin-bottom: 20px; color: var(--primary);">Sensitivity Impact Summary</h3>{sensitivity_table_html}</div>')
    
    # 3. Waterfall Chart for NPV - Cumulative worst case scenario
    # Sort by worst impact (most negative)
    waterfall_npv_data = sorted(sensitivities.items(), key=lambda x: x[1].get('npv_worst_impact', 0))
    waterfall_npv_labels = ["Base Case"] + [name for name, _ in waterfall_npv_data[:10]] + ["Worst Case"]
    
    base_npv = base_metrics['npv']
    measures = ["absolute"] + ["relative"] * min(10, len(waterfall_npv_data)) + ["total"]
    worst_impacts = [data.get('npv_worst_impact', 0) for _, data in waterfall_npv_data[:10]]
    values = [base_npv] + worst_impacts + [0]
    # Calculate final value
    final_val = base_npv + sum(worst_impacts)
    values[-1] = final_val
    
    fig_waterfall_npv = go.Figure(go.Waterfall(
        orientation="v",
        measure=measures,
        x=waterfall_npv_labels,
        textposition="outside",
        text=[f"{v:,.0f}" if abs(v) > 100 else "" for v in values],
        y=values,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig_waterfall_npv.update_layout(
        title="Waterfall Chart: Cumulative Downside Risk (Top 10 Worst Impacts)",
        showlegend=False,
        height=500,
        yaxis_title="NPV (CHF)"
    )
    charts_html.append(f'<div class="chart-container">{fig_waterfall_npv.to_html(include_plotlyjs=False, div_id="waterfallNPV")}</div>')
    
    # 5. Waterfall Chart for IRR - Cumulative worst case
    waterfall_irr_data = sorted(sensitivities.items(), key=lambda x: x[1].get('irr_worst_impact', 0))
    waterfall_irr_labels = ["Base Case"] + [name for name, _ in waterfall_irr_data[:10]] + ["Worst Case"]
    
    base_irr = base_metrics['irr_with_sale_pct']
    measures_irr = ["absolute"] + ["relative"] * min(10, len(waterfall_irr_data)) + ["total"]
    worst_irr_impacts = [data.get('irr_worst_impact', 0) for _, data in waterfall_irr_data[:10]]
    values_irr = [base_irr] + worst_irr_impacts + [0]
    final_irr = base_irr + sum(worst_irr_impacts)
    values_irr[-1] = final_irr
    
    fig_waterfall_irr = go.Figure(go.Waterfall(
        orientation="v",
        measure=measures_irr,
        x=waterfall_irr_labels,
        textposition="outside",
        text=[f"{v:.2f}%" if abs(v) > 0.1 else "" for v in values_irr],
        y=values_irr,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig_waterfall_irr.update_layout(
        title="Waterfall Chart: Cumulative IRR Downside Risk (Top 10 Worst Impacts)",
        showlegend=False,
        height=500,
        yaxis_title="IRR (%)"
    )
    charts_html.append(f'<div class="chart-container">{fig_waterfall_irr.to_html(include_plotlyjs=False, div_id="waterfallIRR")}</div>')
    
    return "\n".join(charts_html)


def export_sensitivities_to_excel(all_sensitivities: Dict[str, pd.DataFrame], output_path: str = "sensitivity_analysis.xlsx"):
    """Export all sensitivity analyses to Excel."""
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for name, df in all_sensitivities.items():
            # Clean sheet name (Excel has 31 char limit)
            sheet_name = name[:31] if len(name) > 31 else name
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"[+] Excel file exported: {output_path}")


def generate_apexcharts_for_sensitivities(all_sensitivities: Dict[str, pd.DataFrame], base_config: BaseCaseConfig) -> str:
    """Generate ApexCharts HTML for all sensitivity analyses."""
    import json
    
    charts_html_parts = []
    chart_id = 0
    
    def format_chf(val):
        return f"new Intl.NumberFormat('de-CH', {{style: 'currency', currency: 'CHF', maximumFractionDigits: 0}}).format({val})"
    
    # Chart for each sensitivity
    for sens_name, df in all_sensitivities.items():
        chart_id += 1
        chart_div_id = f"sensChart{chart_id}"
        
        if sens_name == 'Occupancy Rate':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Occupancy Rate (%)'].tolist(), "title": {"text": "Occupancy Rate (%)"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#3498db"],
                "title": {"text": "Sensitivity: Occupancy Rate Impact on Cash Flow", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "annotations": {"yaxis": [{"y": 0, "borderColor": "#999", "strokeDashArray": 5, "label": {"text": "Break-even"}}]},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
            
        elif sens_name == 'Daily Rate':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Average Daily Rate (CHF)'].tolist(), "title": {"text": "Average Daily Rate (CHF)"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#2ecc71"],
                "title": {"text": "Sensitivity: Average Daily Rate Impact on Cash Flow", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "annotations": {"yaxis": [{"y": 0, "borderColor": "#999", "strokeDashArray": 5, "label": {"text": "Break-even"}}]},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
            
        elif sens_name == 'Owner Nights':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Gross Rental Income", "data": df['Gross Rental Income (CHF)'].tolist()}],
                "xaxis": {"categories": df['Total Owner Nights'].tolist(), "title": {"text": "Total Owner Nights"}},
                "yaxis": {"title": {"text": "Gross Rental Income (CHF)"}},
                "colors": ["#e74c3c"],
                "title": {"text": "Sensitivity: Owner Nights Impact on Rental Income", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
            
        elif sens_name == 'Seasonality':
            chart_config = {
                "chart": {"type": "bar", "height": 400, "toolbar": {"show": True}},
                "plotOptions": {"bar": {"horizontal": False}},
                "series": [{"name": "Monthly Income", "data": df['Monthly Gross Income (CHF)'].tolist()}],
                "xaxis": {"categories": df['Month Name'].tolist(), "title": {"text": "Month"}},
                "yaxis": {"title": {"text": "Monthly Gross Income (CHF)"}},
                "colors": ["#9b59b6"],
                "title": {"text": "Seasonality: Monthly Revenue Distribution", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
            
        elif sens_name == 'Platform Mix':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Cash Flow", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Airbnb Share (%)'].tolist(), "title": {"text": "Airbnb Share (%)"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#f39c12"],
                "title": {"text": "Sensitivity: Platform Mix (Airbnb vs Booking.com)", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "annotations": {"yaxis": [{"y": 0, "borderColor": "#999", "strokeDashArray": 5}]},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
            
        elif sens_name == 'Interest Rate':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Interest Rate (%)'].tolist(), "title": {"text": "Interest Rate (%)"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#e67e22"],
                "title": {"text": "Sensitivity: Interest Rate Impact on Cash Flow", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "annotations": {"yaxis": [{"y": 0, "borderColor": "#999", "strokeDashArray": 5, "label": {"text": "Break-even"}}]},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
            
        elif sens_name == 'Loan-to-Value':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [
                    {"name": "Cash Flow", "data": df['Cash Flow After Debt (CHF)'].tolist()},
                    {"name": "Equity per Owner", "data": df['Equity per Owner (CHF)'].tolist()}
                ],
                "xaxis": {"categories": df['Loan-to-Value (%)'].tolist(), "title": {"text": "Loan-to-Value (%)"}},
                "yaxis": {"title": {"text": "Amount (CHF)"}},
                "colors": ["#3498db", "#2ecc71"],
                "title": {"text": "Sensitivity: Loan-to-Value Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "legend": {"position": "top"},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
            
        elif sens_name == 'Management Fee':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Management Fee Rate (%)'].tolist(), "title": {"text": "Management Fee Rate (%)"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#16a085"],
                "title": {"text": "Sensitivity: Property Management Fee Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "annotations": {"yaxis": [{"y": 0, "borderColor": "#999", "strokeDashArray": 5}]},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
            
        elif sens_name == 'Cleaning Cost':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Cleaning Cost per Stay (CHF)'].tolist(), "title": {"text": "Cleaning Cost per Stay (CHF)"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#e74c3c"],
                "title": {"text": "Sensitivity: Cleaning Cost Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
            
        elif sens_name == 'Utilities':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Utilities Annual (CHF)'].tolist(), "title": {"text": "Utilities Annual (CHF)"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#3498db"],
                "title": {"text": "Sensitivity: Utilities Cost Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
            
        elif sens_name == 'Maintenance Reserve':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Maintenance Rate (%)'].tolist(), "title": {"text": "Maintenance Rate (%)"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#9b59b6"],
                "title": {"text": "Sensitivity: Maintenance Reserve Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
            
        elif sens_name == 'Amortization Rate':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Amortization Rate (%)'].tolist(), "title": {"text": "Amortization Rate (%)"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#f39c12"],
                "title": {"text": "Sensitivity: Amortization Rate Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
            
        elif sens_name == 'Cleaning Pass-Through':
            chart_config = {
                "chart": {"type": "bar", "height": 400, "toolbar": {"show": True}},
                "plotOptions": {"bar": {"horizontal": False}},
                "series": [{"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Scenario'].tolist(), "title": {"text": "Scenario"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#16a085"],
                "title": {"text": "Sensitivity: Cleaning Fee Pass-Through Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
            
        elif sens_name == 'CAPEX Events':
            chart_config = {
                "chart": {"type": "bar", "height": 400, "toolbar": {"show": True}},
                "plotOptions": {"bar": {"horizontal": False}},
                "series": [
                    {"name": "15-Year Net Cash Flow", "data": df['15-Year Net Cash Flow (CHF)'].tolist()},
                    {"name": "CAPEX Cost", "data": df['CAPEX Cost (CHF)'].tolist()}
                ],
                "xaxis": {"categories": df['CAPEX Event'].tolist(), "title": {"text": "CAPEX Event"}},
                "yaxis": {"title": {"text": "Amount (CHF)"}},
                "colors": ["#3498db", "#e74c3c"],
                "title": {"text": "Sensitivity: CAPEX Events Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "legend": {"position": "top"},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
            
        elif sens_name == 'Mortgage Type':
            chart_config = {
                "chart": {"type": "bar", "height": 400, "toolbar": {"show": True}},
                "plotOptions": {"bar": {"horizontal": False}},
                "series": [
                    {"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()},
                    {"name": "Total Equity Build", "data": df['Total Equity Build (CHF)'].tolist()}
                ],
                "xaxis": {"categories": df['Mortgage Type'].tolist(), "title": {"text": "Mortgage Type"}},
                "yaxis": {"title": {"text": "Amount (CHF)"}},
                "colors": ["#2ecc71", "#3498db"],
                "title": {"text": "Sensitivity: Mortgage Type Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "legend": {"position": "top"},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
            
        else:
            # Default chart for other sensitivities
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Value", "data": df.iloc[:, 1].tolist()}],
                "xaxis": {"categories": df.iloc[:, 0].tolist(), "title": {"text": df.columns[0]}},
                "yaxis": {"title": {"text": df.columns[1]}},
                "colors": ["#667eea"],
                "title": {"text": f"Sensitivity: {sens_name}", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
            }
        
        chart_json = json.dumps(chart_config)
        charts_html_parts.append(f'''
    <div class="chart-container">
        <div id="{chart_div_id}" style="min-height: 400px;"></div>
        <script>
            var {chart_div_id.replace('-', '_')}Options = {chart_json};
            {chart_div_id.replace('-', '_')}Options.yaxis = {chart_div_id.replace('-', '_')}Options.yaxis || {{}};
            {chart_div_id.replace('-', '_')}Options.yaxis.labels = {{formatter: function(val) {{ return new Intl.NumberFormat('de-CH', {{style: 'currency', currency: 'CHF', maximumFractionDigits: 0}}).format(val); }}}};
            var {chart_div_id.replace('-', '_')}Chart = new ApexCharts(document.querySelector("#{chart_div_id}"), {chart_div_id.replace('-', '_')}Options);
            {chart_div_id.replace('-', '_')}Chart.render();
        </script>
    </div>
        ''')
    
    return "\n".join(charts_html_parts)


def create_sensitivity_charts(all_sensitivities: Dict[str, pd.DataFrame], base_config: BaseCaseConfig) -> List[Tuple[str, go.Figure]]:
    """Create charts for all sensitivity analyses (kept for compatibility, but we use ApexCharts now)."""
    charts = []
    base_result = compute_annual_cash_flows(base_config)
    
    # Chart 1: Occupancy Rate Sensitivity
    if 'Occupancy Rate' in all_sensitivities:
        df = all_sensitivities['Occupancy Rate']
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Occupancy Rate (%)'],
            y=df['Cash Flow After Debt (CHF)'],
            mode='lines+markers',
            name='Cash Flow After Debt',
            line=dict(color='#3498db', width=3)
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Break-even")
        fig.update_layout(
            title="Sensitivity: Occupancy Rate Impact on Cash Flow",
            xaxis_title="Occupancy Rate (%)",
            yaxis_title="Cash Flow After Debt (CHF)",
            height=400
        )
        charts.append(("occupancy_rate", fig))
    
    # Chart 2: Daily Rate Sensitivity
    if 'Daily Rate' in all_sensitivities:
        df = all_sensitivities['Daily Rate']
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Average Daily Rate (CHF)'],
            y=df['Cash Flow After Debt (CHF)'],
            mode='lines+markers',
            name='Cash Flow After Debt',
            line=dict(color='#2ecc71', width=3)
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Break-even")
        fig.update_layout(
            title="Sensitivity: Average Daily Rate Impact on Cash Flow",
            xaxis_title="Average Daily Rate (CHF)",
            yaxis_title="Cash Flow After Debt (CHF)",
            height=400
        )
        charts.append(("daily_rate", fig))
    
    # Chart 3: Owner Nights Sensitivity
    if 'Owner Nights' in all_sensitivities:
        df = all_sensitivities['Owner Nights']
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Total Owner Nights'],
            y=df['Gross Rental Income (CHF)'],
            mode='lines+markers',
            name='Gross Rental Income',
            line=dict(color='#e74c3c', width=3)
        ))
        fig.update_layout(
            title="Sensitivity: Owner Nights Impact on Rental Income",
            xaxis_title="Total Owner Nights",
            yaxis_title="Gross Rental Income (CHF)",
            height=400
        )
        charts.append(("owner_nights", fig))
    
    # Chart 4: Seasonality
    if 'Seasonality' in all_sensitivities:
        df = all_sensitivities['Seasonality']
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['Month Name'],
            y=df['Monthly Gross Income (CHF)'],
            name='Monthly Income',
            marker_color='#9b59b6'
        ))
        fig.update_layout(
            title="Seasonality: Monthly Revenue Distribution",
            xaxis_title="Month",
            yaxis_title="Monthly Gross Income (CHF)",
            height=400,
            xaxis={'categoryorder': 'array', 'categoryarray': df['Month Name'].tolist()}
        )
        charts.append(("seasonality", fig))
    
    # Chart 5: Platform Mix
    if 'Platform Mix' in all_sensitivities:
        df = all_sensitivities['Platform Mix']
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Airbnb Share (%)'],
            y=df['Cash Flow After Debt (CHF)'],
            mode='lines+markers',
            name='Cash Flow',
            line=dict(color='#f39c12', width=3)
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.update_layout(
            title="Sensitivity: Platform Mix (Airbnb vs Booking.com)",
            xaxis_title="Airbnb Share (%)",
            yaxis_title="Cash Flow After Debt (CHF)",
            height=400
        )
        charts.append(("platform_mix", fig))
    
    # Chart 6: Interest Rate Sensitivity
    if 'Interest Rate' in all_sensitivities:
        df = all_sensitivities['Interest Rate']
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Interest Rate (%)'],
            y=df['Cash Flow After Debt (CHF)'],
            mode='lines+markers',
            name='Cash Flow After Debt',
            line=dict(color='#e67e22', width=3)
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Break-even")
        fig.update_layout(
            title="Sensitivity: Interest Rate Impact on Cash Flow",
            xaxis_title="Interest Rate (%)",
            yaxis_title="Cash Flow After Debt (CHF)",
            height=400
        )
        charts.append(("interest_rate", fig))
    
    # Chart 7: LTV Sensitivity
    if 'Loan-to-Value' in all_sensitivities:
        df = all_sensitivities['Loan-to-Value']
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(x=df['Loan-to-Value (%)'], y=df['Cash Flow After Debt (CHF)'], name="Cash Flow", line=dict(color='#3498db', width=3)),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=df['Loan-to-Value (%)'], y=df['Equity per Owner (CHF)'], name="Equity per Owner", line=dict(color='#2ecc71', width=3)),
            secondary_y=True,
        )
        fig.update_xaxes(title_text="Loan-to-Value (%)")
        fig.update_yaxes(title_text="Cash Flow After Debt (CHF)", secondary_y=False)
        fig.update_yaxes(title_text="Equity per Owner (CHF)", secondary_y=True)
        fig.update_layout(
            title="Sensitivity: Loan-to-Value Impact",
            height=400
        )
        charts.append(("ltv", fig))
    
    # Chart 8: Management Fee Sensitivity
    if 'Management Fee' in all_sensitivities:
        df = all_sensitivities['Management Fee']
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Management Fee Rate (%)'],
            y=df['Cash Flow After Debt (CHF)'],
            mode='lines+markers',
            name='Cash Flow After Debt',
            line=dict(color='#16a085', width=3)
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.update_layout(
            title="Sensitivity: Property Management Fee Impact",
            xaxis_title="Management Fee Rate (%)",
            yaxis_title="Cash Flow After Debt (CHF)",
            height=400
        )
        charts.append(("management_fee", fig))
    
    return charts


def generate_detailed_sensitivity_sections_with_charts(all_sensitivities: Dict[str, pd.DataFrame], 
                                                       sensitivity_descriptions: Dict[str, str],
                                                       base_config: BaseCaseConfig) -> str:
    """Generate detailed HTML sections with charts and tables for each sensitivity."""
    import json
    
    sections = []
    chart_id = 0
    
    def format_currency(value):
        try:
            return f"{float(value):,.0f} CHF"
        except:
            return str(value)
    
    def format_percent(value):
        try:
            return f"{float(value):.2f}%"
        except:
            return str(value)
    
    def format_chf(val):
        return f"new Intl.NumberFormat('de-CH', {{style: 'currency', currency: 'CHF', maximumFractionDigits: 0}}).format({val})"
    
    for sens_name, df in all_sensitivities.items():
        chart_id += 1
        chart_div_id = f"sensChart{chart_id}"
        
        # Generate chart config (same logic as generate_apexcharts_for_sensitivities)
        if sens_name == 'Occupancy Rate':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Occupancy Rate (%)'].tolist(), "title": {"text": "Occupancy Rate (%)"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#3498db"],
                "title": {"text": f"{sens_name} Impact on Cash Flow", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "annotations": {"yaxis": [{"y": 0, "borderColor": "#999", "strokeDashArray": 5, "label": {"text": "Break-even"}}]},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
        elif sens_name == 'Daily Rate':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Average Daily Rate (CHF)'].tolist(), "title": {"text": "Average Daily Rate (CHF)"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#2ecc71"],
                "title": {"text": f"{sens_name} Impact on Cash Flow", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "annotations": {"yaxis": [{"y": 0, "borderColor": "#999", "strokeDashArray": 5, "label": {"text": "Break-even"}}]},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
        elif sens_name == 'Owner Nights':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Gross Rental Income", "data": df['Gross Rental Income (CHF)'].tolist()}],
                "xaxis": {"categories": df['Total Owner Nights'].tolist(), "title": {"text": "Total Owner Nights"}},
                "yaxis": {"title": {"text": "Gross Rental Income (CHF)"}},
                "colors": ["#e74c3c"],
                "title": {"text": f"{sens_name} Impact on Rental Income", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
        elif sens_name == 'Seasonality':
            chart_config = {
                "chart": {"type": "bar", "height": 400, "toolbar": {"show": True}},
                "plotOptions": {"bar": {"horizontal": False}},
                "series": [{"name": "Monthly Income", "data": df['Monthly Gross Income (CHF)'].tolist()}],
                "xaxis": {"categories": df['Month Name'].tolist(), "title": {"text": "Month"}},
                "yaxis": {"title": {"text": "Monthly Gross Income (CHF)"}},
                "colors": ["#9b59b6"],
                "title": {"text": f"{sens_name}: Monthly Revenue Distribution", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
        elif sens_name == 'Platform Mix':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Cash Flow", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Airbnb Share (%)'].tolist(), "title": {"text": "Airbnb Share (%)"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#f39c12"],
                "title": {"text": f"{sens_name} Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "annotations": {"yaxis": [{"y": 0, "borderColor": "#999", "strokeDashArray": 5}]},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
        elif sens_name == 'Cleaning Pass-Through':
            chart_config = {
                "chart": {"type": "bar", "height": 400, "toolbar": {"show": True}},
                "plotOptions": {"bar": {"horizontal": False}},
                "series": [{"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Scenario'].tolist(), "title": {"text": "Scenario"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#16a085"],
                "title": {"text": f"{sens_name} Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
        elif sens_name == 'Management Fee':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Management Fee Rate (%)'].tolist(), "title": {"text": "Management Fee Rate (%)"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#16a085"],
                "title": {"text": f"{sens_name} Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "annotations": {"yaxis": [{"y": 0, "borderColor": "#999", "strokeDashArray": 5}]},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
        elif sens_name == 'Cleaning Cost':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Cleaning Cost per Stay (CHF)'].tolist(), "title": {"text": "Cleaning Cost per Stay (CHF)"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#e74c3c"],
                "title": {"text": f"{sens_name} Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
        elif sens_name == 'Utilities':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Utilities Annual (CHF)'].tolist(), "title": {"text": "Utilities Annual (CHF)"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#3498db"],
                "title": {"text": f"{sens_name} Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
        elif sens_name == 'Maintenance Reserve':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Maintenance Rate (%)'].tolist(), "title": {"text": "Maintenance Rate (%)"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#9b59b6"],
                "title": {"text": f"{sens_name} Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
        elif sens_name == 'CAPEX Events':
            chart_config = {
                "chart": {"type": "bar", "height": 400, "toolbar": {"show": True}},
                "plotOptions": {"bar": {"horizontal": False}},
                "series": [
                    {"name": "15-Year Net Cash Flow", "data": df['15-Year Net Cash Flow (CHF)'].tolist()},
                    {"name": "CAPEX Cost", "data": df['CAPEX Cost (CHF)'].tolist()}
                ],
                "xaxis": {"categories": df['CAPEX Event'].tolist(), "title": {"text": "CAPEX Event"}},
                "yaxis": {"title": {"text": "Amount (CHF)"}},
                "colors": ["#3498db", "#e74c3c"],
                "title": {"text": f"{sens_name} Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "legend": {"position": "top"},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
        elif sens_name == 'Interest Rate':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Interest Rate (%)'].tolist(), "title": {"text": "Interest Rate (%)"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#e67e22"],
                "title": {"text": f"{sens_name} Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "annotations": {"yaxis": [{"y": 0, "borderColor": "#999", "strokeDashArray": 5, "label": {"text": "Break-even"}}]},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
        elif sens_name == 'Amortization Rate':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()}],
                "xaxis": {"categories": df['Amortization Rate (%)'].tolist(), "title": {"text": "Amortization Rate (%)"}},
                "yaxis": {"title": {"text": "Cash Flow After Debt (CHF)"}},
                "colors": ["#f39c12"],
                "title": {"text": f"{sens_name} Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
        elif sens_name == 'Loan-to-Value':
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}, "zoom": {"enabled": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [
                    {"name": "Cash Flow", "data": df['Cash Flow After Debt (CHF)'].tolist()},
                    {"name": "Equity per Owner", "data": df['Equity per Owner (CHF)'].tolist()}
                ],
                "xaxis": {"categories": df['Loan-to-Value (%)'].tolist(), "title": {"text": "Loan-to-Value (%)"}},
                "yaxis": {"title": {"text": "Amount (CHF)"}},
                "colors": ["#3498db", "#2ecc71"],
                "title": {"text": f"{sens_name} Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "legend": {"position": "top"},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
        elif sens_name == 'Mortgage Type':
            chart_config = {
                "chart": {"type": "bar", "height": 400, "toolbar": {"show": True}},
                "plotOptions": {"bar": {"horizontal": False}},
                "series": [
                    {"name": "Cash Flow After Debt", "data": df['Cash Flow After Debt (CHF)'].tolist()},
                    {"name": "Total Equity Build", "data": df['Total Equity Build (CHF)'].tolist()}
                ],
                "xaxis": {"categories": df['Mortgage Type'].tolist(), "title": {"text": "Mortgage Type"}},
                "yaxis": {"title": {"text": "Amount (CHF)"}},
                "colors": ["#2ecc71", "#3498db"],
                "title": {"text": f"{sens_name} Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
                "legend": {"position": "top"},
                "tooltip": {"y": {"formatter": "function(val) { return " + format_chf("val") + "; }"}}
            }
        else:
            # Default chart
            chart_config = {
                "chart": {"type": "line", "height": 400, "toolbar": {"show": True}},
                "stroke": {"curve": "smooth", "width": 3},
                "markers": {"size": 5},
                "series": [{"name": "Value", "data": df.iloc[:, 1].tolist()}],
                "xaxis": {"categories": df.iloc[:, 0].tolist(), "title": {"text": df.columns[0]}},
                "yaxis": {"title": {"text": df.columns[1]}},
                "colors": ["#667eea"],
                "title": {"text": f"{sens_name} Impact", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
            }
        
        chart_json = json.dumps(chart_config)
        
        # Extract key KPIs from the DataFrame
        kpi_html = ""
        if 'Cash Flow After Debt (CHF)' in df.columns:
            min_cf = df['Cash Flow After Debt (CHF)'].min()
            max_cf = df['Cash Flow After Debt (CHF)'].max()
            base_cf = compute_annual_cash_flows(base_config)['cash_flow_after_debt_service']
            
            kpi_html = f'''
            <div class="kpi-mini-grid">
                <div class="kpi-mini-card">
                    <div class="kpi-mini-label">Best Case</div>
                    <div class="kpi-mini-value {'positive' if max_cf >= 0 else 'negative'}">{format_currency(max_cf)}</div>
                </div>
                <div class="kpi-mini-card">
                    <div class="kpi-mini-label">Base Case</div>
                    <div class="kpi-mini-value {'positive' if base_cf >= 0 else 'negative'}">{format_currency(base_cf)}</div>
                </div>
                <div class="kpi-mini-card">
                    <div class="kpi-mini-label">Worst Case</div>
                    <div class="kpi-mini-value {'positive' if min_cf >= 0 else 'negative'}">{format_currency(min_cf)}</div>
                </div>
                <div class="kpi-mini-card">
                    <div class="kpi-mini-label">Range</div>
                    <div class="kpi-mini-value neutral">{format_currency(max_cf - min_cf)}</div>
                </div>
            </div>
            '''
        
        # Create anchor ID for table of contents
        anchor_id = sens_name.lower().replace(" ", "-").replace("/", "-")
        
        sections.append(f'''
        <div class="sensitivity-section" id="sens-{anchor_id}">
            <h3>{sens_name}</h3>
            {f'''
            <div class="intro-box" style="margin-bottom: 25px;">
                <p style="margin-bottom: 12px;"><strong>What this sensitivity evaluates:</strong> {get_sensitivity_ranges_and_descriptions().get(sens_name, {}).get('what_it_evaluates', 'This sensitivity tests how changes in this parameter affect the investment performance.')}</p>
                <p style="margin-bottom: 12px;"><strong>Range tested:</strong> From <strong>{get_sensitivity_ranges_and_descriptions().get(sens_name, {}).get('min', 'N/A')}</strong> (worst case scenario) to <strong>{get_sensitivity_ranges_and_descriptions().get(sens_name, {}).get('max', 'N/A')}</strong> (best case scenario). Base case value: <strong>{get_sensitivity_ranges_and_descriptions().get(sens_name, {}).get('base', 'N/A')}</strong>.</p>
                <p style="margin-bottom: 0;"><strong>Context:</strong> {get_sensitivity_ranges_and_descriptions().get(sens_name, {}).get('description', 'This parameter is an important factor in determining the investment\'s financial performance.')}</p>
            </div>
            ''' if sens_name in get_sensitivity_ranges_and_descriptions() else ''}
            <div class="sensitivity-card">
                <p>
                    {sensitivity_descriptions.get(sens_name, 'Analysis of this sensitivity factor.')}
                </p>
                {kpi_html}
                <div class="chart-container" style="margin-top: 30px;">
                    <div id="{chart_div_id}" style="min-height: 400px;"></div>
                    <script>
                        var {chart_div_id.replace('-', '_')}Options = {chart_json};
                        {chart_div_id.replace('-', '_')}Options.yaxis = {chart_div_id.replace('-', '_')}Options.yaxis || {{}};
                        {chart_div_id.replace('-', '_')}Options.yaxis.labels = {{formatter: function(val) {{ return new Intl.NumberFormat('de-CH', {{style: 'currency', currency: 'CHF', maximumFractionDigits: 0}}).format(val); }}}};
                        var {chart_div_id.replace('-', '_')}Chart = new ApexCharts(document.querySelector("#{chart_div_id}"), {chart_div_id.replace('-', '_')}Options);
                        {chart_div_id.replace('-', '_')}Chart.render();
                    </script>
                </div>
            </div>
        </div>
        ''')
    
    return "\n".join(sections)


def generate_detailed_sensitivity_sections(all_sensitivities: Dict[str, pd.DataFrame], 
                                           sensitivity_descriptions: Dict[str, str]) -> str:
    """Generate detailed HTML sections with tables for each sensitivity."""
    sections = []
    
    def format_currency(value):
        try:
            return f"{float(value):,.0f} CHF"
        except:
            return str(value)
    
    def format_percent(value):
        try:
            return f"{float(value):.2f}%"
        except:
            return str(value)
    
    for sens_name, df in all_sensitivities.items():
        # Create table HTML from DataFrame
        table_rows = []
        
        # Header row
        headers = list(df.columns)
        header_row = "<tr>" + "".join([f'<th>{h}</th>' for h in headers]) + "</tr>"
        table_rows.append(header_row)
        
        # Data rows (limit to 20 rows for readability, or show all if less)
        max_rows = min(20, len(df))
        for idx in range(max_rows):
            row_data = df.iloc[idx]
            cells = []
            for col in headers:
                val = row_data[col]
                if 'CHF' in col or 'Amount' in col or 'Cost' in col or 'Income' in col or 'Expenses' in col or 'Flow' in col or 'Balance' in col or 'Equity' in col or 'Loan' in col or 'Payment' in col or 'Service' in col or 'Revenue' in col or 'Proceeds' in col:
                    cells.append(f'<td>{format_currency(val)}</td>')
                elif '%' in col or 'Rate' in col or 'Ratio' in col:
                    cells.append(f'<td>{format_percent(val)}</td>')
                else:
                    cells.append(f'<td>{val}</td>')
            table_rows.append("<tr>" + "".join(cells) + "</tr>")
        
        if len(df) > max_rows:
            table_rows.append(f'<tr><td colspan="{len(headers)}" style="text-align: center; font-style: italic;">... and {len(df) - max_rows} more rows (see Excel file for complete data)</td></tr>')
        
        table_html = f"""
        <table class="summary-table">
            <thead>
                {header_row}
            </thead>
            <tbody>
                {''.join(table_rows)}
            </tbody>
        </table>
        """
        
        # Get detailed explanation for this sensitivity
        sensitivity_info = get_sensitivity_ranges_and_descriptions()
        sens_info = sensitivity_info.get(sens_name, {})
        
        sections.append(f'''
        <div class="sensitivity-section">
            <h3 style="color: #667eea; font-size: 1.5em; margin-bottom: 15px; margin-top: 30px;">{sens_name}</h3>
            <div class="sensitivity-card">
                <div class="intro-box" style="margin-bottom: 25px;">
                    <p style="margin-bottom: 12px; font-size: 1.05em; line-height: 1.8;"><strong>What this sensitivity evaluates:</strong> {sens_info.get('what_it_evaluates', sensitivity_descriptions.get(sens_name, 'This sensitivity tests how changes in this parameter affect the investment performance.'))}</p>
                    <p style="margin-bottom: 12px; font-size: 1.05em; line-height: 1.8;"><strong>Range tested:</strong> From <strong>{sens_info.get('min', 'N/A')}</strong> (worst case scenario) to <strong>{sens_info.get('max', 'N/A')}</strong> (best case scenario). Base case value: <strong>{sens_info.get('base', 'N/A')}</strong>.</p>
                    <p style="margin-bottom: 0; font-size: 1.05em; line-height: 1.8;"><strong>Context:</strong> {sens_info.get('description', sensitivity_descriptions.get(sens_name, 'This parameter is an important factor in determining the investment\'s financial performance.'))}</p>
                </div>
                {table_html}
            </div>
        </div>
        ''')
    
    return "\n".join(sections)


def generate_sensitivity_html(all_sensitivities: Dict[str, pd.DataFrame], charts: List[Tuple[str, go.Figure]], 
                              base_config: BaseCaseConfig, metrics: Dict = None, output_path: str = "output/sensitivity_analysis.html"):
    """Generate HTML report with sensitivity analyses using ApexCharts."""
    base_result = compute_annual_cash_flows(base_config)
    
    # Generate summary charts if metrics provided
    summary_charts_html = ""
    if metrics:
        summary_charts_html = generate_summary_charts(metrics, base_config, all_sensitivities)
    
    # Generate ApexCharts HTML for individual sensitivities
    charts_html = generate_apexcharts_for_sensitivities(all_sensitivities, base_config)
    
    def format_currency(value):
        return f"{value:,.0f} CHF"
    
    # Create sensitivity descriptions
    sensitivity_descriptions = {
        'Occupancy Rate': 'Occupancy rate directly impacts rental income. Higher occupancy means more nights rented and more revenue, but also higher operating costs.',
        'Daily Rate': 'Average daily rate is a key revenue driver. Small changes in daily rate can significantly impact annual cash flow.',
        'Owner Nights': 'Owner nights reduce rentable nights. More personal use means less rental income, but provides personal value to owners.',
        'Seasonality': 'Engelberg experiences strong seasonality with winter peaks (ski season) and summer lows. Revenue varies significantly by month.',
        'Platform Mix': 'Different booking platforms have different fee structures. Airbnb typically charges 3% but allows higher rates, while Booking.com charges 15% commission.',
        'Cleaning Pass-Through': 'Cleaning costs can be included in management fee, passed through to guests, or borne by owners. Each approach has different cash flow implications.',
        'Management Fee': 'Property management fee is a significant operating expense. The rate directly impacts net operating income.',
        'Cleaning Cost': 'Cleaning cost per turnover affects total operating expenses. Higher costs reduce cash flow.',
        'Utilities': 'Utilities are a fixed annual cost that varies with property usage and energy prices.',
        'Maintenance Reserve': 'Maintenance reserve is set as a percentage of property value. Higher reserves provide more safety but reduce cash flow.',
        'CAPEX Events': 'Major capital expenditures (roof, heating, renovations) are one-time costs that significantly impact cash flow in specific years.',
        'Interest Rate': 'Mortgage interest rate directly affects debt service. Higher rates increase monthly payments and reduce cash flow.',
        'Amortization Rate': 'Amortization rate determines how quickly the loan is paid down. Higher rates reduce cash flow but build equity faster.',
        'Loan-to-Value': 'LTV ratio determines initial equity requirement and loan amount. Higher LTV means more debt service but less initial equity.',
        'Mortgage Type': 'Interest-only mortgages have lower payments but no equity build. Amortizing mortgages build equity but have higher payments.',
        'Variable Interest Rate': 'Variable interest rate mortgages expose the investment to interest rate risk. Rates can increase or decrease over time, significantly impacting debt service and cash flow.',
    }
    
    # Prepare KPI cards if metrics available
    kpi_cards_html = ""
    if metrics:
        base = metrics['base_case']
        kpi_cards_html = f'''
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-label">Base Case NPV</div>
                    <div class="kpi-value {'positive' if base['npv'] >= 0 else 'negative'}">{format_currency(base['npv'])}</div>
                    <div class="kpi-description">15-year discounted value</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">IRR (with sale)</div>
                    <div class="kpi-value positive">{base['irr_with_sale_pct']:.2f}%</div>
                    <div class="kpi-description">Including property sale</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">IRR (without sale)</div>
                    <div class="kpi-value {'positive' if base['irr_without_sale_pct'] >= 0 else 'negative'}">{base['irr_without_sale_pct']:.2f}%</div>
                    <div class="kpi-description">Operating returns only</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Annual Cash Flow</div>
                    <div class="kpi-value {'positive' if base_result['cash_flow_after_debt_service'] >= 0 else 'negative'}">{format_currency(base_result['cash_flow_after_debt_service'])}</div>
                    <div class="kpi-description">After debt service</div>
                </div>
            </div>
        '''
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sensitivity Analysis - Engelberg Property Investment</title>
    <!-- ApexCharts Library -->
    <script src="https://cdn.jsdelivr.net/npm/apexcharts@3.44.0"></script>
    <!-- Plotly Library for specialized financial charts -->
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <!-- Font Awesome for icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary: #1a1a2e;
            --secondary: #0f3460;
            --accent: #16213e;
            --success: #28a745;
            --danger: #dc3545;
            --warning: #ffc107;
            --info: #17a2b8;
            --gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --shadow-sm: 0 2px 4px rgba(0,0,0,0.1);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.15);
            --shadow-lg: 0 10px 40px rgba(0,0,0,0.2);
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            background: #0a0e27;
            padding: 0;
            color: #2c3e50;
            line-height: 1.6;
            overflow-x: hidden;
        }}
        
        .container {{
            max-width: 1920px;
            margin: 0 auto;
            background: white;
            min-height: 100vh;
        }}
        
        .header {{
            background: var(--gradient-1);
            color: white;
            padding: 60px 80px;
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -10%;
            width: 500px;
            height: 500px;
            background: rgba(255,255,255,0.1);
            border-radius: 50%;
            animation: float 20s infinite ease-in-out;
        }}
        
        @keyframes float {{
            0%, 100% {{ transform: translate(0, 0) rotate(0deg); }}
            50% {{ transform: translate(-30px, -30px) rotate(180deg); }}
        }}
        
        .header h1 {{
            font-size: 3.5em;
            font-weight: 700;
            margin-bottom: 15px;
            letter-spacing: -1px;
            position: relative;
            z-index: 1;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header .subtitle {{
            font-size: 1.4em;
            opacity: 0.95;
            margin-bottom: 10px;
            position: relative;
            z-index: 1;
        }}
        
        .header .meta {{
            font-size: 0.95em;
            opacity: 0.85;
            margin-top: 20px;
            position: relative;
            z-index: 1;
        }}
        
        .kpi-card {{
            background: white;
            padding: 30px;
            border-radius: 16px;
            box-shadow: var(--shadow-md);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            border-left: 4px solid var(--primary);
        }}
        
        .kpi-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient-1);
            transform: scaleX(0);
            transform-origin: left;
            transition: transform 0.3s;
        }}
        
        .kpi-card:hover {{
            transform: translateY(-8px);
            box-shadow: var(--shadow-lg);
        }}
        
        .kpi-card:hover::before {{
            transform: scaleX(1);
        }}
        
        .content {{
            padding: 50px 80px;
        }}
        
        .dashboard {{
            padding: 50px 80px;
            background: #f5f7fa;
        }}
        
        .section {{
            padding: 50px 80px;
            background: white;
            margin-bottom: 0;
        }}
        
        .section:nth-child(even) {{
            background: #f8f9fa;
        }}
        
        .section h2 {{
            font-size: 2.2em;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid var(--secondary);
            letter-spacing: -0.5px;
        }}
        
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 50px;
        }}
        
        .kpi-card {{
            background: white;
            padding: 30px;
            border-radius: 16px;
            box-shadow: var(--shadow-md);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            border-left: 4px solid var(--primary);
        }}
        
        .kpi-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient-1);
            transform: scaleX(0);
            transform-origin: left;
            transition: transform 0.3s;
        }}
        
        .kpi-card:hover {{
            transform: translateY(-8px);
            box-shadow: var(--shadow-lg);
        }}
        
        .kpi-card:hover::before {{
            transform: scaleX(1);
        }}
        
        .kpi-label {{
            font-size: 0.85em;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        
        .kpi-value {{
            font-size: 2.5em;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 8px;
            letter-spacing: -1px;
        }}
        
        .kpi-value.positive {{
            color: var(--success);
        }}
        
        .kpi-value.negative {{
            color: var(--danger);
        }}
        
        .kpi-description {{
            font-size: 0.9em;
            color: #868e96;
            margin-top: 8px;
        }}
        
        .scroll-reveal {{
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.6s ease-out;
        }}
        
        .scroll-reveal.revealed {{
            opacity: 1;
            transform: translateY(0);
        }}
        
        .intro-box {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 8px;
            border-left: 4px solid #0f3460;
            margin-bottom: 30px;
        }}
        
        .intro-box p {{
            font-size: 1em;
            color: #495057;
            margin-bottom: 15px;
            line-height: 1.7;
        }}
        
        .intro-box p:last-child {{
            margin-bottom: 0;
        }}
        
        .intro-box strong {{
            color: #1a1a2e;
            font-weight: 600;
        }}
        
        .chart-container {{
            margin: 35px 0;
            background: white;
            padding: 35px;
            border-radius: 16px;
            border: 1px solid #e8ecef;
            box-shadow: var(--shadow-md);
            transition: all 0.3s;
        }}
        
        .chart-container:hover {{
            transform: translateY(-5px);
            box-shadow: var(--shadow-lg);
        }}
        
        .chart-section-title {{
            font-size: 1.1em;
            color: #495057;
            margin-bottom: 25px;
            font-weight: 500;
            line-height: 1.6;
        }}
        
        .sensitivity-section {{
            margin-bottom: 50px;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #e8ecef;
        }}
        
        .sensitivity-section h3 {{
            color: #1a1a2e;
            font-size: 1.4em;
            font-weight: 600;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #dee2e6;
        }}
        
        .sensitivity-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 25px;
            border-left: 4px solid #0f3460;
        }}
        
        .sensitivity-card p {{
            line-height: 1.7;
            color: #495057;
            margin-bottom: 20px;
            font-size: 0.95em;
        }}
        
        .kpi-mini-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        
        .kpi-mini-card {{
            background: white;
            padding: 18px;
            border-radius: 6px;
            border: 1px solid #e8ecef;
            text-align: center;
        }}
        
        .kpi-mini-label {{
            font-size: 0.75em;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            font-weight: 600;
        }}
        
        .kpi-mini-value {{
            font-size: 1.3em;
            font-weight: 700;
        }}
        
        .kpi-mini-value.positive {{
            color: #28a745;
        }}
        
        .kpi-mini-value.negative {{
            color: #dc3545;
        }}
        
        .kpi-mini-value.neutral {{
            color: #6c757d;
        }}
        
        .footer {{
            background: var(--primary);
            color: white;
            padding: 40px 80px;
            text-align: center;
        }}
        
        .footer p {{
            font-size: 1.1em;
            margin-bottom: 10px;
        }}
        
        .footer p:last-child {{
            opacity: 0.8;
            font-size: 0.9em;
        }}
        
        .toc {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 40px;
            border: 1px solid #e8ecef;
        }}
        
        .toc h3 {{
            font-size: 1.1em;
            color: #1a1a2e;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        
        .toc ul {{
            list-style: none;
            columns: 2;
            column-gap: 30px;
        }}
        
        .toc li {{
            margin-bottom: 8px;
            font-size: 0.9em;
        }}
        
        .toc a {{
            color: #0f3460;
            text-decoration: none;
        }}
        
        .toc a:hover {{
            text-decoration: underline;
        }}
        
        @media (max-width: 768px) {{
            .content {{
                padding: 30px 20px;
            }}
            
            .header {{
                padding: 30px 20px;
            }}
            
            .kpi-grid {{
                grid-template-columns: 1fr;
            }}
            
            .toc ul {{
                columns: 1;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-chart-line"></i> Sensitivity Analysis</h1>
            <div class="subtitle">Engelberg Property Investment - Comprehensive Scenario Analysis</div>
            <div class="meta">Generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}</div>
        </div>
        
        <div class="content">
            <!-- Executive Summary with KPIs -->
            <div class="section">
                <h2>Executive Summary</h2>
                {kpi_cards_html}
                <div class="intro-box">
                    <p>
                        This sensitivity analysis examines how key variables impact the financial performance of the Engelberg property investment. 
                        Each scenario tests different assumptions to understand the range of possible outcomes and identify the most critical factors 
                        affecting cash flow and returns.
                    </p>
                    <p>
                        <strong>Base Case Parameters:</strong> Purchase price CHF {format_currency(base_config.financing.purchase_price)}, 
                        {base_config.financing.num_owners} owners, {base_config.rental.occupancy_rate*100:.0f}% occupancy, 
                        CHF {base_config.rental.average_daily_rate:.0f} average daily rate. 
                        Base case annual cash flow: <strong>{format_currency(base_result['cash_flow_after_debt_service'])}</strong>.
                    </p>
                </div>
            </div>
            
            <!-- Summary Charts Section -->
            {f'''
            <div class="section">
                <h2>Sensitivity Impact Analysis</h2>
                <div class="chart-section-title">
                    The following visualizations provide a comprehensive overview of how different sensitivity factors impact the investment. 
                    The first chart shows annual cash-on-cash (unlevered) efficiency - how much money you need to put in or can make per year. 
                    Subsequent tornado charts show NPV and IRR impacts, and waterfall charts 
                    illustrate cumulative impacts across all sensitivity factors.
                </div>
                {summary_charts_html}
            </div>
            ''' if summary_charts_html else ''}
            
            <!-- Table of Contents -->
            <div class="section">
                <div class="toc">
                    <h3>Analysis Sections</h3>
                    <ul>
                        {''.join([f'<li><a href="#sens-{name.lower().replace(" ", "-").replace("/", "-")}">{name}</a></li>' for name in all_sensitivities.keys()])}
                    </ul>
                </div>
            </div>
            
            <!-- Detailed Sensitivities with Charts Only -->
            <div class="section">
                <h2>Detailed Sensitivity Analyses</h2>
                {generate_detailed_sensitivity_sections_with_charts(all_sensitivities, sensitivity_descriptions, base_config)}
            </div>
        </div>
        
        <div class="footer">
            <p>Engelberg Property Investment - Sensitivity Analysis</p>
            <p>This sensitivity analysis was generated automatically by the Engelberg Property Investment Simulation</p>
            <p style="margin-top: 8px; font-size: 0.9em; opacity: 0.8;">For detailed numerical data, please refer to the Excel export file.</p>
        </div>
    </div>
    
    <script>
        // Advanced JavaScript for interactivity and animations
        (function() {{
            // Scroll reveal animation
            const observerOptions = {{
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            }};
            
            const observer = new IntersectionObserver(function(entries) {{
                entries.forEach(entry => {{
                    if (entry.isIntersecting) {{
                        entry.target.classList.add('revealed');
                        observer.unobserve(entry.target);
                    }}
                }});
            }}, observerOptions);
            
            // Observe all scroll-reveal elements
            document.querySelectorAll('.scroll-reveal').forEach(el => {{
                observer.observe(el);
            }});
            
            // Smooth scroll for anchor links
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
                anchor.addEventListener('click', function (e) {{
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {{
                        target.scrollIntoView({{
                            behavior: 'smooth',
                            block: 'start'
                        }});
                    }}
                }});
            }});
            
            // Add fade-in animation to KPI cards
            document.querySelectorAll('.kpi-card').forEach((card, index) => {{
                card.style.animationDelay = `${{index * 0.1}}s`;
                card.classList.add('scroll-reveal');
            }});
        }})();
    </script>
</body>
</html>
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"[+] HTML report generated: {output_path}")


def main():
    """Main function to run sensitivity analysis."""
    print("=" * 70)
    print("Sensitivity Analysis - Engelberg Property Investment")
    print("=" * 70)
    print()
    
    # Load base case configuration
    # IMPORTANT: This must use the SAME base case as run_base_case.py
    # All sensitivity analyses reference this single source of truth
    print("[*] Loading base case configuration...")
    base_config = create_base_case_config()
    base_result = compute_annual_cash_flows(base_config)
    
    print(f"[*] Base case cash flow: {base_result['cash_flow_after_debt_service']:,.0f} CHF/year")
    print()
    
    # Run all sensitivity analyses
    print("[*] Running sensitivity analyses...")
    all_sensitivities = {}
    
    print("  - Occupancy rate (30-70%)...")
    all_sensitivities['Occupancy Rate'] = sensitivity_occupancy_rate(base_config)
    
    print("  - Average daily rate (200-400 CHF)...")
    all_sensitivities['Daily Rate'] = sensitivity_daily_rate(base_config)
    
    print("  - Owner nights (0-150)...")
    all_sensitivities['Owner Nights'] = sensitivity_owner_nights(base_config)
    
    print("  - Seasonality curve...")
    all_sensitivities['Seasonality'] = sensitivity_seasonality(base_config)
    
    print("  - Platform mix (Airbnb vs Booking)...")
    all_sensitivities['Platform Mix'] = sensitivity_platform_mix(base_config)
    
    print("  - Cleaning fee pass-through...")
    all_sensitivities['Cleaning Pass-Through'] = sensitivity_cleaning_pass_through(base_config)
    
    print("  - Property management fee (20-35%)...")
    all_sensitivities['Management Fee'] = sensitivity_property_management_fee(base_config)
    
    print("  - Cleaning cost per turnover...")
    all_sensitivities['Cleaning Cost'] = sensitivity_cleaning_cost(base_config)
    
    print("  - Utilities (2000-4000 CHF)...")
    all_sensitivities['Utilities'] = sensitivity_utilities(base_config)
    
    print("  - Maintenance reserve (0.5-2%)...")
    all_sensitivities['Maintenance Reserve'] = sensitivity_maintenance_reserve(base_config)
    
    print("  - CAPEX events...")
    all_sensitivities['CAPEX Events'] = sensitivity_capex_events(base_config)
    
    print("  - Interest rate (1.2-3.5%)...")
    all_sensitivities['Interest Rate'] = sensitivity_interest_rate(base_config)
    
    print("  - Variable interest rate risk...")
    all_sensitivities['Variable Interest Rate'] = sensitivity_variable_interest_rate(base_config)
    
    print("  - Amortization rate (1-2%)...")
    all_sensitivities['Amortization Rate'] = sensitivity_amortization_rate(base_config)
    
    print("  - Loan-to-value (60-80%)...")
    all_sensitivities['Loan-to-Value'] = sensitivity_ltv(base_config)
    
    print("  - Mortgage type (interest-only vs amortizing)...")
    all_sensitivities['Mortgage Type'] = sensitivity_mortgage_type(base_config)
    
    print()
    
    # Excel export disabled - user only uses HTML reports
    # print("[*] Exporting results to Excel...")
    # export_sensitivities_to_excel(all_sensitivities)
    
    # Ensure output directory exists
    import os
    os.makedirs("output", exist_ok=True)
    
    # Calculate NPV and IRR metrics for summary charts
    print("[*] Calculating NPV and IRR metrics...")
    metrics = calculate_sensitivity_metrics(all_sensitivities, base_config)
    
    # Create charts (kept for compatibility)
    print("[*] Generating charts...")
    charts = create_sensitivity_charts(all_sensitivities, base_config)
    
    # Generate HTML report
    print("[*] Generating HTML report...")
    generate_sensitivity_html(all_sensitivities, charts, base_config, metrics)
    
    print()
    print("=" * 70)
    print("[+] Sensitivity analysis complete!")
    print("=" * 70)
    # print(f"[+] Excel file: sensitivity_analysis.xlsx")  # Excel export disabled
    print(f"[+] HTML report: output/sensitivity_analysis.html")
    print("=" * 70)


if __name__ == "__main__":
    main()


