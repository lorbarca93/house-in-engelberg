"""
Monte Carlo Analysis for Engelberg Property Investment
Enhanced version with:
- Expanded stochastic inputs (seasonality, expenses, inflation)
- Advanced distributions (triangular, Beta, lognormal)
- Correlation support for realistic parameter relationships
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from scipy.stats import beta, lognorm, triang
from scipy.linalg import cholesky
from simulation import (
    create_base_case_config,
    BaseCaseConfig,
    compute_annual_cash_flows,
    compute_15_year_projection,
    calculate_irrs_from_projection,
    apply_sensitivity  # Use the centralized sensitivity function
)
from datetime import datetime
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Import shared layout functions
try:
    from analysis_sensitivity import (
        generate_top_toolbar,
        generate_sidebar_navigation,
        generate_shared_layout_css,
        generate_shared_layout_js
    )
except ImportError:
    # Fallback: define functions locally if import fails
    def generate_top_toolbar(report_title: str, back_link: str = "index.html", subtitle: str = "") -> str:
        return f'''<div class="top-toolbar"><div class="toolbar-left"><a href="{back_link}" class="toolbar-btn"><i class="fas fa-home"></i> <span class="toolbar-btn-text">Home</span></a></div><div class="toolbar-center"><h1 class="toolbar-title">{report_title}</h1>{f'<p class="toolbar-subtitle">{subtitle}</p>' if subtitle else ''}</div><div class="toolbar-right"></div></div>'''
    def generate_sidebar_navigation(sections): 
        nav_items = ''.join([f'<li><a href="#{s.get("id","")}" class="sidebar-item" data-section="{s.get("id","")}"><i class="{s.get("icon","fas fa-circle")}"></i><span class="sidebar-item-text">{s.get("title","")}</span></a></li>' for s in sections])
        return f'<nav class="sidebar"><div class="sidebar-header"><h3><i class="fas fa-bars"></i> Navigation</h3></div><ul class="sidebar-nav">{nav_items}</ul></nav>'
    def generate_shared_layout_css(): return '''.layout-container{display:flex;flex-direction:column;min-height:100vh;background:#f5f7fa}.top-toolbar{position:fixed;top:0;left:0;right:0;height:60px;background:var(--gradient-1);color:white;display:flex;align-items:center;justify-content:space-between;padding:0 20px;z-index:1000;box-shadow:0 2px 8px rgba(0,0,0,0.15)}.toolbar-left,.toolbar-right{display:flex;align-items:center;gap:15px}.toolbar-center{flex:1;text-align:center}.toolbar-title{font-size:1.3em;font-weight:700;margin:0;color:white}.toolbar-subtitle{font-size:0.85em;margin:0;opacity:0.9}.toolbar-btn{display:inline-flex;align-items:center;gap:8px;padding:10px 20px;background:rgba(255,255,255,0.2);color:white;text-decoration:none;border-radius:6px;font-size:0.9em;font-weight:600;transition:all 0.2s ease;border:1px solid rgba(255,255,255,0.3)}.toolbar-btn:hover{background:rgba(255,255,255,0.3);transform:translateY(-1px)}.sidebar{position:fixed;left:0;top:60px;width:250px;height:calc(100vh - 60px);background:white;box-shadow:2px 0 8px rgba(0,0,0,0.1);overflow-y:auto;z-index:999;transition:transform 0.3s ease}.sidebar-header{padding:20px;background:var(--primary);color:white;border-bottom:1px solid rgba(255,255,255,0.1)}.sidebar-header h3{font-size:1.1em;font-weight:600;margin:0;display:flex;align-items:center;gap:10px}.sidebar-nav{list-style:none;padding:0;margin:0}.sidebar-nav li{margin:0}.sidebar-item{display:flex;align-items:center;gap:12px;padding:15px 20px;color:#495057;text-decoration:none;border-left:3px solid transparent;transition:all 0.2s ease;font-size:0.9em}.sidebar-item:hover{background:#f8f9fa;color:var(--primary);border-left-color:var(--primary)}.sidebar-item.active{background:#e7f3ff;color:var(--primary);border-left-color:var(--primary);font-weight:600}.sidebar-item i{width:20px;text-align:center;font-size:0.9em}.sidebar-item-text{flex:1}.main-content{margin-left:250px;margin-top:60px;padding:30px 40px;background:white;min-height:calc(100vh - 60px)}.section{scroll-margin-top:80px}@media (max-width:768px){.sidebar{transform:translateX(-100%);width:250px}.sidebar.open{transform:translateX(0)}.main-content{margin-left:0}.toolbar-btn-text{display:none}.toolbar-title{font-size:1.1em}}.sidebar::-webkit-scrollbar{width:6px}.sidebar::-webkit-scrollbar-track{background:#f1f1f1}.sidebar::-webkit-scrollbar-thumb{background:#888;border-radius:3px}.sidebar::-webkit-scrollbar-thumb:hover{background:#555}'''
    def generate_shared_layout_js(): return '''<script>(function(){document.querySelectorAll('.sidebar-item').forEach(item=>{item.addEventListener('click',function(e){e.preventDefault();const targetId=this.getAttribute('href').substring(1);const targetElement=document.getElementById(targetId);if(targetElement){const offset=80;const elementPosition=targetElement.getBoundingClientRect().top;const offsetPosition=elementPosition+window.pageYOffset-offset;window.scrollTo({top:offsetPosition,behavior:'smooth'});updateActiveSection(targetId)}})});function updateActiveSection(activeId){document.querySelectorAll('.sidebar-item').forEach(item=>{item.classList.remove('active');if(item.getAttribute('data-section')===activeId){item.classList.add('active')}})}const observerOptions={root:null,rootMargin:'-20% 0px -70% 0px',threshold:0};const observer=new IntersectionObserver(function(entries){entries.forEach(entry=>{if(entry.isIntersecting){const sectionId=entry.target.id;if(sectionId){updateActiveSection(sectionId)}}})},observerOptions);document.querySelectorAll('.section[id], h2[id], h3[id]').forEach(section=>{observer.observe(section)})})();</script>'''

# Chart color constants matching CSS variables
CHART_COLORS = {
    'success': '#28a745',
    'danger': '#dc3545',
    'info': '#17a2b8',
    'warning': '#ffc107',
    'gradient_start': '#667eea',
    'gradient_end': '#764ba2'
}

# -----------------------------
# Distribution Types
# -----------------------------

@dataclass
class DistributionConfig:
    """Configuration for a random variable distribution."""
    dist_type: str  # 'uniform', 'normal', 'triangular', 'beta', 'lognormal'
    params: Dict[str, float]  # Distribution-specific parameters
    bounds: Optional[Tuple[float, float]] = None  # Optional min/max bounds for clipping
    
    def sample(self, size: int = 1) -> np.ndarray:
        """Sample from the distribution."""
        if self.dist_type == 'uniform':
            samples = np.random.uniform(self.params['min'], self.params['max'], size)
        elif self.dist_type == 'normal':
            samples = np.random.normal(self.params['mean'], self.params['std'], size)
        elif self.dist_type == 'triangular':
            samples = triang.rvs(
                c=(self.params['mode'] - self.params['min']) / (self.params['max'] - self.params['min']),
                loc=self.params['min'],
                scale=self.params['max'] - self.params['min'],
                size=size
            )
        elif self.dist_type == 'beta':
            # Beta distribution: alpha and beta shape parameters
            # Scale to [min, max] range
            samples = beta.rvs(
                self.params['alpha'],
                self.params['beta'],
                loc=self.params.get('min', 0),
                scale=self.params.get('max', 1) - self.params.get('min', 0),
                size=size
            )
        elif self.dist_type == 'lognormal':
            # Lognormal: mean and std of underlying normal distribution
            samples = lognorm.rvs(
                s=self.params['std'],
                scale=np.exp(self.params['mean']),
                size=size
            )
        else:
            raise ValueError(f"Unknown distribution type: {self.dist_type}")
        
        # Clip to bounds if provided
        if self.bounds:
            samples = np.clip(samples, self.bounds[0], self.bounds[1])
        
        return samples


def sample_correlated_variables(
    distributions: Dict[str, DistributionConfig],
    correlation_matrix: np.ndarray,
    size: int = 1
) -> Dict[str, np.ndarray]:
    """
    Sample correlated random variables using Cholesky decomposition.
    
    Uses a Gaussian copula approach: generate correlated standard normals,
    transform to uniform via CDF, then use inverse CDF of target distributions.
    
    Args:
        distributions: Dictionary mapping variable names to DistributionConfig
        correlation_matrix: Correlation matrix (must be positive semi-definite)
        size: Number of samples to generate
    
    Returns:
        Dictionary mapping variable names to sampled arrays
    """
    var_names = list(distributions.keys())
    n_vars = len(var_names)
    
    # Validate correlation matrix
    if correlation_matrix.shape != (n_vars, n_vars):
        raise ValueError(f"Correlation matrix must be {n_vars}x{n_vars}")
    
    # Check if correlation matrix is valid (symmetric, positive semi-definite)
    if not np.allclose(correlation_matrix, correlation_matrix.T):
        raise ValueError("Correlation matrix must be symmetric")
    
    # Generate independent standard normal samples
    Z = np.random.normal(0, 1, size=(size, n_vars))
    
    # Cholesky decomposition of correlation matrix
    try:
        L = cholesky(correlation_matrix, lower=True)
    except np.linalg.LinAlgError:
        # If not positive definite, use nearest positive definite matrix
        # Simple approach: add small value to diagonal
        correlation_matrix = correlation_matrix + np.eye(n_vars) * 1e-6
        L = cholesky(correlation_matrix, lower=True)
    
    # Transform to correlated standard normals
    X = Z @ L.T
    
    # Transform to uniform [0, 1] using CDF of standard normal
    from scipy.stats import norm
    U = norm.cdf(X)
    
    # Sample from each distribution using inverse transform sampling
    results = {}
    for i, var_name in enumerate(var_names):
        dist = distributions[var_name]
        
        # Use inverse CDF (PPF) for each distribution type
        if dist.dist_type == 'uniform':
            samples = dist.params['min'] + U[:, i] * (dist.params['max'] - dist.params['min'])
        elif dist.dist_type == 'normal':
            samples = norm.ppf(U[:, i], loc=dist.params['mean'], scale=dist.params['std'])
        elif dist.dist_type == 'triangular':
            # Manual inverse CDF for triangular
            c = (dist.params['mode'] - dist.params['min']) / (dist.params['max'] - dist.params['min'])
            u = U[:, i]
            samples = np.where(
                u < c,
                dist.params['min'] + np.sqrt(u * (dist.params['max'] - dist.params['min']) * (dist.params['mode'] - dist.params['min'])),
                dist.params['max'] - np.sqrt((1 - u) * (dist.params['max'] - dist.params['min']) * (dist.params['max'] - dist.params['mode']))
            )
        elif dist.dist_type == 'beta':
            samples = beta.ppf(
                U[:, i],
                dist.params['alpha'],
                dist.params['beta'],
                loc=dist.params.get('min', 0),
                scale=dist.params.get('max', 1) - dist.params.get('min', 0)
            )
        elif dist.dist_type == 'lognormal':
            samples = lognorm.ppf(
                U[:, i],
                s=dist.params['std'],
                scale=np.exp(dist.params['mean'])
            )
        else:
            # Fallback: sample independently
            samples = dist.sample(size)
        
        # Clip to bounds if provided
        if dist.bounds:
            samples = np.clip(samples, dist.bounds[0], dist.bounds[1])
        
        results[var_name] = samples
    
    return results

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
        'plot_bgcolor': 'white',
        'paper_bgcolor': 'white',
        'margin': {'l': 60, 'r': 30, 't': 80, 'b': 60}
    }


def apply_enhanced_sensitivity(
    base_config: BaseCaseConfig,
    occupancy: Optional[float] = None,
    daily_rate: Optional[float] = None,
    management_fee: Optional[float] = None,
    interest_rate: Optional[float] = None,
    seasonal_occupancy: Optional[Dict[str, float]] = None,  # Dict mapping season names to occupancy rates
    seasonal_rates: Optional[Dict[str, float]] = None,  # Dict mapping season names to ADR
    owner_nights: Optional[int] = None,
    nubbing_costs_annual: Optional[float] = None,
    electricity_internet_annual: Optional[float] = None,
    maintenance_rate: Optional[float] = None,
    inflation_rate: Optional[float] = None,
    property_appreciation_rate: Optional[float] = None,
) -> BaseCaseConfig:
    """
    Enhanced version of apply_sensitivity that supports more parameters.
    
    Args:
        base_config: Base case configuration
        occupancy: Overall occupancy rate (applied to all seasons if seasonal_occupancy not provided)
        daily_rate: Overall average daily rate (applied proportionally if seasonal_rates not provided)
        management_fee: Property management fee rate
        interest_rate: Interest rate
        seasonal_occupancy: Dict mapping season names to occupancy rates (e.g., {'Winter Peak': 0.80})
        seasonal_rates: Dict mapping season names to ADR (e.g., {'Winter Peak': 280.0})
        owner_nights: Owner nights per person
        nubbing_costs_annual: Annual nubbing costs (water, heating)
        electricity_internet_annual: Annual electricity and internet costs
        maintenance_rate: Maintenance rate as % of property value
        inflation_rate: Annual inflation rate (for projection, not stored in config)
        property_appreciation_rate: Annual property appreciation rate (for projection, not stored in config)
    
    Returns:
        Modified BaseCaseConfig
    """
    # Use base apply_sensitivity for core parameters
    config = apply_sensitivity(
        base_config,
        occupancy=occupancy,
        daily_rate=daily_rate,
        management_fee=management_fee,
        interest_rate=interest_rate
    )
    
    # Handle seasonal variations if provided
    if seasonal_occupancy or seasonal_rates:
        from simulation import SeasonalParams, RentalParams
        new_seasons = []
        for season in config.rental.seasons:
            new_occ = seasonal_occupancy.get(season.name, season.occupancy_rate) if seasonal_occupancy else season.occupancy_rate
            new_rate = seasonal_rates.get(season.name, season.average_daily_rate) if seasonal_rates else season.average_daily_rate
            
            new_seasons.append(SeasonalParams(
                name=season.name,
                months=season.months,
                occupancy_rate=new_occ,
                average_daily_rate=new_rate,
                nights_in_season=season.nights_in_season
            ))
        
        config.rental = RentalParams(
            owner_nights_per_person=owner_nights if owner_nights is not None else config.rental.owner_nights_per_person,
            num_owners=config.rental.num_owners,
            occupancy_rate=config.rental.occupancy_rate,
            average_daily_rate=config.rental.average_daily_rate,
            days_per_year=config.rental.days_per_year,
            seasons=new_seasons
        )
    
    # Handle owner nights (if not already handled in seasonal section)
    if owner_nights is not None and not (seasonal_occupancy or seasonal_rates):
        from simulation import RentalParams
        config.rental = RentalParams(
            owner_nights_per_person=owner_nights,
            num_owners=config.rental.num_owners,
            occupancy_rate=config.rental.occupancy_rate,
            average_daily_rate=config.rental.average_daily_rate,
            days_per_year=config.rental.days_per_year,
            seasons=config.rental.seasons
        )
    elif owner_nights is not None:
        # Update owner nights in existing rental config
        from simulation import RentalParams
        config.rental = RentalParams(
            owner_nights_per_person=owner_nights,
            num_owners=config.rental.num_owners,
            occupancy_rate=config.rental.occupancy_rate,
            average_daily_rate=config.rental.average_daily_rate,
            days_per_year=config.rental.days_per_year,
            seasons=config.rental.seasons
        )
    
    # Handle expense parameters
    if nubbing_costs_annual is not None or electricity_internet_annual is not None or maintenance_rate is not None:
        from simulation import ExpenseParams
        config.expenses = ExpenseParams(
            property_management_fee_rate=config.expenses.property_management_fee_rate,
            cleaning_cost_per_stay=config.expenses.cleaning_cost_per_stay,
            average_length_of_stay=config.expenses.average_length_of_stay,
            tourist_tax_per_person_per_night=config.expenses.tourist_tax_per_person_per_night,
            avg_guests_per_night=config.expenses.avg_guests_per_night,
            insurance_annual=config.expenses.insurance_annual,
            nubbing_costs_annual=nubbing_costs_annual if nubbing_costs_annual is not None else config.expenses.nubbing_costs_annual,
            electricity_internet_annual=electricity_internet_annual if electricity_internet_annual is not None else config.expenses.electricity_internet_annual,
            maintenance_rate=maintenance_rate if maintenance_rate is not None else config.expenses.maintenance_rate,
            property_value=config.expenses.property_value
        )
    
    return config


def get_default_distributions() -> Dict[str, DistributionConfig]:
    """
    Get default distribution configurations for Monte Carlo simulation.
    Returns distributions for all stochastic parameters.
    """
    return {
        # Core revenue parameters
        'occupancy_rate': DistributionConfig(
            dist_type='beta',
            params={'alpha': 2.0, 'beta': 1.5, 'min': 0.30, 'max': 0.75},
            bounds=(0.30, 0.75)
        ),
        'daily_rate': DistributionConfig(
            dist_type='lognormal',
            params={'mean': np.log(300), 'std': 0.25},
            bounds=(150, 450)
        ),
        
        # Seasonal parameters (winter, summer, offpeak)
        'winter_occupancy': DistributionConfig(
            dist_type='triangular',
            params={'min': 0.60, 'mode': 0.75, 'max': 0.90},
            bounds=(0.60, 0.90)
        ),
        'winter_rate': DistributionConfig(
            dist_type='normal',
            params={'mean': 250, 'std': 40},
            bounds=(180, 350)
        ),
        'summer_occupancy': DistributionConfig(
            dist_type='triangular',
            params={'min': 0.50, 'mode': 0.65, 'max': 0.80},
            bounds=(0.50, 0.80)
        ),
        'summer_rate': DistributionConfig(
            dist_type='normal',
            params={'mean': 200, 'std': 30},
            bounds=(150, 280)
        ),
        'offpeak_occupancy': DistributionConfig(
            dist_type='triangular',
            params={'min': 0.35, 'mode': 0.50, 'max': 0.65},
            bounds=(0.35, 0.65)
        ),
        'offpeak_rate': DistributionConfig(
            dist_type='normal',
            params={'mean': 150, 'std': 25},
            bounds=(100, 220)
        ),
        
        # Financial parameters
        'interest_rate': DistributionConfig(
            dist_type='normal',
            params={'mean': 0.02, 'std': 0.005},
            bounds=(0.010, 0.040)
        ),
        'management_fee': DistributionConfig(
            dist_type='triangular',
            params={'min': 0.18, 'mode': 0.20, 'max': 0.35},
            bounds=(0.18, 0.35)
        ),
        
        # Expense parameters
        'owner_nights': DistributionConfig(
            dist_type='normal',
            params={'mean': 5.0, 'std': 1.0},
            bounds=(3, 8)
        ),
        'nubbing_costs_annual': DistributionConfig(
            dist_type='lognormal',
            params={'mean': np.log(2000), 'std': 0.20},
            bounds=(1200, 3500)
        ),
        'electricity_internet_annual': DistributionConfig(
            dist_type='lognormal',
            params={'mean': np.log(1000), 'std': 0.20},
            bounds=(600, 2000)
        ),
        'maintenance_rate': DistributionConfig(
            dist_type='normal',
            params={'mean': 0.01, 'std': 0.003},
            bounds=(0.005, 0.020)
        ),
        
        # Projection parameters
        'inflation_rate': DistributionConfig(
            dist_type='normal',
            params={'mean': 0.02, 'std': 0.005},
            bounds=(0.005, 0.040)
        ),
        'property_appreciation': DistributionConfig(
            dist_type='normal',
            params={'mean': 0.025, 'std': 0.010},  # Mean 2.5% per year (realistic for Swiss real estate)
            bounds=(0.0, 0.050)  # No negative appreciation, up to 5% per year
        ),
    }


def get_default_correlation_matrix() -> np.ndarray:
    """
    Get default correlation matrix for Monte Carlo simulation.
    Defines realistic correlations between parameters.
    
    Order of variables:
    0: occupancy_rate
    1: daily_rate
    2: winter_occupancy
    3: winter_rate
    4: summer_occupancy
    5: summer_rate
    6: offpeak_occupancy
    7: offpeak_rate
    8: interest_rate
    9: management_fee
    10: owner_nights
    11: nubbing_costs_annual
    12: electricity_internet_annual
    13: maintenance_rate
    14: inflation_rate
    15: property_appreciation
    """
    n = 16  # Updated to 16 to include split utilities
    corr = np.eye(n)
    
    # Revenue correlations: occupancy and ADR are positively correlated
    corr[0, 1] = corr[1, 0] = 0.4  # Overall occupancy vs overall rate
    corr[2, 3] = corr[3, 2] = 0.5  # Winter occupancy vs winter rate
    corr[4, 5] = corr[5, 4] = 0.5  # Summer occupancy vs summer rate
    corr[6, 7] = corr[7, 6] = 0.5  # Offpeak occupancy vs offpeak rate
    
    # Seasonal correlations: peak seasons tend to move together
    corr[2, 4] = corr[4, 2] = 0.3  # Winter vs summer occupancy
    corr[3, 5] = corr[5, 3] = 0.2  # Winter vs summer rates
    
    # Financial correlations: interest rates affect property appreciation
    corr[8, 15] = corr[15, 8] = -0.3  # Interest rate vs appreciation (negative)
    corr[14, 15] = corr[15, 14] = 0.2  # Inflation vs appreciation
    
    # Expense correlations: utilities and maintenance tend to move with inflation
    corr[11, 14] = corr[14, 11] = 0.4  # Nubbing costs vs inflation
    corr[12, 14] = corr[14, 12] = 0.3  # Electricity/internet vs inflation
    corr[13, 14] = corr[14, 13] = 0.3  # Maintenance vs inflation
    
    return corr


def run_monte_carlo_simulation(base_config: BaseCaseConfig, 
                                num_simulations: int = 10000,
                                discount_rate: float = 0.03,  # 3% discount rate (realistic for real estate)
                                use_correlations: bool = True,
                                use_seasonality: bool = True,
                                use_expense_variation: bool = True) -> pd.DataFrame:
    """
    Run enhanced Monte Carlo simulation with expanded stochastic inputs and correlations.
    
    Args:
        base_config: Base case configuration
        num_simulations: Number of simulation runs
        discount_rate: Discount rate for NPV calculation
        use_correlations: Whether to use correlation matrix for sampling
        use_seasonality: Whether to vary seasonal parameters independently
        use_expense_variation: Whether to vary expense parameters
    
    Returns:
        DataFrame with simulation results including all sampled parameters
    """
    print(f"[*] Running {num_simulations:,} Monte Carlo simulations...")
    print(f"    - Correlations: {'Enabled' if use_correlations else 'Disabled'}")
    print(f"    - Seasonality: {'Enabled' if use_seasonality else 'Disabled'}")
    print(f"    - Expense Variation: {'Enabled' if use_expense_variation else 'Disabled'}")
    
    # Get distribution configurations
    all_distributions = get_default_distributions()
    
    # Select which distributions to use based on flags
    active_distributions = {}
    var_order = []
    
    # Core parameters (always used)
    active_distributions['occupancy_rate'] = all_distributions['occupancy_rate']
    active_distributions['daily_rate'] = all_distributions['daily_rate']
    active_distributions['interest_rate'] = all_distributions['interest_rate']
    active_distributions['management_fee'] = all_distributions['management_fee']
    var_order.extend(['occupancy_rate', 'daily_rate', 'interest_rate', 'management_fee'])
    
    # Seasonal parameters
    if use_seasonality:
        active_distributions['winter_occupancy'] = all_distributions['winter_occupancy']
        active_distributions['winter_rate'] = all_distributions['winter_rate']
        active_distributions['summer_occupancy'] = all_distributions['summer_occupancy']
        active_distributions['summer_rate'] = all_distributions['summer_rate']
        active_distributions['offpeak_occupancy'] = all_distributions['offpeak_occupancy']
        active_distributions['offpeak_rate'] = all_distributions['offpeak_rate']
        var_order.extend(['winter_occupancy', 'winter_rate', 'summer_occupancy', 'summer_rate', 
                         'offpeak_occupancy', 'offpeak_rate'])
    
    # Expense parameters
    if use_expense_variation:
        active_distributions['owner_nights'] = all_distributions['owner_nights']
        active_distributions['nubbing_costs_annual'] = all_distributions['nubbing_costs_annual']
        active_distributions['electricity_internet_annual'] = all_distributions['electricity_internet_annual']
        active_distributions['maintenance_rate'] = all_distributions['maintenance_rate']
        var_order.extend(['owner_nights', 'nubbing_costs_annual', 'electricity_internet_annual', 'maintenance_rate'])
    
    # Projection parameters (always used)
    active_distributions['inflation_rate'] = all_distributions['inflation_rate']
    active_distributions['property_appreciation'] = all_distributions['property_appreciation']
    var_order.extend(['inflation_rate', 'property_appreciation'])
    
    # Get correlation matrix (subset for active variables)
    if use_correlations:
        full_corr = get_default_correlation_matrix()
        # Map variable names to indices in full correlation matrix
        full_var_order = ['occupancy_rate', 'daily_rate', 'winter_occupancy', 'winter_rate',
                          'summer_occupancy', 'summer_rate', 'offpeak_occupancy', 'offpeak_rate',
                          'interest_rate', 'management_fee', 'owner_nights', 'nubbing_costs_annual',
                          'electricity_internet_annual', 'maintenance_rate', 'inflation_rate', 'property_appreciation']
        var_indices = [full_var_order.index(v) for v in var_order]
        correlation_matrix = full_corr[np.ix_(var_indices, var_indices)]
    else:
        correlation_matrix = np.eye(len(var_order))
    
    results = []
    
    # Sample all parameters at once (more efficient)
    if use_correlations and len(var_order) > 1:
        # Use correlated sampling
        samples = sample_correlated_variables(active_distributions, correlation_matrix, num_simulations)
    else:
        # Sample independently
        samples = {}
        for var_name in var_order:
            samples[var_name] = active_distributions[var_name].sample(num_simulations)
    
    # Run simulations
    for i in range(num_simulations):
        if (i + 1) % 1000 == 0:
            print(f"  Progress: {i + 1:,} / {num_simulations:,} simulations ({100 * (i + 1) / num_simulations:.1f}%)")
        
        # Extract sampled values for this simulation
        occupancy = float(samples['occupancy_rate'][i])
        daily_rate = float(samples['daily_rate'][i])
        interest_rate = float(samples['interest_rate'][i])
        management_fee = float(samples['management_fee'][i])
        inflation_rate = float(samples['inflation_rate'][i])
        property_appreciation = float(samples['property_appreciation'][i])
        
        # Seasonal parameters
        seasonal_occupancy = None
        seasonal_rates = None
        if use_seasonality:
            seasonal_occupancy = {
                'Winter Peak (Ski Season)': float(samples['winter_occupancy'][i]),
                'Summer Peak (Hiking Season)': float(samples['summer_occupancy'][i]),
                'Off-Peak (Shoulder Seasons)': float(samples['offpeak_occupancy'][i])
            }
            seasonal_rates = {
                'Winter Peak (Ski Season)': float(samples['winter_rate'][i]),
                'Summer Peak (Hiking Season)': float(samples['summer_rate'][i]),
                'Off-Peak (Shoulder Seasons)': float(samples['offpeak_rate'][i])
            }
        
        # Expense parameters
        owner_nights = None
        nubbing_costs_annual = None
        electricity_internet_annual = None
        maintenance_rate = None
        if use_expense_variation:
            owner_nights = int(round(samples['owner_nights'][i]))
            nubbing_costs_annual = float(samples['nubbing_costs_annual'][i])
            electricity_internet_annual = float(samples['electricity_internet_annual'][i])
            maintenance_rate = float(samples['maintenance_rate'][i])
        
        # Create modified configuration
        config = apply_enhanced_sensitivity(
            base_config,
            occupancy=occupancy if not use_seasonality else None,  # Only use if not using seasonality
            daily_rate=daily_rate if not use_seasonality else None,
            interest_rate=interest_rate,
            management_fee=management_fee,
            seasonal_occupancy=seasonal_occupancy,
            seasonal_rates=seasonal_rates,
            owner_nights=owner_nights,
            nubbing_costs_annual=nubbing_costs_annual,
            electricity_internet_annual=electricity_internet_annual,
            maintenance_rate=maintenance_rate
        )
        
        # Calculate annual cash flows
        annual_result = compute_annual_cash_flows(config)
        
        # Calculate 15-year projection with variable inflation and appreciation
        projection = compute_15_year_projection(
            config, 
            start_year=2026, 
            inflation_rate=inflation_rate, 
            property_appreciation_rate=property_appreciation
        )
        
        # Get final values
        final_property_value = projection[-1]['property_value']
        final_loan_balance = projection[-1]['remaining_loan_balance']
        initial_equity = annual_result['equity_per_owner']
        
        # Calculate IRRs
        irr_results = calculate_irrs_from_projection(
            projection,
            initial_equity,
            final_property_value,
            final_loan_balance,
            config.financing.num_owners,
            purchase_price=config.financing.purchase_price
        )
        
        # Calculate NPV
        cash_flows = [year['cash_flow_per_owner'] for year in projection]
        sale_proceeds_per_owner = (final_property_value - final_loan_balance) / config.financing.num_owners
        
        npv = -initial_equity
        for j, cf in enumerate(cash_flows):
            npv += cf / ((1 + discount_rate) ** (j + 1))
        npv += sale_proceeds_per_owner / ((1 + discount_rate) ** len(cash_flows))
        
        # Store results with all sampled parameters
        result_row = {
            'simulation': i + 1,
            'occupancy_rate': occupancy,
            'daily_rate': daily_rate,
            'interest_rate': interest_rate,
            'management_fee_rate': management_fee,
            'inflation_rate': inflation_rate,
            'property_appreciation': property_appreciation,
            'annual_cash_flow': annual_result['cash_flow_after_debt_service'],
            'cash_flow_per_owner': annual_result['cash_flow_per_owner'],
            'gross_rental_income': annual_result['gross_rental_income'],
            'net_operating_income': annual_result['net_operating_income'],
            'npv': npv,
            'irr_with_sale': irr_results['irr_with_sale_pct'],
            'irr_without_sale': irr_results['irr_without_sale_pct'],
            'final_property_value': final_property_value,
            'sale_proceeds_per_owner': sale_proceeds_per_owner
        }
        
        # Add seasonal parameters if used
        if use_seasonality:
            result_row.update({
                'winter_occupancy': seasonal_occupancy['Winter Peak (Ski Season)'],
                'winter_rate': seasonal_rates['Winter Peak (Ski Season)'],
                'summer_occupancy': seasonal_occupancy['Summer Peak (Hiking Season)'],
                'summer_rate': seasonal_rates['Summer Peak (Hiking Season)'],
                'offpeak_occupancy': seasonal_occupancy['Off-Peak (Shoulder Seasons)'],
                'offpeak_rate': seasonal_rates['Off-Peak (Shoulder Seasons)']
            })
        
        # Add expense parameters if used
        if use_expense_variation:
            result_row.update({
                'owner_nights': owner_nights,
                'nubbing_costs_annual': nubbing_costs_annual,
                'electricity_internet_annual': electricity_internet_annual,
                'maintenance_rate': maintenance_rate
            })
        
        results.append(result_row)
    
    print(f"[+] Completed {num_simulations:,} simulations")
    
    return pd.DataFrame(results)


def calculate_statistics(df: pd.DataFrame) -> dict:
    """Calculate summary statistics from simulation results."""
    return {
        'npv': {
            'mean': df['npv'].mean(),
            'median': df['npv'].median(),
            'std': df['npv'].std(),
            'min': df['npv'].min(),
            'max': df['npv'].max(),
            'p5': df['npv'].quantile(0.05),
            'p10': df['npv'].quantile(0.10),
            'p25': df['npv'].quantile(0.25),
            'p75': df['npv'].quantile(0.75),
            'p90': df['npv'].quantile(0.90),
            'p95': df['npv'].quantile(0.95),
            'positive_prob': (df['npv'] > 0).sum() / len(df),
        },
        'irr_with_sale': {
            'mean': df['irr_with_sale'].mean(),
            'median': df['irr_with_sale'].median(),
            'std': df['irr_with_sale'].std(),
            'min': df['irr_with_sale'].min(),
            'max': df['irr_with_sale'].max(),
            'p5': df['irr_with_sale'].quantile(0.05),
            'p95': df['irr_with_sale'].quantile(0.95),
        },
        'annual_cash_flow': {
            'mean': df['annual_cash_flow'].mean(),
            'median': df['annual_cash_flow'].median(),
            'std': df['annual_cash_flow'].std(),
            'min': df['annual_cash_flow'].min(),
            'max': df['annual_cash_flow'].max(),
            'positive_prob': (df['annual_cash_flow'] > 0).sum() / len(df),
        }
    }


def create_monte_carlo_charts(df: pd.DataFrame, stats: dict) -> list:
    """Create visualization charts for Monte Carlo results."""
    charts = []
    
    # Chart 1: NPV Distribution Histogram
    fig1 = go.Figure()
    fig1.add_trace(go.Histogram(
        x=df['npv'],
        nbinsx=100,
        name='NPV Distribution',
        marker_color='#667eea',
        opacity=0.7
    ))
    
    # Add vertical lines for key statistics
    fig1.add_vline(x=stats['npv']['mean'], line_dash="dash", line_color="red", 
                   annotation_text=f"Mean: {stats['npv']['mean']:,.0f} CHF")
    fig1.add_vline(x=stats['npv']['median'], line_dash="dash", line_color="green",
                   annotation_text=f"Median: {stats['npv']['median']:,.0f} CHF")
    fig1.add_vline(x=0, line_dash="solid", line_color="black", line_width=2,
                   annotation_text="Break-even")
    
    fig1.update_layout(
        title="NPV Distribution - Monte Carlo Simulation",
        xaxis_title="NPV (CHF)",
        yaxis_title="Frequency",
        height=500,
        showlegend=False
    )
    charts.append(("npv_distribution", fig1))
    
    # Chart 2: IRR Distribution Histogram
    fig2 = go.Figure()
    fig2.add_trace(go.Histogram(
        x=df['irr_with_sale'],
        nbinsx=100,
        name='IRR Distribution',
        marker=dict(
            color=CHART_COLORS['success'],
            line=dict(color='#ffffff', width=1),
            opacity=0.75
        ),
        hovertemplate='<b>IRR Range</b><br>Value: %{x:.2f}%<br>Frequency: %{y}<extra></extra>'
    ))
    
    fig2.add_vline(
        x=stats['irr_with_sale']['mean'],
        line_dash="dash",
        line_color=CHART_COLORS['danger'],
        line_width=2,
        annotation_text=f"Mean: {stats['irr_with_sale']['mean']:.2f}%",
        annotation_position="top",
        annotation_font_size=11
    )
    fig2.add_vline(
        x=stats['irr_with_sale']['median'],
        line_dash="dash",
        line_color=CHART_COLORS['info'],
        line_width=2,
        annotation_text=f"Median: {stats['irr_with_sale']['median']:.2f}%",
        annotation_position="top",
        annotation_font_size=11
    )
    
    template = get_chart_template()
    layout_updates = template.copy()
    layout_updates.update({
        'title': {
            'text': "IRR (with Sale) Distribution - Monte Carlo Simulation",
            'font': template['title_font'],
            'x': template['title_x'],
            'xanchor': template['title_xanchor'],
            'pad': template['title_pad']
        },
        'xaxis_title': "IRR (%)",
        'yaxis_title': "Frequency",
        'height': 550,
        'showlegend': False
    })
    fig2.update_layout(**layout_updates)
    charts.append(("irr_distribution", fig2))
    
    # Chart 3: Cumulative Probability Distribution (NPV)
    sorted_npv = np.sort(df['npv'])
    cumulative_prob = np.arange(1, len(sorted_npv) + 1) / len(sorted_npv)
    
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=sorted_npv,
        y=cumulative_prob * 100,
        mode='lines',
        name='Cumulative Probability',
        line=dict(color='#667eea', width=2)
    ))
    
    fig3.add_hline(y=50, line_dash="dash", line_color="gray",
                   annotation_text="50th Percentile (Median)")
    fig3.add_hline(y=90, line_dash="dash", line_color="orange",
                   annotation_text="90th Percentile")
    fig3.add_hline(y=10, line_dash="dash", line_color="orange",
                   annotation_text="10th Percentile")
    
    fig3.update_traces(
        line=dict(color=CHART_COLORS['gradient_start'], width=3),
        hovertemplate='<b>Cumulative Probability</b><br>NPV: %{x:,.0f} CHF<br>Probability: %{y:.1f}%<extra></extra>'
    )
    template = get_chart_template()
    layout_updates = template.copy()
    layout_updates.update({
        'title': {
            'text': "NPV Cumulative Probability Distribution",
            'font': template['title_font'],
            'x': template['title_x'],
            'xanchor': template['title_xanchor'],
            'pad': template['title_pad']
        },
        'xaxis_title': "NPV (CHF)",
        'yaxis_title': "Probability (%)",
        'height': 550
    })
    fig3.update_layout(**layout_updates)
    charts.append(("npv_cumulative", fig3))
    
    # Chart 4: Scatter Plot - Occupancy vs Daily Rate (colored by NPV)
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=df['occupancy_rate'] * 100,
        y=df['daily_rate'],
        mode='markers',
        marker=dict(
            size=5,
            color=df['npv'],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="NPV (CHF)"),
            opacity=0.6
        ),
        text=[f"NPV: {n:,.0f} CHF<br>IRR: {i:.2f}%" 
              for n, i in zip(df['npv'], df['irr_with_sale'])],
        hovertemplate='Occupancy: %{x:.1f}%<br>Daily Rate: %{y:.0f} CHF<br>%{text}<extra></extra>',
        name='Simulations'
    ))
    
    fig4.update_traces(
        marker=dict(
            size=6,
            opacity=0.6,
            line=dict(width=0.5, color='rgba(255, 255, 255, 0.3)')
        ),
        hovertemplate='<b>Simulation</b><br>Occupancy: %{x:.1f}%<br>Daily Rate: %{y:.0f} CHF<br>%{text}<extra></extra>'
    )
    layout_updates = template.copy()
    layout_updates.update({
        'title': {
            'text': "NPV Sensitivity: Occupancy Rate vs Daily Rate",
            'font': template['title_font'],
            'x': template['title_x'],
            'xanchor': template['title_xanchor'],
            'pad': template['title_pad']
        },
        'xaxis_title': "Occupancy Rate (%)",
        'yaxis_title': "Daily Rate (CHF)",
        'height': 550,
        'showlegend': False
    })
    fig4.update_layout(**layout_updates)
    charts.append(("occupancy_daily_scatter", fig4))
    
    # Chart 5: Scatter Plot - Interest Rate vs Management Fee (colored by NPV)
    fig5_scatter = go.Figure()
    fig5_scatter.add_trace(go.Scatter(
        x=df['interest_rate'] * 100,
        y=df['management_fee_rate'] * 100,
        mode='markers',
        marker=dict(
            size=5,
            color=df['npv'],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="NPV (CHF)"),
            opacity=0.6
        ),
        text=[f"NPV: {n:,.0f} CHF<br>IRR: {i:.2f}%" 
              for n, i in zip(df['npv'], df['irr_with_sale'])],
        hovertemplate='Interest Rate: %{x:.2f}%<br>Management Fee: %{y:.1f}%<br>%{text}<extra></extra>',
        name='Simulations'
    ))
    
    fig5_scatter.update_traces(
        marker=dict(
            size=6,
            opacity=0.6,
            line=dict(width=0.5, color='rgba(255, 255, 255, 0.3)')
        ),
        hovertemplate='<b>Simulation</b><br>Interest Rate: %{x:.2f}%<br>Management Fee: %{y:.1f}%<br>%{text}<extra></extra>'
    )
    layout_updates = template.copy()
    layout_updates.update({
        'title': {
            'text': "NPV Sensitivity: Interest Rate vs Management Fee Rate",
            'font': template['title_font'],
            'x': template['title_x'],
            'xanchor': template['title_xanchor'],
            'pad': template['title_pad']
        },
        'xaxis_title': "Interest Rate (%)",
        'yaxis_title': "Management Fee Rate (%)",
        'height': 550,
        'showlegend': False
    })
    fig5_scatter.update_layout(**layout_updates)
    charts.append(("interest_management_scatter", fig5_scatter))
    
    # Chart 6: Box Plot - NPV by Parameter Quartiles
    fig6 = make_subplots(
        rows=2, cols=2,
        subplot_titles=('NPV by Occupancy Quartile', 'NPV by Daily Rate Quartile',
                        'NPV by Interest Rate Quartile', 'NPV by Management Fee Quartile'),
        vertical_spacing=0.12,
        horizontal_spacing=0.10
    )
    
    # Occupancy quartiles
    df['occ_quartile'] = pd.qcut(df['occupancy_rate'], q=4, labels=['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)'], duplicates='drop')
    for q in df['occ_quartile'].cat.categories:
        subset = df[df['occ_quartile'] == q]['npv']
        if len(subset) > 0:
            fig6.add_trace(go.Box(y=subset, name=str(q), showlegend=False), row=1, col=1)
    
    # Daily rate quartiles
    df['rate_quartile'] = pd.qcut(df['daily_rate'], q=4, labels=['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)'], duplicates='drop')
    for q in df['rate_quartile'].cat.categories:
        subset = df[df['rate_quartile'] == q]['npv']
        if len(subset) > 0:
            fig6.add_trace(go.Box(y=subset, name=str(q), showlegend=False), row=1, col=2)
    
    # Interest rate quartiles
    df['int_quartile'] = pd.qcut(df['interest_rate'], q=4, labels=['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)'], duplicates='drop')
    for q in df['int_quartile'].cat.categories:
        subset = df[df['int_quartile'] == q]['npv']
        if len(subset) > 0:
            fig6.add_trace(go.Box(y=subset, name=str(q), showlegend=False), row=2, col=1)
    
    # Management fee quartiles
    df['mgmt_quartile'] = pd.qcut(df['management_fee_rate'], q=4, labels=['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)'], duplicates='drop')
    for q in df['mgmt_quartile'].cat.categories:
        subset = df[df['mgmt_quartile'] == q]['npv']
        if len(subset) > 0:
            fig6.add_trace(go.Box(y=subset, name=str(q), showlegend=False), row=2, col=2)
    
    fig6.update_layout(
        height=800, 
        title_text="NPV Distribution by Parameter Quartiles", 
        showlegend=False,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    fig6.update_yaxes(title_text="NPV (CHF)", row=1, col=1)
    fig6.update_yaxes(title_text="NPV (CHF)", row=1, col=2)
    fig6.update_yaxes(title_text="NPV (CHF)", row=2, col=1)
    fig6.update_yaxes(title_text="NPV (CHF)", row=2, col=2)
    
    charts.append(("npv_by_quartiles", fig6))
    
    # Chart 7: Correlation Charts - NPV vs each key parameter
    fig7 = make_subplots(
        rows=2, cols=2,
        subplot_titles=('NPV vs Occupancy Rate', 'NPV vs Daily Rate',
                        'NPV vs Interest Rate', 'NPV vs Management Fee Rate'),
        vertical_spacing=0.12,
        horizontal_spacing=0.10
    )
    
    # NPV vs Occupancy Rate
    fig7.add_trace(go.Scatter(
        x=df['occupancy_rate'] * 100,
        y=df['npv'],
        mode='markers',
        marker=dict(size=3, opacity=0.5, color='#667eea'),
        name='Occupancy',
        showlegend=False
    ), row=1, col=1)
    
    # NPV vs Daily Rate
    fig7.add_trace(go.Scatter(
        x=df['daily_rate'],
        y=df['npv'],
        mode='markers',
        marker=dict(size=3, opacity=0.5, color='#2ecc71'),
        name='Daily Rate',
        showlegend=False
    ), row=1, col=2)
    
    # NPV vs Interest Rate
    fig7.add_trace(go.Scatter(
        x=df['interest_rate'] * 100,
        y=df['npv'],
        mode='markers',
        marker=dict(size=3, opacity=0.5, color='#e74c3c'),
        name='Interest Rate',
        showlegend=False
    ), row=2, col=1)
    
    # NPV vs Management Fee
    fig7.add_trace(go.Scatter(
        x=df['management_fee_rate'] * 100,
        y=df['npv'],
        mode='markers',
        marker=dict(size=3, opacity=0.5, color='#f39c12'),
        name='Management Fee',
        showlegend=False
    ), row=2, col=2)
    
    fig7.update_layout(
        height=600,
        title_text="NPV vs Key Parameters",
        showlegend=False,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    fig7.update_xaxes(title_text="Occupancy Rate (%)", row=1, col=1)
    fig7.update_xaxes(title_text="Daily Rate (CHF)", row=1, col=2)
    fig7.update_xaxes(title_text="Interest Rate (%)", row=2, col=1)
    fig7.update_xaxes(title_text="Management Fee Rate (%)", row=2, col=2)
    fig7.update_yaxes(title_text="NPV (CHF)", row=1, col=1)
    fig7.update_yaxes(title_text="NPV (CHF)", row=1, col=2)
    fig7.update_yaxes(title_text="NPV (CHF)", row=2, col=1)
    fig7.update_yaxes(title_text="NPV (CHF)", row=2, col=2)
    
    charts.append(("correlation_charts", fig7))
    
    return charts


def generate_monte_carlo_html(df: pd.DataFrame, stats: dict, charts: list, 
                              base_config: BaseCaseConfig, num_simulations: int,
                              output_path: str = "website/report_monte_carlo.html"):
    """Generate HTML report for Monte Carlo analysis."""
    
    def format_currency(value):
        return f"{value:,.0f} CHF"
    
    def format_percent(value):
        return f"{value:.2f}%"
    
    # Calculate base case for comparison
    from simulation import compute_annual_cash_flows, compute_15_year_projection, calculate_irrs_from_projection
    base_result = compute_annual_cash_flows(base_config)
    base_projection = compute_15_year_projection(base_config, start_year=2026, inflation_rate=0.02, property_appreciation_rate=0.025)  # 2.5% property appreciation per year
    base_final_value = base_projection[-1]['property_value']
    base_final_loan = base_projection[-1]['remaining_loan_balance']
    base_irr = calculate_irrs_from_projection(
        base_projection,
        base_result['equity_per_owner'],
        base_final_value,
        base_final_loan,
        base_config.financing.num_owners,
        purchase_price=base_config.financing.purchase_price
    )
    
    # Calculate base NPV using 3% discount rate
    discount_rate = 0.03  # 3% discount rate (realistic for real estate investments)
    base_cash_flows = [y['cash_flow_per_owner'] for y in base_projection]
    base_sale_proceeds = (base_final_value - base_final_loan) / base_config.financing.num_owners
    base_npv = -base_result['equity_per_owner']
    for i, cf in enumerate(base_cash_flows):
        base_npv += cf / ((1 + discount_rate) ** (i + 1))
    base_npv += base_sale_proceeds / ((1 + discount_rate) ** len(base_cash_flows))
    
    # Generate Plotly charts HTML - use to_html() directly for each chart
    charts_html = ""
    correlation_chart_html = ""  # Extract correlation chart separately
    plotly_js_parts = []
    first_chart = True
    correlation_fig = None  # Store correlation chart figure
    
    for chart_name, fig in charts:
        # Get chart title
        chart_title = chart_name.replace('_', ' ').title()
        if hasattr(fig.layout, 'title') and fig.layout.title:
            if hasattr(fig.layout.title, 'text'):
                chart_title = fig.layout.title.text
            elif isinstance(fig.layout.title, str):
                chart_title = fig.layout.title
        
        # Extract correlation chart separately for dedicated section
        if chart_name == "correlation_charts":
            # Store the figure for later use
            correlation_fig = fig
            continue  # Skip adding to main charts_html
        
        # Use to_html() directly - it handles everything including the script
        if first_chart:
            # First chart includes Plotly JS
            chart_html = fig.to_html(include_plotlyjs="cdn", div_id=chart_name, full_html=False)
            first_chart = False
        else:
            # Subsequent charts don't include Plotly JS
            chart_html = fig.to_html(include_plotlyjs=False, div_id=chart_name, full_html=False)
        
        # Wrap in container
        charts_html += f'''
        <div class="chart-container scroll-reveal">
            <div class="chart-title">{chart_title}</div>
            {chart_html}
        </div>
        '''
    
    # Generate correlation chart HTML
    if correlation_fig is not None:
        # Use to_html() to generate the chart HTML
        # Since Plotly JS is already loaded from first chart, we don't need to include it again
        correlation_chart_html = correlation_fig.to_html(include_plotlyjs=False, div_id="correlation_charts", full_html=False)
    
    # No need for separate plotly_js since it's embedded in the HTML
    plotly_js = ""
    
    # Define sections for sidebar navigation
    sections = [
        {'id': 'executive-summary', 'title': 'Executive Summary', 'icon': 'fas fa-file-alt'},
        {'id': 'simulation-results', 'title': 'Simulation Results', 'icon': 'fas fa-chart-line'},
        {'id': 'distribution-charts', 'title': 'Distribution Charts', 'icon': 'fas fa-chart-bar'},
        {'id': 'risk-metrics', 'title': 'Risk Metrics', 'icon': 'fas fa-shield-alt'},
        {'id': 'correlation-analysis', 'title': 'Correlation Analysis', 'icon': 'fas fa-project-diagram'},
    ]
    
    # Generate sidebar and toolbar
    sidebar_html = generate_sidebar_navigation(sections)
    toolbar_html = generate_top_toolbar(
        report_title="Monte Carlo Analysis",
        back_link="index.html",
        subtitle="Engelberg Property Investment - Probabilistic Risk Analysis"
    )
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monte Carlo Analysis - Engelberg Property Investment</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        {generate_shared_layout_css()}
        
        :root {{
            --primary: #1a1a2e;
            --secondary: #0f3460;
            --success: #28a745;
            --danger: #dc3545;
            --warning: #ffc107;
            --info: #17a2b8;
            --gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --shadow-sm: 0 2px 4px rgba(0,0,0,0.1);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.15);
            --shadow-lg: 0 10px 40px rgba(0,0,0,0.2);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            background: #0a0e27;
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
            padding: 40px 60px;
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
            font-size: 2.2em;
            font-weight: 700;
            margin-bottom: 15px;
            letter-spacing: -1px;
            position: relative;
            z-index: 1;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header .subtitle {{
            font-size: 1.1em;
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
        
        .section {{
            padding: 30px 40px;
            background: white;
        }}
        
        .section:nth-child(even) {{
            background: #f8f9fa;
        }}
        
        .section h2 {{
            font-size: 1.8em;
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
        
        .chart-container {{
            background: white;
            padding: 35px;
            border-radius: 16px;
            box-shadow: var(--shadow-md);
            transition: all 0.3s;
            margin-bottom: 30px;
        }}
        
        .chart-container:hover {{
            transform: translateY(-5px);
            box-shadow: var(--shadow-lg);
        }}
        
        .chart-title {{
            font-size: 1.3em;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e8ecef;
        }}
        
        .info-box {{
            background: linear-gradient(135deg, #e8f4f8 0%, #d1ecf1 100%);
            border-left: 4px solid var(--info);
            padding: 25px;
            border-radius: 12px;
            margin: 25px 0;
        }}
        
        .methodology-box {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 12px;
            border-left: 4px solid var(--primary);
            margin: 25px 0;
        }}
        
        .methodology-box h3 {{
            color: var(--primary);
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        
        .methodology-box ul {{
            margin-left: 20px;
            line-height: 2;
        }}
        
        .methodology-box li {{
            margin-bottom: 10px;
        }}
        
        .stats-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: var(--shadow-sm);
            margin: 20px 0;
        }}
        
        .stats-table th {{
            background: var(--gradient-1);
            color: white;
            padding: 18px 20px;
            text-align: left;
            font-weight: 600;
        }}
        
        .stats-table td {{
            padding: 15px 20px;
            border-bottom: 1px solid #e8ecef;
        }}
        
        .stats-table tr:hover td {{
            background: #f8f9fa;
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
        
        .footer {{
            background: var(--primary);
            color: white;
            padding: 40px 80px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="layout-container">
        {toolbar_html}
        {sidebar_html}
        <div class="main-content">
        <!-- Executive Summary -->
        <div class="section" id="executive-summary">
            <h2><i class="fas fa-chart-line"></i> Executive Summary</h2>
            <div class="kpi-grid">
                <div class="kpi-card scroll-reveal">
                    <div class="kpi-label"><i class="fas fa-calculator"></i> Mean NPV</div>
                    <div class="kpi-value {'positive' if stats['npv']['mean'] >= 0 else 'negative'}">{format_currency(stats['npv']['mean'])}</div>
                    <div class="kpi-description">Average across all simulations</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <div class="kpi-label"><i class="fas fa-chart-bar"></i> Median NPV</div>
                    <div class="kpi-value {'positive' if stats['npv']['median'] >= 0 else 'negative'}">{format_currency(stats['npv']['median'])}</div>
                    <div class="kpi-description">50th percentile</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <div class="kpi-label"><i class="fas fa-percent"></i> Probability NPV > 0</div>
                    <div class="kpi-value">{stats['npv']['positive_prob']*100:.1f}%</div>
                    <div class="kpi-description">Chance of positive returns</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <div class="kpi-label"><i class="fas fa-trending-up"></i> Mean IRR</div>
                    <div class="kpi-value positive">{stats['irr_with_sale']['mean']:.2f}%</div>
                    <div class="kpi-description">Average IRR (with sale)</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <div class="kpi-label"><i class="fas fa-arrow-down"></i> 10th Percentile NPV</div>
                    <div class="kpi-value {'positive' if stats['npv']['p10'] >= 0 else 'negative'}">{format_currency(stats['npv']['p10'])}</div>
                    <div class="kpi-description">Worst case (90% better)</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <div class="kpi-label"><i class="fas fa-arrow-up"></i> 90th Percentile NPV</div>
                    <div class="kpi-value positive">{format_currency(stats['npv']['p90'])}</div>
                    <div class="kpi-description">Best case (10% better)</div>
                </div>
            </div>
            
            <div class="info-box">
                <h3 style="margin-bottom: 15px; color: var(--primary);">
                    <i class="fas fa-info-circle"></i> Key Insights
                </h3>
                <p style="font-size: 1.05em; line-height: 1.8;">
                    Based on {num_simulations:,} Monte Carlo simulations, the investment shows a 
                    <strong>{stats['npv']['positive_prob']*100:.1f}% probability</strong> of generating positive NPV. 
                    The mean NPV of <strong>{format_currency(stats['npv']['mean'])}</strong> indicates a favorable expected return, 
                    with a median of <strong>{format_currency(stats['npv']['median'])}</strong>. 
                    The 10th percentile (worst case) shows <strong>{format_currency(stats['npv']['p10'])}</strong>, 
                    while the 90th percentile (best case) reaches <strong>{format_currency(stats['npv']['p90'])}</strong>.
                </p>
            </div>
        </div>
        
        <!-- Methodology -->
        <div class="section" id="simulation-results">
            <h2><i class="fas fa-book"></i> Methodology</h2>
            <div class="methodology-box">
                <h3>Monte Carlo Simulation Approach</h3>
                <p style="margin-bottom: 20px; font-size: 1.05em; line-height: 1.8;">
                    This analysis uses Monte Carlo simulation to assess the uncertainty and risk associated with the Engelberg property investment. 
                    The simulation randomly varies four critical parameters across their plausible ranges to generate {num_simulations:,} different scenarios.
                </p>
                
                <h3 style="margin-top: 25px; margin-bottom: 15px;">Parameters Varied</h3>
                <p style="margin-bottom: 15px; font-size: 1.05em;">
                    This enhanced Monte Carlo simulation varies multiple parameters using advanced probability distributions:
                </p>
                <ul style="font-size: 1.05em; line-height: 2;">
                    <li><strong>Occupancy Rate:</strong> Beta distribution (α=2.0, β=1.5) bounded [30%, 75%] - captures realistic occupancy patterns</li>
                    <li><strong>Average Daily Rate:</strong> Lognormal distribution (mean=ln(300), σ=0.25) bounded [150, 450] CHF - reflects pricing uncertainty</li>
                    <li><strong>Seasonal Parameters:</strong> Independent triangular/normal distributions for each season (Winter, Summer, Off-Peak) - allows season-specific variations</li>
                    <li><strong>Interest Rate:</strong> Normal distribution (μ=2%, σ=0.5%) bounded [1.0%, 4.0%] - models interest rate uncertainty</li>
                    <li><strong>Property Management Fee:</strong> Triangular distribution (min=18%, mode=20%, max=35%) - reflects fee structure variability</li>
                    <li><strong>Owner Nights:</strong> Normal distribution (μ=5, σ=1) bounded [3, 8] nights - accounts for usage variation</li>
                    <li><strong>Utilities:</strong> Lognormal distribution (mean=ln(3000), σ=0.20) bounded [2000, 5000] CHF - models expense uncertainty</li>
                    <li><strong>Maintenance Rate:</strong> Normal distribution (μ=1%, σ=0.3%) bounded [0.5%, 2.0%] - captures maintenance variability</li>
                    <li><strong>Inflation Rate:</strong> Normal distribution (μ=2%, σ=0.5%) bounded [0.5%, 4.0%] - models economic uncertainty</li>
                    <li><strong>Property Appreciation:</strong> Normal distribution (μ=2.5%, σ=1.0%) bounded [0%, 5%] - realistic for Swiss real estate market</li>
                </ul>
                
                <h3 style="margin-top: 25px; margin-bottom: 15px;">Correlation Structure</h3>
                <p style="margin-bottom: 15px; font-size: 1.05em;">
                    Parameters are sampled with realistic correlations using a Gaussian copula approach:
                </p>
                <ul style="font-size: 1.05em; line-height: 2;">
                    <li><strong>Revenue Correlations:</strong> Occupancy and ADR are positively correlated (ρ=0.4-0.5) - higher demand enables higher pricing</li>
                    <li><strong>Seasonal Correlations:</strong> Peak seasons (Winter/Summer) show moderate positive correlation (ρ=0.2-0.3)</li>
                    <li><strong>Financial Correlations:</strong> Interest rates negatively correlate with property appreciation (ρ=-0.3) - higher rates reduce property values</li>
                    <li><strong>Expense Correlations:</strong> Nubbing costs and electricity/internet correlate with inflation (ρ=0.3-0.4) - expenses rise with inflation</li>
                </ul>
                
                <h3 style="margin-top: 25px; margin-bottom: 15px;">Simulation Process</h3>
                <ul style="font-size: 1.05em; line-height: 2;">
                    <li>For each simulation, correlated random values are drawn using Cholesky decomposition of the correlation matrix</li>
                    <li>Values are transformed to target distributions using inverse CDF (quantile function)</li>
                    <li>A complete 15-year financial projection is calculated for each scenario with variable inflation and appreciation</li>
                    <li>NPV and IRR are computed using a 3% discount rate (realistic for real estate investments)</li>
                    <li>Results are aggregated to show probability distributions, correlations, and key statistics</li>
                </ul>
                
                <h3 style="margin-top: 25px; margin-bottom: 15px;">Assumptions Held Constant</h3>
                <ul style="font-size: 1.05em; line-height: 2;">
                    <li>Property purchase price: {format_currency(base_config.financing.purchase_price)}</li>
                    <li>Loan-to-value ratio: {base_config.financing.ltv*100:.0f}%</li>
                    <li>Amortization rate: {base_config.financing.amortization_rate*100:.1f}%</li>
                    <li>Inflation rate: 2% per year</li>
                    <li>Property appreciation: 2.5% per year (base case)</li>
                    <li>Other operating expenses (insurance, utilities, maintenance reserve)</li>
                </ul>
            </div>
        </div>
        
        <!-- Statistical Summary -->
        <div class="section" id="risk-metrics">
            <h2><i class="fas fa-table"></i> Statistical Summary</h2>
            <table class="stats-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Mean</th>
                        <th>Median</th>
                        <th>Std Dev</th>
                        <th>Min</th>
                        <th>Max</th>
                        <th>10th %ile</th>
                        <th>90th %ile</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>NPV (CHF)</strong></td>
                        <td>{format_currency(stats['npv']['mean'])}</td>
                        <td>{format_currency(stats['npv']['median'])}</td>
                        <td>{format_currency(stats['npv']['std'])}</td>
                        <td>{format_currency(stats['npv']['min'])}</td>
                        <td>{format_currency(stats['npv']['max'])}</td>
                        <td>{format_currency(stats['npv']['p10'])}</td>
                        <td>{format_currency(stats['npv']['p90'])}</td>
                    </tr>
                    <tr>
                        <td><strong>IRR with Sale (%)</strong></td>
                        <td>{stats['irr_with_sale']['mean']:.2f}%</td>
                        <td>{stats['irr_with_sale']['median']:.2f}%</td>
                        <td>{stats['irr_with_sale']['std']:.2f}%</td>
                        <td>{stats['irr_with_sale']['min']:.2f}%</td>
                        <td>{stats['irr_with_sale']['max']:.2f}%</td>
                        <td>{stats['irr_with_sale']['p5']:.2f}%</td>
                        <td>{stats['irr_with_sale']['p95']:.2f}%</td>
                    </tr>
                    <tr>
                        <td><strong>Annual Cash Flow (CHF)</strong></td>
                        <td>{format_currency(stats['annual_cash_flow']['mean'])}</td>
                        <td>{format_currency(stats['annual_cash_flow']['median'])}</td>
                        <td>{format_currency(stats['annual_cash_flow']['std'])}</td>
                        <td>{format_currency(stats['annual_cash_flow']['min'])}</td>
                        <td>{format_currency(stats['annual_cash_flow']['max'])}</td>
                        <td>-</td>
                        <td>-</td>
                    </tr>
                </tbody>
            </table>
            
            <div class="info-box" style="margin-top: 30px;">
                <h3 style="margin-bottom: 15px; color: var(--primary);">
                    <i class="fas fa-chart-pie"></i> Base Case Comparison
                </h3>
                <p style="font-size: 1.05em; line-height: 1.8;">
                    <strong>Base Case NPV:</strong> {format_currency(base_npv)} | 
                    <strong>Base Case IRR:</strong> {base_irr['irr_with_sale_pct']:.2f}%<br>
                    The base case falls at the <strong>{(df['npv'] <= base_npv).sum() / len(df) * 100:.1f}th percentile</strong> of the Monte Carlo distribution, 
                    meaning {(df['npv'] <= base_npv).sum() / len(df) * 100:.1f}% of simulations show worse results than the base case.
                </p>
            </div>
        </div>
        
        <!-- Visualizations -->
        <div class="section" id="distribution-charts">
            <h2><i class="fas fa-chart-bar"></i> Results Visualization</h2>
            <p style="font-size: 1.1em; color: #555; margin-bottom: 30px;">
                The following charts show the distribution of outcomes from {num_simulations:,} Monte Carlo simulations.
                Each simulation randomly varies four key parameters (Occupancy Rate, Daily Rate, Interest Rate, Management Fee)
                to assess the range of possible investment outcomes.
            </p>
            {charts_html}
        </div>
        
        <!-- Additional Analysis: Key Sensitivity Correlations -->
        <div class="section" id="correlation-analysis">
            <h2><i class="fas fa-project-diagram"></i> Parameter Correlation Analysis</h2>
            <p style="font-size: 1.1em; color: #555; margin-bottom: 30px;">
                These charts show how different parameter combinations affect NPV and IRR outcomes.
            </p>
            <div class="chart-container scroll-reveal">
                <div class="chart-title">NPV vs Key Parameters</div>
                {correlation_chart_html if correlation_chart_html else '<div id="correlation_charts" style="min-height: 600px;"></div>'}
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer" style="margin-top: 40px; padding: 30px; background: #f8f9fa; text-align: center; border-top: 1px solid #dee2e6;">
            <p style="margin: 0; font-size: 0.9em; color: #6c757d;">Engelberg Property Investment - Monte Carlo Analysis</p>
            <p style="margin: 5px 0 0 0; font-size: 0.85em; color: #6c757d;">Generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')} | {num_simulations:,} Simulations</p>
        </div>
        </div>
    </div>
    
    {generate_shared_layout_js()}
    <script>
        // Scroll reveal animation
        (function() {{
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
            
            document.querySelectorAll('.scroll-reveal').forEach(el => {{
                observer.observe(el);
            }});
        }})();
        
        // Initialize Plotly charts
        {plotly_js}
        
    </script>
</body>
</html>
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"[+] HTML report generated: {output_path}")


def export_to_excel(df: pd.DataFrame, stats: dict, output_path: str = "monte_carlo_results.xlsx"):
    """Export Monte Carlo results to Excel."""
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Summary statistics
        summary_data = {
            'Metric': [
                'Mean NPV (CHF)',
                'Median NPV (CHF)',
                'Std Dev NPV (CHF)',
                'Min NPV (CHF)',
                'Max NPV (CHF)',
                '10th Percentile NPV (CHF)',
                '90th Percentile NPV (CHF)',
                'Probability NPV > 0 (%)',
                'Mean IRR with Sale (%)',
                'Median IRR with Sale (%)',
                'Mean Annual Cash Flow (CHF)',
                'Probability Positive Cash Flow (%)',
            ],
            'Value': [
                stats['npv']['mean'],
                stats['npv']['median'],
                stats['npv']['std'],
                stats['npv']['min'],
                stats['npv']['max'],
                stats['npv']['p10'],
                stats['npv']['p90'],
                stats['npv']['positive_prob'] * 100,
                stats['irr_with_sale']['mean'],
                stats['irr_with_sale']['median'],
                stats['annual_cash_flow']['mean'],
                stats['annual_cash_flow']['positive_prob'] * 100,
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary Statistics", index=False)
        
        # All simulation results (sample of 1000 for performance)
        sample_df = df.sample(min(1000, len(df))) if len(df) > 1000 else df
        sample_df.to_excel(writer, sheet_name="Simulation Results", index=False)
        
        # Parameter distributions
        param_stats = {
            'Parameter': ['Occupancy Rate', 'Daily Rate (CHF)', 'Interest Rate (%)', 'Management Fee Rate (%)'],
            'Min': [
                df['occupancy_rate'].min() * 100,
                df['daily_rate'].min(),
                df['interest_rate'].min() * 100,
                df['management_fee_rate'].min() * 100
            ],
            'Max': [
                df['occupancy_rate'].max() * 100,
                df['daily_rate'].max(),
                df['interest_rate'].max() * 100,
                df['management_fee_rate'].max() * 100
            ],
            'Mean': [
                df['occupancy_rate'].mean() * 100,
                df['daily_rate'].mean(),
                df['interest_rate'].mean() * 100,
                df['management_fee_rate'].mean() * 100
            ],
            'Std Dev': [
                df['occupancy_rate'].std() * 100,
                df['daily_rate'].std(),
                df['interest_rate'].std() * 100,
                df['management_fee_rate'].std() * 100
            ]
        }
        pd.DataFrame(param_stats).to_excel(writer, sheet_name="Parameter Distributions", index=False)
    
    print(f"[+] Excel file exported: {output_path}")


def main():
    """Main function to run Monte Carlo analysis."""
    print("=" * 70)
    print("Monte Carlo Analysis - Engelberg Property Investment")
    print("=" * 70)
    print()
    
    # Load base case configuration
    # IMPORTANT: This must use the SAME base case as analysis_base_case.py
    # All Monte Carlo simulations reference this single source of truth
    print("[*] Loading base case configuration...")
    base_config = create_base_case_config()
    
    # Run enhanced Monte Carlo simulation
    num_simulations = 10000
    print(f"[*] Running {num_simulations:,} enhanced Monte Carlo simulations...")
    print("     This may take several minutes...")
    print("     Features: Advanced distributions, correlations, seasonality, expense variation")
    print()
    
    df = run_monte_carlo_simulation(
        base_config, 
        num_simulations=num_simulations,
        use_correlations=True,
        use_seasonality=True,
        use_expense_variation=True
    )
    
    # Calculate statistics
    print("[*] Calculating statistics...")
    stats = calculate_statistics(df)
    
    # Create charts
    print("[*] Generating charts...")
    charts = create_monte_carlo_charts(df, stats)
    
    # Excel export disabled - user only uses HTML reports
    # print("[*] Exporting results to Excel...")
    # export_to_excel(df, stats)
    
    # Ensure output directory exists
    import os
    os.makedirs("website", exist_ok=True)
    
    # Generate HTML report
    print("[*] Generating HTML report...")
    generate_monte_carlo_html(df, stats, charts, base_config, num_simulations)
    
    print()
    print("=" * 70)
    print("[+] Monte Carlo analysis complete!")
    print("=" * 70)
    # print(f"[+] Excel file: monte_carlo_results.xlsx")  # Excel export disabled
    print(f"[+] HTML report: website/report_monte_carlo.html")
    print("=" * 70)
    print()
    print("KEY RESULTS:")
    print(f"  Mean NPV: {stats['npv']['mean']:>15,.0f} CHF")
    print(f"  Median NPV: {stats['npv']['median']:>13,.0f} CHF")
    print(f"  Probability NPV > 0: {stats['npv']['positive_prob']*100:>8.1f}%")
    print(f"  10th Percentile: {stats['npv']['p10']:>15,.0f} CHF")
    print(f"  90th Percentile: {stats['npv']['p90']:>15,.0f} CHF")
    print("=" * 70)


if __name__ == "__main__":
    main()

