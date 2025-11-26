"""
Sensitivity Analysis Script for Engelberg Property Investment
Analyzes various scenarios and generates comprehensive Excel and HTML reports
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from scipy.interpolate import interp1d
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

# Professional color palette for charts
CHART_COLORS = {
    'primary': '#1a1a2e',
    'secondary': '#0f3460',
    'success': '#2ecc71',
    'danger': '#e74c3c',
    'warning': '#f39c12',
    'info': '#3498db',
    'purple': '#9b59b6',
    'orange': '#e67e22',
    'teal': '#1abc9c',
    'gradient_start': '#667eea',
    'gradient_end': '#764ba2',
}

# Professional chart template
def get_chart_template():
    """Returns a professional chart template configuration."""
    return {
        'font': {
            'family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
            'size': 12,
            'color': '#2c3e50'
        },
        'title_font': {
            'size': 18,
            'color': '#1a1a2e',
            'family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto'
        },
        'title_x': 0.05,
        'title_xanchor': 'left',
        'title_pad': {'t': 10, 'b': 20},
        'xaxis': {
            'showgrid': True,
            'gridcolor': '#e8ecef',
            'gridwidth': 1,
            'showline': True,
            'linecolor': '#dee2e6',
            'linewidth': 1,
            'title': {'font': {'size': 13, 'color': '#495057'}}
        },
        'yaxis': {
            'showgrid': True,
            'gridcolor': '#e8ecef',
            'gridwidth': 1,
            'showline': True,
            'linecolor': '#dee2e6',
            'linewidth': 1,
            'title': {'font': {'size': 13, 'color': '#495057'}}
        },
        'plot_bgcolor': '#ffffff',
        'paper_bgcolor': '#ffffff',
        'hovermode': 'closest',
        'hoverlabel': {
            'bgcolor': 'rgba(26, 26, 46, 0.9)',
            'font_size': 12,
            'font_family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto',
            'font_color': '#ffffff',
            'bordercolor': '#1a1a2e'
        },
        'legend': {
            'bgcolor': 'rgba(255, 255, 255, 0.9)',
            'bordercolor': '#dee2e6',
            'borderwidth': 1,
            'font': {'size': 11, 'color': '#495057'},
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'right',
            'x': 1
        },
        'margin': {'l': 60, 'r': 20, 't': 70, 'b': 50}
    }


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
        fixed_expenses = base_result['insurance'] + base_result['nubbing_costs'] + base_result['electricity_internet'] + base_result['maintenance_reserve']
        
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
            result['nubbing_costs'] +
            result['electricity_internet'] +
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
        nubbing_costs_annual=base_config.expenses.nubbing_costs_annual,
        electricity_internet_annual=base_config.expenses.electricity_internet_annual,
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
        result_pass_through['nubbing_costs'] +
        result_pass_through['electricity_internet'] +
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
            nubbing_costs_annual=base_config.expenses.nubbing_costs_annual,
            electricity_internet_annual=base_config.expenses.electricity_internet_annual,
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
            nubbing_costs_annual=base_config.expenses.nubbing_costs_annual,
            electricity_internet_annual=base_config.expenses.electricity_internet_annual,
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


def sensitivity_utilities(base_config: BaseCaseConfig, min_total: float = 2000, max_total: float = 4000, steps: int = 9) -> pd.DataFrame:
    """Analyze sensitivity to total utilities cost (nubbing + electricity/internet, 2000 to 4000 CHF)."""
    results = []
    total_utilities_range = np.linspace(min_total, max_total, steps)
    
    # Split proportionally: 2/3 nubbing, 1/3 electricity/internet (based on base case 2000/1000)
    base_nubbing = base_config.expenses.nubbing_costs_annual
    base_electricity = base_config.expenses.electricity_internet_annual
    base_total = base_nubbing + base_electricity
    nubbing_ratio = base_nubbing / base_total if base_total > 0 else 2/3
    electricity_ratio = base_electricity / base_total if base_total > 0 else 1/3
    
    for total_utilities in total_utilities_range:
        nubbing_costs = total_utilities * nubbing_ratio
        electricity_internet = total_utilities * electricity_ratio
        
        new_expenses = ExpenseParams(
            property_management_fee_rate=base_config.expenses.property_management_fee_rate,
            cleaning_cost_per_stay=base_config.expenses.cleaning_cost_per_stay,
            average_length_of_stay=base_config.expenses.average_length_of_stay,
            tourist_tax_per_person_per_night=base_config.expenses.tourist_tax_per_person_per_night,
            avg_guests_per_night=base_config.expenses.avg_guests_per_night,
            insurance_annual=base_config.expenses.insurance_annual,
            nubbing_costs_annual=nubbing_costs,
            electricity_internet_annual=electricity_internet,
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
            'Total Utilities Annual (CHF)': total_utilities,
            'Nubbing Costs (CHF)': nubbing_costs,
            'Electricity & Internet (CHF)': electricity_internet,
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
            nubbing_costs_annual=base_config.expenses.nubbing_costs_annual,
            electricity_internet_annual=base_config.expenses.electricity_internet_annual,
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


def calculate_npv_irr_for_config(config: BaseCaseConfig, discount_rate: float = 0.03) -> Dict[str, float]:
    """
    Calculate NPV and IRR for a given configuration.
    
    Args:
        config: BaseCaseConfig to analyze
        discount_rate: Discount rate for NPV calculation (default 3% - realistic for real estate)
    
    Returns:
        Dictionary with NPV and IRR metrics
    """
    # Get initial equity per owner (calculate once, reuse)
    initial_result = compute_annual_cash_flows(config)
    initial_equity = initial_result['equity_per_owner']
    
    # Calculate 15-year projection
    projection = compute_15_year_projection(config, start_year=2026, inflation_rate=0.02, property_appreciation_rate=0.025)  # 2.5% property appreciation per year
    
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


def generate_top_toolbar(report_title: str, back_link: str = "index.html", subtitle: str = "") -> str:
    """
    Generate top toolbar HTML with navigation and actions.
    
    Args:
        report_title: Title of the report
        back_link: Link to home/index page
        subtitle: Optional subtitle
    
    Returns:
        HTML string for top toolbar
    """
    return f'''
    <div class="top-toolbar">
        <div class="toolbar-left">
            <a href="{back_link}" class="toolbar-btn" title="Back to Home">
                <i class="fas fa-home"></i> <span class="toolbar-btn-text">Home</span>
            </a>
        </div>
        <div class="toolbar-center">
            <h1 class="toolbar-title">{report_title}</h1>
            {f'<p class="toolbar-subtitle">{subtitle}</p>' if subtitle else ''}
        </div>
        <div class="toolbar-right">
            <!-- Future toolbar actions can be added here -->
        </div>
    </div>
    '''


def generate_sidebar_navigation(sections: List[Dict[str, str]]) -> str:
    """
    Generate sidebar navigation HTML.
    
    Args:
        sections: List of dictionaries with 'id', 'title', and optionally 'icon'
    
    Returns:
        HTML string for sidebar navigation
    """
    nav_items = []
    for section in sections:
        section_id = section.get('id', '')
        section_title = section.get('title', '')
        section_icon = section.get('icon', 'fas fa-circle')
        
        nav_items.append(f'''
            <li>
                <a href="#{section_id}" class="sidebar-item" data-section="{section_id}">
                    <i class="{section_icon}"></i>
                    <span class="sidebar-item-text">{section_title}</span>
                </a>
            </li>
        ''')
    
    return f'''
    <nav class="sidebar">
        <div class="sidebar-header">
            <h3><i class="fas fa-bars"></i> Navigation</h3>
        </div>
        <ul class="sidebar-nav">
            {''.join(nav_items)}
        </ul>
    </nav>
    '''


def generate_shared_layout_css() -> str:
    """
    Generate shared CSS for sidebar and toolbar layout.
    
    Returns:
        CSS string for layout components
    """
    return '''
        /* Layout Container */
        .layout-container {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            background: #f5f7fa;
        }
        
        /* Top Toolbar */
        .top-toolbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: var(--gradient-1);
            color: white;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            z-index: 1000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }
        
        .toolbar-left, .toolbar-right {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .toolbar-center {
            flex: 1;
            text-align: center;
        }
        
        .toolbar-title {
            font-size: 1.3em;
            font-weight: 700;
            margin: 0;
            color: white;
        }
        
        .toolbar-subtitle {
            font-size: 0.85em;
            margin: 0;
            opacity: 0.9;
        }
        
        .toolbar-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: rgba(255,255,255,0.2);
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-size: 0.9em;
            font-weight: 600;
            transition: all 0.2s ease;
            border: 1px solid rgba(255,255,255,0.3);
        }
        
        .toolbar-btn:hover {
            background: rgba(255,255,255,0.3);
            transform: translateY(-1px);
        }
        
        /* Sidebar */
        .sidebar {
            position: fixed;
            left: 0;
            top: 60px;
            width: 250px;
            height: calc(100vh - 60px);
            background: white;
            box-shadow: 2px 0 8px rgba(0,0,0,0.1);
            overflow-y: auto;
            z-index: 999;
            transition: transform 0.3s ease;
        }
        
        .sidebar-header {
            padding: 20px;
            background: var(--primary);
            color: white;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .sidebar-header h3 {
            font-size: 1.1em;
            font-weight: 600;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .sidebar-nav {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .sidebar-nav li {
            margin: 0;
        }
        
        .sidebar-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 15px 20px;
            color: #495057;
            text-decoration: none;
            border-left: 3px solid transparent;
            transition: all 0.2s ease;
            font-size: 0.9em;
        }
        
        .sidebar-item:hover {
            background: #f8f9fa;
            color: var(--primary);
            border-left-color: var(--primary);
        }
        
        .sidebar-item.active {
            background: #e7f3ff;
            color: var(--primary);
            border-left-color: var(--primary);
            font-weight: 600;
        }
        
        .sidebar-item i {
            width: 20px;
            text-align: center;
            font-size: 0.9em;
        }
        
        .sidebar-item-text {
            flex: 1;
        }
        
        /* Main Content */
        .main-content {
            margin-left: 250px;
            margin-top: 60px;
            padding: 30px 40px;
            background: white;
            min-height: calc(100vh - 60px);
        }
        
        /* Section IDs for navigation */
        .section {
            scroll-margin-top: 80px;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .sidebar {
                transform: translateX(-100%);
                width: 250px;
            }
            
            .sidebar.open {
                transform: translateX(0);
            }
            
            .main-content {
                margin-left: 0;
            }
            
            .toolbar-btn-text {
                display: none;
            }
            
            .toolbar-title {
                font-size: 1.1em;
            }
        }
        
        /* Scrollbar styling for sidebar */
        .sidebar::-webkit-scrollbar {
            width: 6px;
        }
        
        .sidebar::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        .sidebar::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 3px;
        }
        
        .sidebar::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
    '''


def generate_shared_layout_js() -> str:
    """
    Generate shared JavaScript for sidebar and toolbar functionality.
    
    Returns:
        JavaScript string for layout interactions
    """
    return '''
    <script>
        (function() {
            // Smooth scroll to sections
            document.querySelectorAll('.sidebar-item').forEach(item => {
                item.addEventListener('click', function(e) {
                    e.preventDefault();
                    const targetId = this.getAttribute('href').substring(1);
                    const targetElement = document.getElementById(targetId);
                    
                    if (targetElement) {
                        const offset = 80; // Account for fixed toolbar
                        const elementPosition = targetElement.getBoundingClientRect().top;
                        const offsetPosition = elementPosition + window.pageYOffset - offset;
                        
                        window.scrollTo({
                            top: offsetPosition,
                            behavior: 'smooth'
                        });
                        
                        // Update active state
                        updateActiveSection(targetId);
                    }
                });
            });
            
            // Update active section based on scroll position
            function updateActiveSection(activeId) {
                document.querySelectorAll('.sidebar-item').forEach(item => {
                    item.classList.remove('active');
                    if (item.getAttribute('data-section') === activeId) {
                        item.classList.add('active');
                    }
                });
            }
            
            // Intersection Observer for auto-highlighting active section
            const observerOptions = {
                root: null,
                rootMargin: '-20% 0px -70% 0px',
                threshold: 0
            };
            
            const observer = new IntersectionObserver(function(entries) {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const sectionId = entry.target.id;
                        if (sectionId) {
                            updateActiveSection(sectionId);
                        }
                    }
                });
            }, observerOptions);
            
            // Observe all sections with IDs
            document.querySelectorAll('.section[id], h2[id], h3[id]').forEach(section => {
                observer.observe(section);
            });
            
            // Mobile sidebar toggle (if needed)
            const sidebar = document.querySelector('.sidebar');
            if (window.innerWidth <= 768) {
                // Add mobile menu toggle if needed
                // This can be enhanced with a hamburger menu button
            }
            
            // Handle window resize
            window.addEventListener('resize', function() {
                if (window.innerWidth > 768) {
                    sidebar.classList.remove('open');
                }
            });
        })();
    </script>
    '''


def calculate_break_even_points(all_sensitivities: Dict[str, pd.DataFrame], base_config: BaseCaseConfig) -> Dict[str, Dict[str, any]]:
    """
    Calculate break-even points for each sensitivity factor.
    Break-even is defined as the parameter value where cash flow after debt service = 0.
    
    Returns:
        Dictionary mapping sensitivity name to break-even information:
        {
            'break_even_value': parameter value at break-even,
            'base_case_value': current base case value,
            'margin_to_break_even': difference between base and break-even,
            'margin_pct': margin as percentage of base,
            'is_above_break_even': True if base case is above break-even (positive cash flow)
        }
    """
    
    base_result = compute_annual_cash_flows(base_config)
    base_cf = base_result['cash_flow_after_debt_service']
    
    break_even_results = {}
    
    # Parameters that can have break-even points
    break_even_params = [
        'Occupancy Rate',
        'Daily Rate', 
        'Interest Rate',
        'Loan-to-Value',
        'Management Fee',
        'Owner Nights'
    ]
    
    for sens_name in break_even_params:
        if sens_name not in all_sensitivities:
            continue
            
        df = all_sensitivities[sens_name]
        if 'Cash Flow After Debt (CHF)' not in df.columns:
            continue
        
        param_col = df.columns[0]  # First column is the parameter
        param_values = df[param_col].values
        cash_flows = df['Cash Flow After Debt (CHF)'].values
        
        # Check if break-even exists in the tested range
        min_cf = cash_flows.min()
        max_cf = cash_flows.max()
        
        # Break-even exists if cash flow crosses zero
        if min_cf <= 0 <= max_cf:
            # Use interpolation to find exact break-even point
            try:
                # Sort by parameter value for interpolation
                sorted_indices = np.argsort(param_values)
                sorted_params = param_values[sorted_indices]
                sorted_cfs = cash_flows[sorted_indices]
                
                # Create interpolation function
                interp_func = interp1d(sorted_cfs, sorted_params, kind='linear', 
                                     bounds_error=False, fill_value='extrapolate')
                break_even_value = float(interp_func(0))
                
                # Get base case parameter value
                # Note: base_result was already calculated at the start of the function
                if sens_name == 'Occupancy Rate':
                    # Get overall occupancy rate from results
                    base_param = base_result.get('overall_occupancy_rate', base_config.rental.occupancy_rate) * 100
                elif sens_name == 'Daily Rate':
                    # Get weighted average daily rate from results
                    base_param = base_result.get('average_daily_rate', 200.0)
                elif sens_name == 'Interest Rate':
                    base_param = base_config.financing.interest_rate * 100
                elif sens_name == 'Loan-to-Value':
                    base_param = base_config.financing.ltv * 100
                elif sens_name == 'Management Fee':
                    base_param = base_config.expenses.property_management_fee_rate * 100
                elif sens_name == 'Owner Nights':
                    base_param = base_config.rental.owner_nights_per_person * base_config.financing.num_owners
                else:
                    base_param = None
                
                if base_param is not None:
                    margin = base_param - break_even_value
                    margin_pct = (margin / break_even_value * 100) if break_even_value != 0 else 0
                    is_above = base_param > break_even_value
                    
                    break_even_results[sens_name] = {
                        'break_even_value': break_even_value,
                        'base_case_value': base_param,
                        'margin_to_break_even': margin,
                        'margin_pct': margin_pct,
                        'is_above_break_even': is_above,
                        'break_even_exists': True
                    }
                else:
                    break_even_results[sens_name] = {
                        'break_even_exists': False,
                        'reason': 'Base case parameter not found'
                    }
            except Exception as e:
                break_even_results[sens_name] = {
                    'break_even_exists': False,
                    'reason': f'Interpolation error: {str(e)}'
                }
        else:
            # Break-even doesn't exist in tested range
            if min_cf > 0:
                status = 'All tested values positive'
            else:
                status = 'All tested values negative'
            
            break_even_results[sens_name] = {
                'break_even_exists': False,
                'reason': status,
                'min_cf_tested': min_cf,
                'max_cf_tested': max_cf
            }
    
    return break_even_results


def calculate_sensitivity_metrics(all_sensitivities: Dict[str, pd.DataFrame], base_config: BaseCaseConfig) -> Dict[str, Dict[str, float]]:
    """
    Calculate NPV and IRR impact for each sensitivity by comparing best/worst scenarios to base case.
    For each sensitivity, calculates the actual NPV/IRR for best and worst case scenarios.
    
    Returns:
        Dictionary with base case metrics and sensitivity impacts (with both positive and negative impacts)
    """
    discount_rate = 0.03  # 3% discount rate for NPV (realistic for real estate investments)
    
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
            
            # Get parameter values from dataframe
            param_col = df.columns[0]
            best_param_val = df.loc[best_idx, param_col]
            worst_param_val = df.loc[worst_idx, param_col]
            
            sensitivity_impacts[sens_name] = {
                'npv_best_impact': npv_best_impact,
                'npv_worst_impact': npv_worst_impact,
                'irr_best_impact': irr_best_impact,
                'irr_worst_impact': irr_worst_impact,
                'best_cf': best_cf,
                'worst_cf': worst_cf,
                'best_param_value': best_param_val,  # Store actual parameter value for best case
                'worst_param_value': worst_param_val  # Store actual parameter value for worst case
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
                'worst_cf': df.loc[worst_idx, 'Cash Flow After Debt (CHF)'],
                'best_param_value': best_param_val,  # Store actual parameter value for best case
                'worst_param_value': worst_param_val  # Store actual parameter value for worst case
            }
    
    # Calculate ranking metrics
    ranking_data = []
    for sens_name, impacts in sensitivity_impacts.items():
        # Calculate absolute impact range
        npv_range = abs(impacts['npv_best_impact']) + abs(impacts['npv_worst_impact'])
        irr_range = abs(impacts['irr_best_impact']) + abs(impacts['irr_worst_impact'])
        
        # Composite risk score (weighted combination)
        # Higher score = more impactful/risky
        composite_score = (
            abs(impacts['npv_best_impact']) * 0.4 +  # NPV impact weight
            abs(impacts['npv_worst_impact']) * 0.4 +
            abs(impacts['irr_best_impact']) * 0.1 +  # IRR impact weight
            abs(impacts['irr_worst_impact']) * 0.1
        )
        
        ranking_data.append({
            'sensitivity': sens_name,
            'npv_range': npv_range,
            'irr_range': irr_range,
            'composite_score': composite_score,
            'npv_best_impact': impacts['npv_best_impact'],
            'npv_worst_impact': impacts['npv_worst_impact'],
            'irr_best_impact': impacts['irr_best_impact'],
            'irr_worst_impact': impacts['irr_worst_impact']
        })
    
    # Sort by composite score (highest first)
    ranking_data.sort(key=lambda x: x['composite_score'], reverse=True)
    
    # Add ranks
    for i, item in enumerate(ranking_data):
        item['rank'] = i + 1
    
    # Calculate statistical measures for each sensitivity
    statistical_summary = calculate_statistical_summary(all_sensitivities, base_config, base_metrics)
    
    # Calculate elasticity metrics
    elasticity_metrics = calculate_elasticity_metrics(all_sensitivities, base_config, base_metrics)
    
    return {
        'base_case': base_metrics,
        'sensitivities': sensitivity_impacts,
        'ranking': ranking_data,
        'statistics': statistical_summary,
        'elasticity': elasticity_metrics
    }


def create_scenario_configs(base_config: BaseCaseConfig, all_sensitivities: Dict[str, pd.DataFrame], 
                            metrics: Dict) -> Dict[str, BaseCaseConfig]:
    """
    Create scenario configurations (Optimistic, Pessimistic, Base).
    
    Args:
        base_config: Base case configuration
        all_sensitivities: Dictionary of sensitivity DataFrames
        metrics: Metrics dictionary with ranking
    
    Returns:
        Dictionary mapping scenario name to configuration
    """
    scenarios = {'Base': base_config}
    
    if 'ranking' not in metrics or not metrics['ranking']:
        return scenarios
    
    # Get top 5 parameters by impact
    top_5_params = metrics['ranking'][:5]
    
    # Create optimistic scenario (best values for top 5 parameters)
    optimistic_config = base_config
    for item in top_5_params:
        sens_name = item['sensitivity']
        if sens_name not in all_sensitivities:
            continue
        
        df = all_sensitivities[sens_name]
        if 'Cash Flow After Debt (CHF)' not in df.columns:
            continue
        
        # Find best case parameter value
        best_idx = df['Cash Flow After Debt (CHF)'].idxmax()
        param_col = df.columns[0]
        best_param_val = df.loc[best_idx, param_col]
        
        # Apply best case value
        if sens_name == 'Occupancy Rate':
            best_occ = best_param_val / 100.0 if best_param_val > 1.0 else best_param_val
            optimistic_config = apply_sensitivity(optimistic_config, occupancy=best_occ)
        elif sens_name == 'Daily Rate':
            optimistic_config = apply_sensitivity(optimistic_config, daily_rate=best_param_val)
        elif sens_name == 'Interest Rate':
            best_int = best_param_val / 100.0 if best_param_val > 1.0 else best_param_val
            optimistic_config = apply_sensitivity(optimistic_config, interest_rate=best_int)
        elif sens_name == 'Management Fee':
            best_mgmt = best_param_val / 100.0 if best_param_val > 1.0 else best_param_val
            optimistic_config = apply_sensitivity(optimistic_config, management_fee=best_mgmt)
        elif sens_name == 'Loan-to-Value':
            best_ltv = best_param_val / 100.0 if best_param_val > 1.0 else best_param_val
            new_financing = FinancingParams(
                purchase_price=optimistic_config.financing.purchase_price,
                ltv=best_ltv,
                interest_rate=optimistic_config.financing.interest_rate,
                amortization_rate=optimistic_config.financing.amortization_rate,
                num_owners=optimistic_config.financing.num_owners
            )
            optimistic_config = BaseCaseConfig(
                financing=new_financing,
                rental=optimistic_config.rental,
                expenses=optimistic_config.expenses
            )
    
    scenarios['Optimistic'] = optimistic_config
    
    # Create pessimistic scenario (worst values for top 5 parameters)
    pessimistic_config = base_config
    for item in top_5_params:
        sens_name = item['sensitivity']
        if sens_name not in all_sensitivities:
            continue
        
        df = all_sensitivities[sens_name]
        if 'Cash Flow After Debt (CHF)' not in df.columns:
            continue
        
        # Find worst case parameter value
        worst_idx = df['Cash Flow After Debt (CHF)'].idxmin()
        param_col = df.columns[0]
        worst_param_val = df.loc[worst_idx, param_col]
        
        # Apply worst case value
        if sens_name == 'Occupancy Rate':
            worst_occ = worst_param_val / 100.0 if worst_param_val > 1.0 else worst_param_val
            pessimistic_config = apply_sensitivity(pessimistic_config, occupancy=worst_occ)
        elif sens_name == 'Daily Rate':
            pessimistic_config = apply_sensitivity(pessimistic_config, daily_rate=worst_param_val)
        elif sens_name == 'Interest Rate':
            worst_int = worst_param_val / 100.0 if worst_param_val > 1.0 else worst_param_val
            pessimistic_config = apply_sensitivity(pessimistic_config, interest_rate=worst_int)
        elif sens_name == 'Management Fee':
            worst_mgmt = worst_param_val / 100.0 if worst_param_val > 1.0 else worst_param_val
            pessimistic_config = apply_sensitivity(pessimistic_config, management_fee=worst_mgmt)
        elif sens_name == 'Loan-to-Value':
            worst_ltv = worst_param_val / 100.0 if worst_param_val > 1.0 else worst_param_val
            new_financing = FinancingParams(
                purchase_price=pessimistic_config.financing.purchase_price,
                ltv=worst_ltv,
                interest_rate=pessimistic_config.financing.interest_rate,
                amortization_rate=pessimistic_config.financing.amortization_rate,
                num_owners=pessimistic_config.financing.num_owners
            )
            pessimistic_config = BaseCaseConfig(
                financing=new_financing,
                rental=pessimistic_config.rental,
                expenses=pessimistic_config.expenses
            )
    
    scenarios['Pessimistic'] = pessimistic_config
    
    return scenarios


def analyze_scenarios(scenario_configs: Dict[str, BaseCaseConfig]) -> pd.DataFrame:
    """
    Analyze scenarios and return comparison DataFrame.
    
    Args:
        scenario_configs: Dictionary mapping scenario name to configuration
    
    Returns:
        DataFrame with scenario comparison
    """
    results = []
    discount_rate = 0.03
    
    for scenario_name, config in scenario_configs.items():
        # Calculate annual cash flows
        annual_result = compute_annual_cash_flows(config)
        
        # Calculate 15-year projection
        projection = compute_15_year_projection(config, start_year=2026, inflation_rate=0.02, property_appreciation_rate=0.025)
        
        # Calculate NPV and IRR
        npv_irr = calculate_npv_irr_for_config(config, discount_rate)
        
        results.append({
            'Scenario': scenario_name,
            'Annual Cash Flow (CHF)': annual_result['cash_flow_after_debt_service'],
            'NPV (CHF)': npv_irr['npv'],
            'IRR (%)': npv_irr['irr_with_sale_pct'],
            'IRR without Sale (%)': npv_irr['irr_without_sale_pct'],
            'Cap Rate (%)': annual_result['cap_rate_pct'],
            'Cash-on-Cash Return (%)': annual_result['cash_on_cash_return_pct'],
            'Debt Coverage Ratio': annual_result['debt_coverage_ratio'],
            'Initial Equity per Owner (CHF)': annual_result['equity_per_owner'],
            'Total Cash Flow 15Y (CHF)': sum(year['cash_flow_per_owner'] for year in projection),
            'Sale Proceeds per Owner (CHF)': npv_irr['sale_proceeds']
        })
    
    return pd.DataFrame(results)


def generate_scenario_analysis_html(scenario_configs: Dict[str, BaseCaseConfig], 
                                   scenario_results: pd.DataFrame) -> str:
    """
    Generate HTML section for scenario analysis.
    
    Args:
        scenario_configs: Dictionary of scenario configurations
        scenario_results: DataFrame from analyze_scenarios()
    
    Returns:
        HTML string for scenario analysis section
    """
    def format_currency(value):
        return f"{value:,.0f} CHF"
    
    def format_percent(value):
        return f"{value:.2f}%"
    
    # Create comparison table
    table_rows = []
    for _, row in scenario_results.iterrows():
        scenario_name = row['Scenario']
        color = '#28a745' if scenario_name == 'Optimistic' else '#dc3545' if scenario_name == 'Pessimistic' else '#6c757d'
        
        table_rows.append(f'''
            <tr style="background: {color}15;">
                <td><strong style="color: {color};">{scenario_name}</strong></td>
                <td>{format_currency(row['Annual Cash Flow (CHF)'])}</td>
                <td>{format_currency(row['NPV (CHF)'])}</td>
                <td>{format_percent(row['IRR (%)'])}</td>
                <td>{format_percent(row['IRR without Sale (%)'])}</td>
                <td>{format_percent(row['Cap Rate (%)'])}</td>
                <td>{format_percent(row['Cash-on-Cash Return (%)'])}</td>
                <td>{row['Debt Coverage Ratio']:.2f}</td>
            </tr>
        ''')
    
    # Create comparison charts
    fig_comparison = go.Figure()
    
    scenarios = scenario_results['Scenario'].tolist()
    npv_values = scenario_results['NPV (CHF)'].tolist()
    irr_values = scenario_results['IRR (%)'].tolist()
    
    fig_comparison.add_trace(go.Bar(
        name='NPV (CHF)',
        x=scenarios,
        y=npv_values,
        yaxis='y',
        offsetgroup=1,
        marker_color=['#28a745', '#6c757d', '#dc3545']
    ))
    
    fig_comparison.add_trace(go.Bar(
        name='IRR (%)',
        x=scenarios,
        y=irr_values,
        yaxis='y2',
        offsetgroup=2,
        marker_color=['#28a745', '#6c757d', '#dc3545']
    ))
    
    fig_comparison.update_layout(
        title='Scenario Comparison: NPV and IRR',
        xaxis_title='Scenario',
        yaxis=dict(title='NPV (CHF)', side='left'),
        yaxis2=dict(title='IRR (%)', side='right', overlaying='y'),
        barmode='group',
        height=500
    )
    
    return f'''
    <div class="section" id="scenario-analysis">
        <h2><i class="fas fa-project-diagram"></i> Scenario Analysis</h2>
        <div class="sensitivity-card">
            <div class="intro-box" style="margin-bottom: 18px;">
                <p style="margin-bottom: 10px; font-size: 0.9em; line-height: 1.6;">
                    <strong>What is Scenario Analysis?</strong> This analysis combines multiple parameter changes to model realistic scenarios. 
                    The <strong>Optimistic</strong> scenario uses the best values for the top 5 most impactful parameters. 
                    The <strong>Pessimistic</strong> scenario uses the worst values for these same parameters. 
                    The <strong>Base</strong> scenario represents the current assumptions.
                </p>
                <p style="margin-bottom: 0; font-size: 0.9em; line-height: 1.6;">
                    <strong>Use Case:</strong> Scenario analysis helps understand the range of possible outcomes when multiple factors change simultaneously, 
                    which is more realistic than one-way sensitivity analysis. It provides a framework for risk assessment and decision-making.
                </p>
            </div>
            <div class="chart-container">
                {fig_comparison.to_html(include_plotlyjs=False, div_id="scenario_comparison")}
            </div>
            <table class="summary-table" style="margin-top: 30px;">
                <thead>
                    <tr>
                        <th>Scenario</th>
                        <th>Annual Cash Flow</th>
                        <th>NPV (15Y)</th>
                        <th>IRR (with Sale)</th>
                        <th>IRR (without Sale)</th>
                        <th>Cap Rate</th>
                        <th>Cash-on-Cash Return</th>
                        <th>Debt Coverage Ratio</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
        </div>
    </div>
    '''


def identify_critical_thresholds(all_sensitivities: Dict[str, pd.DataFrame], base_config: BaseCaseConfig) -> Dict[str, Dict]:
    """
    Identify critical thresholds for financial viability.
    
    Returns:
        Dictionary mapping threshold type to threshold information:
        {
            'threshold_value': parameter value at threshold,
            'base_case_value': current base case value,
            'safety_margin': difference between base and threshold,
            'safety_margin_pct': margin as percentage,
            'status': 'Safe', 'Warning', 'Critical'
        }
    """
    base_result = compute_annual_cash_flows(base_config)
    base_cf = base_result['cash_flow_after_debt_service']
    
    thresholds = {}
    
    # Minimum occupancy for positive cash flow
    if 'Occupancy Rate' in all_sensitivities:
        df = all_sensitivities['Occupancy Rate']
        if 'Cash Flow After Debt (CHF)' in df.columns:
            positive_cf = df[df['Cash Flow After Debt (CHF)'] > 0]
            if len(positive_cf) > 0:
                min_occ = positive_cf['Occupancy Rate (%)'].min()
                base_occ = base_result.get('overall_occupancy_rate', base_config.rental.occupancy_rate) * 100
                margin = base_occ - min_occ
                margin_pct = (margin / min_occ * 100) if min_occ > 0 else 0
                
                if margin_pct < 10:
                    status = 'Critical'
                elif margin_pct < 25:
                    status = 'Warning'
                else:
                    status = 'Safe'
                
                thresholds['Minimum Occupancy'] = {
                    'threshold_value': min_occ,
                    'base_case_value': base_occ,
                    'safety_margin': margin,
                    'safety_margin_pct': margin_pct,
                    'status': status,
                    'unit': '%'
                }
    
    # Break-even daily rate
    if 'Daily Rate' in all_sensitivities:
        df = all_sensitivities['Daily Rate']
        if 'Cash Flow After Debt (CHF)' in df.columns:
            # Find where cash flow crosses zero
            positive_cf = df[df['Cash Flow After Debt (CHF)'] > 0]
            if len(positive_cf) > 0:
                min_rate = positive_cf['Average Daily Rate (CHF)'].min()
                base_rate = base_result.get('average_daily_rate', 200.0)
                margin = base_rate - min_rate
                margin_pct = (margin / min_rate * 100) if min_rate > 0 else 0
                
                if margin_pct < 10:
                    status = 'Critical'
                elif margin_pct < 25:
                    status = 'Warning'
                else:
                    status = 'Safe'
                
                thresholds['Minimum Daily Rate'] = {
                    'threshold_value': min_rate,
                    'base_case_value': base_rate,
                    'safety_margin': margin,
                    'safety_margin_pct': margin_pct,
                    'status': status,
                    'unit': 'CHF'
                }
    
    # Maximum interest rate before negative returns
    if 'Interest Rate' in all_sensitivities:
        df = all_sensitivities['Interest Rate']
        if 'Cash Flow After Debt (CHF)' in df.columns:
            positive_cf = df[df['Cash Flow After Debt (CHF)'] > 0]
            if len(positive_cf) > 0:
                max_rate = positive_cf['Interest Rate (%)'].max()
                base_rate = base_config.financing.interest_rate * 100
                margin = max_rate - base_rate
                margin_pct = (margin / base_rate * 100) if base_rate > 0 else 0
                
                if margin_pct < 10:
                    status = 'Critical'
                elif margin_pct < 25:
                    status = 'Warning'
                else:
                    status = 'Safe'
                
                thresholds['Maximum Interest Rate'] = {
                    'threshold_value': max_rate,
                    'base_case_value': base_rate,
                    'safety_margin': margin,
                    'safety_margin_pct': margin_pct,
                    'status': status,
                    'unit': '%'
                }
    
    # Maximum management fee before negative cash flow
    if 'Management Fee' in all_sensitivities:
        df = all_sensitivities['Management Fee']
        if 'Cash Flow After Debt (CHF)' in df.columns:
            positive_cf = df[df['Cash Flow After Debt (CHF)'] > 0]
            if len(positive_cf) > 0:
                max_fee = positive_cf['Management Fee (%)'].max()
                base_fee = base_config.expenses.property_management_fee_rate * 100
                margin = max_fee - base_fee
                margin_pct = (margin / base_fee * 100) if base_fee > 0 else 0
                
                if margin_pct < 10:
                    status = 'Critical'
                elif margin_pct < 25:
                    status = 'Warning'
                else:
                    status = 'Safe'
                
                thresholds['Maximum Management Fee'] = {
                    'threshold_value': max_fee,
                    'base_case_value': base_fee,
                    'safety_margin': margin,
                    'safety_margin_pct': margin_pct,
                    'status': status,
                    'unit': '%'
                }
    
    return thresholds


def generate_critical_thresholds_html(thresholds: Dict[str, Dict]) -> str:
    """
    Generate HTML section for critical thresholds analysis.
    
    Args:
        thresholds: Dictionary from identify_critical_thresholds()
    
    Returns:
        HTML string for critical thresholds section
    """
    if not thresholds:
        return ''
    
    def format_number(value, unit):
        if unit == '%':
            return f"{value:.2f}%"
        elif unit == 'CHF':
            return f"{value:,.0f} CHF"
        else:
            return f"{value:.2f} {unit}"
    
    table_rows = []
    for threshold_name, data in thresholds.items():
        status = data['status']
        threshold_val = data['threshold_value']
        base_val = data['base_case_value']
        margin = data['safety_margin']
        margin_pct = data['safety_margin_pct']
        unit = data.get('unit', '')
        
        if status == 'Critical':
            status_color = '#dc3545'
            status_icon = '🔴'
        elif status == 'Warning':
            status_color = '#ffc107'
            status_icon = '🟡'
        else:
            status_color = '#28a745'
            status_icon = '🟢'
        
        table_rows.append(f'''
            <tr>
                <td><strong>{threshold_name}</strong></td>
                <td>{format_number(threshold_val, unit)}</td>
                <td>{format_number(base_val, unit)}</td>
                <td style="color: {status_color}; font-weight: 600;">{status_icon} {status}</td>
                <td>{format_number(margin, unit)}</td>
                <td>{margin_pct:.1f}%</td>
            </tr>
        ''')
    
    return f'''
    <div class="section" id="critical-thresholds">
        <h2><i class="fas fa-exclamation-triangle"></i> Critical Thresholds</h2>
        <div class="sensitivity-card">
            <div class="intro-box" style="margin-bottom: 18px;">
                <p style="margin-bottom: 10px; font-size: 0.9em; line-height: 1.6;">
                    <strong>What are Critical Thresholds?</strong> Critical thresholds identify the parameter values at which the investment transitions 
                    from viable to non-viable (e.g., positive to negative cash flow). These thresholds help identify safety margins and risk levels.
                </p>
                <p style="margin-bottom: 0; font-size: 0.9em; line-height: 1.6;">
                    <strong>Safety Status:</strong> <strong>Safe</strong> indicates a comfortable margin (>25%) from threshold. 
                    <strong>Warning</strong> indicates moderate margin (10-25%). <strong>Critical</strong> indicates narrow margin (<10%) requiring immediate attention.
                </p>
            </div>
            <table class="summary-table" style="margin-top: 20px;">
                <thead>
                    <tr>
                        <th>Threshold</th>
                        <th>Threshold Value</th>
                        <th>Base Case Value</th>
                        <th>Safety Status</th>
                        <th>Safety Margin</th>
                        <th>Margin (%)</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
            <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
                <p style="font-size: 0.9em; line-height: 1.6; margin: 0;">
                    <strong>⚠️ Risk Warnings:</strong> Parameters with Critical or Warning status require careful monitoring. 
                    Consider implementing contingency plans or adjusting assumptions to increase safety margins.
                </p>
            </div>
        </div>
    </div>
    '''


def identify_top_parameter_pairs(metrics: Dict) -> List[Tuple[str, str]]:
    """
    Identify top parameter pairs with highest combined impact.
    
    Args:
        metrics: Dictionary from calculate_sensitivity_metrics()
    
    Returns:
        List of tuples (param1, param2) representing top parameter pairs
    """
    if 'ranking' not in metrics:
        return []
    
    # Get top 5 parameters by composite score
    top_params = [item['sensitivity'] for item in metrics['ranking'][:5]]
    
    # Generate pairs from top parameters
    pairs = []
    for i, param1 in enumerate(top_params):
        for param2 in top_params[i+1:]:
            pairs.append((param1, param2))
    
    # Return top 3 pairs (can be enhanced with actual co-impact analysis)
    return pairs[:3]


def calculate_two_way_sensitivity(base_config: BaseCaseConfig, param1_name: str, param2_name: str, 
                                 ranges1: np.ndarray, ranges2: np.ndarray) -> pd.DataFrame:
    """
    Calculate two-way sensitivity by varying two parameters simultaneously.
    
    Args:
        base_config: Base case configuration
        param1_name: Name of first parameter
        param2_name: Name of second parameter
        ranges1: Array of values for parameter 1
        ranges2: Array of values for parameter 2
    
    Returns:
        DataFrame with both parameters and resulting metrics
    """
    results = []
    
    for val1 in ranges1:
        for val2 in ranges2:
            # Create modified config based on parameter types
            config = base_config
            
            if param1_name == 'Occupancy Rate':
                occ1 = val1 / 100.0 if val1 > 1.0 else val1
                config = apply_sensitivity(config, occupancy=occ1)
            elif param1_name == 'Daily Rate':
                config = apply_sensitivity(config, daily_rate=val1)
            elif param1_name == 'Interest Rate':
                int1 = val1 / 100.0 if val1 > 1.0 else val1
                config = apply_sensitivity(config, interest_rate=int1)
            elif param1_name == 'Management Fee':
                mgmt1 = val1 / 100.0 if val1 > 1.0 else val1
                config = apply_sensitivity(config, management_fee=mgmt1)
            elif param1_name == 'Loan-to-Value':
                # LTV requires special handling
                new_financing = FinancingParams(
                    purchase_price=base_config.financing.purchase_price,
                    ltv=val1 / 100.0 if val1 > 1.0 else val1,
                    interest_rate=base_config.financing.interest_rate,
                    amortization_rate=base_config.financing.amortization_rate,
                    num_owners=base_config.financing.num_owners
                )
                config = BaseCaseConfig(
                    financing=new_financing,
                    rental=base_config.rental,
                    expenses=base_config.expenses
                )
            
            # Apply second parameter
            if param2_name == 'Occupancy Rate':
                occ2 = val2 / 100.0 if val2 > 1.0 else val2
                config = apply_sensitivity(config, occupancy=occ2)
            elif param2_name == 'Daily Rate':
                config = apply_sensitivity(config, daily_rate=val2)
            elif param2_name == 'Interest Rate':
                int2 = val2 / 100.0 if val2 > 1.0 else val2
                config = apply_sensitivity(config, interest_rate=int2)
            elif param2_name == 'Management Fee':
                mgmt2 = val2 / 100.0 if val2 > 1.0 else val2
                config = apply_sensitivity(config, management_fee=mgmt2)
            elif param2_name == 'Loan-to-Value':
                # LTV requires special handling
                new_financing = FinancingParams(
                    purchase_price=config.financing.purchase_price,
                    ltv=val2 / 100.0 if val2 > 1.0 else val2,
                    interest_rate=config.financing.interest_rate,
                    amortization_rate=config.financing.amortization_rate,
                    num_owners=config.financing.num_owners
                )
                config = BaseCaseConfig(
                    financing=new_financing,
                    rental=config.rental,
                    expenses=config.expenses
                )
            
            # Calculate results
            result = compute_annual_cash_flows(config)
            
            # Calculate NPV and IRR for this combination
            discount_rate = 0.03
            npv_irr = calculate_npv_irr_for_config(config, discount_rate)
            
            results.append({
                param1_name: val1,
                param2_name: val2,
                'Cash Flow After Debt (CHF)': result['cash_flow_after_debt_service'],
                'NPV': npv_irr['npv'],
                'IRR (%)': npv_irr['irr_with_sale_pct']
            })
    
    return pd.DataFrame(results)


def generate_two_way_sensitivity_html(all_sensitivities: Dict[str, pd.DataFrame], base_config: BaseCaseConfig, 
                                      metrics: Dict) -> str:
    """
    Generate HTML section for two-way sensitivity analysis.
    
    Args:
        all_sensitivities: Dictionary of sensitivity DataFrames
        base_config: Base case configuration
        metrics: Metrics dictionary
    
    Returns:
        HTML string for two-way sensitivity section
    """
    # Identify top parameter pairs
    top_pairs = identify_top_parameter_pairs(metrics)
    
    if not top_pairs:
        return ''
    
    # Limit to top 3 pairs for performance
    top_pairs = top_pairs[:3]
    
    sections = []
    
    for param1_name, param2_name in top_pairs:
        # Get parameter ranges from existing sensitivities
        if param1_name not in all_sensitivities or param2_name not in all_sensitivities:
            continue
        
        df1 = all_sensitivities[param1_name]
        df2 = all_sensitivities[param2_name]
        
        param1_col = df1.columns[0]
        param2_col = df2.columns[0]
        
        # Check if parameters are numeric (skip categorical parameters like "Mortgage Type")
        try:
            param1_min = float(df1[param1_col].min())
            param1_max = float(df1[param1_col].max())
            param2_min = float(df2[param2_col].min())
            param2_max = float(df2[param2_col].max())
        except (ValueError, TypeError):
            # Skip non-numeric parameters
            continue
        
        # Use subset of values for performance (10x10 grid = 100 scenarios)
        param1_values = np.linspace(param1_min, param1_max, 10)
        param2_values = np.linspace(param2_min, param2_max, 10)
        
        # Calculate two-way sensitivity
        two_way_df = calculate_two_way_sensitivity(base_config, param1_name, param2_name, 
                                                    param1_values, param2_values)
        
        # Create contour plot
        pivot_npv = two_way_df.pivot_table(
            values='NPV',
            index=param1_name,
            columns=param2_name,
            aggfunc='mean'
        )
        
        pivot_irr = two_way_df.pivot_table(
            values='IRR (%)',
            index=param1_name,
            columns=param2_name,
            aggfunc='mean'
        )
        
        # Create Plotly contour plots
        fig_npv = go.Figure(data=go.Contour(
            z=pivot_npv.values,
            x=pivot_npv.columns,
            y=pivot_npv.index,
            colorscale='RdYlGn',
            colorbar=dict(title="NPV (CHF)")
        ))
        fig_npv.update_layout(
            title=f'NPV: {param1_name} vs {param2_name}',
            xaxis_title=param2_name,
            yaxis_title=param1_name,
            height=500
        )
        
        fig_irr = go.Figure(data=go.Contour(
            z=pivot_irr.values,
            x=pivot_irr.columns,
            y=pivot_irr.index,
            colorscale='RdYlGn',
            colorbar=dict(title="IRR (%)")
        ))
        fig_irr.update_layout(
            title=f'IRR: {param1_name} vs {param2_name}',
            xaxis_title=param2_name,
            yaxis_title=param1_name,
            height=500
        )
        
        sections.append(f'''
        <div class="sensitivity-card" style="margin-bottom: 30px;">
            <h3 style="font-size: 1.2em; margin-bottom: 15px; color: var(--primary);">
                {param1_name} vs {param2_name}
            </h3>
            <p style="font-size: 0.9em; margin-bottom: 20px; color: #555;">
                This two-way sensitivity analysis shows how simultaneous changes in <strong>{param1_name}</strong> and <strong>{param2_name}</strong> 
                affect investment performance. Warmer colors (green/yellow) indicate better outcomes, cooler colors (red) indicate worse outcomes.
            </p>
            <div class="chart-container">
                {fig_npv.to_html(include_plotlyjs=False, div_id=f"twoway_npv_{param1_name}_{param2_name}".replace(' ', '_').replace('-', '_'))}
            </div>
            <div class="chart-container" style="margin-top: 20px;">
                {fig_irr.to_html(include_plotlyjs=False, div_id=f"twoway_irr_{param1_name}_{param2_name}".replace(' ', '_').replace('-', '_'))}
            </div>
        </div>
        ''')
    
    if not sections:
        return ''
    
    return f'''
    <div class="section" id="two-way-sensitivity">
        <h2><i class="fas fa-th"></i> Two-Way Sensitivity Analysis</h2>
        <div class="sensitivity-card">
            <div class="intro-box" style="margin-bottom: 18px;">
                <p style="margin-bottom: 10px; font-size: 0.9em; line-height: 1.6;">
                    <strong>What is Two-Way Sensitivity Analysis?</strong> This analysis examines how two parameters interact when changed simultaneously. 
                    Unlike one-way sensitivity (which varies one parameter at a time), two-way analysis reveals parameter interactions and identifies 
                    combinations that lead to optimal or suboptimal outcomes.
                </p>
                <p style="margin-bottom: 0; font-size: 0.9em; line-height: 1.6;">
                    <strong>How to Read:</strong> Contour plots show NPV and IRR across parameter combinations. Each point represents a scenario with 
                    specific values for both parameters. The color intensity indicates performance level. Break-even lines (where NPV = 0 or IRR = threshold) 
                    can be identified by the color transitions.
                </p>
            </div>
            {''.join(sections)}
        </div>
    </div>
    '''


def calculate_elasticity_metrics(all_sensitivities: Dict[str, pd.DataFrame], base_config: BaseCaseConfig, base_metrics: Dict) -> Dict[str, Dict]:
    """
    Calculate elasticity coefficients for each sensitivity.
    Elasticity = (% change in output) / (% change in input)
    
    Returns:
        Dictionary mapping sensitivity name to elasticity measures:
        {
            'elasticity_cf': elasticity of cash flow,
            'elasticity_npv': elasticity of NPV,
            'elasticity_irr': elasticity of IRR,
            'classification': 'Highly elastic' (>1.5), 'Moderately elastic' (0.5-1.5), 'Inelastic' (<0.5)
        }
    """
    base_cf = compute_annual_cash_flows(base_config)['cash_flow_after_debt_service']
    base_npv = base_metrics['npv']
    base_irr = base_metrics['irr_with_sale_pct']
    
    elasticity_results = {}
    
    for sens_name, df in all_sensitivities.items():
        if 'Cash Flow After Debt (CHF)' not in df.columns:
            continue
        
        param_col = df.columns[0]
        param_values = df[param_col].values
        cash_flows = df['Cash Flow After Debt (CHF)'].values
        
        # Get base case parameter value
        if sens_name == 'Occupancy Rate':
            base_param = base_config.rental.occupancy_rate * 100
        elif sens_name == 'Daily Rate':
            base_result = compute_annual_cash_flows(base_config)
            base_param = base_result.get('average_daily_rate', 200.0)
        elif sens_name == 'Interest Rate':
            base_param = base_config.financing.interest_rate * 100
        elif sens_name == 'Loan-to-Value':
            base_param = base_config.financing.ltv * 100
        elif sens_name == 'Management Fee':
            base_param = base_config.expenses.property_management_fee_rate * 100
        elif sens_name == 'Owner Nights':
            base_param = base_config.rental.owner_nights_per_person * base_config.financing.num_owners
        else:
            continue  # Skip if we can't determine base parameter
        
        # Find closest parameter value to base case
        closest_idx = np.argmin(np.abs(param_values - base_param))
        closest_param = param_values[closest_idx]
        closest_cf = cash_flows[closest_idx]
        
        # Calculate elasticity using best and worst cases
        best_idx = cash_flows.argmax()
        worst_idx = cash_flows.argmin()
        
        best_param = param_values[best_idx]
        worst_param = param_values[worst_idx]
        best_cf = cash_flows[best_idx]
        worst_cf = cash_flows[worst_idx]
        
        # Calculate elasticity for cash flow (using best case)
        if base_param != 0 and base_cf != 0:
            pct_change_param = ((best_param - base_param) / base_param) * 100
            pct_change_cf = ((best_cf - base_cf) / abs(base_cf)) * 100
            elasticity_cf = (pct_change_cf / pct_change_param) if pct_change_param != 0 else 0
        else:
            elasticity_cf = 0
        
        # For NPV and IRR, we need to calculate them for best/worst cases
        # This is simplified - we'll use the impacts from sensitivity_impacts if available
        # For now, we'll focus on cash flow elasticity which is most direct
        
        # Classify elasticity
        if abs(elasticity_cf) > 1.5:
            classification = 'Highly Elastic'
        elif abs(elasticity_cf) > 0.5:
            classification = 'Moderately Elastic'
        else:
            classification = 'Inelastic'
        
        elasticity_results[sens_name] = {
            'elasticity_cf': elasticity_cf,
            'classification': classification,
            'base_param': base_param,
            'base_cf': base_cf
        }
    
    return elasticity_results


def calculate_statistical_summary(all_sensitivities: Dict[str, pd.DataFrame], base_config: BaseCaseConfig, base_metrics: Dict) -> Dict[str, Dict]:
    """
    Calculate statistical measures for each sensitivity.
    
    Returns:
        Dictionary mapping sensitivity name to statistical measures:
        {
            'cv': coefficient of variation,
            'p10', 'p25', 'p50', 'p75', 'p90': percentiles,
            'range_pct': range as percentage of base case,
            'volatility_rank': rank by volatility (1 = most volatile)
        }
    """
    base_npv = base_metrics['npv']
    base_irr = base_metrics['irr_with_sale_pct']
    base_cf = compute_annual_cash_flows(base_config)['cash_flow_after_debt_service']
    
    statistical_results = {}
    
    for sens_name, df in all_sensitivities.items():
        if 'Cash Flow After Debt (CHF)' not in df.columns:
            continue
        
        cash_flows = df['Cash Flow After Debt (CHF)'].values
        
        # Calculate percentiles
        p10 = np.percentile(cash_flows, 10)
        p25 = np.percentile(cash_flows, 25)
        p50 = np.percentile(cash_flows, 50)  # median
        p75 = np.percentile(cash_flows, 75)
        p90 = np.percentile(cash_flows, 90)
        
        # Calculate mean and standard deviation
        mean_cf = np.mean(cash_flows)
        std_cf = np.std(cash_flows)
        
        # Coefficient of Variation (CV)
        cv = (std_cf / abs(mean_cf)) if mean_cf != 0 else float('inf')
        
        # Range as percentage of base case
        min_cf = cash_flows.min()
        max_cf = cash_flows.max()
        range_abs = max_cf - min_cf
        range_pct = (range_abs / abs(base_cf) * 100) if base_cf != 0 else 0
        
        statistical_results[sens_name] = {
            'mean': mean_cf,
            'std': std_cf,
            'cv': cv,
            'p10': p10,
            'p25': p25,
            'p50': p50,
            'p75': p75,
            'p90': p90,
            'min': min_cf,
            'max': max_cf,
            'range': range_abs,
            'range_pct': range_pct,
            'base_cf': base_cf
        }
    
    # Rank by volatility (CV)
    volatility_ranking = sorted(statistical_results.items(), key=lambda x: x[1]['cv'], reverse=True)
    for rank, (sens_name, _) in enumerate(volatility_ranking, 1):
        statistical_results[sens_name]['volatility_rank'] = rank
    
    return statistical_results


def generate_statistical_analysis_html(statistics: Dict[str, Dict]) -> str:
    """
    Generate HTML section for statistical analysis.
    
    Args:
        statistics: Dictionary from calculate_statistical_summary()
    
    Returns:
        HTML string for statistical analysis section
    """
    if not statistics:
        return ''
    
    def format_currency(value):
        return f"{value:,.0f} CHF"
    
    def format_percent(value):
        return f"{value:.2f}%"
    
    # Sort by volatility rank
    sorted_stats = sorted(statistics.items(), key=lambda x: x[1].get('volatility_rank', 999))
    
    table_rows = []
    for sens_name, stats in sorted_stats:
        cv = stats['cv']
        range_pct = stats['range_pct']
        volatility_rank = stats.get('volatility_rank', 999)
        
        # Determine volatility level
        if cv > 1.0:
            volatility_level = '🔴 High Volatility'
            vol_color = '#dc3545'
        elif cv > 0.5:
            volatility_level = '🟡 Medium Volatility'
            vol_color = '#ffc107'
        else:
            volatility_level = '🟢 Low Volatility'
            vol_color = '#28a745'
        
        table_rows.append(f'''
            <tr>
                <td><strong>{sens_name}</strong></td>
                <td style="text-align: center;">#{volatility_rank}</td>
                <td style="color: {vol_color}; font-weight: 600;">{volatility_level}</td>
                <td>{cv:.3f}</td>
                <td>{format_currency(stats['mean'])}</td>
                <td>{format_currency(stats['std'])}</td>
                <td>{format_currency(stats['p10'])}</td>
                <td>{format_currency(stats['p25'])}</td>
                <td>{format_currency(stats['p50'])}</td>
                <td>{format_currency(stats['p75'])}</td>
                <td>{format_currency(stats['p90'])}</td>
                <td>{format_currency(stats['range'])}</td>
                <td>{range_pct:.1f}%</td>
            </tr>
        ''')
    
    return f'''
    <div class="section" id="statistical-analysis">
        <h2><i class="fas fa-chart-bar"></i> Statistical Analysis</h2>
        <div class="sensitivity-card">
            <div class="intro-box" style="margin-bottom: 18px;">
                <p style="margin-bottom: 10px; font-size: 0.9em; line-height: 1.6;">
                    <strong>What is Statistical Analysis?</strong> This analysis provides detailed statistical measures for each sensitivity factor, including percentiles, coefficient of variation (CV), and range metrics. These measures help understand the distribution and volatility of outcomes.
                </p>
                <p style="margin-bottom: 0; font-size: 0.9em; line-height: 1.6;">
                    <strong>Key Metrics:</strong> CV (Coefficient of Variation) = std/mean, measures relative volatility. Higher CV indicates more volatile outcomes. Percentiles (P10, P25, P50, P75, P90) show the distribution of cash flow outcomes across tested parameter values.
                </p>
            </div>
            <table class="summary-table" style="margin-top: 20px; font-size: 0.85em;">
                <thead>
                    <tr>
                        <th>Sensitivity Factor</th>
                        <th>Volatility Rank</th>
                        <th>Volatility Level</th>
                        <th>CV</th>
                        <th>Mean</th>
                        <th>Std Dev</th>
                        <th>P10</th>
                        <th>P25</th>
                        <th>P50 (Median)</th>
                        <th>P75</th>
                        <th>P90</th>
                        <th>Range</th>
                        <th>Range % of Base</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
            <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #17a2b8;">
                <p style="font-size: 0.9em; line-height: 1.6; margin: 0;">
                    <strong>Interpretation:</strong> Factors with high CV (>1.0) show significant variability in outcomes and require careful monitoring. The range as % of base shows how much the cash flow can vary relative to the base case. Percentiles help identify likely outcome ranges (e.g., P25-P75 represents the interquartile range where 50% of outcomes fall).
                </p>
            </div>
        </div>
    </div>
    '''


def generate_sensitivity_ranking_table(metrics: Dict) -> str:
    """
    Generate HTML table for sensitivity ranking.
    
    Args:
        metrics: Dictionary from calculate_sensitivity_metrics() including 'ranking' key
    
    Returns:
        HTML string for ranking table
    """
    if 'ranking' not in metrics or not metrics['ranking']:
        return ''
    
    def format_currency(value):
        return f"{value:,.0f} CHF"
    
    def format_percent(value):
        return f"{value:.2f}%"
    
    # Get elasticity data if available
    elasticity_data = metrics.get('elasticity', {})
    
    table_rows = []
    for item in metrics['ranking']:
        sens_name = item['sensitivity']
        rank = item['rank']
        npv_range = item['npv_range']
        irr_range = item['irr_range']
        composite_score = item['composite_score']
        npv_best = item['npv_best_impact']
        npv_worst = item['npv_worst_impact']
        irr_best = item['irr_best_impact']
        irr_worst = item['irr_worst_impact']
        
        # Get elasticity if available
        elasticity_info = elasticity_data.get(sens_name, {})
        elasticity_cf = elasticity_info.get('elasticity_cf', 0)
        elasticity_class = elasticity_info.get('classification', 'N/A')
        
        # Determine risk level based on composite score
        max_score = max([x['composite_score'] for x in metrics['ranking']])
        risk_pct = (composite_score / max_score * 100) if max_score > 0 else 0
        
        if risk_pct >= 70:
            risk_level = '🔴 High Risk'
            risk_color = '#dc3545'
        elif risk_pct >= 40:
            risk_level = '🟡 Medium Risk'
            risk_color = '#ffc107'
        else:
            risk_level = '🟢 Low Risk'
            risk_color = '#28a745'
        
        # Elasticity color coding
        if abs(elasticity_cf) > 1.5:
            elast_color = '#dc3545'
        elif abs(elasticity_cf) > 0.5:
            elast_color = '#ffc107'
        else:
            elast_color = '#28a745'
        
        table_rows.append(f'''
            <tr>
                <td style="text-align: center; font-weight: 700;">#{rank}</td>
                <td><strong>{sens_name}</strong></td>
                <td style="color: {risk_color}; font-weight: 600;">{risk_level}</td>
                <td>{format_currency(npv_range)}</td>
                <td>{format_percent(irr_range)}</td>
                <td style="color: {elast_color}; font-weight: 600;">{elasticity_class}</td>
                <td>{elasticity_cf:.2f}</td>
                <td>{format_currency(composite_score)}</td>
                <td>{format_currency(npv_best)}</td>
                <td>{format_currency(npv_worst)}</td>
                <td>{format_percent(irr_best)}</td>
                <td>{format_percent(irr_worst)}</td>
            </tr>
        ''')
    
    return f'''
    <div class="section" id="sensitivity-ranking">
        <h2><i class="fas fa-trophy"></i> Sensitivity Ranking</h2>
        <div class="sensitivity-card">
            <div class="intro-box" style="margin-bottom: 18px;">
                <p style="margin-bottom: 10px; font-size: 0.9em; line-height: 1.6;">
                    <strong>What is Sensitivity Ranking?</strong> This table ranks all sensitivity factors by their impact on investment performance. Factors are ranked by a composite risk score that combines NPV and IRR impacts. Higher-ranked factors have the greatest potential to affect returns.
                </p>
                <p style="margin-bottom: 10px; font-size: 0.9em; line-height: 1.6;">
                    <strong>Risk Levels:</strong> High Risk factors require careful monitoring and may need contingency planning. Medium Risk factors should be tracked regularly. Low Risk factors have minimal impact on overall returns.
                </p>
                <p style="margin-bottom: 0; font-size: 0.9em; line-height: 1.6;">
                    <strong>Elasticity:</strong> Measures the proportional sensitivity of cash flow to parameter changes. Highly Elastic (>1.5) means output changes more than proportionally to input changes. Moderately Elastic (0.5-1.5) means proportional response. Inelastic (<0.5) means output changes less than proportionally.
                </p>
            </div>
            <table class="summary-table" style="margin-top: 20px;">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Sensitivity Factor</th>
                        <th>Risk Level</th>
                        <th>NPV Range</th>
                        <th>IRR Range</th>
                        <th>Elasticity Class</th>
                        <th>Elasticity</th>
                        <th>Composite Score</th>
                        <th>NPV Best</th>
                        <th>NPV Worst</th>
                        <th>IRR Best</th>
                        <th>IRR Worst</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
            <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #17a2b8;">
                <p style="font-size: 0.9em; line-height: 1.6; margin: 0;">
                    <strong>Methodology:</strong> Composite score = 40% × |NPV best impact| + 40% × |NPV worst impact| + 10% × |IRR best impact| + 10% × |IRR worst impact|. This weighting emphasizes NPV as the primary metric while considering IRR for context.
                </p>
            </div>
        </div>
    </div>
    '''


def generate_break_even_analysis_html(break_even_results: Dict[str, Dict], base_config: BaseCaseConfig) -> str:
    """
    Generate HTML section for break-even analysis.
    
    Args:
        break_even_results: Dictionary from calculate_break_even_points()
        base_config: Base case configuration
    
    Returns:
        HTML string for break-even analysis section
    """
    def format_currency(value):
        return f"{value:,.0f} CHF"
    
    def format_percent(value):
        return f"{value:.2f}%"
    
    def format_number(value, decimals=1):
        if isinstance(value, float):
            return f"{value:.{decimals}f}"
        return str(value)
    
    # Parameter display names and units
    param_display = {
        'Occupancy Rate': {'unit': '%', 'format': format_percent},
        'Daily Rate': {'unit': 'CHF', 'format': format_currency},
        'Interest Rate': {'unit': '%', 'format': format_percent},
        'Loan-to-Value': {'unit': '%', 'format': format_percent},
        'Management Fee': {'unit': '%', 'format': format_percent},
        'Owner Nights': {'unit': 'nights', 'format': lambda x: f"{x:.0f}"}
    }
    
    table_rows = []
    for sens_name, data in break_even_results.items():
        if not data.get('break_even_exists', False):
            continue
        
        be_value = data['break_even_value']
        base_value = data['base_case_value']
        margin = data['margin_to_break_even']
        margin_pct = data['margin_pct']
        is_above = data['is_above_break_even']
        
        display_info = param_display.get(sens_name, {'unit': '', 'format': format_number})
        format_func = display_info['format']
        unit = display_info['unit']
        
        # Determine safety status
        if abs(margin_pct) < 10:
            safety_status = '⚠️ Critical'
            safety_color = '#dc3545'
        elif abs(margin_pct) < 25:
            safety_status = '⚠️ Low Margin'
            safety_color = '#ffc107'
        else:
            safety_status = '✓ Safe'
            safety_color = '#28a745'
        
        direction = 'above' if is_above else 'below'
        margin_text = f"{abs(margin):.2f} {unit}" if unit else f"{abs(margin):.2f}"
        
        table_rows.append(f'''
            <tr>
                <td><strong>{sens_name}</strong></td>
                <td>{format_func(be_value)} {unit}</td>
                <td>{format_func(base_value)} {unit}</td>
                <td style="color: {safety_color}; font-weight: 600;">{safety_status}</td>
                <td>{margin_text} {direction} break-even</td>
                <td>{abs(margin_pct):.1f}%</td>
            </tr>
        ''')
    
    if not table_rows:
        return '''
        <div class="section">
            <h2><i class="fas fa-balance-scale"></i> Break-Even Analysis</h2>
            <div class="sensitivity-card">
                <p>Break-even analysis is not applicable for the current sensitivity ranges. All tested parameter values result in either positive or negative cash flow, with no zero-crossing point.</p>
            </div>
        </div>
        '''
    
    return f'''
    <div class="section" id="break-even">
        <h2><i class="fas fa-balance-scale"></i> Break-Even Analysis</h2>
        <div class="sensitivity-card">
            <div class="intro-box" style="margin-bottom: 18px;">
                <p style="margin-bottom: 10px; font-size: 0.9em; line-height: 1.6;">
                    <strong>What is Break-Even Analysis?</strong> Break-even analysis identifies the parameter value where cash flow after debt service equals zero. This is a critical threshold - values below break-even require owner contributions, while values above break-even generate positive returns.
                </p>
                <p style="margin-bottom: 0; font-size: 0.9em; line-height: 1.6;">
                    <strong>Safety Margin:</strong> The margin shows how far the base case is from break-even. A larger margin provides more protection against adverse changes. Parameters with margins below 25% are considered higher risk.
                </p>
            </div>
            <table class="summary-table" style="margin-top: 20px;">
                <thead>
                    <tr>
                        <th>Parameter</th>
                        <th>Break-Even Value</th>
                        <th>Base Case Value</th>
                        <th>Safety Status</th>
                        <th>Margin</th>
                        <th>Margin (%)</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
            <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #17a2b8;">
                <p style="font-size: 0.9em; line-height: 1.6; margin: 0;">
                    <strong>Interpretation:</strong> Parameters with break-even values close to the base case are more sensitive and require careful monitoring. A negative margin indicates the base case is below break-even (negative cash flow), which may be acceptable if personal use value and appreciation are considered.
                </p>
            </div>
        </div>
    </div>
    '''


def generate_sensitivity_impact_table(monthly_cf_data, cap_rate_data, cash_on_cash_data, npv_data, irr_data, sensitivities, sensitivity_info) -> str:
    """
    Generate a comprehensive table showing all sensitivity impacts (Monthly Cash Flow, IRR, NPV, Cap Rate, Cash-on-Cash Return).
    """
    # Create a dictionary to collect all sensitivity data
    all_sens_data = {}
    
    # Collect all sensitivity names
    all_sens_names = set()
    all_sens_names.update([name for name, _ in cap_rate_data])
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
            'monthly_cf_worst': None,
            'monthly_cf_best': None,
            'cap_rate_worst': None,
            'cap_rate_best': None,
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
        
        # Get Monthly Cash Flow data (practical metric)
        monthly_cf_entry = next((data for name, data in monthly_cf_data if name == sens_name), None)
        if monthly_cf_entry:
            sens_entry['monthly_cf_worst'] = monthly_cf_entry.get('worst_impact', 0)
            sens_entry['monthly_cf_best'] = monthly_cf_entry.get('best_impact', 0)
        
        # Get Cap Rate data (unlevered)
        cap_rate_entry = next((data for name, data in cap_rate_data if name == sens_name), None)
        if cap_rate_entry:
            sens_entry['cap_rate_worst'] = cap_rate_entry.get('worst_impact', 0)
            sens_entry['cap_rate_best'] = cap_rate_entry.get('best_impact', 0)
        
        # Get Cash-on-Cash Return data (levered)
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
        <h4 style="color: #0f3460; margin-bottom: 15px; font-size: 1.1em; font-weight: 600;">Comprehensive Sensitivity Impact Table</h4>
        <p style="margin-bottom: 15px; color: #495057; line-height: 1.6; font-size: 0.9em;">
            This table shows the impact of each sensitivity factor on three key metrics: 
            <strong>Cash-on-Cash (Unlevered)</strong>, <strong>NPV</strong>, and <strong>IRR</strong>. 
            Values show the impact relative to the base case (worst case = negative impact, best case = positive impact).
            <br><br>
            <strong>Range Tested:</strong> Shows the minimum (worst case) and maximum (best case) parameter values tested. 
            Each sensitivity factor is tested across its full range, with both extremes clearly indicated.
        </p>
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <thead>
                    <tr style="background: linear-gradient(135deg, #0f3460 0%, #1a1a2e 100%); color: white;">
                    <th style="padding: 12px; text-align: left; font-weight: 600; border-right: 1px solid rgba(255,255,255,0.2); font-size: 0.9em;">Sensitivity Factor</th>
                    <th style="padding: 12px; text-align: left; font-weight: 600; border-right: 1px solid rgba(255,255,255,0.2); font-size: 0.9em;">Range Tested</th>
                    <th style="padding: 12px; text-align: center; font-weight: 600; border-right: 1px solid rgba(255,255,255,0.2); font-size: 0.9em;" colspan="2">Monthly CF Impact (CHF)</th>
                    <th style="padding: 12px; text-align: center; font-weight: 600; border-right: 1px solid rgba(255,255,255,0.2); font-size: 0.9em;" colspan="2">Cap Rate Impact (pp)</th>
                    <th style="padding: 12px; text-align: center; font-weight: 600; border-right: 1px solid rgba(255,255,255,0.2); font-size: 0.9em;" colspan="2">Cash-on-Cash Impact (pp)</th>
                    <th style="padding: 12px; text-align: center; font-weight: 600; border-right: 1px solid rgba(255,255,255,0.2); font-size: 0.9em;" colspan="2">NPV Impact (CHF)</th>
                    <th style="padding: 12px; text-align: center; font-weight: 600; font-size: 0.9em;" colspan="2">IRR Impact (pp)</th>
                    </tr>
                <tr style="background: #e8ecef; color: #495057;">
                    <th style="padding: 8px 12px; border-right: 1px solid #dee2e6;"></th>
                    <th style="padding: 8px 12px; border-right: 1px solid #dee2e6;"></th>
                    <th style="padding: 8px 12px; text-align: center; border-right: 1px solid #dee2e6; font-size: 0.85em; font-weight: 500;">Worst</th>
                    <th style="padding: 8px 12px; text-align: center; border-right: 1px solid #dee2e6; font-size: 0.85em; font-weight: 500;">Best</th>
                    <th style="padding: 8px 12px; text-align: center; border-right: 1px solid #dee2e6; font-size: 0.85em; font-weight: 500;">Worst</th>
                    <th style="padding: 8px 12px; text-align: center; border-right: 1px solid #dee2e6; font-size: 0.85em; font-weight: 500;">Best</th>
                    <th style="padding: 8px 12px; text-align: center; border-right: 1px solid #dee2e6; font-size: 0.85em; font-weight: 500;">Worst</th>
                    <th style="padding: 8px 12px; text-align: center; border-right: 1px solid #dee2e6; font-size: 0.85em; font-weight: 500;">Best</th>
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
        # Format range with clear indication of extremes
        range_str = f"<strong>Min:</strong> {sens['range_min']} | <strong>Max:</strong> {sens['range_max']}<br><small style='color: #6c757d;'>(Base Case: {sens['range_base']})</small>"
        
        # Format Monthly Cash Flow
        monthly_cf_worst_str = f"<span style='color: #e74c3c; font-weight: 600;'>{sens['monthly_cf_worst']:,.0f} CHF</span>" if sens['monthly_cf_worst'] is not None else "<span style='color: #999;'>N/A</span>"
        monthly_cf_best_str = f"<span style='color: #2ecc71; font-weight: 600;'>{sens['monthly_cf_best']:,.0f} CHF</span>" if sens['monthly_cf_best'] is not None else "<span style='color: #999;'>N/A</span>"
        
        # Format Cap Rate
        cap_rate_worst_str = f"<span style='color: #e74c3c; font-weight: 600;'>{sens['cap_rate_worst']:.2f} pp</span>" if sens['cap_rate_worst'] is not None else "<span style='color: #999;'>N/A</span>"
        cap_rate_best_str = f"<span style='color: #2ecc71; font-weight: 600;'>{sens['cap_rate_best']:.2f} pp</span>" if sens['cap_rate_best'] is not None else "<span style='color: #999;'>N/A</span>"
        
        # Format Cash-on-Cash Return
        coc_worst_str = f"<span style='color: #e74c3c; font-weight: 600;'>{sens['coc_worst']:.2f} pp</span>" if sens['coc_worst'] is not None else "<span style='color: #999;'>N/A</span>"
        coc_best_str = f"<span style='color: #2ecc71; font-weight: 600;'>{sens['coc_best']:.2f} pp</span>" if sens['coc_best'] is not None else "<span style='color: #999;'>N/A</span>"
        
        # Format NPV
        npv_worst_str = f"<span style='color: #e74c3c; font-weight: 600;'>{sens['npv_worst']:,.0f}</span>" if sens['npv_worst'] is not None else "<span style='color: #999;'>N/A</span>"
        npv_best_str = f"<span style='color: #2ecc71; font-weight: 600;'>{sens['npv_best']:,.0f}</span>" if sens['npv_best'] is not None else "<span style='color: #999;'>N/A</span>"
        
        # Format IRR
        irr_worst_str = f"<span style='color: #e67e22; font-weight: 600;'>{sens['irr_worst']:.2f} pp</span>" if sens['irr_worst'] is not None else "<span style='color: #999;'>N/A</span>"
        irr_best_str = f"<span style='color: #2ecc71; font-weight: 600;'>{sens['irr_best']:.2f} pp</span>" if sens['irr_best'] is not None else "<span style='color: #999;'>N/A</span>"
        
        table_html += f'''
                    <tr style="border-bottom: 1px solid #e8ecef;">
                        <td style="padding: 15px; font-weight: 600; color: #1a1a2e; border-right: 1px solid #e8ecef;">{sens['name']}</td>
                        <td style="padding: 15px; color: #495057; border-right: 1px solid #e8ecef; font-size: 0.9em;">{range_str}</td>
                        <td style="padding: 15px; text-align: center; border-right: 1px solid #e8ecef;">{monthly_cf_worst_str}</td>
                        <td style="padding: 15px; text-align: center; border-right: 1px solid #dee2e6;">{monthly_cf_best_str}</td>
                        <td style="padding: 15px; text-align: center; border-right: 1px solid #dee2e6;">{cap_rate_worst_str}</td>
                        <td style="padding: 15px; text-align: center; border-right: 1px solid #dee2e6;">{cap_rate_best_str}</td>
                        <td style="padding: 15px; text-align: center; border-right: 1px solid #dee2e6;">{coc_worst_str}</td>
                        <td style="padding: 15px; text-align: center; border-right: 1px solid #dee2e6;">{coc_best_str}</td>
                        <td style="padding: 15px; text-align: center; border-right: 1px solid #dee2e6;">{npv_worst_str}</td>
                        <td style="padding: 15px; text-align: center; border-right: 1px solid #dee2e6;">{npv_best_str}</td>
                        <td style="padding: 15px; text-align: center; border-right: 1px solid #dee2e6;">{irr_worst_str}</td>
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
    
    # Calculate MONTHLY CASH FLOW PER OWNER impact for each sensitivity
    # Monthly Cash Flow = Annual Cash Flow per Owner / 12
    # This is the practical metric showing how much each participant needs to pay or receives monthly
    monthly_cash_flow_data = []
    # Calculate CAP RATE (unlevered) impact for each sensitivity
    # Cap Rate = NOI / Purchase Price (industry standard unlevered metric)
    cap_rate_data = []
    # Calculate LEVERED Cash-on-Cash Return impact for each sensitivity
    # Cash-on-Cash Return = (Cash Flow After Debt Service / Initial Equity Investment) × 100
    cash_on_cash_data = []
    
    if all_sensitivities:
        base_result = compute_annual_cash_flows(base_config)
        base_noi = base_result['net_operating_income']  # Net Operating Income (unlevered)
        base_purchase_price = base_config.financing.purchase_price
        base_equity = base_result['equity_total']  # Initial equity investment
        base_cf_after_debt = base_result['cash_flow_after_debt_service']  # Levered cash flow
        base_cf_per_owner = base_result['cash_flow_per_owner']  # Annual cash flow per owner
        base_monthly_cf_per_owner = base_cf_per_owner / 12.0  # Monthly cash flow per owner
        
        # Base case metrics
        base_cap_rate = (base_noi / base_purchase_price) * 100  # Cap Rate (unlevered)
        base_coc_return = (base_cf_after_debt / base_equity) * 100 if base_equity > 0 else 0  # Cash-on-Cash Return (levered)
        
        for sens_name, df in all_sensitivities.items():
            if 'Cash Flow After Debt (CHF)' not in df.columns:
                continue
            
            # Get best and worst case scenarios
            best_idx = df['Cash Flow After Debt (CHF)'].idxmax()
            worst_idx = df['Cash Flow After Debt (CHF)'].idxmin()
            
            best_cf_after_debt = df.loc[best_idx, 'Cash Flow After Debt (CHF)']
            worst_cf_after_debt = df.loc[worst_idx, 'Cash Flow After Debt (CHF)']
            
            # Get cash flow per owner for best and worst cases
            if 'Cash Flow per Owner (CHF)' in df.columns:
                best_cf_per_owner = df.loc[best_idx, 'Cash Flow per Owner (CHF)']
                worst_cf_per_owner = df.loc[worst_idx, 'Cash Flow per Owner (CHF)']
            else:
                # Calculate from total cash flow
                best_cf_per_owner = best_cf_after_debt / base_config.financing.num_owners
                worst_cf_per_owner = worst_cf_after_debt / base_config.financing.num_owners
            
            # Calculate monthly cash flow per owner
            best_monthly_cf = best_cf_per_owner / 12.0
            worst_monthly_cf = worst_cf_per_owner / 12.0
            
            # Impact relative to base case (in CHF per month)
            monthly_impact_best = best_monthly_cf - base_monthly_cf_per_owner
            monthly_impact_worst = worst_monthly_cf - base_monthly_cf_per_owner
            
            # Store Monthly Cash Flow data
            monthly_cash_flow_data.append((sens_name, {
                'best_impact': monthly_impact_best,
                'worst_impact': monthly_impact_worst,
                'best_monthly_cf': best_monthly_cf,
                'worst_monthly_cf': worst_monthly_cf,
                'base_monthly_cf': base_monthly_cf_per_owner
            }))
            
            # Get debt service from base case (assume constant for sensitivity)
            base_debt_service = base_result['debt_service']
            
            # Calculate NOI (unlevered) = Cash Flow After Debt + Debt Service
            best_noi = best_cf_after_debt + base_debt_service
            worst_noi = worst_cf_after_debt + base_debt_service
            
            # CAP RATE (unlevered metric) = NOI / Purchase Price
            best_cap_rate = (best_noi / base_purchase_price) * 100
            worst_cap_rate = (worst_noi / base_purchase_price) * 100
            cap_rate_impact_best = best_cap_rate - base_cap_rate
            cap_rate_impact_worst = worst_cap_rate - base_cap_rate
            
            # CASH-ON-CASH RETURN (levered metric) = (Cash Flow After Debt / Equity) × 100
            best_coc_return = (best_cf_after_debt / base_equity) * 100 if base_equity > 0 else 0
            worst_coc_return = (worst_cf_after_debt / base_equity) * 100 if base_equity > 0 else 0
            coc_impact_best = best_coc_return - base_coc_return
            coc_impact_worst = worst_coc_return - base_coc_return
            
            # Store Cap Rate data (unlevered)
            cap_rate_data.append((sens_name, {
                'best_impact': cap_rate_impact_best,
                'worst_impact': cap_rate_impact_worst,
                'best_cap_rate': best_cap_rate,
                'worst_cap_rate': worst_cap_rate,
                'base_cap_rate': base_cap_rate
            }))
            
            # Store Cash-on-Cash Return data (levered)
            cash_on_cash_data.append((sens_name, {
                'best_impact': coc_impact_best,
                'worst_impact': coc_impact_worst,
                'best_coc': best_coc_return,
                'worst_coc': worst_coc_return,
                'base_coc': base_coc_return
            }))
    
    # Get sensitivity info for ranges (needed for tooltips and table)
    sensitivity_info = get_sensitivity_ranges_and_descriptions()
    
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
    monthly_cash_flow_data = sorted(monthly_cash_flow_data, key=lambda x: max(abs(x[1]['best_impact']), abs(x[1]['worst_impact'])), reverse=True)[:10]
    cap_rate_data = sorted(cap_rate_data, key=lambda x: max(abs(x[1]['best_impact']), abs(x[1]['worst_impact'])), reverse=True)[:10]
    cash_on_cash_data = sorted(cash_on_cash_data, key=lambda x: max(abs(x[1]['best_impact']), abs(x[1]['worst_impact'])), reverse=True)[:10]
    
    charts_html = []
    
    # 0. Tornado Chart for Monthly Cash Flow per Owner - FIRST CHART (Most Practical)
    # Monthly Cash Flow = Annual Cash Flow per Owner / 12
    # Shows how much each participant needs to pay (negative) or receives (positive) monthly
    if monthly_cash_flow_data:
        monthly_cf_categories = [name for name, _ in monthly_cash_flow_data]
        monthly_cf_categories = monthly_cf_categories[::-1]
        
        monthly_cf_positive = [data['best_impact'] for _, data in monthly_cash_flow_data[::-1]]
        monthly_cf_negative = [data['worst_impact'] for _, data in monthly_cash_flow_data[::-1]]
        
        # Prepare hover text with range information
        monthly_cf_hover_negative = []
        monthly_cf_hover_positive = []
        for name, data in monthly_cash_flow_data[::-1]:
            sens_info = sensitivity_info.get(name, {})
            min_val = sens_info.get('min', 'N/A')
            max_val = sens_info.get('max', 'N/A')
            base_val = sens_info.get('base', 'N/A')
            
            # Get actual parameter values if available
            sens_data = sensitivities.get(name, {})
            worst_param = sens_data.get('worst_param_value', None)
            best_param = sens_data.get('best_param_value', None)
            
            if worst_param is not None:
                worst_display = f"{worst_param:.1f}" if isinstance(worst_param, float) else str(worst_param)
                min_val = worst_display
            if best_param is not None:
                best_display = f"{best_param:.1f}" if isinstance(best_param, float) else str(best_param)
                max_val = best_display
            
            # Format hover text for Monthly Cash Flow
            hover_text_neg = f"<b>{name}</b><br>"
            hover_text_neg += f"Parameter Range: {sens_info.get('min', 'N/A')} to {sens_info.get('max', 'N/A')}<br>"
            hover_text_neg += f"Base Case: {base_val}<br>"
            hover_text_neg += f"Worst Case Parameter: {min_val}<br>"
            hover_text_neg += f"Monthly Impact: %{{value:,.0f}} CHF<br>"
            hover_text_neg += f"Base Monthly CF: {data['base_monthly_cf']:,.0f} CHF<br>"
            hover_text_neg += f"Worst Monthly CF: {data['worst_monthly_cf']:,.0f} CHF<br>"
            hover_text_neg += f"<small>Annual: {data['worst_monthly_cf']*12:,.0f} CHF</small>"
            
            hover_text_pos = f"<b>{name}</b><br>"
            hover_text_pos += f"Parameter Range: {sens_info.get('min', 'N/A')} to {sens_info.get('max', 'N/A')}<br>"
            hover_text_pos += f"Base Case: {base_val}<br>"
            hover_text_pos += f"Best Case Parameter: {max_val}<br>"
            hover_text_pos += f"Monthly Impact: %{{value:,.0f}} CHF<br>"
            hover_text_pos += f"Base Monthly CF: {data['base_monthly_cf']:,.0f} CHF<br>"
            hover_text_pos += f"Best Monthly CF: {data['best_monthly_cf']:,.0f} CHF<br>"
            hover_text_pos += f"<small>Annual: {data['best_monthly_cf']*12:,.0f} CHF</small>"
            
            monthly_cf_hover_negative.append(hover_text_neg)
            monthly_cf_hover_positive.append(hover_text_pos)
        
        fig_tornado_monthly_cf = go.Figure()
        
        # Negative impacts (left side, red) - money they need to pay
        fig_tornado_monthly_cf.add_trace(go.Bar(
            name="Worst Case Impact",
            y=monthly_cf_categories,
            x=monthly_cf_negative,
            orientation='h',
            marker_color='#e74c3c',
            hovertemplate=monthly_cf_hover_negative,
            text=[f"{x:,.0f}" for x in monthly_cf_negative],
            textposition='outside'
        ))
        
        # Positive impacts (right side, green) - money they receive
        fig_tornado_monthly_cf.add_trace(go.Bar(
            name="Best Case Impact",
            y=monthly_cf_categories,
            x=monthly_cf_positive,
            orientation='h',
            marker_color='#2ecc71',
            hovertemplate=monthly_cf_hover_positive,
            text=[f"{x:,.0f}" for x in monthly_cf_positive],
            textposition='outside'
        ))
        
        template = get_chart_template()
        layout_updates = template.copy()
        layout_updates.update({
            'title': {
                'text': "Tornado Chart: Monthly Cash Flow per Investor Impact by Sensitivity Factor",
                'font': template['title_font'],
                'x': template['title_x'],
                'xanchor': template['title_xanchor'],
                'pad': template['title_pad']
            },
            'xaxis_title': "Monthly Cash Flow Impact (CHF per month per investor)",
            'yaxis_title': "Sensitivity Factor",
            'height': 550,
            'barmode': 'relative',
            'showlegend': True,
            'xaxis': dict(
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='#495057',
                showgrid=True,
                gridcolor=template['xaxis']['gridcolor'],
                gridwidth=template['xaxis']['gridwidth'],
                side='bottom'
            ),
            'yaxis': dict(
                showgrid=False,
                side='left'
            ),
            'margin': dict(l=150, r=50, t=80, b=60),
            'hovermode': 'closest',
            'plot_bgcolor': 'white',
            'paper_bgcolor': 'white'
        })
        fig_tornado_monthly_cf.update_layout(**layout_updates)
        
        charts_html.append(f'<div class="chart-container"><h3 style="margin-bottom: 20px; color: var(--primary);">Monthly Cash Flow per Investor Sensitivity Analysis</h3><p style="margin-bottom: 20px; color: #555; line-height: 1.7;">This chart shows the <strong>monthly cash flow impact</strong> for each investor in the property. This is the most practical metric, showing how much money each investor will need to <strong>pay monthly</strong> (negative values, left side in red) or will <strong>receive monthly</strong> (positive values, right side in green) under different scenarios. The monthly cash flow is calculated as the annual cash flow per investor divided by 12 months.<br><br><strong>Red bars (left)</strong> show worst-case scenarios where investors need to contribute money monthly to keep the investment running. <strong>Green bars (right)</strong> show best-case scenarios where investors receive monthly cash distributions.<br><br><strong>Hover over each bar</strong> to see the exact parameter values tested (minimum and maximum extremes), the monthly cash flow amounts, and the annual equivalent.</p>{fig_tornado_monthly_cf.to_html(include_plotlyjs="cdn", div_id="tornadoMonthlyCF")}</div>')
    
    # 1. Tornado Chart for Cap Rate (Unlevered) - SECOND CHART
    # Cap Rate = NOI / Purchase Price (industry standard unlevered metric)
    if cap_rate_data:
        cap_rate_categories = [name for name, _ in cap_rate_data]
        cap_rate_categories = cap_rate_categories[::-1]
        
        cap_rate_positive = [data['best_impact'] for _, data in cap_rate_data[::-1]]
        cap_rate_negative = [data['worst_impact'] for _, data in cap_rate_data[::-1]]
        
        # Prepare hover text with range information
        cap_rate_hover_negative = []
        cap_rate_hover_positive = []
        for name, data in cap_rate_data[::-1]:
            sens_info = sensitivity_info.get(name, {})
            min_val = sens_info.get('min', 'N/A')
            max_val = sens_info.get('max', 'N/A')
            base_val = sens_info.get('base', 'N/A')
            
            # Get actual parameter values if available
            sens_data = sensitivities.get(name, {})
            worst_param = sens_data.get('worst_param_value', None)
            best_param = sens_data.get('best_param_value', None)
            
            if worst_param is not None:
                worst_display = f"{worst_param:.1f}" if isinstance(worst_param, float) else str(worst_param)
                min_val = worst_display
            if best_param is not None:
                best_display = f"{best_param:.1f}" if isinstance(best_param, float) else str(best_param)
                max_val = best_display
            
            # Format hover text for Cap Rate
            hover_text_neg = f"<b>{name}</b><br>"
            hover_text_neg += f"Parameter Range: {sens_info.get('min', 'N/A')} to {sens_info.get('max', 'N/A')}<br>"
            hover_text_neg += f"Base Case: {base_val}<br>"
            hover_text_neg += f"Worst Case Parameter: {min_val}<br>"
            hover_text_neg += f"Cap Rate Impact: %{{value:.2f}} pp<br>"
            hover_text_neg += f"Base Cap Rate: {data['base_cap_rate']:.2f}%<br>"
            hover_text_neg += f"Worst Cap Rate: {data['worst_cap_rate']:.2f}%"
            
            hover_text_pos = f"<b>{name}</b><br>"
            hover_text_pos += f"Parameter Range: {sens_info.get('min', 'N/A')} to {sens_info.get('max', 'N/A')}<br>"
            hover_text_pos += f"Base Case: {base_val}<br>"
            hover_text_pos += f"Best Case Parameter: {max_val}<br>"
            hover_text_pos += f"Cap Rate Impact: %{{value:.2f}} pp<br>"
            hover_text_pos += f"Base Cap Rate: {data['base_cap_rate']:.2f}%<br>"
            hover_text_pos += f"Best Cap Rate: {data['best_cap_rate']:.2f}%"
            
            cap_rate_hover_negative.append(hover_text_neg)
            cap_rate_hover_positive.append(hover_text_pos)
        
        fig_tornado_cap_rate = go.Figure()
        
        # Negative impacts (left side, red)
        fig_tornado_cap_rate.add_trace(go.Bar(
            name="Worst Case Impact",
            y=cap_rate_categories,
            x=cap_rate_negative,
            orientation='h',
            marker_color='#e74c3c',
            hovertemplate=cap_rate_hover_negative,
            text=[f"{x:.2f} pp" for x in cap_rate_negative],
            textposition='outside'
        ))
        
        # Positive impacts (right side, green)
        fig_tornado_cap_rate.add_trace(go.Bar(
            name="Best Case Impact",
            y=cap_rate_categories,
            x=cap_rate_positive,
            orientation='h',
            marker_color='#2ecc71',
            hovertemplate=cap_rate_hover_positive,
            text=[f"{x:.2f} pp" for x in cap_rate_positive],
            textposition='outside'
        ))
        
        template = get_chart_template()
        layout_updates = template.copy()
        layout_updates.update({
            'title': {
                'text': "Tornado Chart: Cap Rate Impact by Sensitivity Factor (Unlevered)",
                'font': template['title_font'],
                'x': template['title_x'],
                'xanchor': template['title_xanchor'],
                'pad': template['title_pad']
            },
            'xaxis_title': "Cap Rate Impact (percentage points)",
            'yaxis_title': "Sensitivity Factor",
            'height': 550,
            'barmode': 'relative',
            'showlegend': True,
            'xaxis': dict(
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='#495057',
                showgrid=True,
                gridcolor=template['xaxis']['gridcolor'],
                gridwidth=template['xaxis']['gridwidth'],
                side='bottom'
            ),
            'yaxis': dict(
                showgrid=False,
                side='left'
            ),
            'margin': dict(l=150, r=50, t=80, b=60),
            'hovermode': 'closest',
            'plot_bgcolor': 'white',
            'paper_bgcolor': 'white'
        })
        fig_tornado_cap_rate.update_layout(**layout_updates)
        
        charts_html.append(f'<div class="chart-container"><h3 style="margin-bottom: 20px; color: var(--primary);">Cap Rate Sensitivity Analysis (Unlevered)</h3><p style="margin-bottom: 20px; color: #555; line-height: 1.7;">This chart shows the impact of each sensitivity factor on the <strong>Cap Rate</strong> (Capitalization Rate), which is calculated as Net Operating Income (NOI) divided by Purchase Price. Cap Rate is an <strong>unlevered metric</strong> that measures the property\'s operating performance independent of financing structure. It represents the unlevered yield on the property investment. Higher cap rates indicate better operating performance. <strong>Red bars (left)</strong> show scenarios that reduce the cap rate, <strong>green bars (right)</strong> show scenarios that increase it.<br><br><strong>Hover over each bar</strong> to see the exact parameter values tested (minimum and maximum extremes), the cap rate impact in percentage points, and the resulting cap rate values.</p>{fig_tornado_cap_rate.to_html(include_plotlyjs="cdn", div_id="tornadoCapRate")}</div>')
        
        # 0b. Tornado Chart for Cash-on-Cash Return (Levered) - SECOND CHART
        if cash_on_cash_data:
            coc_categories = [name for name, _ in cash_on_cash_data]
            coc_categories = coc_categories[::-1]
            
            coc_positive = [data['best_impact'] for _, data in cash_on_cash_data[::-1]]
            coc_negative = [data['worst_impact'] for _, data in cash_on_cash_data[::-1]]
            
            # Prepare hover text with range information
            coc_hover_negative = []
            coc_hover_positive = []
            for name, data in cash_on_cash_data[::-1]:
                sens_info = sensitivity_info.get(name, {})
                min_val = sens_info.get('min', 'N/A')
                max_val = sens_info.get('max', 'N/A')
                base_val = sens_info.get('base', 'N/A')
                
                # Get actual parameter values if available
                sens_data = sensitivities.get(name, {})
                best_param_val = sens_data.get('best_param_value', 'N/A')
                worst_param_val = sens_data.get('worst_param_value', 'N/A')
                
                # Format hover text for Cash-on-Cash Return
                hover_text_neg = f"<b>{name}</b><br>"
                hover_text_neg += f"Parameter Range: {min_val} to {max_val}<br>"
                hover_text_neg += f"Base Case: {base_val}<br>"
                hover_text_neg += f"Worst Case Parameter: {worst_param_val}<br>"
                hover_text_neg += f"Cash-on-Cash Impact: %{{value:.2f}}%<br>"
                hover_text_neg += f"Base CoC Return: {data['base_coc']:.2f}%<br>"
                hover_text_neg += f"Worst CoC Return: {data['worst_coc']:.2f}%"
                
                hover_text_pos = f"<b>{name}</b><br>"
                hover_text_pos += f"Parameter Range: {min_val} to {max_val}<br>"
                hover_text_pos += f"Base Case: {base_val}<br>"
                hover_text_pos += f"Best Case Parameter: {best_param_val}<br>"
                hover_text_pos += f"Cash-on-Cash Impact: %{{value:.2f}}%<br>"
                hover_text_pos += f"Base CoC Return: {data['base_coc']:.2f}%<br>"
                hover_text_pos += f"Best CoC Return: {data['best_coc']:.2f}%"
                
                coc_hover_negative.append(hover_text_neg)
                coc_hover_positive.append(hover_text_pos)
            
            fig_tornado_coc = go.Figure()
            
            # Negative impacts (left side, red)
            fig_tornado_coc.add_trace(go.Bar(
                name="Worst Case Impact",
                y=coc_categories,
                x=coc_negative,
                orientation='h',
                marker_color='#e74c3c',
                hovertemplate=coc_hover_negative,
                text=[f"{x:.2f}%" for x in coc_negative],
                textposition='outside'
            ))
            
            # Positive impacts (right side, green)
            fig_tornado_coc.add_trace(go.Bar(
                name="Best Case Impact",
                y=coc_categories,
                x=coc_positive,
                orientation='h',
                marker_color='#2ecc71',
                hovertemplate=coc_hover_positive,
                text=[f"{x:.2f}%" for x in coc_positive],
                textposition='outside'
            ))
            
            template = get_chart_template()
            layout_updates = template.copy()
            layout_updates.update({
                'title': {
                    'text': "Tornado Chart: Cash-on-Cash Return Impact by Sensitivity Factor (Levered)",
                    'font': template['title_font'],
                    'x': template['title_x'],
                    'xanchor': template['title_xanchor'],
                    'pad': template['title_pad']
                },
                'xaxis_title': "Cash-on-Cash Return Impact (percentage points)",
                'yaxis_title': "Sensitivity Factor",
                'height': 550,
                'barmode': 'relative',
                'showlegend': True,
                'xaxis': dict(
                    zeroline=True,
                    zerolinewidth=2,
                    zerolinecolor='#495057',
                    showgrid=True,
                    gridcolor=template['xaxis']['gridcolor'],
                    gridwidth=template['xaxis']['gridwidth']
                )
            })
            fig_tornado_coc.update_layout(**layout_updates)
            
            charts_html.append(f'<div class="chart-container"><h3 style="margin-bottom: 20px; color: var(--primary);">Cash-on-Cash Return Sensitivity Analysis (Levered)</h3><p style="margin-bottom: 20px; color: #555; line-height: 1.7;">This chart shows the impact of each sensitivity factor on the <strong>Cash-on-Cash Return</strong>, which is calculated as (Cash Flow After Debt Service / Initial Equity Investment) × 100. Cash-on-Cash Return is a <strong>levered metric</strong> that measures the annual return on the equity investment after debt service. It shows how much cash return you receive on your invested equity. Higher returns indicate better investment performance. Red bars (left) show scenarios that reduce the return, green bars (right) show scenarios that increase it.<br><br><strong>Hover over each bar</strong> to see the exact parameter values tested (minimum and maximum extremes) and the range covered by each sensitivity analysis.</p>{fig_tornado_coc.to_html(include_plotlyjs="cdn", div_id="tornadoCoC")}</div>')
    
    # 1. Tornado Chart for NPV - BIDIRECTIONAL
    # For tornado chart, we want bars extending from zero (negative left, positive right)
    npv_categories = [name for name, _, _ in npv_data]
    # Reverse for display (top to bottom)
    npv_categories = npv_categories[::-1]
    
    # Get best (positive) and worst (negative) impacts
    npv_positive = [data.get('npv_best_impact', 0) for _, data, _ in npv_data[::-1]]
    npv_negative = [data.get('npv_worst_impact', 0) for _, data, _ in npv_data[::-1]]
    
    # Prepare hover text with range information
    npv_hover_negative = []
    npv_hover_positive = []
    for name, data, _ in npv_data[::-1]:
        sens_info = sensitivity_info.get(name, {})
        min_val = sens_info.get('min', 'N/A')
        max_val = sens_info.get('max', 'N/A')
        base_val = sens_info.get('base', 'N/A')
        
        # Get actual parameter values if available
        worst_param = data.get('worst_param_value', None)
        best_param = data.get('best_param_value', None)
        
        if worst_param is not None:
            worst_display = f"{worst_param:.1f}" if isinstance(worst_param, float) else str(worst_param)
            min_val = worst_display
        if best_param is not None:
            best_display = f"{best_param:.1f}" if isinstance(best_param, float) else str(best_param)
            max_val = best_display
        
        npv_hover_negative.append(
            f"<b>{name}</b><br>" +
            f"Worst Case NPV Impact: {data.get('npv_worst_impact', 0):,.0f} CHF<br>" +
            f"Parameter Value: {min_val}<br>" +
            f"Range Tested: {sens_info.get('min', 'N/A')} to {sens_info.get('max', 'N/A')}<br>" +
            f"Base Case: {base_val}"
        )
        npv_hover_positive.append(
            f"<b>{name}</b><br>" +
            f"Best Case NPV Impact: {data.get('npv_best_impact', 0):,.0f} CHF<br>" +
            f"Parameter Value: {max_val}<br>" +
            f"Range Tested: {sens_info.get('min', 'N/A')} to {sens_info.get('max', 'N/A')}<br>" +
            f"Base Case: {base_val}"
        )
    
    fig_tornado_npv = go.Figure()
    
    # Negative impact bar (extends left from zero) - ALWAYS show even if zero
    fig_tornado_npv.add_trace(go.Bar(
        y=npv_categories,
        x=[v if v < 0 else 0 for v in npv_negative],  # Show 0 if positive
        orientation='h',
        name='Worst Case Impact',
        marker_color='#e74c3c',
        text=[f"{abs(v):,.0f}" if v < 0 else "" for v in npv_negative],
        textposition='outside',
        textfont=dict(color='#e74c3c', size=10),
        base=0,  # Bars start from zero
        hovertemplate='%{customdata}<extra></extra>',
        customdata=npv_hover_negative
    ))
    
    # Positive impact bar (extends right from zero) - ALWAYS show even if zero
    fig_tornado_npv.add_trace(go.Bar(
        y=npv_categories,
        x=[v if v > 0 else 0 for v in npv_positive],  # Show 0 if negative
        orientation='h',
        name='Best Case Impact',
        marker_color='#2ecc71',
        text=[f"{v:,.0f}" if v > 0 else "" for v in npv_positive],
        textposition='outside',
        textfont=dict(color='#2ecc71', size=10),
        base=0,  # Bars start from zero
        hovertemplate='%{customdata}<extra></extra>',
        customdata=npv_hover_positive
    ))
    
    template = get_chart_template()
    layout_updates = template.copy()
    layout_updates.update({
        'title': {
            'text': "Tornado Chart: NPV Impact Range by Sensitivity Factor",
            'font': template['title_font'],
            'x': template['title_x'],
            'xanchor': template['title_xanchor'],
            'pad': template['title_pad']
        },
        'xaxis_title': "NPV Impact (CHF)",
        'yaxis_title': "Sensitivity Factor",
        'height': 550,
        'barmode': 'relative',
        'showlegend': True,
        'xaxis': dict(
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='#495057',
            showgrid=True,
            gridcolor=template['xaxis']['gridcolor'],
            gridwidth=template['xaxis']['gridwidth']
        )
    })
    fig_tornado_npv.update_layout(**layout_updates)
    
    charts_html.append(f'<div class="chart-container"><h3 style="margin-bottom: 20px; color: var(--primary);">NPV Impact Analysis</h3><p style="margin-bottom: 20px; color: #555; line-height: 1.7;">This tornado chart shows how each sensitivity factor impacts the Net Present Value (NPV) of the investment over 15 years. NPV represents the total discounted value of all future cash flows. Red bars (left) show negative impact (reduces NPV), green bars (right) show positive impact (increases NPV). The longer the bar, the greater the impact.<br><br><strong>Hover over each bar</strong> to see the exact parameter values tested (minimum and maximum extremes) and the range covered by each sensitivity analysis. Each sensitivity shows both upper and lower extremes.</p>{fig_tornado_npv.to_html(include_plotlyjs="cdn", div_id="tornadoNPV")}</div>')
    
    # 2. Tornado Chart for IRR - BIDIRECTIONAL
    irr_categories = [name for name, _, _ in irr_data]
    irr_categories = irr_categories[::-1]
    
    irr_positive = [data.get('irr_best_impact', 0) for _, data, _ in irr_data[::-1]]
    irr_negative = [data.get('irr_worst_impact', 0) for _, data, _ in irr_data[::-1]]
    
    # Prepare hover text with range information
    irr_hover_negative = []
    irr_hover_positive = []
    for name, data, _ in irr_data[::-1]:
        sens_info = sensitivity_info.get(name, {})
        min_val = sens_info.get('min', 'N/A')
        max_val = sens_info.get('max', 'N/A')
        base_val = sens_info.get('base', 'N/A')
        
        # Get actual parameter values if available
        worst_param = data.get('worst_param_value', None)
        best_param = data.get('best_param_value', None)
        
        if worst_param is not None:
            worst_display = f"{worst_param:.1f}" if isinstance(worst_param, float) else str(worst_param)
            min_val = worst_display
        if best_param is not None:
            best_display = f"{best_param:.1f}" if isinstance(best_param, float) else str(best_param)
            max_val = best_display
        
        irr_hover_negative.append(
            f"<b>{name}</b><br>" +
            f"Worst Case IRR Impact: {data.get('irr_worst_impact', 0):.2f}%<br>" +
            f"Parameter Value: {min_val}<br>" +
            f"Range Tested: {sens_info.get('min', 'N/A')} to {sens_info.get('max', 'N/A')}<br>" +
            f"Base Case: {base_val}"
        )
        irr_hover_positive.append(
            f"<b>{name}</b><br>" +
            f"Best Case IRR Impact: {data.get('irr_best_impact', 0):.2f}%<br>" +
            f"Parameter Value: {max_val}<br>" +
            f"Range Tested: {sens_info.get('min', 'N/A')} to {sens_info.get('max', 'N/A')}<br>" +
            f"Base Case: {base_val}"
        )
    
    fig_tornado_irr = go.Figure()
    
    # Negative impact bar (extends left from zero) - ALWAYS show even if zero
    fig_tornado_irr.add_trace(go.Bar(
        y=irr_categories,
        x=[v if v < 0 else 0 for v in irr_negative],  # Show 0 if positive
        orientation='h',
        name='Worst Case Impact',
        marker_color='#e67e22',
        text=[f"{abs(v):.2f}%" if v < 0 else "" for v in irr_negative],
        textposition='outside',
        textfont=dict(color='#e67e22', size=10),
        base=0,  # Bars start from zero
        hovertemplate='%{customdata}<extra></extra>',
        customdata=irr_hover_negative
    ))
    
    # Positive impact bar (extends right from zero) - ALWAYS show even if zero
    fig_tornado_irr.add_trace(go.Bar(
        y=irr_categories,
        x=[v if v > 0 else 0 for v in irr_positive],  # Show 0 if negative
        orientation='h',
        name='Best Case Impact',
        marker_color='#2ecc71',
        text=[f"{v:.2f}%" if v > 0 else "" for v in irr_positive],
        textposition='outside',
        textfont=dict(color='#2ecc71', size=10),
        base=0,  # Bars start from zero
        hovertemplate='%{customdata}<extra></extra>',
        customdata=irr_hover_positive
    ))
    
    template = get_chart_template()
    layout_updates = template.copy()
    layout_updates.update({
        'title': {
            'text': "Tornado Chart: IRR Impact Range by Sensitivity Factor",
            'font': template['title_font'],
            'x': template['title_x'],
            'xanchor': template['title_xanchor'],
            'pad': template['title_pad']
        },
        'xaxis_title': "IRR Impact (%)",
        'yaxis_title': "Sensitivity Factor",
        'height': 550,
        'barmode': 'relative',
        'showlegend': True,
        'xaxis': dict(
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='#495057',
            showgrid=True,
            gridcolor=template['xaxis']['gridcolor'],
            gridwidth=template['xaxis']['gridwidth']
        )
    })
    fig_tornado_irr.update_layout(**layout_updates)
    
    charts_html.append(f'<div class="chart-container"><h3 style="margin-bottom: 20px; color: var(--primary);">IRR Impact Analysis</h3><p style="margin-bottom: 20px; color: #555; line-height: 1.7;">This tornado chart shows how each sensitivity factor impacts the Internal Rate of Return (IRR) of the investment. IRR is the annualized return percentage, including both operating cash flows and the property sale at the end of 15 years. Higher IRR means better returns. Red bars (left) show scenarios that reduce IRR, green bars (right) show scenarios that increase IRR.<br><br><strong>Hover over each bar</strong> to see the exact parameter values tested (minimum and maximum extremes) and the range covered by each sensitivity analysis. Each sensitivity shows both upper and lower extremes.</p>{fig_tornado_irr.to_html(include_plotlyjs=False, div_id="tornadoIRR")}</div>')
    
    # Generate comprehensive sensitivity impact table (sensitivity_info already retrieved above)
    sensitivity_table_html = generate_sensitivity_impact_table(
        monthly_cash_flow_data,
        cap_rate_data,
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
    
    template = get_chart_template()
    layout_updates = template.copy()
    layout_updates.update({
        'title': {
            'text': "Waterfall Chart: Cumulative IRR Downside Risk (Top 10 Worst Impacts)",
            'font': template['title_font'],
            'x': template['title_x'],
            'xanchor': template['title_xanchor'],
            'pad': template['title_pad']
        },
        'showlegend': False,
        'height': 550,
        'yaxis_title': "IRR (%)"
    })
    fig_waterfall_irr.update_layout(**layout_updates)
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
                "xaxis": {"categories": df['Total Utilities Annual (CHF)'].tolist(), "title": {"text": "Total Utilities Annual (CHF)"}},
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
                "xaxis": {"categories": df['Total Utilities Annual (CHF)'].tolist(), "title": {"text": "Total Utilities Annual (CHF)"}},
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
            <h3 style="color: #667eea; font-size: 1.2em; margin-bottom: 12px; margin-top: 20px;">{sens_name}</h3>
            <div class="sensitivity-card">
                <div class="intro-box" style="margin-bottom: 18px;">
                    <p style="margin-bottom: 10px; font-size: 0.9em; line-height: 1.6;"><strong>What this sensitivity evaluates:</strong> {sens_info.get('what_it_evaluates', sensitivity_descriptions.get(sens_name, 'This sensitivity tests how changes in this parameter affect the investment performance.'))}</p>
                    <p style="margin-bottom: 10px; font-size: 0.9em; line-height: 1.6;"><strong>Range tested:</strong> From <strong>{sens_info.get('min', 'N/A')}</strong> (worst case scenario) to <strong>{sens_info.get('max', 'N/A')}</strong> (best case scenario). Base case value: <strong>{sens_info.get('base', 'N/A')}</strong>.</p>
                    <p style="margin-bottom: 0; font-size: 0.9em; line-height: 1.6;"><strong>Context:</strong> {sens_info.get('description', sensitivity_descriptions.get(sens_name, 'This parameter is an important factor in determining the investment\'s financial performance.'))}</p>
                </div>
                {table_html}
            </div>
        </div>
        ''')
    
    return "\n".join(sections)


def generate_sensitivity_html(all_sensitivities: Dict[str, pd.DataFrame], charts: List[Tuple[str, go.Figure]], 
                              base_config: BaseCaseConfig, metrics: Dict = None, output_path: str = "website/report_sensitivity.html"):
    """Generate HTML report with sensitivity analyses using ApexCharts."""
    base_result = compute_annual_cash_flows(base_config)
    
    # Generate summary charts if metrics provided
    summary_charts_html = ""
    if metrics:
        summary_charts_html = generate_summary_charts(metrics, base_config, all_sensitivities)
    
    # Pre-calculate scenario configs and results for efficiency
    scenario_configs = None
    scenario_results = None
    if metrics:
        scenario_configs = create_scenario_configs(base_config, all_sensitivities, metrics)
        scenario_results = analyze_scenarios(scenario_configs)
    
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
    
    # Define sections for sidebar navigation
    sections = [
        {'id': 'executive-summary', 'title': 'Executive Summary', 'icon': 'fas fa-chart-line'},
        {'id': 'sensitivity-impact', 'title': 'Sensitivity Impact Analysis', 'icon': 'fas fa-chart-bar'},
        {'id': 'break-even', 'title': 'Break-Even Analysis', 'icon': 'fas fa-balance-scale'},
        {'id': 'sensitivity-ranking', 'title': 'Sensitivity Ranking', 'icon': 'fas fa-trophy'},
        {'id': 'statistical-analysis', 'title': 'Statistical Analysis', 'icon': 'fas fa-chart-bar'},
        {'id': 'two-way-sensitivity', 'title': 'Two-Way Sensitivity', 'icon': 'fas fa-th'},
        {'id': 'scenario-analysis', 'title': 'Scenario Analysis', 'icon': 'fas fa-project-diagram'},
        {'id': 'critical-thresholds', 'title': 'Critical Thresholds', 'icon': 'fas fa-exclamation-triangle'},
        {'id': 'detailed-sensitivities', 'title': 'Detailed Analyses', 'icon': 'fas fa-list'},
        {'id': 'methodology', 'title': 'Methodology & Assumptions', 'icon': 'fas fa-book'},
    ]
    
    # Generate sidebar and toolbar
    sidebar_html = generate_sidebar_navigation(sections)
    toolbar_html = generate_top_toolbar(
        report_title="Sensitivity Analysis",
        back_link="index.html",
        subtitle="Engelberg Property Investment - Comprehensive Scenario Analysis"
    )
    
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
        {generate_shared_layout_css()}
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
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            min-height: 100vh;
        }}
        
        .header {{
            background: var(--gradient-1);
            color: white;
            padding: 30px 50px;
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -10%;
            width: 400px;
            height: 400px;
            background: rgba(255,255,255,0.1);
            border-radius: 50%;
            animation: float 20s infinite ease-in-out;
        }}
        
        @keyframes float {{
            0%, 100% {{ transform: translate(0, 0) rotate(0deg); }}
            50% {{ transform: translate(-30px, -30px) rotate(180deg); }}
        }}
        
        .header h1 {{
            font-size: 2.0em;
            font-weight: 700;
            margin-bottom: 6px;
            letter-spacing: -0.5px;
            position: relative;
            z-index: 1;
        }}
        
        .header .subtitle {{
            font-size: 0.95em;
            opacity: 0.95;
            margin-bottom: 6px;
            position: relative;
            z-index: 1;
        }}
        
        .header .meta {{
            font-size: 0.85em;
            opacity: 0.85;
            margin-top: 8px;
            position: relative;
            z-index: 1;
        }}
        
        .kpi-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: var(--shadow-sm);
            transition: all 0.2s ease;
            position: relative;
            overflow: hidden;
            border-left: 3px solid var(--primary);
        }}
        
        .kpi-card:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }}
        
        .content {{
            padding: 30px 40px;
        }}
        
        .dashboard {{
            padding: 30px 40px;
            background: #f5f7fa;
        }}
        
        .section {{
            padding: 20px 30px;
            background: white;
            margin-bottom: 0;
        }}
        
        .section:nth-child(even) {{
            background: #f8f9fa;
        }}
        
        .section h2 {{
            font-size: 1.5em;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid var(--secondary);
            letter-spacing: -0.5px;
        }}
        
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 18px;
            margin-bottom: 30px;
        }}
        
        .kpi-card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
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
            transform: translateY(-5px);
            box-shadow: var(--shadow-lg);
        }}
        
        .kpi-card:hover::before {{
            transform: scaleX(1);
        }}
        
        .kpi-label {{
            font-size: 0.8em;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
            font-weight: 600;
        }}
        
        .kpi-value {{
            font-size: 2.0em;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 6px;
            letter-spacing: -1px;
        }}
        
        .kpi-value.positive {{
            color: var(--success);
        }}
        
        .kpi-value.negative {{
            color: var(--danger);
        }}
        
        .kpi-description {{
            font-size: 0.85em;
            color: #868e96;
            margin-top: 6px;
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
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #0f3460;
            margin-bottom: 20px;
        }}
        
        .intro-box p {{
            font-size: 0.9em;
            color: #495057;
            margin-bottom: 12px;
            line-height: 1.6;
        }}
        
        .intro-box p:last-child {{
            margin-bottom: 0;
        }}
        
        .intro-box strong {{
            color: #1a1a2e;
            font-weight: 600;
        }}
        
        .chart-container {{
            margin: 20px 0;
            background: white;
            padding: 24px;
            border-radius: 12px;
            border: 1px solid #e8ecef;
            box-shadow: var(--shadow-md);
            transition: all 0.3s;
        }}
        
        .chart-container:hover {{
            transform: translateY(-3px);
            box-shadow: var(--shadow-lg);
        }}
        
        .chart-section-title {{
            font-size: 1.0em;
            color: #495057;
            margin-bottom: 18px;
            font-weight: 500;
            line-height: 1.5;
        }}
        
        .sensitivity-section {{
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #e8ecef;
        }}
        
        .sensitivity-section h3 {{
            color: #1a1a2e;
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 2px solid #dee2e6;
        }}
        
        .sensitivity-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #0f3460;
        }}
        
        .sensitivity-card p {{
            line-height: 1.6;
            color: #495057;
            margin-bottom: 15px;
            font-size: 0.9em;
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
    <div class="layout-container">
        {toolbar_html}
        {sidebar_html}
        <div class="main-content">
            <!-- Executive Summary with KPIs -->
            <div class="section" id="executive-summary">
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
            <div class="section" id="sensitivity-impact">
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
            
            <!-- Break-Even Analysis -->
            {generate_break_even_analysis_html(calculate_break_even_points(all_sensitivities, base_config), base_config)}
            
            <!-- Sensitivity Ranking -->
            {generate_sensitivity_ranking_table(metrics) if metrics and 'ranking' in metrics else ''}
            
            <!-- Statistical Analysis -->
            {generate_statistical_analysis_html(metrics.get('statistics', {})) if metrics and 'statistics' in metrics else ''}
            
            <!-- Two-Way Sensitivity Analysis -->
            {generate_two_way_sensitivity_html(all_sensitivities, base_config, metrics) if metrics else ''}
            
            <!-- Scenario Analysis -->
            {generate_scenario_analysis_html(scenario_configs, scenario_results) if scenario_configs and scenario_results is not None and not scenario_results.empty else ''}
            
            <!-- Critical Thresholds -->
            {generate_critical_thresholds_html(identify_critical_thresholds(all_sensitivities, base_config))}
            
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
            <div class="section" id="detailed-sensitivities">
                <h2>Detailed Sensitivity Analyses</h2>
                {generate_detailed_sensitivity_sections_with_charts(all_sensitivities, sensitivity_descriptions, base_config)}
            </div>
            
            <!-- Methodology & Assumptions -->
            <div class="section" id="methodology">
                <h2><i class="fas fa-book"></i> Methodology & Assumptions</h2>
                <div class="sensitivity-card">
                    <h3 style="font-size: 1.1em; margin-bottom: 15px; color: var(--primary);">Sensitivity Analysis Methodology</h3>
                    <p style="font-size: 0.9em; line-height: 1.7; margin-bottom: 15px;">
                        This sensitivity analysis employs a comprehensive one-way and two-way parameter variation approach to assess investment risk and return variability. 
                        Each parameter is systematically varied across a realistic range while holding all other parameters constant at their base case values.
                    </p>
                    <p style="font-size: 0.9em; line-height: 1.7; margin-bottom: 15px;">
                        <strong>One-Way Sensitivity:</strong> Tests individual parameter impacts by varying one parameter at a time. This approach isolates the effect of each factor 
                        and helps identify which parameters have the greatest impact on investment performance.
                    </p>
                    <p style="font-size: 0.9em; line-height: 1.7; margin-bottom: 15px;">
                        <strong>Two-Way Sensitivity:</strong> Examines parameter interactions by varying two parameters simultaneously. This reveals how parameters interact and 
                        identifies combinations that lead to optimal or suboptimal outcomes.
                    </p>
                    <p style="font-size: 0.9em; line-height: 1.7; margin-bottom: 15px;">
                        <strong>Scenario Analysis:</strong> Combines multiple parameter changes to model realistic scenarios (Optimistic, Base, Pessimistic). 
                        This provides a framework for understanding the range of possible outcomes under different market conditions.
                    </p>
                    
                    <h3 style="font-size: 1.1em; margin-top: 30px; margin-bottom: 15px; color: var(--primary);">Parameter Range Justifications</h3>
                    <ul style="font-size: 0.9em; line-height: 1.7; margin-left: 20px; margin-bottom: 15px;">
                        <li><strong>Occupancy Rate (30-70%):</strong> Based on Engelberg market data and seasonal patterns. 30% represents low-demand scenarios, 70% represents strong demand.</li>
                        <li><strong>Daily Rate (120-300 CHF):</strong> Reflects pricing strategies from discounted off-peak rates to premium peak-season rates, calibrated to local market conditions.</li>
                        <li><strong>Interest Rate (1.2-3.5%):</strong> Covers current low-rate environment to historical averages, accounting for potential rate increases.</li>
                        <li><strong>Management Fee (20-35%):</strong> Represents typical range for property management services in Swiss vacation rental markets.</li>
                        <li><strong>Loan-to-Value (60-80%):</strong> Standard range for Swiss real estate financing, balancing leverage and equity requirements.</li>
                    </ul>
                    
                    <h3 style="font-size: 1.1em; margin-top: 30px; margin-bottom: 15px; color: var(--primary);">Key Assumptions</h3>
                    <ul style="font-size: 0.9em; line-height: 1.7; margin-left: 20px; margin-bottom: 15px;">
                        <li><strong>Time Horizon:</strong> 15-year investment period with property sale at end of period</li>
                        <li><strong>Inflation Rate:</strong> 2% annual inflation applied to revenues and variable expenses</li>
                        <li><strong>Property Appreciation:</strong> 2.5% annual appreciation rate</li>
                        <li><strong>Discount Rate:</strong> 3% for NPV calculations (realistic for real estate investments)</li>
                        <li><strong>Tax Considerations:</strong> Analysis is pre-tax; actual returns may vary based on individual tax situations</li>
                        <li><strong>Market Stability:</strong> Assumes no major market disruptions or regulatory changes</li>
                    </ul>
                    
                    <h3 style="font-size: 1.1em; margin-top: 30px; margin-bottom: 15px; color: var(--primary);">Limitations</h3>
                    <ul style="font-size: 0.9em; line-height: 1.7; margin-left: 20px; margin-bottom: 15px;">
                        <li><strong>One-Way Analysis Limitation:</strong> One-way sensitivity assumes parameters are independent. In reality, parameters may be correlated (e.g., higher occupancy may require lower rates).</li>
                        <li><strong>Static Assumptions:</strong> Analysis uses fixed assumptions for inflation, appreciation, and discount rates. Actual rates may vary over time.</li>
                        <li><strong>No Tax Considerations:</strong> Analysis is pre-tax. Tax benefits (depreciation, deductions) and tax liabilities may significantly impact actual returns.</li>
                        <li><strong>Market Risk:</strong> Analysis does not account for market crashes, regulatory changes, or other black swan events.</li>
                        <li><strong>Operating Assumptions:</strong> Assumes consistent property management quality and maintenance standards. Actual operating performance may vary.</li>
                        <li><strong>Financing Assumptions:</strong> Assumes fixed-rate financing. Variable-rate mortgages introduce additional interest rate risk.</li>
                    </ul>
                    
                    <h3 style="font-size: 1.1em; margin-top: 30px; margin-bottom: 15px; color: var(--primary);">Industry Benchmarks</h3>
                    <ul style="font-size: 0.9em; line-height: 1.7; margin-left: 20px; margin-bottom: 15px;">
                        <li><strong>Cap Rates:</strong> Swiss vacation rental properties typically show cap rates of 3-6%, depending on location and property type</li>
                        <li><strong>Occupancy Rates:</strong> Engelberg vacation rentals typically achieve 40-60% annual occupancy, with strong seasonality</li>
                        <li><strong>Management Fees:</strong> Standard range is 20-30% of gross rental income for full-service management</li>
                        <li><strong>Cash-on-Cash Returns:</strong> Levered vacation rental investments typically target 5-10% cash-on-cash returns</li>
                        <li><strong>IRR Targets:</strong> Real estate investors typically target 8-12% IRR for vacation rental properties</li>
                    </ul>
                    
                    <div style="margin-top: 30px; padding: 20px; background: #e7f3ff; border-radius: 8px; border-left: 4px solid #17a2b8;">
                        <p style="font-size: 0.9em; line-height: 1.7; margin: 0;">
                            <strong>Note:</strong> This analysis is a tool for decision-making and risk assessment. It should be used in conjunction with professional financial advice, 
                            market research, and consideration of personal circumstances. Actual investment performance may differ from projections due to market conditions, 
                            operational factors, and unforeseen events.
                        </p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer" style="margin-top: 40px; padding: 30px; background: #f8f9fa; text-align: center; border-top: 1px solid #dee2e6;">
            <p style="margin: 0; font-size: 0.9em; color: #6c757d;">Engelberg Property Investment - Sensitivity Analysis</p>
            <p style="margin: 5px 0 0 0; font-size: 0.85em; color: #6c757d;">Generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}</p>
            <p style="margin: 5px 0 0 0; font-size: 0.8em; color: #adb5bd;">For detailed numerical data, please refer to the Excel export file.</p>
        </div>
        </div>
    </div>
    
    {generate_shared_layout_js()}
    <script>
        // Additional JavaScript for interactivity and animations
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
    # IMPORTANT: This must use the SAME base case as analysis_base_case.py
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
    os.makedirs("website", exist_ok=True)
    
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
    print(f"[+] HTML report: website/report_sensitivity.html")
    print("=" * 70)


if __name__ == "__main__":
    main()


