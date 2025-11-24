"""
Real Estate Investment Simulation for Engelberg Property
Refined version with comprehensive financial modeling
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime


# -----------------------------
# Data classes for parameters
# -----------------------------

@dataclass
class FinancingParams:
    purchase_price: float  # CHF
    ltv: float             # loan to value, for example 0.75
    interest_rate: float   # annual interest rate, for example 0.019
    amortization_rate: float  # annual amortization rate as percent of initial loan
    num_owners: int

    @property
    def loan_amount(self) -> float:
        return self.purchase_price * self.ltv

    @property
    def equity_total(self) -> float:
        return self.purchase_price - self.loan_amount

    @property
    def equity_per_owner(self) -> float:
        return self.equity_total / self.num_owners

    @property
    def annual_interest(self) -> float:
        return self.loan_amount * self.interest_rate

    @property
    def annual_amortization(self) -> float:
        return self.loan_amount * self.amortization_rate

    @property
    def annual_debt_service(self) -> float:
        return self.annual_interest + self.annual_amortization


@dataclass
class SeasonalParams:
    """Parameters for each season in Engelberg."""
    name: str
    months: List[int]  # Month numbers (1-12)
    occupancy_rate: float  # Occupancy rate for this season
    average_daily_rate: float  # CHF per night for this season
    nights_in_season: int  # Total nights in this season
    
    @property
    def rented_nights(self) -> float:
        return self.nights_in_season * self.occupancy_rate
    
    @property
    def season_income(self) -> float:
        return self.rented_nights * self.average_daily_rate


@dataclass
class RentalParams:
    owner_nights_per_person: int
    num_owners: int
    occupancy_rate: float       # share of rentable nights that are occupied (legacy - used if no seasons)
    average_daily_rate: float   # CHF per night (legacy - used if no seasons)
    days_per_year: int = 365
    seasons: Optional[List[SeasonalParams]] = None  # Seasonal breakdown (if provided, overrides occupancy_rate and average_daily_rate)

    @property
    def total_owner_nights(self) -> int:
        return self.owner_nights_per_person * self.num_owners

    @property
    def rentable_nights(self) -> int:
        return self.days_per_year - self.total_owner_nights

    @property
    def rented_nights(self) -> float:
        """Calculate total rented nights, accounting for seasons if provided."""
        if self.seasons:
            return sum(season.rented_nights for season in self.seasons)
        return self.rentable_nights * self.occupancy_rate

    @property
    def gross_rental_income(self) -> float:
        """Calculate gross rental income, accounting for seasonal rates if provided."""
        if self.seasons:
            return sum(season.season_income for season in self.seasons)
        return self.rented_nights * self.average_daily_rate
    
    def get_seasonal_breakdown(self) -> Dict[str, Dict[str, float]]:
        """Get detailed breakdown by season."""
        if not self.seasons:
            return {
                'Annual': {
                    'nights': self.rented_nights,
                    'income': self.gross_rental_income,
                    'rate': self.average_daily_rate,
                    'occupancy': self.occupancy_rate
                }
            }
        
        breakdown = {}
        for season in self.seasons:
            breakdown[season.name] = {
                'nights': season.rented_nights,
                'income': season.season_income,
                'rate': season.average_daily_rate,
                'occupancy': season.occupancy_rate,
                'available_nights': season.nights_in_season
            }
        return breakdown


@dataclass
class ExpenseParams:
    property_management_fee_rate: float  # share of gross rental revenue, for example 0.25
    cleaning_cost_per_stay: float       # CHF
    average_length_of_stay: float       # nights per stay
    tourist_tax_per_person_per_night: float  # CHF
    avg_guests_per_night: float
    insurance_annual: float             # CHF
    utilities_annual: float             # CHF
    maintenance_rate: float             # percent of property value per year
    property_value: float               # CHF

    def property_management_cost(self, gross_rental_income: float) -> float:
        return gross_rental_income * self.property_management_fee_rate

    def cleaning_cost(self, rented_nights: float) -> float:
        # number of stays equals rented nights divided by average stay length
        num_stays = rented_nights / self.average_length_of_stay
        return num_stays * self.cleaning_cost_per_stay

    def tourist_tax(self, rented_nights: float) -> float:
        return rented_nights * self.avg_guests_per_night * self.tourist_tax_per_person_per_night

    @property
    def maintenance_reserve(self) -> float:
        return self.property_value * self.maintenance_rate


@dataclass
class BaseCaseConfig:
    financing: FinancingParams
    rental: RentalParams
    expenses: ExpenseParams


# -----------------------------
# Base case configuration
# -----------------------------

def create_base_case_config() -> BaseCaseConfig:
    """
    Create the base case configuration with seasonal parameters for Engelberg.
    
    ⚠️ SINGLE SOURCE OF TRUTH ⚠️
    This function defines the base case scenario. ALL other analyses
    (sensitivity, Monte Carlo, etc.) MUST reference this base case to ensure
    consistency across the entire codebase.
    
    DO NOT create alternative base case configurations in other scripts.
    Always use this function and then apply variations using apply_sensitivity().
    
    Engelberg has three distinct seasons:
    1. Winter Peak (Dec-Mar): Ski season, highest rates and occupancy
    2. Summer Peak (Jun-Sep): Hiking and mountain activities
    3. Off-Peak (Apr-May, Oct-Nov): Shoulder seasons with lower demand
    """
    purchase_price = 1_300_000.0
    num_owners = 4
    
    # Calculate total owner nights (distributed across year)
    total_owner_nights = 5 * num_owners  # 20 nights total
    
    # Days per month (approximate)
    days_per_month = {
        1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
        7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
    }
    
    # Define seasons based on Engelberg tourism patterns
    # Winter Peak: December, January, February, March (ski season)
    winter_months = [12, 1, 2, 3]
    winter_nights = sum(days_per_month[m] for m in winter_months)  # 120 nights
    
    # Summer Peak: June, July, August, September (hiking season)
    summer_months = [6, 7, 8, 9]
    summer_nights = sum(days_per_month[m] for m in summer_months)  # 122 nights
    
    # Off-Peak: April, May, October, November (shoulder seasons)
    offpeak_months = [4, 5, 10, 11]
    offpeak_nights = sum(days_per_month[m] for m in offpeak_months)  # 123 nights
    
    # Distribute owner nights proportionally (more in peak seasons)
    # Winter: 8 nights, Summer: 7 nights, Off-peak: 5 nights
    owner_nights_winter = 8
    owner_nights_summer = 7
    owner_nights_offpeak = 5
    
    # Calculate rentable nights per season
    rentable_winter = winter_nights - owner_nights_winter
    rentable_summer = summer_nights - owner_nights_summer
    rentable_offpeak = offpeak_nights - owner_nights_offpeak
    
    # Engelberg-specific seasonal parameters (based on Swiss mountain resort data)
    # Updated to average 50% overall occupancy
    # Winter Peak: High demand, premium rates
    winter_season = SeasonalParams(
        name="Winter Peak (Ski Season)",
        months=winter_months,
        occupancy_rate=0.60,  # 60% occupancy during ski season (reduced from 75%)
        average_daily_rate=380.0,  # Premium rates: 350-450 CHF typical for Engelberg
        nights_in_season=rentable_winter
    )
    
    # Summer Peak: Good demand, moderate-high rates
    summer_season = SeasonalParams(
        name="Summer Peak (Hiking Season)",
        months=summer_months,
        occupancy_rate=0.50,  # 50% occupancy during summer (reduced from 65%)
        average_daily_rate=320.0,  # Good rates: 280-360 CHF typical
        nights_in_season=rentable_summer
    )
    
    # Off-Peak: Lower demand, discounted rates
    offpeak_season = SeasonalParams(
        name="Off-Peak (Shoulder Seasons)",
        months=offpeak_months,
        occupancy_rate=0.40,  # 40% occupancy during shoulder seasons (reduced from 45%)
        average_daily_rate=240.0,  # Discounted rates: 200-280 CHF
        nights_in_season=rentable_offpeak
    )
    
    financing = FinancingParams(
        purchase_price=purchase_price,
        ltv=0.75,               # 75 percent loan to value
        interest_rate=0.019,    # 1.9 percent interest
        amortization_rate=0.01, # 1 percent amortization on initial loan
        num_owners=num_owners
    )

    rental = RentalParams(
        owner_nights_per_person=5,    # five nights per owner (distributed across seasons)
        num_owners=num_owners,
        occupancy_rate=0.60,          # legacy - not used when seasons are provided
        average_daily_rate=280.0,     # legacy - not used when seasons are provided
        seasons=[winter_season, summer_season, offpeak_season]  # Seasonal breakdown
    )

    expenses = ExpenseParams(
        property_management_fee_rate=0.20,  # twenty percent of gross rental income (cleaning is separate)
        cleaning_cost_per_stay=80.0,        # cleaning cost per stay (variable with occupancy and nights)
        average_length_of_stay=1.7,         # 1.7 nights per stay (reduced from 2.0)
        tourist_tax_per_person_per_night=3.0,
        avg_guests_per_night=2.0,
        insurance_annual=1_000.0,
        utilities_annual=3_000.0,
        maintenance_rate=0.01,             # one percent of property value per year
        property_value=purchase_price
    )

    return BaseCaseConfig(
        financing=financing,
        rental=rental,
        expenses=expenses
    )


# -----------------------------
# Core calculation logic
# -----------------------------

def compute_annual_cash_flows(config: BaseCaseConfig) -> Dict[str, float]:
    """
    Compute annual cash flows and key financial metrics.
    
    Returns a dictionary with all calculated values.
    """
    f = config.financing
    r = config.rental
    e = config.expenses

    # Revenue
    gross_rental_income = r.gross_rental_income
    rented_nights = r.rented_nights

    # Operating Expenses
    # Note: In base case, cleaning is included in property management fee (30%)
    # But if cleaning_cost_per_stay > 0, it means cleaning is separate and should be included
    property_management_cost = e.property_management_cost(gross_rental_income)
    
    # Calculate cleaning cost if it's separate (not included in management fee)
    # If cleaning_cost_per_stay is 0, cleaning is included in management fee
    if e.cleaning_cost_per_stay > 0:
        cleaning_cost = e.cleaning_cost(rented_nights)
    else:
        cleaning_cost = 0.0  # Cleaning is included in property management fee
    
    tourist_tax = e.tourist_tax(rented_nights)
    insurance = e.insurance_annual
    utilities = e.utilities_annual
    maintenance_reserve = e.maintenance_reserve

    total_operating_expenses = (
        property_management_cost
        + cleaning_cost  # Include cleaning cost if it's separate
        + tourist_tax
        + insurance
        + utilities
        + maintenance_reserve
    )

    # Net Operating Income
    net_operating_income = gross_rental_income - total_operating_expenses

    # Debt Service
    debt_service = f.annual_debt_service
    interest_payment = f.annual_interest
    amortization_payment = f.annual_amortization

    # Cash Flow
    cash_flow_after_debt_service = net_operating_income - debt_service
    cash_flow_per_owner = cash_flow_after_debt_service / f.num_owners

    # Additional Metrics
    cap_rate = (net_operating_income / f.purchase_price) * 100
    cash_on_cash_return = (cash_flow_after_debt_service / f.equity_total) * 100
    debt_coverage_ratio = net_operating_income / debt_service if debt_service > 0 else 0
    operating_expense_ratio = (total_operating_expenses / gross_rental_income * 100) if gross_rental_income > 0 else 0

    result = {
        # Revenue
        "gross_rental_income": gross_rental_income,
        "rented_nights": rented_nights,
        "rentable_nights": r.rentable_nights,
        "total_owner_nights": r.total_owner_nights,
        
        # Operating Expenses (detailed)
        "property_management_cost": property_management_cost,
        "cleaning_cost": cleaning_cost,
        "tourist_tax": tourist_tax,
        "insurance": insurance,
        "utilities": utilities,
        "maintenance_reserve": maintenance_reserve,
        "total_operating_expenses": total_operating_expenses,
        
        # Net Operating Income
        "net_operating_income": net_operating_income,
        
        # Debt Service (detailed)
        "interest_payment": interest_payment,
        "amortization_payment": amortization_payment,
        "debt_service": debt_service,
        
        # Cash Flow
        "cash_flow_after_debt_service": cash_flow_after_debt_service,
        "cash_flow_per_owner": cash_flow_per_owner,
        
        # Financing
        "equity_total": f.equity_total,
        "equity_per_owner": f.equity_per_owner,
        "loan_amount": f.loan_amount,
        "purchase_price": f.purchase_price,
        
        # Key Performance Indicators
        "cap_rate_pct": cap_rate,
        "cash_on_cash_return_pct": cash_on_cash_return,
        "debt_coverage_ratio": debt_coverage_ratio,
        "operating_expense_ratio_pct": operating_expense_ratio,
    }
    
    # Add seasonal breakdown if seasons are defined
    if r.seasons:
        result["seasonal_breakdown"] = r.get_seasonal_breakdown()
        # Calculate weighted average daily rate
        total_income = sum(season.season_income for season in r.seasons)
        total_nights = sum(season.rented_nights for season in r.seasons)
        result["average_daily_rate"] = total_income / total_nights if total_nights > 0 else 0
        result["overall_occupancy_rate"] = total_nights / r.rentable_nights if r.rentable_nights > 0 else 0
    else:
        result["average_daily_rate"] = r.average_daily_rate
        result["overall_occupancy_rate"] = r.occupancy_rate
    
    return result


def compute_15_year_projection(config: BaseCaseConfig, start_year: int = 2026, 
                               inflation_rate: float = 0.02, property_appreciation_rate: float = 0.01) -> List[Dict[str, any]]:
    """
    Compute 15-year projection of cash flows and financial metrics.
    
    Assumptions:
    - Purchase in January of start_year
    - Loan amount decreases each year due to amortization
    - Interest is calculated on remaining loan balance
    - Inflation applied to revenue and variable expenses (default 2%)
    - Property appreciation applied annually (default 1%)
    
    Returns a list of dictionaries, one for each year.
    """
    projection = []
    current_loan = config.financing.loan_amount
    current_property_value = config.financing.purchase_price
    year = start_year
    
    # Base year results (no inflation)
    base_result = compute_annual_cash_flows(config)
    base_gross_income = base_result['gross_rental_income']
    base_property_mgmt = base_result['property_management_cost']
    base_tourist_tax = base_result['tourist_tax']
    base_insurance = base_result['insurance']
    base_utilities = base_result['utilities']
    base_maintenance = base_result['maintenance_reserve']
    
    for year_num in range(1, 16):  # Years 1-15
        # Apply inflation and appreciation
        inflation_factor = (1 + inflation_rate) ** (year_num - 1)
        appreciation_factor = (1 + property_appreciation_rate) ** (year_num - 1)
        
        # Inflated revenue and variable expenses
        gross_rental_income = base_gross_income * inflation_factor
        property_management_cost = base_property_mgmt * inflation_factor
        tourist_tax = base_tourist_tax * inflation_factor
        
        # Fixed expenses (insurance, utilities) also inflate
        insurance = base_insurance * inflation_factor
        utilities = base_utilities * inflation_factor
        
        # Maintenance reserve based on appreciated property value
        current_property_value = config.financing.purchase_price * appreciation_factor
        maintenance_reserve = current_property_value * config.expenses.maintenance_rate
        
        total_operating_expenses = (
            property_management_cost +
            tourist_tax +
            insurance +
            utilities +
            maintenance_reserve
        )
        
        net_operating_income = gross_rental_income - total_operating_expenses
        
        # Calculate debt service based on current loan balance
        interest_payment = current_loan * config.financing.interest_rate
        amortization_payment = config.financing.loan_amount * config.financing.amortization_rate
        debt_service = interest_payment + amortization_payment
        
        cash_flow_after_debt_service = net_operating_income - debt_service
        cash_flow_per_owner = cash_flow_after_debt_service / config.financing.num_owners
        
        # Calculate metrics
        debt_coverage_ratio = net_operating_income / debt_service if debt_service > 0 else 0
        cap_rate = (net_operating_income / current_property_value) * 100
        
        # Update loan balance after calculating debt service for this year
        # (loan balance at start of year is used for interest calculation)
        current_loan -= amortization_payment
        
        annual_results = {
            'year': year,
            'year_number': year_num,
            'inflation_factor': inflation_factor,
            'appreciation_factor': appreciation_factor,
            'property_value': current_property_value,
            'gross_rental_income': gross_rental_income,
            'total_operating_expenses': total_operating_expenses,
            'net_operating_income': net_operating_income,
            'interest_payment': interest_payment,
            'amortization_payment': amortization_payment,
            'debt_service': debt_service,
            'cash_flow_after_debt_service': cash_flow_after_debt_service,
            'cash_flow_per_owner': cash_flow_per_owner,
            'remaining_loan_balance': current_loan,  # Balance at end of year (after amortization)
            'debt_coverage_ratio': debt_coverage_ratio,
            'cap_rate_pct': cap_rate,
        }
        
        projection.append(annual_results)
        year += 1
    
    return projection


def calculate_irr(cash_flows: List[float], initial_investment: float, sale_proceeds: float = 0) -> float:
    """
    Calculate Internal Rate of Return (IRR) using iterative method.
    
    Args:
        cash_flows: List of annual cash flows (positive for returns)
        initial_investment: Initial equity investment (positive)
        sale_proceeds: Sale proceeds at end of period (added to final cash flow)
    
    Returns:
        IRR as a decimal (e.g., 0.05 for 5%)
    """
    # Prepare cash flow array
    cf_array = [-initial_investment] + cash_flows
    if sale_proceeds > 0:
        cf_array[-1] += sale_proceeds
    
    # Define NPV function
    def npv(rate):
        try:
            return sum(cf / (1 + rate) ** i for i, cf in enumerate(cf_array))
        except:
            return float('inf')
    
    # Check if we have a sign change (required for IRR)
    npv_low = npv(-0.99)  # -99%
    npv_high = npv(9.99)  # 999%
    
    # If both are positive or both negative, no IRR exists
    if (npv_low > 0 and npv_high > 0) or (npv_low < 0 and npv_high < 0):
        # Try to find a reasonable rate
        for test_rate in [-0.5, -0.2, -0.1, 0.0, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0]:
            if abs(npv(test_rate)) < abs(initial_investment) * 0.01:  # Within 1% of initial investment
                return test_rate
        return 0.0
    
    # Binary search for IRR (where NPV = 0)
    low, high = -0.99, 9.99
    tolerance = 1e-8
    max_iterations = 200
    
    for iteration in range(max_iterations):
        mid = (low + high) / 2
        npv_mid = npv(mid)
        
        if abs(npv_mid) < tolerance:
            return mid
        
        if npv_mid > 0:
            low = mid
        else:
            high = mid
        
        if abs(high - low) < tolerance:
            break
    
    # Return the best estimate
    final_rate = (low + high) / 2
    return final_rate if abs(npv(final_rate)) < abs(initial_investment) * 0.1 else 0.0


def calculate_irrs_from_projection(projection: List[Dict], initial_equity: float, 
                                   final_property_value: float, final_loan_balance: float,
                                   num_owners: int = 4, purchase_price: float = None) -> Dict[str, float]:
    """
    Calculate multiple IRRs:
    1. Equity IRR with sale (levered, includes debt service)
    2. Equity IRR without sale (levered, includes debt service)
    3. Project IRR with sale (unlevered, no debt, 100% equity)
    4. Project IRR without sale (unlevered, no debt, 100% equity)
    
    Args:
        projection: 15-year projection data
        initial_equity: Initial equity investment per owner
        final_property_value: Property value at end of 15 years
        final_loan_balance: Remaining loan balance at end of 15 years
        num_owners: Number of owners
        purchase_price: Total purchase price (needed for unlevered IRR)
    
    Returns:
        Dictionary with all IRR metrics (as percentages)
    """
    # Extract cash flows per owner (levered - after debt service)
    equity_cash_flows = [year['cash_flow_per_owner'] for year in projection]
    
    # Extract NOI (unlevered - before debt service) per owner
    unlevered_cash_flows = [year['net_operating_income'] / num_owners for year in projection]
    
    # Calculate sale proceeds per owner (net of loan payoff for levered)
    sale_proceeds_per_owner = (final_property_value - final_loan_balance) / num_owners
    
    # For unlevered, sale proceeds = full property value (no loan to pay)
    unlevered_sale_proceeds_per_owner = final_property_value / num_owners if purchase_price else 0
    
    # Equity IRR (levered) with sale
    equity_irr_with_sale = calculate_irr(equity_cash_flows, initial_equity, sale_proceeds_per_owner)
    
    # Equity IRR (levered) without sale
    equity_irr_without_sale = calculate_irr(equity_cash_flows, initial_equity, 0)
    
    # Project IRR (unlevered) with sale
    if purchase_price:
        initial_investment_per_owner = purchase_price / num_owners
        project_irr_with_sale = calculate_irr(unlevered_cash_flows, initial_investment_per_owner, unlevered_sale_proceeds_per_owner)
        project_irr_without_sale = calculate_irr(unlevered_cash_flows, initial_investment_per_owner, 0)
    else:
        project_irr_with_sale = 0.0
        project_irr_without_sale = 0.0
    
    return {
        'equity_irr_with_sale_pct': equity_irr_with_sale * 100,
        'equity_irr_without_sale_pct': equity_irr_without_sale * 100,
        'project_irr_with_sale_pct': project_irr_with_sale * 100,
        'project_irr_without_sale_pct': project_irr_without_sale * 100,
        # Legacy names for backward compatibility
        'irr_with_sale_pct': equity_irr_with_sale * 100,
        'irr_without_sale_pct': equity_irr_without_sale * 100,
        'sale_proceeds_per_owner': sale_proceeds_per_owner,
        'final_property_value': final_property_value,
        'final_loan_balance': final_loan_balance,
    }


def compute_detailed_expenses(config: BaseCaseConfig) -> Dict[str, float]:
    """Compute detailed breakdown of expenses."""
    r = config.rental
    e = config.expenses
    
    gross_rental_income = r.gross_rental_income
    rented_nights = r.rented_nights
    
    return {
        "Property Management (incl. Cleaning)": e.property_management_cost(gross_rental_income),
        "Tourist Tax": e.tourist_tax(rented_nights),
        "Insurance": e.insurance_annual,
        "Utilities": e.utilities_annual,
        "Maintenance Reserve": e.maintenance_reserve,
    }


# -----------------------------
# Sensitivity analysis
# -----------------------------

@dataclass
class SensitivityConfig:
    """Configuration for sensitivity analysis."""
    occupancy_values: List[float]
    daily_rate_values: List[float]
    management_fee_values: List[float]
    interest_rate_values: List[float]


def apply_sensitivity(
    base_config: BaseCaseConfig,
    occupancy: Optional[float] = None,
    daily_rate: Optional[float] = None,
    management_fee: Optional[float] = None,
    interest_rate: Optional[float] = None,
) -> BaseCaseConfig:
    """
    Return a new config instance with some parameters modified.
    Useful for scenario analysis or Monte Carlo sampling.
    
    IMPORTANT: This function preserves the base case structure and only modifies
    specified parameters. All other parameters are inherited from the base case to
    maintain consistency across all analyses.
    
    Args:
        base_config: Base case configuration (single source of truth)
        occupancy: Override occupancy rate (if None, uses base)
        daily_rate: Override average daily rate (if None, uses base)
        management_fee: Override property management fee rate (if None, uses base)
        interest_rate: Override interest rate (if None, uses base)
    
    Returns:
        Modified BaseCaseConfig with specified parameters changed
    """
    new_financing = FinancingParams(
        purchase_price=base_config.financing.purchase_price,
        ltv=base_config.financing.ltv,
        interest_rate=interest_rate if interest_rate is not None else base_config.financing.interest_rate,
        amortization_rate=base_config.financing.amortization_rate,
        num_owners=base_config.financing.num_owners
    )

    # Handle seasonal model - preserve seasons if they exist
    base_rental = base_config.rental
    if base_rental.seasons:
        # Adjust seasonal parameters proportionally
        seasons = []
        for season in base_rental.seasons:
            # Adjust occupancy if provided
            new_occupancy = occupancy if occupancy is not None else season.occupancy_rate
            
            # Adjust daily rate if provided (proportional to base rate)
            if daily_rate is not None:
                # Calculate multiplier based on weighted average of base case
                base_avg_rate = base_config.rental.gross_rental_income / base_config.rental.rented_nights if base_config.rental.rented_nights > 0 else base_config.rental.average_daily_rate
                multiplier = daily_rate / base_avg_rate
                new_rate = season.average_daily_rate * multiplier
            else:
                new_rate = season.average_daily_rate
            
            seasons.append(SeasonalParams(
                name=season.name,
                months=season.months,
                occupancy_rate=new_occupancy,
                average_daily_rate=new_rate,
                nights_in_season=season.nights_in_season
            ))
        
        new_rental = RentalParams(
            owner_nights_per_person=base_rental.owner_nights_per_person,
            num_owners=base_rental.num_owners,
            occupancy_rate=occupancy if occupancy is not None else base_rental.occupancy_rate,
            average_daily_rate=daily_rate if daily_rate is not None else base_rental.average_daily_rate,
            days_per_year=base_rental.days_per_year,
            seasons=seasons  # Preserve seasonal structure
        )
    else:
        # Non-seasonal model
        new_rental = RentalParams(
            owner_nights_per_person=base_rental.owner_nights_per_person,
            num_owners=base_rental.num_owners,
            occupancy_rate=occupancy if occupancy is not None else base_rental.occupancy_rate,
            average_daily_rate=daily_rate if daily_rate is not None else base_rental.average_daily_rate,
            days_per_year=base_rental.days_per_year
        )

    new_expenses = ExpenseParams(
        property_management_fee_rate=management_fee if management_fee is not None else base_config.expenses.property_management_fee_rate,
        cleaning_cost_per_stay=base_config.expenses.cleaning_cost_per_stay,
        average_length_of_stay=base_config.expenses.average_length_of_stay,
        tourist_tax_per_person_per_night=base_config.expenses.tourist_tax_per_person_per_night,
        avg_guests_per_night=base_config.expenses.avg_guests_per_night,
        insurance_annual=base_config.expenses.insurance_annual,
        utilities_annual=base_config.expenses.utilities_annual,
        maintenance_rate=base_config.expenses.maintenance_rate,
        property_value=base_config.expenses.property_value
    )

    return BaseCaseConfig(
        financing=new_financing,
        rental=new_rental,
        expenses=new_expenses
    )

