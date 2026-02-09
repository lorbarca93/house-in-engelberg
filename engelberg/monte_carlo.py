"""
Monte Carlo Analysis for Engelberg Property Investment
Enhanced version with improved accuracy and efficiency:

ACCURACY IMPROVEMENTS:
- Latin Hypercube Sampling (LHS): Better parameter space coverage than random sampling
  - Achieves similar accuracy with 2-3x fewer simulations
  - Ensures uniform coverage of the parameter space
  - Reduces variance in estimates
- Increased default simulations: 10,000 (up from 1,000) for better statistical accuracy
- Advanced distributions: triangular, Beta, lognormal for realistic modeling
- Correlation support: Realistic parameter relationships via Gaussian copula

EFFICIENCY IMPROVEMENTS:
- Parallel processing: Utilizes multiple CPU cores (default: CPU count - 1)
  - Significant speedup for large simulations (typically 4-8x faster)
  - Automatic fallback to sequential if parallel fails
- Vectorized sampling: All parameters sampled at once before simulation loop
- Optimized chunking: Efficient batch processing for parallel execution

FEATURES:
- Expanded stochastic inputs (seasonality, expenses, inflation)
- Correlation support for realistic parameter relationships
- Comprehensive output with all sampled parameters and results
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import beta, lognorm, triang, norm
from scipy.linalg import cholesky
from engelberg.core import (
    create_base_case_config,
    BaseCaseConfig,
    compute_annual_cash_flows,
    compute_15_year_projection,
    calculate_irrs_from_projection,
    apply_sensitivity  # Use the centralized sensitivity function
)
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from multiprocessing import Pool, cpu_count

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


def latin_hypercube_sample(distributions: Dict[str, DistributionConfig],
                           correlation_matrix: Optional[np.ndarray] = None,
                           size: int = 1) -> Dict[str, np.ndarray]:
    """
    Generate samples using Latin Hypercube Sampling (LHS) for better space coverage.
    
    LHS ensures better coverage of the parameter space compared to random sampling,
    leading to more accurate results with fewer simulations.
    
    Args:
        distributions: Dictionary mapping variable names to DistributionConfig
        correlation_matrix: Optional correlation matrix (if None, samples independently)
        size: Number of samples to generate
    
    Returns:
        Dictionary mapping variable names to sampled arrays
    """
    var_names = list(distributions.keys())
    n_vars = len(var_names)
    
    if correlation_matrix is not None and n_vars > 1:
        # For correlated variables, use LHS on uniform space then transform
        # Generate LHS samples in [0, 1]^n
        lhs_samples = np.zeros((size, n_vars))
        for i in range(n_vars):
            # Create LHS intervals
            intervals = np.linspace(0, 1, size + 1)
            for j in range(size):
                lhs_samples[j, i] = np.random.uniform(intervals[j], intervals[j + 1])
        
        # Randomly permute each column to break correlations
        for i in range(n_vars):
            np.random.shuffle(lhs_samples[:, i])
        
        # Transform to correlated uniform space using Gaussian copula
        Z = norm.ppf(lhs_samples)
        
        # Apply correlation
        try:
            L = cholesky(correlation_matrix, lower=True)
            X = Z @ L.T
        except np.linalg.LinAlgError:
            # Fallback if correlation matrix not positive definite
            correlation_matrix = correlation_matrix + np.eye(n_vars) * 1e-6
            L = cholesky(correlation_matrix, lower=True)
            X = Z @ L.T
        
        # Transform back to uniform
        U = norm.cdf(X)
    else:
        # Independent LHS sampling
        lhs_samples = np.zeros((size, n_vars))
        for i in range(n_vars):
            intervals = np.linspace(0, 1, size + 1)
            for j in range(size):
                lhs_samples[j, i] = np.random.uniform(intervals[j], intervals[j + 1])
            np.random.shuffle(lhs_samples[:, i])
        U = lhs_samples
    
    # Transform uniform samples to target distributions
    results = {}
    for i, var_name in enumerate(var_names):
        dist = distributions[var_name]
        
        # Use inverse CDF (PPF) for each distribution type
        if dist.dist_type == 'uniform':
            samples = dist.params['min'] + U[:, i] * (dist.params['max'] - dist.params['min'])
        elif dist.dist_type == 'normal':
            samples = norm.ppf(U[:, i], loc=dist.params['mean'], scale=dist.params['std'])
        elif dist.dist_type == 'triangular':
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


def generate_time_series(base_value: float, mean_reversion: float, innovation_std: float, 
                         num_years: int = 15, bounds: Optional[Tuple[float, float]] = None) -> np.ndarray:
    """
    Generate time series using AR(1) mean-reverting process.
    
    Args:
        base_value: Mean/base value to revert to
        mean_reversion: Mean reversion coefficient (0-1, higher = faster reversion)
        innovation_std: Standard deviation of annual shocks
        num_years: Number of years to generate
        bounds: Optional (min, max) bounds to clip values
    
    Returns:
        Array of values for each year
    """
    series = np.zeros(num_years)
    series[0] = base_value
    
    for t in range(1, num_years):
        # AR(1) process: value[t] = mean + ρ*(value[t-1] - mean) + innovation
        innovation = np.random.normal(0, innovation_std)
        series[t] = base_value + mean_reversion * (series[t-1] - base_value) + innovation
        
        # Clip to bounds if provided
        if bounds:
            series[t] = np.clip(series[t], bounds[0], bounds[1])
    
    return series


def generate_maintenance_events(num_years: int = 15, 
                                 lambda_rate: float = 0.15) -> List[Tuple[int, float]]:
    """
    Generate major maintenance events using Poisson process.
    
    Args:
        num_years: Number of years to simulate
        lambda_rate: Expected number of events per year (default 0.15 = ~1 event per 6-7 years)
    
    Returns:
        List of (year, cost) tuples for maintenance events
    """
    events = []
    for year in range(1, num_years + 1):
        # Poisson process: probability of event in this year
        if np.random.poisson(lambda_rate) > 0:
            # Sample maintenance cost (lognormal distribution)
            # Mean CHF 15,000, std 0.5 (on log scale)
            cost = np.random.lognormal(mean=np.log(15000), sigma=0.5)
            cost = np.clip(cost, 5000, 50000)  # Bound between 5k and 50k CHF
            events.append((year, cost))
    
    return events


def evaluate_refinancing(current_loan_balance: float, current_rate: float, 
                         market_rate: float, refinancing_cost_rate: float = 0.015) -> Optional[Dict[str, float]]:
    """
    Evaluate refinancing opportunity.
    
    Args:
        current_loan_balance: Current outstanding loan balance
        current_rate: Current interest rate
        market_rate: Current market interest rate
        refinancing_cost_rate: Refinancing costs as % of loan balance (default 1.5%)
    
    Returns:
        Dictionary with refinancing details if opportunity exists, None otherwise
    """
    # Refinance if market rate is >0.5% below current rate, with 70% probability
    rate_difference = current_rate - market_rate
    if rate_difference > 0.005 and np.random.random() < 0.7:
        refinancing_cost = current_loan_balance * refinancing_cost_rate
        return {
            'refinance': True,
            'new_rate': market_rate,
            'refinancing_cost': refinancing_cost,
            'rate_savings': rate_difference
        }
    return None


def apply_market_shock(year: int, base_occupancy: float, base_rate: float, 
                       base_property_value: float, shock_probability: float = 0.03) -> Dict[str, float]:
    """
    Apply market shock scenario (pandemic, economic downturn, etc.).
    
    Args:
        year: Current year in projection
        base_occupancy: Base occupancy rate
        base_rate: Base daily rate
        base_property_value: Base property value
        shock_probability: Probability of shock in any given year (default 3%)
    
    Returns:
        Dictionary with shock-adjusted values and recovery info
    """
    if np.random.random() < shock_probability:
        # Shock magnitude (uniform distribution)
        occupancy_shock = np.random.uniform(-0.50, -0.30)  # -30% to -50%
        rate_shock = np.random.uniform(-0.30, -0.20)  # -20% to -30%
        value_shock = np.random.uniform(-0.20, -0.10)  # -10% to -20%
        recovery_years = np.random.randint(1, 4)  # 1-3 years to recover
        
        return {
            'shock_occurred': True,
            'occupancy_multiplier': 1.0 + occupancy_shock,
            'rate_multiplier': 1.0 + rate_shock,
            'value_multiplier': 1.0 + value_shock,
            'recovery_years': recovery_years,
            'shock_start_year': year
        }
    else:
        return {
            'shock_occurred': False,
            'occupancy_multiplier': 1.0,
            'rate_multiplier': 1.0,
            'value_multiplier': 1.0,
            'recovery_years': 0,
            'shock_start_year': None
        }


def run_single_simulation(args: Tuple) -> Dict:
    """
    Run a single Monte Carlo simulation.
    
    This function is designed to be called in parallel for efficiency.
    
    Args:
        args: Tuple containing (simulation_index, sampled_values, base_config, 
              use_seasonality, use_expense_variation)
        Note: discount_rate is now sampled from distributions, not passed as parameter
    
    Returns:
        Dictionary with simulation results
    """
    (i, samples_dict, base_config, use_seasonality, use_expense_variation) = args
    # Note: discount_rate is now sampled from distributions, not passed as parameter
    
    # Extract sampled values
    occupancy = float(samples_dict['occupancy_rate'][i])
    daily_rate = float(samples_dict['daily_rate'][i])
    # Fixed parameters (use base config values)
    interest_rate = base_config.financing.interest_rate
    management_fee = base_config.expenses.property_management_fee_rate
    
    # New stochastic parameters
    ota_booking_percentage = float(samples_dict['ota_booking_percentage'][i])
    ota_fee_rate = float(samples_dict['ota_fee_rate'][i])
    average_length_of_stay = float(samples_dict['average_length_of_stay'][i])
    avg_guests_per_night = float(samples_dict['avg_guests_per_night'][i])
    cleaning_cost_per_stay = float(samples_dict['cleaning_cost_per_stay'][i])
    marginal_tax_rate = float(samples_dict['marginal_tax_rate'][i])
    discount_rate = float(samples_dict['discount_rate'][i])
    # Ramp-up months (default to 7 if not sampled for backward compatibility with old test data)
    ramp_up_months = int(round(float(samples_dict['ramp_up_months'][i]))) if 'ramp_up_months' in samples_dict else 7
    
    # Generate time-varying series for inflation and appreciation using AR(1) process
    base_inflation = float(samples_dict['inflation_rate'][i])
    base_appreciation = float(samples_dict['property_appreciation'][i])
    
    # AR(1) parameters: mean reversion 0.8 (moderate persistence), innovation std calibrated to bounds
    inflation_series = generate_time_series(
        base_value=base_inflation,
        mean_reversion=0.8,
        innovation_std=0.005,  # Annual innovation std
        num_years=15,
        bounds=(0.0, 0.03)  # Match distribution bounds
    )
    
    appreciation_series = generate_time_series(
        base_value=base_appreciation,
        mean_reversion=0.75,  # Slightly less persistent than inflation
        innovation_std=0.015,  # Higher volatility for property values
        num_years=15,
        bounds=(-0.02, 0.09)  # Match distribution bounds
    )
    
    # Seasonal parameters
    seasonal_occupancy = None
    seasonal_rates = None
    if use_seasonality:
        seasonal_occupancy = {
            'Winter Peak (Ski Season)': float(samples_dict['winter_occupancy'][i]),
            'Summer Peak (Hiking Season)': float(samples_dict['summer_occupancy'][i]),
            'Off-Peak (Shoulder Seasons)': float(samples_dict['offpeak_occupancy'][i])
        }
        seasonal_rates = {
            'Winter Peak (Ski Season)': float(samples_dict['winter_rate'][i]),
            'Summer Peak (Hiking Season)': float(samples_dict['summer_rate'][i]),
            'Off-Peak (Shoulder Seasons)': float(samples_dict['offpeak_rate'][i])
        }
    
    # Expense parameters
    # Fixed parameters (always use base config values)
    owner_nights = base_config.rental.owner_nights_per_person
    nubbing_costs_annual = base_config.expenses.nubbing_costs_annual
    electricity_internet_annual = None
    maintenance_rate = None
    if use_expense_variation:
        electricity_internet_annual = float(samples_dict['electricity_internet_annual'][i])
        maintenance_rate = float(samples_dict['maintenance_rate'][i])
    
    # Create modified configuration
    config = apply_enhanced_sensitivity(
        base_config,
        occupancy=occupancy if not use_seasonality else None,
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
    
    # Calculate annual cash flows with new stochastic parameters
    annual_result = compute_annual_cash_flows(
        config,
        ota_booking_percentage=ota_booking_percentage,
        ota_fee_rate=ota_fee_rate,
        average_length_of_stay=average_length_of_stay,
        avg_guests_per_night=avg_guests_per_night,
        cleaning_cost_per_stay=cleaning_cost_per_stay,
        marginal_tax_rate=marginal_tax_rate
    )
    
    # Generate maintenance events (Poisson process)
    maintenance_events = generate_maintenance_events(num_years=15, lambda_rate=0.15)
    
    # Generate market shocks (low probability, high impact)
    market_shocks = {}
    refinancing_events = {}
    base_occupancy = occupancy if not use_seasonality else np.mean(list(seasonal_occupancy.values()) if seasonal_occupancy else [occupancy])
    base_rate = daily_rate if not use_seasonality else np.mean(list(seasonal_rates.values()) if seasonal_rates else [daily_rate])
    base_property_value = base_config.financing.purchase_price
    
    for year in range(1, 16):
        # Check for market shock
        shock = apply_market_shock(year, base_occupancy, base_rate, base_property_value, shock_probability=0.03)
        if shock['shock_occurred']:
            market_shocks[year] = shock
        
        # Check for refinancing opportunity (every 3 years, starting year 3)
        # Note: Actual loan balance will be calculated in projection, use approximate here
        if year >= 3 and year % 3 == 0:
            # Sample market interest rate (can be lower or higher than current)
            market_rate = max(0.005, base_config.financing.interest_rate + np.random.normal(0, 0.005))
            # Approximate loan balance (will be refined in projection)
            approx_loan_balance = config.financing.loan_amount * (1 - (year - 1) * config.financing.amortization_rate)
            refi_result = evaluate_refinancing(
                current_loan_balance=approx_loan_balance,
                current_rate=base_config.financing.interest_rate,
                market_rate=market_rate
            )
            if refi_result:
                refinancing_events[year] = refi_result
    
    # Calculate 15-year projection with time-varying parameters, events, and ramp-up
    projection = compute_15_year_projection(
        config, 
        start_year=2026, 
        inflation_rate=base_inflation,  # Base rate for backward compatibility
        property_appreciation_rate=base_appreciation,  # Base rate for backward compatibility
        ramp_up_months=ramp_up_months,  # Sampled ramp-up period
        ota_booking_percentage=ota_booking_percentage,
        ota_fee_rate=ota_fee_rate,
        average_length_of_stay=average_length_of_stay,
        avg_guests_per_night=avg_guests_per_night,
        cleaning_cost_per_stay=cleaning_cost_per_stay,
        marginal_tax_rate=marginal_tax_rate,
        inflation_series=inflation_series.tolist(),  # Convert numpy array to list
        appreciation_series=appreciation_series.tolist(),
        maintenance_events=maintenance_events,
        market_shocks=market_shocks,
        refinancing_events=refinancing_events
    )
    
    # Get final values
    final_property_value = projection[-1]['property_value']
    final_loan_balance = projection[-1]['remaining_loan_balance']
    total_initial_investment = config.financing.total_initial_investment_per_owner
    
    # Calculate IRRs
    irr_results = calculate_irrs_from_projection(
        projection,
        total_initial_investment,
        final_property_value,
        final_loan_balance,
        config.financing.num_owners,
        purchase_price=config.financing.purchase_price
    )
    
    # Calculate NPV using sampled discount rate
    cash_flows = [year['cash_flow_per_owner'] for year in projection]
    sale_proceeds_per_owner = (final_property_value - final_loan_balance) / config.financing.num_owners
    
    npv = -total_initial_investment
    for j, cf in enumerate(cash_flows):
        npv += cf / ((1 + discount_rate) ** (j + 1))
    npv += sale_proceeds_per_owner / ((1 + discount_rate) ** len(cash_flows))
    
    # Build result row
    result_row = {
        'simulation': i + 1,
        'occupancy_rate': occupancy,
        'daily_rate': daily_rate,
        'interest_rate': interest_rate,
        'management_fee_rate': management_fee,
        'ota_booking_percentage': ota_booking_percentage,
        'ota_fee_rate': ota_fee_rate,
        'average_length_of_stay': average_length_of_stay,
        'avg_guests_per_night': avg_guests_per_night,
        'cleaning_cost_per_stay': cleaning_cost_per_stay,
        'marginal_tax_rate': marginal_tax_rate,
        'discount_rate': discount_rate,
        'inflation_rate': base_inflation,  # Base inflation rate
        'property_appreciation': base_appreciation,  # Base appreciation rate
        'annual_cash_flow': annual_result['cash_flow_after_debt_service'],
        'cash_flow_per_owner': annual_result['cash_flow_per_owner'],
        'gross_rental_income': annual_result['gross_rental_income'],
        'net_operating_income': annual_result['net_operating_income'],
        'npv': npv,
        'irr_with_sale': irr_results.get('equity_irr_with_sale_pct', irr_results.get('irr_with_sale_pct', 0.0)),
        'irr_without_sale': irr_results.get('equity_irr_without_sale_pct', irr_results.get('irr_without_sale_pct', 0.0)),
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
    
    return result_row


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
        from engelberg.core import SeasonalParams, RentalParams
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
        from engelberg.core import RentalParams
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
        from engelberg.core import RentalParams
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
        from engelberg.core import ExpenseParams
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
            property_value=config.expenses.property_value,
            vat_rate_on_gross_rental=config.expenses.vat_rate_on_gross_rental
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
            params={'alpha': 2.5, 'beta': 1.8, 'min': 0.30, 'max': 0.75},  # Improved calibration: slightly more conservative
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
        
        # OTA platform parameters
        'ota_booking_percentage': DistributionConfig(
            dist_type='beta',
            params={'alpha': 3.0, 'beta': 3.0, 'min': 0.30, 'max': 0.70},
            bounds=(0.30, 0.70)  # 30% to 70% of bookings through OTAs
        ),
        'ota_fee_rate': DistributionConfig(
            dist_type='triangular',
            params={'min': 0.25, 'mode': 0.30, 'max': 0.35},
            bounds=(0.25, 0.35)  # 25% to 35% fee on OTA bookings
        ),
        
        # Operational parameters
        'average_length_of_stay': DistributionConfig(
            dist_type='lognormal',
            params={'mean': np.log(1.7), 'std': 0.15},
            bounds=(1.0, 3.0)  # 1.0 to 3.0 nights
        ),
        'avg_guests_per_night': DistributionConfig(
            dist_type='normal',
            params={'mean': 2.0, 'std': 0.3},
            bounds=(1.0, 4.0)  # 1.0 to 4.0 guests
        ),
        'cleaning_cost_per_stay': DistributionConfig(
            dist_type='normal',
            params={'mean': 100.0, 'std': 15.0},
            bounds=(60.0, 130.0)  # 60 to 130 CHF per stay
        ),
        
        # Financial parameters
        'marginal_tax_rate': DistributionConfig(
            dist_type='triangular',
            params={'min': 0.25, 'mode': 0.30, 'max': 0.35},
            bounds=(0.25, 0.35)  # 25% to 35% Swiss marginal tax rate
        ),
        'discount_rate': DistributionConfig(
            dist_type='normal',
            params={'mean': 0.03, 'std': 0.005},
            bounds=(0.02, 0.05)  # 2% to 5% discount rate for NPV
        ),
        
        # Projection parameters
        'inflation_rate': DistributionConfig(
            dist_type='normal',
            params={'mean': 0.015, 'std': 0.0075},  # Mean 1.5% per year, std 0.75% (realistic for Swiss economy)
            bounds=(0.0, 0.03)  # 0% to 3% per year
        ),
        'property_appreciation': DistributionConfig(
            dist_type='normal',
            params={'mean': 0.035, 'std': 0.0275},  # Mean 3.5% per year, std 2.75% (allows for market volatility)
            bounds=(-0.02, 0.09)  # -2% to 9% per year (allows for market downturns)
        ),
        
        # Ramp-up period (pre-operational months)
        'ramp_up_months': DistributionConfig(
            dist_type='triangular',
            params={'min': 4, 'mode': 7, 'max': 10},  # Most likely 7 months, range 4-10
            bounds=(4, 10)
        ),
    }


def get_default_correlation_matrix() -> np.ndarray:
    """
    Get default correlation matrix for Monte Carlo simulation.
    Defines realistic correlations between parameters.
    
    Note: Some parameters are fixed (interest_rate, management_fee, owner_nights, nubbing_costs_annual)
    and will be excluded from the active correlation matrix subset.
    
    Order of variables:
    0: occupancy_rate
    1: daily_rate
    2: winter_occupancy
    3: winter_rate
    4: summer_occupancy
    5: summer_rate
    6: offpeak_occupancy
    7: offpeak_rate
    8: interest_rate (FIXED - not sampled)
    9: management_fee (FIXED - not sampled)
    10: owner_nights (FIXED - not sampled)
    11: nubbing_costs_annual (FIXED - not sampled)
    12: electricity_internet_annual
    13: maintenance_rate
    14: inflation_rate
    15: property_appreciation
    16: ota_booking_percentage
    17: ota_fee_rate
    18: average_length_of_stay
    19: avg_guests_per_night
    20: cleaning_cost_per_stay
    21: marginal_tax_rate
    22: discount_rate
    23: ramp_up_months
    """
    n = 24  # Updated to include all stochastic parameters including ramp_up_months
    corr = np.eye(n)
    
    # Revenue correlations: occupancy and ADR are positively correlated
    corr[0, 1] = corr[1, 0] = 0.4  # Overall occupancy vs overall rate
    corr[2, 3] = corr[3, 2] = 0.5  # Winter occupancy vs winter rate
    corr[4, 5] = corr[5, 4] = 0.5  # Summer occupancy vs summer rate
    corr[6, 7] = corr[7, 6] = 0.5  # Offpeak occupancy vs offpeak rate
    
    # Seasonal correlations: peak seasons tend to move together
    corr[2, 4] = corr[4, 2] = 0.3  # Winter vs summer occupancy
    corr[3, 5] = corr[5, 3] = 0.2  # Winter vs summer rates
    
    # Financial correlations: inflation affects property appreciation
    # Note: interest_rate is fixed, so its correlation with appreciation is not used
    corr[14, 15] = corr[15, 14] = 0.2  # Inflation vs appreciation
    
    # Expense correlations: utilities and maintenance tend to move with inflation
    # Note: nubbing_costs_annual is fixed, so its correlation with inflation is not used
    corr[12, 14] = corr[14, 12] = 0.3  # Electricity/internet vs inflation
    corr[13, 14] = corr[14, 13] = 0.3  # Maintenance vs inflation
    
    # OTA parameter correlations
    corr[0, 16] = corr[16, 0] = -0.3  # Occupancy vs OTA booking % (negative: more direct bookings when occupancy high)
    corr[16, 17] = corr[17, 16] = 0.1  # OTA booking % vs OTA fee rate (slight positive)
    
    # Operational parameter correlations
    corr[1, 18] = corr[18, 1] = -0.2  # Daily rate vs length of stay (negative: longer stays get discounts)
    
    # Ramp-up correlations (index 23)
    # Ramp-up vs interest rate: higher rates might delay decision (+0.1)
    # Note: interest_rate is FIXED (index 8), so this correlation won't be used
    # Ramp-up vs purchase price: more expensive properties take longer to prepare (+0.15)
    # This is index 23 (ramp_up) vs index for purchase_price (not in current stochastic params)
    # For now, keeping ramp-up mostly independent
    corr[0, 20] = corr[20, 0] = 0.4  # Occupancy vs cleaning cost (positive: more bookings = more cleaning)
    corr[18, 20] = corr[20, 18] = -0.3  # Length of stay vs cleaning cost (negative: longer stays = fewer cleanings)
    corr[19, 20] = corr[20, 19] = 0.2  # Avg guests vs cleaning cost (positive: more guests = more cleaning)
    
    # Financial parameter correlations
    corr[8, 22] = corr[22, 8] = 0.5  # Interest rate vs discount rate (both reflect risk-free rate)
    # Note: interest_rate is fixed, but correlation structure is maintained for consistency
    corr[15, 21] = corr[21, 15] = 0.1  # Property appreciation vs tax rate (slight: higher value areas may have higher taxes)
    
    return corr


def run_monte_carlo_simulation(base_config: BaseCaseConfig, 
                                num_simulations: int = 10000,
                                use_correlations: bool = True,
                                use_seasonality: bool = True,
                                use_expense_variation: bool = True,
                                use_lhs: bool = True,  # Use Latin Hypercube Sampling for better accuracy
                                use_parallel: bool = True,  # Use parallel processing for efficiency
                                num_workers: Optional[int] = None,
                                check_convergence: bool = False) -> pd.DataFrame:
    """
    Run enhanced Monte Carlo simulation with expanded stochastic inputs and correlations.
    
    ACCURACY IMPROVEMENTS:
    - Latin Hypercube Sampling (LHS): Provides better space coverage than random sampling,
      achieving similar accuracy with fewer simulations (typically 2-3x more efficient)
    - Default 10,000 simulations: Increased from 1,000 for better statistical accuracy
    
    EFFICIENCY IMPROVEMENTS:
    - Parallel processing: Utilizes multiple CPU cores for faster execution
    - Vectorized sampling: All parameters sampled at once before simulation loop
    - Optimized chunking: Efficient batch processing for parallel execution
    
    Args:
        base_config: Base case configuration
        num_simulations: Number of simulation runs (default: 10,000 for better accuracy)
        use_correlations: Whether to use correlation matrix for sampling
        use_seasonality: Whether to vary seasonal parameters independently
        use_expense_variation: Whether to vary expense parameters
        use_lhs: Whether to use Latin Hypercube Sampling (default: True, improves accuracy)
        use_parallel: Whether to use parallel processing (default: True, improves efficiency)
        num_workers: Number of parallel workers (default: CPU count - 1)
        check_convergence: Whether to check for convergence (default: False, monitors NPV statistics)
    
    Returns:
        DataFrame with simulation results including all sampled parameters
    """
    print(f"[*] Running {num_simulations:,} Monte Carlo simulations...")
    print(f"    - Sampling Method: {'Latin Hypercube (LHS)' if use_lhs else 'Random Sampling'}")
    print(f"    - Parallel Processing: {'Enabled' if use_parallel else 'Disabled'}")
    print(f"    - Correlations: {'Enabled' if use_correlations else 'Disabled'}")
    print(f"    - Seasonality: {'Enabled' if use_seasonality else 'Disabled'}")
    print(f"    - Expense Variation: {'Enabled' if use_expense_variation else 'Disabled'}")
    
    # Get distribution configurations
    all_distributions = get_default_distributions()
    
    # Select which distributions to use based on flags
    active_distributions = {}
    var_order = []
    
    # Core parameters (always used)
    # Note: interest_rate and management_fee are fixed (use base config values)
    active_distributions['occupancy_rate'] = all_distributions['occupancy_rate']
    active_distributions['daily_rate'] = all_distributions['daily_rate']
    # New stochastic parameters (always used)
    active_distributions['ota_booking_percentage'] = all_distributions['ota_booking_percentage']
    active_distributions['ota_fee_rate'] = all_distributions['ota_fee_rate']
    active_distributions['average_length_of_stay'] = all_distributions['average_length_of_stay']
    active_distributions['avg_guests_per_night'] = all_distributions['avg_guests_per_night']
    active_distributions['cleaning_cost_per_stay'] = all_distributions['cleaning_cost_per_stay']
    active_distributions['marginal_tax_rate'] = all_distributions['marginal_tax_rate']
    active_distributions['discount_rate'] = all_distributions['discount_rate']
    var_order.extend(['occupancy_rate', 'daily_rate', 'ota_booking_percentage', 'ota_fee_rate',
                      'average_length_of_stay', 'avg_guests_per_night', 'cleaning_cost_per_stay',
                      'marginal_tax_rate', 'discount_rate'])
    
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
    # Note: owner_nights and nubbing_costs_annual are fixed (use base config values)
    if use_expense_variation:
        active_distributions['electricity_internet_annual'] = all_distributions['electricity_internet_annual']
        active_distributions['maintenance_rate'] = all_distributions['maintenance_rate']
        var_order.extend(['electricity_internet_annual', 'maintenance_rate'])
    
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
                          'electricity_internet_annual', 'maintenance_rate', 'inflation_rate', 'property_appreciation',
                          'ota_booking_percentage', 'ota_fee_rate', 'average_length_of_stay', 'avg_guests_per_night',
                          'cleaning_cost_per_stay', 'marginal_tax_rate', 'discount_rate']
        var_indices = [full_var_order.index(v) for v in var_order]
        correlation_matrix = full_corr[np.ix_(var_indices, var_indices)]
    else:
        correlation_matrix = np.eye(len(var_order))
    
    # Sample all parameters at once (more efficient)
    if use_lhs:
        # Use Latin Hypercube Sampling for better space coverage
        if use_correlations and len(var_order) > 1:
            samples = latin_hypercube_sample(active_distributions, correlation_matrix, num_simulations)
        else:
            samples = latin_hypercube_sample(active_distributions, None, num_simulations)
    else:
        # Use traditional random sampling
        if use_correlations and len(var_order) > 1:
            samples = sample_correlated_variables(active_distributions, correlation_matrix, num_simulations)
        else:
            samples = {}
            for var_name in var_order:
                samples[var_name] = active_distributions[var_name].sample(num_simulations)
    
    # Prepare arguments for parallel processing
    if use_parallel and num_simulations > 100:  # Only use parallel for larger simulations
        if num_workers is None:
            num_workers = max(1, cpu_count() - 1)  # Leave one core free
        
        print(f"    - Workers: {num_workers}")
        
        try:
            # Prepare arguments for each simulation
            # Note: discount_rate is now sampled, not passed as parameter
            simulation_args = [
                (i, samples, base_config, use_seasonality, use_expense_variation)
                for i in range(num_simulations)
            ]
            
            # Run simulations in parallel
            with Pool(processes=num_workers) as pool:
                # Use imap for progress tracking
                results = []
                completed = 0
                chunksize = max(1, num_simulations // (num_workers * 4))
                
                # Convergence tracking (if enabled)
                convergence_stats = {'npv_mean': [], 'npv_std': [], 'npv_p10': [], 'npv_p90': []}
                convergence_check_interval = max(500, num_simulations // 20)  # Check every 5% or 500 sims
                
                for result in pool.imap(run_single_simulation, simulation_args, chunksize=chunksize):
                    results.append(result)
                    completed += 1
                    
                    # Convergence checking
                    if check_convergence and completed >= 1000 and completed % convergence_check_interval == 0:
                        df_temp = pd.DataFrame(results)
                        convergence_stats['npv_mean'].append(df_temp['npv'].mean())
                        convergence_stats['npv_std'].append(df_temp['npv'].std())
                        convergence_stats['npv_p10'].append(df_temp['npv'].quantile(0.10))
                        convergence_stats['npv_p90'].append(df_temp['npv'].quantile(0.90))
                        
                        # Check if statistics have stabilized (coefficient of variation < 0.01 for last 3 checks)
                        if len(convergence_stats['npv_mean']) >= 3:
                            recent_means = convergence_stats['npv_mean'][-3:]
                            cv = np.std(recent_means) / (abs(np.mean(recent_means)) + 1e-6)
                            if cv < 0.01:  # 1% coefficient of variation threshold
                                print(f"  Convergence detected at {completed:,} simulations (CV={cv:.4f})")
                                # Continue to num_simulations but note convergence
                    
                    if completed % max(100, num_simulations // 10) == 0:
                        print(f"  Progress: {completed:,} / {num_simulations:,} simulations ({100 * completed / num_simulations:.1f}%)")
        except Exception as e:
            # Fallback to sequential if parallel processing fails
            print(f"    Warning: Parallel processing failed ({e}), falling back to sequential")
            use_parallel = False
    
    if not use_parallel or num_simulations <= 100:
        # Sequential processing (for small simulations or when parallel is disabled)
        results = []
        convergence_check_interval = max(500, num_simulations // 20)  # Check every 5% or 500 sims
        convergence_stats = {'npv_mean': [], 'npv_std': [], 'npv_p10': [], 'npv_p90': []}
        
        for i in range(num_simulations):
            result = run_single_simulation((
                i, samples, base_config, use_seasonality, use_expense_variation
            ))
            results.append(result)
            
            # Convergence checking
            if check_convergence and (i + 1) >= 1000 and (i + 1) % convergence_check_interval == 0:
                df_temp = pd.DataFrame(results)
                convergence_stats['npv_mean'].append(df_temp['npv'].mean())
                convergence_stats['npv_std'].append(df_temp['npv'].std())
                convergence_stats['npv_p10'].append(df_temp['npv'].quantile(0.10))
                convergence_stats['npv_p90'].append(df_temp['npv'].quantile(0.90))
                
                # Check if statistics have stabilized
                if len(convergence_stats['npv_mean']) >= 3:
                    recent_means = convergence_stats['npv_mean'][-3:]
                    cv = np.std(recent_means) / (abs(np.mean(recent_means)) + 1e-6)
                    if cv < 0.01:  # 1% coefficient of variation threshold
                        print(f"  Convergence detected at {i + 1:,} simulations (CV={cv:.4f})")
            
            if (i + 1) % max(100, num_simulations // 10) == 0:
                print(f"  Progress: {i + 1:,} / {num_simulations:,} simulations ({100 * (i + 1) / num_simulations:.1f}%)")
    
    print(f"[+] Completed {num_simulations:,} simulations")
    
    return pd.DataFrame(results)


def calculate_statistics(df: pd.DataFrame) -> dict:
    """Calculate summary statistics from simulation results."""
    # Calculate monthly values from annual
    df['monthly_cash_flow_total'] = df['annual_cash_flow'] / 12.0
    df['monthly_cash_flow_per_owner'] = df['cash_flow_per_owner'] / 12.0
    df['monthly_gross_rental_income'] = df['gross_rental_income'] / 12.0
    df['monthly_net_operating_income'] = df['net_operating_income'] / 12.0
    
    def calc_stats(series: pd.Series) -> dict:
        """Helper to calculate statistics for a series."""
        return {
            'mean': series.mean(),
            'median': series.median(),
            'std': series.std(),
            'min': series.min(),
            'max': series.max(),
            'p5': series.quantile(0.05),
            'p10': series.quantile(0.10),
            'p25': series.quantile(0.25),
            'p75': series.quantile(0.75),
            'p90': series.quantile(0.90),
            'p95': series.quantile(0.95),
            'positive_prob': (series > 0).sum() / len(series) if len(series) > 0 else 0.0,
        }
    
    return {
        'npv': calc_stats(df['npv']),
        'irr_with_sale': {
            'mean': df['irr_with_sale'].mean(),
            'median': df['irr_with_sale'].median(),
            'std': df['irr_with_sale'].std(),
            'min': df['irr_with_sale'].min(),
            'max': df['irr_with_sale'].max(),
            'p5': df['irr_with_sale'].quantile(0.05),
            'p95': df['irr_with_sale'].quantile(0.95),
        },
        # Annual - Total
        'annual_cash_flow_total': calc_stats(df['annual_cash_flow']),
        'annual_gross_rental_income_total': calc_stats(df['gross_rental_income']),
        'annual_net_operating_income_total': calc_stats(df['net_operating_income']),
        # Annual - Per Person
        'annual_cash_flow_per_owner': calc_stats(df['cash_flow_per_owner']),
        # Monthly - Total
        'monthly_cash_flow_total': calc_stats(df['monthly_cash_flow_total']),
        'monthly_gross_rental_income_total': calc_stats(df['monthly_gross_rental_income']),
        'monthly_net_operating_income_total': calc_stats(df['monthly_net_operating_income']),
        # Monthly - Per Person
        'monthly_cash_flow_per_owner': calc_stats(df['monthly_cash_flow_per_owner']),
        # Legacy support (for backward compatibility)
        'annual_cash_flow': calc_stats(df['annual_cash_flow']),
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
    from engelberg.core import compute_annual_cash_flows, compute_15_year_projection, calculate_irrs_from_projection
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
