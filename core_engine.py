"""
Real Estate Investment Simulation for Engelberg Property
Refined version with comprehensive financial modeling
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
import json
import os


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
    # SARON variable rate mortgage parameters
    mortgage_type: str = "fixed"  # "fixed" or "saron_variable"
    saron_spread: float = 0.0     # spread added to SARON rate
    saron_min_rate: float = 0.0   # minimum SARON rate
    saron_max_rate: float = 0.0   # maximum SARON rate
    saron_fluctuation_years: int = 15  # years over which SARON fluctuates

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
    property_management_fee_rate: float  # share of gross rental revenue, 20% (can vary 15-30% in sensitivities)
    cleaning_cost_per_stay: float       # CHF per stay, 80 CHF (can vary 60-130 CHF in sensitivities)
    average_length_of_stay: float       # nights per stay, 1.7
    tourist_tax_per_person_per_night: float  # CHF
    avg_guests_per_night: float
    insurance_annual: float             # CHF, 0.4% of property value
    nubbing_costs_annual: float         # CHF, shared expenses for shared parts (water, heating)
    electricity_internet_annual: float  # CHF, electricity and internet
    maintenance_rate: float             # percent of property value per year, 1%
    property_value: float               # CHF
    ota_booking_percentage: float       # percentage of bookings coming from OTAs (0.50 = 50%)
    ota_fee_rate: float                 # fee rate charged by OTAs on revenue (0.30 = 30%)

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
class TaxParams:
    marginal_tax_rate: float  # e.g., 0.21 for 21%
    depreciation_rate: float  # e.g., 0.02 for 2% annually
    
    def depreciation(self, property_value: float) -> float:
        return property_value * self.depreciation_rate


@dataclass
class BaseCaseConfig:
    financing: FinancingParams
    rental: RentalParams
    expenses: ExpenseParams
    tax: TaxParams


# -----------------------------
# JSON Configuration Loader
# -----------------------------

def load_assumptions_from_json(json_path: str = "assumptions/assumptions.json") -> Dict:
    """
    Load assumption parameters from JSON file.
    
    This function loads all assumption parameters from a centralized JSON file,
    ensuring a single source of truth for all analyses.
    
    Args:
        json_path: Path to the JSON assumptions file (default: "assumptions/assumptions.json")
    
    Returns:
        Dictionary containing all assumption parameters organized by category
    
    Raises:
        FileNotFoundError: If JSON file does not exist
        json.JSONDecodeError: If JSON file is malformed
        ValueError: If required fields are missing or invalid
    """
    # Check if file exists
    if not os.path.exists(json_path):
        raise FileNotFoundError(
            f"Assumptions file not found: {json_path}\n"
            f"Please ensure the assumptions file exists at the specified path."
        )
    
    # Load JSON file
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            assumptions = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON format in {json_path}: {str(e)}",
            e.doc,
            e.pos
        )
    
    # Validate required sections exist
    required_sections = ['financing', 'rental', 'expenses', 'seasonal', 'projection', 'tax']
    missing_sections = [section for section in required_sections if section not in assumptions]
    
    # If missing sections and this isn't the base assumptions.json, merge with base
    base_path = "assumptions/assumptions.json"
    if missing_sections and json_path != base_path and os.path.exists(base_path):
        # Load base assumptions
        with open(base_path, 'r', encoding='utf-8') as f:
            base_assumptions = json.load(f)
        
        # Merge: scenario overrides base
        for section in required_sections:
            if section not in assumptions:
                assumptions[section] = base_assumptions.get(section, {})
            elif section in assumptions and section in base_assumptions:
                # Deep merge for sections that exist in both
                merged_section = base_assumptions[section].copy()
                merged_section.update(assumptions[section])
                assumptions[section] = merged_section
        
        # Re-check for missing sections after merge
        missing_sections = [section for section in required_sections if section not in assumptions]
    
    if missing_sections:
        raise ValueError(
            f"Missing required sections in {json_path}: {', '.join(missing_sections)}"
        )
    
    # Validate financing section (check for either direct values or value objects)
    financing = assumptions['financing']
    required_financing = ['purchase_price', 'ltv', 'interest_rate', 'amortization_rate', 'num_owners']
    
    # Skip explanation fields (starting with _) when checking for required fields
    missing_financing = [field for field in required_financing if field not in financing or (isinstance(financing[field], str) and financing[field].startswith('_'))]
    if missing_financing:
        raise ValueError(
            f"Missing required financing fields: {', '.join(missing_financing)}"
        )
    
    # Validate rental section
    rental = assumptions['rental']
    required_rental = ['owner_nights_per_person', 'days_per_year']
    missing_rental = [field for field in required_rental if field not in rental]
    if missing_rental:
        raise ValueError(
            f"Missing required rental fields: {', '.join(missing_rental)}"
        )
    
    # Validate seasonal section
    seasonal = assumptions['seasonal']
    required_seasons = ['winter_peak', 'summer_peak', 'offpeak']
    missing_seasons = [season for season in required_seasons if season not in seasonal]
    if missing_seasons:
        raise ValueError(
            f"Missing required seasons: {', '.join(missing_seasons)}"
        )
    
    # Validate each season has required fields (skip metadata keys starting with _)
    for season_name, season_data in seasonal.items():
        if season_name.startswith('_'):
            continue  # Skip metadata fields like _explanation
        required_season_fields = ['name', 'months', 'occupancy_rate', 'average_daily_rate']
        missing_fields = [field for field in required_season_fields if field not in season_data]
        if missing_fields:
            raise ValueError(
                f"Season '{season_name}' missing required fields: {', '.join(missing_fields)}"
            )
        # Validate occupancy_rate is between 0 and 1
        occ_rate = season_data.get('occupancy_rate')
        if occ_rate is not None and not isinstance(occ_rate, str) and not 0 <= float(occ_rate) <= 1:
            raise ValueError(
                f"Season '{season_name}' occupancy_rate must be between 0 and 1, got {occ_rate}"
            )
    
    # Validate expenses section
    expenses = assumptions['expenses']
    required_expenses = [
        'property_management_fee_rate', 'cleaning_cost_per_stay', 'average_length_of_stay',
        'tourist_tax_per_person_per_night', 'avg_guests_per_night', 'insurance_rate',
        'nubbing_costs_annual', 'electricity_internet_annual', 'maintenance_rate'
    ]
    missing_expenses = [field for field in required_expenses if field not in expenses]
    if missing_expenses:
        raise ValueError(
            f"Missing required expense fields: {', '.join(missing_expenses)}"
        )
    
    # Validate projection section
    projection = assumptions['projection']
    required_projection = ['inflation_rate', 'property_appreciation_rate']
    missing_projection = [field for field in required_projection if field not in projection]
    if missing_projection:
        raise ValueError(
            f"Missing required projection fields: {', '.join(missing_projection)}"
        )
    
    # Validate numeric ranges (skip explanation fields)
    ltv_val = assumptions['financing'].get('ltv')
    if ltv_val is not None and not isinstance(ltv_val, str) and not 0 < float(ltv_val) < 1:
        raise ValueError(f"LTV must be between 0 and 1, got {ltv_val}")
    
    mgmt_fee_val = assumptions['expenses'].get('property_management_fee_rate')
    if mgmt_fee_val is not None and not isinstance(mgmt_fee_val, str) and not 0 <= float(mgmt_fee_val) <= 1:
        raise ValueError(
            f"Property management fee rate must be between 0 and 1, "
            f"got {mgmt_fee_val}"
        )
    
    return assumptions


def get_projection_defaults(json_path: str = "assumptions/assumptions.json") -> Dict:
    """
    Get projection default values from JSON.
    
    This helper function allows analysis scripts to use the same projection defaults
    as defined in the assumptions JSON file, ensuring consistency.
    
    Args:
        json_path: Path to the assumptions JSON file (default: "assumptions/assumptions.json")
    
    Returns:
        Dictionary with projection parameters including rates, years, selling costs, and optional refinancing config
    """
    assumptions = load_assumptions_from_json(json_path)
    projection = assumptions['projection']
    selling_costs = projection.get('selling_costs', {})
    
    # Extract refinancing config if present
    refinancing_config = None
    if 'refinancing' in projection:
        ref_config = projection['refinancing']
        refinancing_config = {
            'refinance_year': int(ref_config.get('refinance_year', 6)),
            'new_interest_rate': float(ref_config.get('new_interest_rate', 0.0))
        }
    
    defaults = {
        'inflation_rate': float(projection.get('inflation_rate', 0.01)),
        'property_appreciation_rate': float(projection.get('property_appreciation_rate', 0.025)),  # Default 2.5% to match function signature
        'start_year': int(projection.get('start_year', 2026)),
        'projection_years': int(projection.get('projection_years', 15)),
        'discount_rate': float(projection.get('discount_rate', 0.05)),
        'selling_costs_rate': float(selling_costs.get('total_rate', 0.078)),
        'broker_fee_rate': float(selling_costs.get('broker_fee_rate', 0.03)),
        'notary_fee_rate': float(selling_costs.get('notary_fee_rate', 0.015)),
        'transfer_tax_rate': float(selling_costs.get('transfer_tax_rate', 0.033)),
        'refinancing_config': refinancing_config
    }
    
    return defaults


# -----------------------------
# Base case configuration
# -----------------------------

def create_base_case_config(json_path: str = "assumptions/assumptions.json") -> BaseCaseConfig:
    """
    Create the base case configuration with seasonal parameters for Engelberg.
    
    ⚠️ SINGLE SOURCE OF TRUTH ⚠️
    This function defines the base case scenario. ALL other analyses
    (sensitivity, Monte Carlo, etc.) MUST reference this base case to ensure
    consistency across the entire codebase.
    
    DO NOT create alternative base case configurations in other scripts.
    Always use this function and then apply variations using apply_sensitivity().
    
    All assumptions are loaded from the assumptions JSON file, ensuring a single
    source of truth for all parameters across all analyses.
    
    Calibrated to real Engelberg Airbnb analytics:
    - Average annual revenue: 46,000 CHF
    - Average occupancy rate: 63%
    - Average nightly rate: 200 CHF
    
    Engelberg has three distinct seasons:
    1. Winter Peak (Dec-Mar): Ski season, highest rates and occupancy
    2. Summer Peak (Jun-Sep): Hiking and mountain activities
    3. Off-Peak (Apr-May, Oct-Nov): Shoulder seasons with lower demand
    
    Args:
        json_path: Path to the assumptions JSON file (default: "assumptions/assumptions.json")
    
    Returns:
        BaseCaseConfig with all parameters loaded from JSON file
    """
    # Load assumptions from JSON file
    assumptions = load_assumptions_from_json(json_path)
    
    # Extract financing parameters (skip fields starting with _)
    financing_data = assumptions['financing']
    
    def get_value(data, key):
        """Extract value, skipping explanation fields starting with _"""
        if key not in data:
            return None
        val = data[key]
        # Skip explanation fields
        if isinstance(val, str) and key.startswith('_'):
            return None
        return val
    
    purchase_price = float(financing_data.get('purchase_price', 1300000.0))
    num_owners = int(financing_data.get('num_owners', 4))
    
    # Extract rental parameters
    rental_data = assumptions['rental']
    owner_nights_per_person = int(rental_data.get('owner_nights_per_person', 5))
    days_per_year = int(rental_data.get('days_per_year', 365))
    
    # Days per month (approximate)
    days_per_month = {
        1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
        7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
    }
    
    # Extract seasonal parameters
    seasonal_data = assumptions['seasonal']
    owner_nights_dist_raw = rental_data.get('owner_nights_distribution', {
        'winter': 8,
        'summer': 7,
        'offpeak': 5
    })
    
    # Extract owner nights distribution (skip explanation fields)
    owner_nights_dist = {}
    for season in ['winter', 'summer', 'offpeak']:
        if season in owner_nights_dist_raw and not season.startswith('_'):
            val = owner_nights_dist_raw[season]
            if not isinstance(val, str) or not val.startswith('_'):
                owner_nights_dist[season] = int(val)
        else:
            owner_nights_dist[season] = {'winter': 8, 'summer': 7, 'offpeak': 5}[season]
    
    # Winter Peak season
    winter_data = seasonal_data['winter_peak']
    winter_months = winter_data['months']
    winter_nights = sum(days_per_month[m] for m in winter_months)
    owner_nights_winter = owner_nights_dist.get('winter', 8)
    rentable_winter = winter_nights - owner_nights_winter
    
    winter_season = SeasonalParams(
        name=winter_data['name'],
        months=winter_months,
        occupancy_rate=float(winter_data.get('occupancy_rate', 0.75)),
        average_daily_rate=float(winter_data.get('average_daily_rate', 250.0)),
        nights_in_season=rentable_winter
    )
    
    # Summer Peak season
    summer_data = seasonal_data['summer_peak']
    summer_months = summer_data['months']
    summer_nights = sum(days_per_month[m] for m in summer_months)
    owner_nights_summer = owner_nights_dist.get('summer', 7)
    rentable_summer = summer_nights - owner_nights_summer
    
    summer_season = SeasonalParams(
        name=summer_data['name'],
        months=summer_months,
        occupancy_rate=float(summer_data.get('occupancy_rate', 0.65)),
        average_daily_rate=float(summer_data.get('average_daily_rate', 200.0)),
        nights_in_season=rentable_summer
    )
    
    # Off-Peak season
    offpeak_data = seasonal_data['offpeak']
    offpeak_months = offpeak_data['months']
    offpeak_nights = sum(days_per_month[m] for m in offpeak_months)
    owner_nights_offpeak = owner_nights_dist.get('offpeak', 5)
    rentable_offpeak = offpeak_nights - owner_nights_offpeak
    
    offpeak_season = SeasonalParams(
        name=offpeak_data['name'],
        months=offpeak_months,
        occupancy_rate=float(offpeak_data.get('occupancy_rate', 0.5)),
        average_daily_rate=float(offpeak_data.get('average_daily_rate', 150.0)),
        nights_in_season=rentable_offpeak
    )
    
    # Create financing parameters
    financing = FinancingParams(
        purchase_price=purchase_price,
        ltv=float(financing_data.get('ltv', 0.75)),
        interest_rate=float(financing_data.get('interest_rate', 0.013)),
        amortization_rate=float(financing_data.get('amortization_rate', 0.01)),
        num_owners=num_owners,
        mortgage_type=financing_data.get('mortgage_type', 'fixed'),
        saron_spread=float(financing_data.get('saron_spread', 0.0)),
        saron_min_rate=float(financing_data.get('saron_min_rate', 0.0)),
        saron_max_rate=float(financing_data.get('saron_max_rate', 0.0)),
        saron_fluctuation_years=int(financing_data.get('saron_fluctuation_years', 15))
    )

    # Create rental parameters
    rental = RentalParams(
        owner_nights_per_person=owner_nights_per_person,
        num_owners=num_owners,
        occupancy_rate=float(rental_data.get('legacy_occupancy_rate', 0.63)),
        average_daily_rate=float(rental_data.get('legacy_average_daily_rate', 200.0)),
        days_per_year=days_per_year,
        seasons=[winter_season, summer_season, offpeak_season]
    )

    # Create expense parameters
    expenses_data = assumptions['expenses']
    expenses = ExpenseParams(
        property_management_fee_rate=float(expenses_data.get('property_management_fee_rate', 0.20)),
        cleaning_cost_per_stay=float(expenses_data.get('cleaning_cost_per_stay', 80.0)),
        average_length_of_stay=float(expenses_data.get('average_length_of_stay', 1.7)),
        tourist_tax_per_person_per_night=float(expenses_data.get('tourist_tax_per_person_per_night', 3.0)),
        avg_guests_per_night=float(expenses_data.get('avg_guests_per_night', 2.0)),
        insurance_annual=purchase_price * float(expenses_data.get('insurance_rate', 0.004)),
        nubbing_costs_annual=float(expenses_data.get('nubbing_costs_annual', 2000.0)),
        electricity_internet_annual=float(expenses_data.get('electricity_internet_annual', 1000.0)),
        maintenance_rate=float(expenses_data.get('maintenance_rate', 0.01)),
        property_value=purchase_price,
        ota_booking_percentage=float(expenses_data.get('ota_booking_percentage', 0.50)),
        ota_fee_rate=float(expenses_data.get('ota_fee_rate', 0.30))
    )

    # Create tax parameters
    tax_data = assumptions.get('tax', {})
    tax = TaxParams(
        marginal_tax_rate=float(tax_data.get('marginal_tax_rate', 0.21)),
        depreciation_rate=float(tax_data.get('depreciation_rate', 0.02))
    )

    return BaseCaseConfig(
        financing=financing,
        rental=rental,
        expenses=expenses,
        tax=tax
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
    t = config.tax

    # Revenue
    gross_rental_income = r.gross_rental_income
    rented_nights = r.rented_nights

    # Operating Expenses
    # Note: In base case, cleaning is included in property management fee (30%)
    # But if cleaning_cost_per_stay > 0, it means cleaning is separate and should be included
    property_management_cost = e.property_management_cost(gross_rental_income)

    # Platform/OTA fees: calculated as percentage of bookings × OTA fee rate
    # Effective fee = ota_booking_percentage × ota_fee_rate (e.g., 50% × 30% = 15%)
    platform_fee = gross_rental_income * e.ota_booking_percentage * e.ota_fee_rate
    
    # Calculate cleaning cost if it's separate (not included in management fee)
    # If cleaning_cost_per_stay is 0, cleaning is included in management fee
    if e.cleaning_cost_per_stay > 0:
        cleaning_cost = e.cleaning_cost(rented_nights)
    else:
        cleaning_cost = 0.0  # Cleaning is included in property management fee
    
    tourist_tax = e.tourist_tax(rented_nights)
    insurance = e.insurance_annual
    nubbing_costs = e.nubbing_costs_annual
    electricity_internet = e.electricity_internet_annual
    maintenance_reserve = e.maintenance_reserve

    total_operating_expenses = (
        property_management_cost
        + platform_fee
        + cleaning_cost  # Separate cleaning cost (80 CHF per stay, can vary 60-130)
        + tourist_tax
        + insurance
        + nubbing_costs  # Shared expenses (water, heating)
        + electricity_internet  # Electricity and internet
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

    # Tax Calculations - Owner Level Tax Benefits
    # Interest and amortization are deductible from owners' personal taxable income
    # This creates tax savings that represent positive cash flow to owners
    owner_tax_deductions = interest_payment + amortization_payment
    owner_tax_benefit = owner_tax_deductions * t.marginal_tax_rate
    owner_tax_benefit_per_owner = owner_tax_benefit / f.num_owners

    # Property-level tax calculation (may have different rules, but simplified here)
    depreciation = t.depreciation(f.purchase_price)
    property_taxable_income = gross_rental_income - total_operating_expenses - depreciation  # Interest may flow through to owners
    property_tax_liability = max(0, property_taxable_income) * t.marginal_tax_rate

    # Overall after-tax cash flow = Pre-tax cash flow + Owner tax benefits - Property tax liability
    after_tax_cash_flow = cash_flow_after_debt_service + owner_tax_benefit - property_tax_liability
    after_tax_cash_flow_per_owner = after_tax_cash_flow / f.num_owners

    # For backward compatibility and clarity
    taxable_income = property_taxable_income
    tax_liability = property_tax_liability
    tax_benefit = owner_tax_benefit_per_owner * f.num_owners  # Total owner tax benefit

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
        "platform_fee": platform_fee,
        "cleaning_cost": cleaning_cost,
        "tourist_tax": tourist_tax,
        "insurance": insurance,
        "nubbing_costs": nubbing_costs,
        "electricity_internet": electricity_internet,
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
        
        # Tax Calculations
        "depreciation": depreciation,
        "taxable_income": taxable_income,
        "tax_liability": tax_liability,
        "tax_benefit": tax_benefit,
        "after_tax_cash_flow": after_tax_cash_flow,
        "after_tax_cash_flow_per_owner": after_tax_cash_flow_per_owner,
        
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
        # Calculate weighted average daily rate (reuse already calculated values for efficiency)
        # gross_rental_income and rented_nights are already calculated above
        result["average_daily_rate"] = gross_rental_income / rented_nights if rented_nights > 0 else 0
        result["overall_occupancy_rate"] = rented_nights / r.rentable_nights if r.rentable_nights > 0 else 0
    else:
        result["average_daily_rate"] = r.average_daily_rate
        result["overall_occupancy_rate"] = r.occupancy_rate
    
    return result


def compute_15_year_projection(config: BaseCaseConfig, start_year: int = 2026, 
                               inflation_rate: float = 0.02, property_appreciation_rate: float = 0.025,
                               refinancing_config: Optional[Dict] = None,
                               num_years: int = 15) -> List[Dict[str, any]]:
    """
    Compute multi-year projection of cash flows and financial metrics.
    
    Assumptions:
    - Purchase in January of start_year
    - Loan amount decreases each year due to amortization
    - Interest is calculated on remaining loan balance
    - Inflation applied to revenue and variable expenses (default 2%)
    - Property appreciation applied annually (default 2.5% - realistic for Swiss real estate)
    - Optional refinancing: if refinancing_config is provided, interest rate changes after specified year
    
    Args:
        config: Base case configuration
        start_year: Starting year for projection
        inflation_rate: Annual inflation rate
        property_appreciation_rate: Annual property appreciation rate
        refinancing_config: Optional dict with 'refinance_year' and 'new_interest_rate'
        num_years: Number of years to project (default 15, can be set to 6 for early exit scenarios)
    
    Returns a list of dictionaries, one for each year.
    """
    projection = []
    current_loan = config.financing.loan_amount
    initial_loan_amount = config.financing.loan_amount  # Store for amortization calculation
    year = start_year
    
    # Determine interest rate for each year (support refinancing and SARON)
    def get_interest_rate_for_year(year_num: int) -> float:
        if refinancing_config and year_num >= refinancing_config.get('refinance_year', 999):
            return refinancing_config.get('new_interest_rate', config.financing.interest_rate)

        # Handle SARON variable rate mortgage
        if getattr(config.financing, 'mortgage_type', 'fixed') == 'saron_variable':
            import math
            saron_min = getattr(config.financing, 'saron_min_rate', 0.006)
            saron_max = getattr(config.financing, 'saron_max_rate', 0.013)
            saron_spread = getattr(config.financing, 'saron_spread', 0.009)
            fluctuation_years = getattr(config.financing, 'saron_fluctuation_years', 15)

            # Create a sinusoidal fluctuation pattern over the specified period
            # This gives a smooth oscillation between min and max rates
            cycle_progress = (year_num - 1) / fluctuation_years  # 0 to 1 over the period
            # Use sine wave to oscillate: sin goes from -1 to 1, we want 0 to 1
            oscillation = (math.sin(2 * math.pi * cycle_progress) + 1) / 2  # 0 to 1

            # Calculate SARON rate for this year
            saron_rate = saron_min + (saron_max - saron_min) * oscillation

            # Add spread to get final mortgage rate
            final_rate = saron_rate + saron_spread

            return final_rate

        # Default to fixed rate
        return config.financing.interest_rate
    
    # Base year results (no inflation)
    base_result = compute_annual_cash_flows(config)
    base_gross_income = base_result['gross_rental_income']
    base_property_mgmt = base_result['property_management_cost']
    base_cleaning = base_result.get('cleaning_cost', 0.0)  # Get cleaning cost if separate
    base_tourist_tax = base_result['tourist_tax']  # Tourist tax from base result
    base_insurance = base_result['insurance']
    base_nubbing_costs = base_result['nubbing_costs']
    base_electricity_internet = base_result['electricity_internet']
    base_maintenance = base_result['maintenance_reserve']
    
    # Pre-calculate inflation and appreciation factors for efficiency
    inflation_factors = [(1 + inflation_rate) ** (year_num - 1) for year_num in range(1, num_years + 1)]
    appreciation_factors = [(1 + property_appreciation_rate) ** (year_num - 1) for year_num in range(1, num_years + 1)]
    
    for year_num in range(1, num_years + 1):  # Years 1 to num_years
        # Apply inflation and appreciation (using pre-calculated factors)
        inflation_factor = inflation_factors[year_num - 1]
        appreciation_factor = appreciation_factors[year_num - 1]
        
        # Inflated revenue and variable expenses
        gross_rental_income = base_gross_income * inflation_factor
        property_management_cost = base_property_mgmt * inflation_factor
        cleaning_cost = base_cleaning * inflation_factor  # Cleaning is variable, inflates with occupancy/revenue
        tourist_tax = base_tourist_tax * inflation_factor
        
        # Fixed expenses (insurance, nubbing costs, electricity/internet) also inflate
        insurance = base_insurance * inflation_factor
        nubbing_costs = base_nubbing_costs * inflation_factor
        electricity_internet = base_electricity_internet * inflation_factor
        
        # Maintenance reserve based on appreciated property value (1% of current property value)
        current_property_value = config.financing.purchase_price * appreciation_factor
        maintenance_reserve = current_property_value * config.expenses.maintenance_rate
        
        total_operating_expenses = (
            property_management_cost +
            cleaning_cost +  # Separate cleaning cost (80 CHF per stay, can vary 60-130)
            tourist_tax +
            insurance +
            nubbing_costs +  # Shared expenses (water, heating)
            electricity_internet +  # Electricity and internet
            maintenance_reserve
        )
        
        net_operating_income = gross_rental_income - total_operating_expenses
        
        # Calculate debt service based on current loan balance and year-specific interest rate
        current_interest_rate = get_interest_rate_for_year(year_num)
        interest_payment = current_loan * current_interest_rate
        amortization_payment = initial_loan_amount * config.financing.amortization_rate  # Use stored initial loan amount
        debt_service = interest_payment + amortization_payment
        
        cash_flow_after_debt_service = net_operating_income - debt_service
        cash_flow_per_owner = cash_flow_after_debt_service / config.financing.num_owners
        
        # Tax Calculations - Owner Level Tax Benefits
        owner_tax_deductions = interest_payment + amortization_payment
        owner_tax_benefit = owner_tax_deductions * config.tax.marginal_tax_rate
        owner_tax_benefit_per_owner = owner_tax_benefit / config.financing.num_owners

        # Property-level tax calculation
        depreciation = config.tax.depreciation(current_property_value)
        property_taxable_income = gross_rental_income - total_operating_expenses - depreciation
        property_tax_liability = max(0, property_taxable_income) * config.tax.marginal_tax_rate

        # Overall after-tax cash flow = Pre-tax cash flow + Owner tax benefits - Property tax liability
        after_tax_cash_flow = cash_flow_after_debt_service + owner_tax_benefit - property_tax_liability
        after_tax_cash_flow_per_owner = after_tax_cash_flow / config.financing.num_owners

        # For backward compatibility
        taxable_income = property_taxable_income
        tax_liability = property_tax_liability
        tax_benefit = owner_tax_benefit_per_owner * config.financing.num_owners
        
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
            'interest_rate': current_interest_rate,
            'interest_payment': interest_payment,
            'amortization_payment': amortization_payment,
            'debt_service': debt_service,
            'cash_flow_after_debt_service': cash_flow_after_debt_service,
            'cash_flow_per_owner': cash_flow_per_owner,
            'remaining_loan_balance': current_loan,  # Balance at end of year (after amortization)
            'debt_coverage_ratio': debt_coverage_ratio,
            'cap_rate_pct': cap_rate,
            # Tax Calculations
            'depreciation': depreciation,
            'taxable_income': taxable_income,
            'tax_liability': tax_liability,
            'tax_benefit': tax_benefit,
            'after_tax_cash_flow': after_tax_cash_flow,
            'after_tax_cash_flow_per_owner': after_tax_cash_flow_per_owner,
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
    
    # Define NPV function (optimized with pre-calculated discount factors)
    def npv(rate):
        try:
            # Pre-calculate discount factors for efficiency
            discount_factors = [(1 + rate) ** i for i in range(len(cf_array))]
            return sum(cf / df for cf, df in zip(cf_array, discount_factors))
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
                                   num_owners: int = 4, purchase_price: float = None,
                                   selling_costs_rate: float = 0.078,
                                   discount_rate: float = 0.05) -> Dict[str, float]:
    """
    Calculate multiple IRRs with selling costs:
    1. Equity IRR with sale (levered, includes debt service and selling costs)
    2. Equity IRR without sale (levered, cash flow only)
    3. Project IRR with sale (unlevered, no debt, includes selling costs)
    4. Project IRR without sale (unlevered, cash flow only)
    
    Selling costs in Switzerland (typically 7.8%):
    - Broker fee: 3%
    - Notary fees: 1.5%
    - Transfer tax: 3.3% (varies by canton, Obwalden has high rate)
    
    Args:
        projection: Multi-year projection data (typically 15 years, can be shorter for early exit)
        initial_equity: Initial equity investment per owner
        final_property_value: Property value at end of projection period
        final_loan_balance: Remaining loan balance at end of projection period
        num_owners: Number of owners
        purchase_price: Total purchase price (needed for unlevered IRR)
        selling_costs_rate: Total selling costs as % of sale price (default 7.8%)
    
    Returns:
        Dictionary with all IRR metrics (as percentages), NPV, MOIC, and payback period
    """
    # Extract cash flows per owner (levered - after debt service)
    equity_cash_flows = [year['cash_flow_per_owner'] for year in projection]
    
    # Extract after-tax cash flows per owner (levered - after debt service and tax)
    after_tax_equity_cash_flows = [year.get('after_tax_cash_flow_per_owner', year['cash_flow_per_owner']) for year in projection]
    
    # Extract NOI (unlevered - before debt service) per owner
    unlevered_cash_flows = [year['net_operating_income'] / num_owners for year in projection]
    
    # Calculate selling costs
    selling_costs_total = final_property_value * selling_costs_rate
    net_sale_price = final_property_value - selling_costs_total
    
    # Calculate sale proceeds per owner (net of loan payoff and selling costs for levered)
    sale_proceeds_per_owner = (net_sale_price - final_loan_balance) / num_owners
    
    # For unlevered, sale proceeds = net sale price (no loan to pay, but still have selling costs)
    unlevered_sale_proceeds_per_owner = net_sale_price / num_owners if purchase_price else 0
    
    # Equity IRR (levered) with sale
    equity_irr_with_sale = calculate_irr(equity_cash_flows, initial_equity, sale_proceeds_per_owner)
    
    # Equity IRR (levered) without sale
    equity_irr_without_sale = calculate_irr(equity_cash_flows, initial_equity, 0)
    
    # After-Tax Equity IRR (levered) with sale
    after_tax_equity_irr_with_sale = calculate_irr(after_tax_equity_cash_flows, initial_equity, sale_proceeds_per_owner)
    
    # After-Tax Equity IRR (levered) without sale
    after_tax_equity_irr_without_sale = calculate_irr(after_tax_equity_cash_flows, initial_equity, 0)
    
    # Project IRR (unlevered) with sale
    if purchase_price:
        initial_investment_per_owner = purchase_price / num_owners
        project_irr_with_sale = calculate_irr(unlevered_cash_flows, initial_investment_per_owner, unlevered_sale_proceeds_per_owner)
        project_irr_without_sale = calculate_irr(unlevered_cash_flows, initial_investment_per_owner, 0)
    else:
        project_irr_with_sale = 0.0
        project_irr_without_sale = 0.0
    
    # Calculate NPV using provided discount rate
    npv = -initial_equity
    for i, cash_flow in enumerate(equity_cash_flows, 1):
        npv += cash_flow / ((1 + discount_rate) ** i)
    npv += sale_proceeds_per_owner / ((1 + discount_rate) ** len(equity_cash_flows))
    
    # Calculate MOIC (Multiple on Invested Capital)
    total_cash_returned = sum(equity_cash_flows) + sale_proceeds_per_owner
    moic = total_cash_returned / initial_equity if initial_equity > 0 else 0
    
    # Calculate Payback Period (years until cumulative cash flow turns positive)
    cumulative_cash = -initial_equity
    payback_period = None
    for i, cash_flow in enumerate(equity_cash_flows, 1):
        cumulative_cash += cash_flow
        if cumulative_cash >= 0 and payback_period is None:
            payback_period = i
    # If never pays back from cash flows alone, payback is at sale
    if payback_period is None:
        cumulative_cash += sale_proceeds_per_owner
        if cumulative_cash >= 0:
            payback_period = len(equity_cash_flows)  # Payback at final year with sale
    
    return {
        'equity_irr_with_sale_pct': equity_irr_with_sale * 100,
        'equity_irr_without_sale_pct': equity_irr_without_sale * 100,
        'project_irr_with_sale_pct': project_irr_with_sale * 100,
        'project_irr_without_sale_pct': project_irr_without_sale * 100,
        # After-tax IRRs
        'after_tax_equity_irr_with_sale_pct': after_tax_equity_irr_with_sale * 100,
        'after_tax_equity_irr_without_sale_pct': after_tax_equity_irr_without_sale * 100,
        # New metrics
        'npv_at_5pct': npv,
        'moic': moic,
        'payback_period_years': payback_period,
        # Sale details
        'gross_sale_price': final_property_value,
        'selling_costs': selling_costs_total,
        'net_sale_price': net_sale_price,
        'selling_costs_rate_pct': selling_costs_rate * 100,
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
    
    # Calculate cleaning cost if separate
    cleaning_cost = e.cleaning_cost(rented_nights) if e.cleaning_cost_per_stay > 0 else 0.0
    
    return {
        "Property Management": e.property_management_cost(gross_rental_income),  # 20% (can vary 15-30%)
        "Cleaning": cleaning_cost,  # 80 CHF per stay (can vary 60-130)
        "Tourist Tax": e.tourist_tax(rented_nights),
        "Insurance": e.insurance_annual,  # 0.4% of property value
        "Nubbing Costs (Water, Heating)": e.nubbing_costs_annual,
        "Electricity & Internet": e.electricity_internet_annual,
        "Maintenance Reserve": e.maintenance_reserve,  # 1% of property value
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
        num_owners=base_config.financing.num_owners,
        mortgage_type=base_config.financing.mortgage_type,
        saron_spread=base_config.financing.saron_spread,
        saron_min_rate=base_config.financing.saron_min_rate,
        saron_max_rate=base_config.financing.saron_max_rate,
        saron_fluctuation_years=base_config.financing.saron_fluctuation_years
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
        nubbing_costs_annual=base_config.expenses.nubbing_costs_annual,
        electricity_internet_annual=base_config.expenses.electricity_internet_annual,
        maintenance_rate=base_config.expenses.maintenance_rate,
        property_value=base_config.expenses.property_value,
        ota_booking_percentage=base_config.expenses.ota_booking_percentage,
        ota_fee_rate=base_config.expenses.ota_fee_rate
    )

    return BaseCaseConfig(
        financing=new_financing,
        rental=new_rental,
        expenses=new_expenses,
        tax=base_config.tax  # Preserve tax parameters
    )


# -----------------------------
# JSON Export Functions
# -----------------------------

def export_base_case_to_json(config: BaseCaseConfig, results: Dict[str, float], 
                             projection: List[Dict], irr_results: Dict[str, float]) -> Dict[str, Any]:
    """
    Export base case analysis results to a structured dictionary ready for JSON serialization.
    
    Args:
        config: Base case configuration
        results: Annual cash flow results from compute_annual_cash_flows
        projection: Multi-year projection from compute_15_year_projection (typically 15 years, can be shorter)
        irr_results: IRR calculation results from calculate_irrs_from_projection
    
    Returns:
        Dictionary with all base case data structured for JSON export
    """
    # Convert config to dict (handling dataclasses)
    config_dict = {
        'financing': {
            'purchase_price': config.financing.purchase_price,
            'ltv': config.financing.ltv,
            'interest_rate': config.financing.interest_rate,
            'amortization_rate': config.financing.amortization_rate,
            'num_owners': config.financing.num_owners,
            'loan_amount': config.financing.loan_amount,
            'equity_total': config.financing.equity_total,
            'equity_per_owner': config.financing.equity_per_owner
        },
        'rental': {
            'owner_nights_per_person': config.rental.owner_nights_per_person,
            'num_owners': config.rental.num_owners,
            'occupancy_rate': config.rental.occupancy_rate,
            'average_daily_rate': config.rental.average_daily_rate,
            'days_per_year': config.rental.days_per_year,
            'gross_rental_income': config.rental.gross_rental_income,
            'rented_nights': config.rental.rented_nights,
            'seasons': [
                {
                    'name': s.name,
                    'months': s.months,
                    'occupancy_rate': s.occupancy_rate,
                    'average_daily_rate': s.average_daily_rate,
                    'nights_in_season': s.nights_in_season,
                    'rented_nights': s.rented_nights,
                    'season_income': s.season_income
                }
                for s in config.rental.seasons
            ]
        },
        'expenses': {
            'property_management_fee_rate': config.expenses.property_management_fee_rate,
            'cleaning_cost_per_stay': config.expenses.cleaning_cost_per_stay,
            'average_length_of_stay': config.expenses.average_length_of_stay,
            'tourist_tax_per_person_per_night': config.expenses.tourist_tax_per_person_per_night,
            'avg_guests_per_night': config.expenses.avg_guests_per_night,
            'insurance_annual': config.expenses.insurance_annual,
            'nubbing_costs_annual': config.expenses.nubbing_costs_annual,
            'electricity_internet_annual': config.expenses.electricity_internet_annual,
            'maintenance_rate': config.expenses.maintenance_rate,
            'property_value': config.expenses.property_value
        },
        'tax': {
            'marginal_tax_rate': config.tax.marginal_tax_rate,
            'depreciation_rate': config.tax.depreciation_rate
        }
    }
    
    # Structure annual results
    annual_results = {
        'purchase_price': results.get('purchase_price', config.financing.purchase_price),
        'loan_amount': results.get('loan_amount', config.financing.loan_amount),
        'equity_total': results.get('equity_total', config.financing.equity_total),
        'equity_per_owner': results.get('equity_per_owner', config.financing.equity_per_owner),
        'total_owner_nights': results.get('total_owner_nights', 0),
        'rentable_nights': results.get('rentable_nights', 0),
        'rented_nights': results.get('rented_nights', 0),
        'gross_rental_income': results.get('gross_rental_income', 0),
        'property_management_cost': results.get('property_management_cost', 0),
        'cleaning_cost': results.get('cleaning_cost', 0),
        'tourist_tax': results.get('tourist_tax', 0),
        'insurance': results.get('insurance', 0),
        'nubbing_costs': results.get('nubbing_costs', 0),
        'electricity_internet': results.get('electricity_internet', 0),
        'maintenance_reserve': results.get('maintenance_reserve', 0),
        'total_operating_expenses': results.get('total_operating_expenses', 0),
        'net_operating_income': results.get('net_operating_income', 0),
        'interest_payment': results.get('interest_payment', 0),
        'amortization_payment': results.get('amortization_payment', 0),
        'debt_service': results.get('debt_service', 0),
        'cash_flow_after_debt_service': results.get('cash_flow_after_debt_service', 0),
        'cash_flow_per_owner': results.get('cash_flow_per_owner', 0),
        'cap_rate_pct': results.get('cap_rate_pct', 0),
        'cash_on_cash_return_pct': results.get('cash_on_cash_return_pct', 0),
        'debt_coverage_ratio': results.get('debt_coverage_ratio', 0),
        'operating_expense_ratio_pct': results.get('operating_expense_ratio_pct', 0),
        # Tax Calculations
        'depreciation': results.get('depreciation', 0),
        'taxable_income': results.get('taxable_income', 0),
        'tax_liability': results.get('tax_liability', 0),
        'tax_benefit': results.get('tax_benefit', 0),
        'after_tax_cash_flow': results.get('after_tax_cash_flow', 0),
        'after_tax_cash_flow_per_owner': results.get('after_tax_cash_flow_per_owner', 0)
    }
    
    # Add seasonal breakdown if available
    if 'seasonal_breakdown' in results:
        annual_results['seasonal_breakdown'] = results['seasonal_breakdown']
    
    # Structure KPIs
    kpis = {
        'cap_rate_pct': results.get('cap_rate_pct', 0),
        'cash_on_cash_return_pct': results.get('cash_on_cash_return_pct', 0),
        'debt_coverage_ratio': results.get('debt_coverage_ratio', 0),
        'operating_expense_ratio_pct': results.get('operating_expense_ratio_pct', 0)
    }
    
    # Structure IRR results (include all new metrics)
    irr_data = {
        'equity_irr_with_sale_pct': irr_results.get('equity_irr_with_sale_pct', irr_results.get('irr_with_sale_pct', 0)),
        'equity_irr_without_sale_pct': irr_results.get('equity_irr_without_sale_pct', irr_results.get('irr_without_sale_pct', 0)),
        'project_irr_with_sale_pct': irr_results.get('project_irr_with_sale_pct', 0),
        'project_irr_without_sale_pct': irr_results.get('project_irr_without_sale_pct', 0),
        # After-tax IRRs
        'after_tax_equity_irr_with_sale_pct': irr_results.get('after_tax_equity_irr_with_sale_pct', 0),
        'after_tax_equity_irr_without_sale_pct': irr_results.get('after_tax_equity_irr_without_sale_pct', 0),
        'sale_proceeds_per_owner': irr_results.get('sale_proceeds_per_owner', 0),
        'final_property_value': irr_results.get('final_property_value', 0),
        'final_loan_balance': irr_results.get('final_loan_balance', 0),
        # New metrics
        'npv_at_5pct': irr_results.get('npv_at_5pct', 0),
        'moic': irr_results.get('moic', 0),
        'payback_period_years': irr_results.get('payback_period_years'),
        # Selling cost details
        'gross_sale_price': irr_results.get('gross_sale_price', 0),
        'selling_costs': irr_results.get('selling_costs', 0),
        'net_sale_price': irr_results.get('net_sale_price', 0),
        'selling_costs_rate_pct': irr_results.get('selling_costs_rate_pct', 0)
    }
    
    return {
        'config': config_dict,
        'annual_results': annual_results,
        'projection': projection,  # Variable length projection (typically 15 years, can be 6 for early exit)
        'projection_15yr': projection,  # Legacy key for backward compatibility
        'irr_results': irr_data,
        'kpis': kpis,
        'timestamp': datetime.now().isoformat()
    }


def export_sensitivity_to_json(sensitivities_dict: Dict[str, Dict]) -> Dict[str, Any]:
    """
    Export sensitivity analysis results to a structured dictionary ready for JSON serialization.
    
    Args:
        sensitivities_dict: Dictionary mapping parameter names to sensitivity results
                          Each value should be a dict with 'values' (list of parameter values),
                          'metrics' (dict mapping metric names to lists of values),
                          and optionally 'base_value' and 'base_metrics'
    
    Returns:
        Dictionary with all sensitivity data structured for JSON export
    """
    export_data = {
        'sensitivities': {},
        'timestamp': datetime.now().isoformat()
    }
    
    for param_name, param_data in sensitivities_dict.items():
        export_data['sensitivities'][param_name] = {
            'parameter_name': param_name,
            'base_value': param_data.get('base_value'),
            'base_metrics': param_data.get('base_metrics', {}),
            'values': param_data.get('values', []),
            'metrics': param_data.get('metrics', {})
        }
    
    return export_data


def export_monte_carlo_to_json(df: pd.DataFrame, stats: Dict[str, float]) -> Dict[str, Any]:
    """
    Export Monte Carlo simulation results to a structured dictionary ready for JSON serialization.
    
    Args:
        df: DataFrame with simulation results (one row per simulation)
        stats: Dictionary with summary statistics (mean, std, percentiles, etc.)
    
    Returns:
        Dictionary with Monte Carlo data structured for JSON export
    """
    # Sample a subset of data for charting (to keep JSON size manageable)
    # Use every Nth row or limit to 2000 rows max for better chart quality
    sample_size = min(2000, len(df))
    step = max(1, len(df) // sample_size)
    df_sample = df.iloc[::step].copy()
    
    # Convert DataFrame to records (list of dicts)
    sample_data = df_sample.to_dict('records')
    
    # Convert numpy types to native Python types for JSON serialization
    for record in sample_data:
        for key, value in record.items():
            if hasattr(value, 'item'):  # numpy scalar
                record[key] = value.item()
            elif pd.isna(value):
                record[key] = None
    
    # Convert stats to native types
    stats_clean = {}
    for key, value in stats.items():
        if hasattr(value, 'item'):
            stats_clean[key] = value.item()
        elif pd.isna(value):
            stats_clean[key] = None
        else:
            stats_clean[key] = value
    
    return {
        'statistics': stats_clean,
        'sample_data': sample_data,
        'total_simulations': len(df),
        'sample_size': len(sample_data),
        'timestamp': datetime.now().isoformat()
    }

