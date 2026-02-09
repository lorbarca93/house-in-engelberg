# Monte Carlo Simulation Engine - Technical Reference

This document explains in detail how the Monte Carlo simulation is designed, engineered, and executed in the Engelberg Property Investment Simulation.

---

## Table of Contents

1. [Overview and Design Philosophy](#overview-and-design-philosophy)
2. [Architecture](#architecture)
3. [Distribution System](#distribution-system)
4. [Sampling Methods](#sampling-methods)
5. [Time-Varying Parameters](#time-varying-parameters)
6. [Event Generation](#event-generation)
7. [Single Simulation Execution](#single-simulation-execution)
8. [Parallel Processing](#parallel-processing)
9. [Convergence Checking](#convergence-checking)
10. [Result Aggregation](#result-aggregation)
11. [Performance Optimizations](#performance-optimizations)

---

## Overview and Design Philosophy

### What is Monte Carlo Simulation?

Monte Carlo simulation is a probabilistic method that runs many scenarios (typically 1,000-10,000) where uncertain parameters are sampled from probability distributions. Each scenario produces a result (e.g., NPV, IRR), and the collection of results forms a distribution that quantifies risk and uncertainty.

### Design Goals

1. **Accuracy**: Better coverage of parameter space than naive random sampling
2. **Efficiency**: Fast execution through parallel processing and optimized algorithms
3. **Realism**: Captures correlations, time-varying behavior, and rare events
4. **Flexibility**: Configurable features (seasonality, expense variation, correlations)

### Key Features

- **Latin Hypercube Sampling (LHS)**: Stratified sampling for better space coverage (2-3x more efficient than random)
- **Correlation Modeling**: Gaussian copula preserves realistic parameter relationships
- **Time-Varying Parameters**: AR(1) mean-reverting processes for inflation and property appreciation
- **Event Modeling**: Poisson process for maintenance, low-probability market shocks, refinancing opportunities
- **Parallel Processing**: Multi-core execution for faster results
- **Convergence Checking**: Optional adaptive stopping when statistics stabilize

---

## Architecture

### High-Level Flow

```
1. Load base configuration
   v
2. Define distributions for all stochastic parameters
   v
3. Sample all parameters at once (LHS or random, with/without correlations)
   v
4. For each simulation (parallel or sequential):
   a. Extract sampled values for this simulation
   b. Generate time-varying series (inflation, appreciation)
   c. Generate events (maintenance, market shocks, refinancing)
   d. Build modified configuration
   e. Calculate Year 1 cash flows
   f. Calculate 15-year projection (with time-varying params and events)
   g. Calculate NPV and IRR
   h. Store results
   v
5. Aggregate results (mean, median, percentiles, probabilities)
   v
6. Return DataFrame with all simulation results
```

### Core Components

| Component | Purpose | Location |
|-----------|---------|----------|
| `DistributionConfig` | Defines probability distribution for a parameter | `monte_carlo.py` |
| `get_default_distributions()` | Returns all 23 stochastic parameter distributions | `monte_carlo.py` |
| `latin_hypercube_sample()` | Generates LHS samples with optional correlations | `monte_carlo.py` |
| `sample_correlated_variables()` | Generates correlated samples using Gaussian copula | `monte_carlo.py` |
| `generate_time_series()` | Creates AR(1) mean-reverting time series | `monte_carlo.py` |
| `generate_maintenance_events()` | Generates Poisson-distributed maintenance events | `monte_carlo.py` |
| `apply_market_shock()` | Generates low-probability market disruption events | `monte_carlo.py` |
| `evaluate_refinancing()` | Evaluates refinancing opportunities | `monte_carlo.py` |
| `run_single_simulation()` | Executes one complete simulation | `monte_carlo.py` |
| `run_monte_carlo_simulation()` | Orchestrates all simulations (parallel/sequential) | `monte_carlo.py` |
| `calculate_statistics()` | Aggregates results into summary statistics | `monte_carlo.py` |

---

## Distribution System

### Distribution Types

The system supports five distribution types, each appropriate for different parameter characteristics:

#### 1. Uniform Distribution

**Use case**: When all values in a range are equally likely.

```python
DistributionConfig(
    dist_type='uniform',
    params={'min': 0.0, 'max': 1.0},
    bounds=(0.0, 1.0)  # Optional clipping
)
```

**Sampling**: `np.random.uniform(min, max, size)`

#### 2. Normal Distribution

**Use case**: Symmetric uncertainty around a mean (e.g., utilities, maintenance rate).

```python
DistributionConfig(
    dist_type='normal',
    params={'mean': 2.0, 'std': 0.3},
    bounds=(1.0, 4.0)  # Clip outliers
)
```

**Sampling**: `np.random.normal(mean, std, size)`, then clip to bounds.

#### 3. Triangular Distribution

**Use case**: Bounded uncertainty with a most-likely value (mode) between min and max (e.g., OTA fee rate, tax rate).

```python
DistributionConfig(
    dist_type='triangular',
    params={'min': 0.25, 'mode': 0.30, 'max': 0.35},
    bounds=(0.25, 0.35)
)
```

**Sampling**: Uses `scipy.stats.triang` with `c = (mode - min) / (max - min)`.

#### 4. Beta Distribution

**Use case**: Bounded parameters with flexible shape (e.g., occupancy rate, OTA booking percentage).

```python
DistributionConfig(
    dist_type='beta',
    params={'alpha': 2.5, 'beta': 1.8, 'min': 0.30, 'max': 0.75},
    bounds=(0.30, 0.75)
)
```

**Sampling**: Uses `scipy.stats.beta` scaled to `[min, max]` range.

**Shape interpretation**:
- `alpha = beta`: Symmetric (e.g., `alpha=3, beta=3` for OTA booking %)
- `alpha > beta`: Skewed left (higher values more likely)
- `alpha < beta`: Skewed right (lower values more likely)

#### 5. Lognormal Distribution

**Use case**: Positive values with multiplicative uncertainty (e.g., daily rates, utilities, maintenance costs).

```python
DistributionConfig(
    dist_type='lognormal',
    params={'mean': np.log(300), 'std': 0.25},
    bounds=(150, 450)
)
```

**Sampling**: Uses `scipy.stats.lognorm` with `scale = exp(mean)` and `s = std`.

**Note**: `mean` and `std` are the mean and standard deviation of the **underlying normal distribution** (log space), not the final distribution.

### All Stochastic Parameters

| Parameter | Distribution | Parameters | Bounds | Rationale |
|-----------|-------------|------------|--------|-----------|
| **Occupancy Rate** | Beta | alpha=2.5, beta=1.8 | 30-75% | Bounded, slightly right-skewed |
| **Daily Rate** | Lognormal | mu=ln(300), sigma=0.25 | 150-450 CHF | Multiplicative uncertainty |
| **OTA Booking %** | Beta | alpha=3, beta=3 | 30-70% | Symmetric, centered around 50% |
| **OTA Fee Rate** | Triangular | min=25%, mode=30%, max=35% | 25-35% | Most likely 30% |
| **Length of Stay** | Lognormal | mu=ln(1.7), sigma=0.15 | 1.0-3.0 nights | Positive, multiplicative |
| **Guests per Night** | Normal | mu=2.0, sigma=0.3 | 1.0-4.0 | Symmetric around 2.0 |
| **Cleaning Cost** | Normal | mu=100, sigma=15 | 60-130 CHF | Symmetric around 100 CHF |
| **Tax Rate** | Triangular | min=25%, mode=30%, max=35% | 25-35% | Most likely 30% |
| **Discount Rate** | Normal | mu=3%, sigma=0.5% | 2-5% | Symmetric around 3% |
| **Inflation** | Normal | mu=1.5%, sigma=0.75% | 0-3% | Time-varying (AR(1)) |
| **Property Appreciation** | Normal | mu=3.5%, sigma=2.75% | -2% to 9% | Time-varying (AR(1)) |
| **Maintenance Rate** | Normal | mu=1%, sigma=0.3% | 0.5-2.0% | Symmetric around 1% |
| **Utilities** | Lognormal | mu=ln(2000), sigma=0.20 | 1,200-3,500 CHF | Multiplicative uncertainty |
| **Winter Occupancy** | Triangular | min=60%, mode=75%, max=90% | 60-90% | Peak season |
| **Winter Rate** | Normal | mu=250, sigma=40 | 180-350 CHF | Peak pricing |
| **Summer Occupancy** | Triangular | min=50%, mode=65%, max=80% | 50-80% | High season |
| **Summer Rate** | Normal | mu=200, sigma=30 | 150-280 CHF | High pricing |
| **Off-Peak Occupancy** | Triangular | min=35%, mode=50%, max=65% | 35-65% | Shoulder season |
| **Off-Peak Rate** | Normal | mu=150, sigma=25 | 100-220 CHF | Lower pricing |

### Fixed Parameters (Not Sampled)

These parameters use the **base case value** for all simulations:

- **Interest Rate**: `base_config.financing.interest_rate`
- **Management Fee Rate**: `base_config.expenses.property_management_fee_rate`
- **Owner Nights**: `base_config.rental.owner_nights_per_person`
- **Nubbing Costs**: `base_config.expenses.nubbing_costs_annual`

**Rationale**: These are contractual or policy parameters that don't vary randomly in the short term.

---

## Sampling Methods

### Latin Hypercube Sampling (LHS)

**Purpose**: Better coverage of parameter space than random sampling.

**How it works**:

1. **Stratification**: For each parameter, divide the range into `N` equal intervals (where `N = num_simulations`).
2. **One sample per interval**: Randomly select one value from each interval.
3. **Random permutation**: Shuffle the samples to break correlations.
4. **Inverse transform**: Convert uniform samples to target distributions using inverse CDF (PPF).

**Benefits**:
- **Better coverage**: Every interval is sampled exactly once
- **Lower variance**: More accurate estimates with fewer simulations
- **Efficiency**: Typically 2-3x more efficient than random sampling

**Example**: For 1,000 simulations and occupancy rate [0.30, 0.75]:
- Divide into 1,000 intervals: [0.30, 0.30045), [0.30045, 0.3009), ..., [0.74955, 0.75]
- Sample one value from each interval
- Shuffle to randomize order
- Transform to Beta distribution using inverse CDF

**Implementation**: `latin_hypercube_sample()` in `monte_carlo.py`

### Correlation Modeling (Gaussian Copula)

**Purpose**: Preserve realistic relationships between parameters (e.g., high occupancy correlates with higher rates).

**How it works**:

1. **Correlation matrix**: Define pairwise correlations (e.g., occupancy vs. daily rate = 0.4).
2. **Cholesky decomposition**: Factor correlation matrix: `C = L x L^T`.
3. **Correlated normals**: Generate independent standard normals `Z`, then `X = Z x L^T` (correlated).
4. **Transform to uniform**: `U = Phi(X)` where `Phi` is standard normal CDF.
5. **Inverse transform**: Use `U` with inverse CDF of each target distribution.

**Key insight**: The Gaussian copula preserves correlation structure while allowing different marginal distributions.

**Example correlations**:
- Occupancy vs. Daily Rate: +0.4 (high occupancy -> higher rates)
- Occupancy vs. OTA Booking %: -0.3 (high occupancy -> more direct bookings)
- Daily Rate vs. Length of Stay: -0.2 (higher rates -> shorter stays)
- Inflation vs. Property Appreciation: +0.2 (economic growth -> property growth)

**Implementation**: `sample_correlated_variables()` and integrated into `latin_hypercube_sample()` when `correlation_matrix` is provided.

### Independent Sampling

If `use_correlations=False`, each parameter is sampled independently from its distribution. This is simpler but less realistic.

---

## Time-Varying Parameters

### AR(1) Mean-Reverting Process

**Purpose**: Model parameters that change over time but revert toward a long-term mean (e.g., inflation, property appreciation).

**Formula**:

```
value[t] = mean + rho x (value[t-1] - mean) + innovation[t]
```

Where:
- `mean`: Long-term mean (base value)
- `rho` (rho): Mean reversion coefficient (0-1, higher = faster reversion)
- `innovation[t]`: Random shock ~ N(0, sigma^2)

**Properties**:
- **Mean-reverting**: Deviations from mean decay over time
- **Persistence**: Higher `rho` -> slower reversion (more persistence)
- **Volatility**: Higher `sigma` -> more year-to-year variation

### Inflation Series

```python
inflation_series = generate_time_series(
    base_value=base_inflation,      # Sampled from distribution (mean 1.5%)
    mean_reversion=0.8,             # Moderate persistence
    innovation_std=0.005,            # 0.5% annual volatility
    num_years=15,
    bounds=(0.0, 0.03)               # Clip to 0-3%
)
```

**Interpretation**: Inflation tends to revert to 1.5% but can deviate year-to-year with 0.5% volatility.

### Property Appreciation Series

```python
appreciation_series = generate_time_series(
    base_value=base_appreciation,   # Sampled from distribution (mean 3.5%)
    mean_reversion=0.75,             # Slightly less persistent than inflation
    innovation_std=0.015,            # 1.5% annual volatility (higher than inflation)
    num_years=15,
    bounds=(-0.02, 0.09)             # Clip to -2% to 9%
)
```

**Interpretation**: Property appreciation reverts to 3.5% but has higher volatility and can be negative (market downturns).

### Usage in Projection

The 15-year projection uses these series year-by-year:

- **Year 1**: Uses `inflation_series[0]` and `appreciation_series[0]` (base values)
- **Year 2**: Uses `inflation_series[1]` and `appreciation_series[1]` (first AR(1) step)
- **Year N**: Uses `inflation_series[N-1]` and `appreciation_series[N-1]`

This creates realistic year-to-year variation rather than constant rates.

---

## Event Generation

### Major Maintenance Events (Poisson Process)

**Purpose**: Model rare, high-cost maintenance events (roof replacement, heating system, major renovations).

**Process**:
- **Poisson distribution**: Probability of event in year `t` = `lambda` (default `lambda = 0.15` = ~1 event per 6-7 years)
- **Cost distribution**: Lognormal (mean 15,000 CHF, sigma=0.5 on log scale), bounded 5,000-50,000 CHF

**Implementation**:

```python
for year in range(1, 16):
    if np.random.poisson(lambda_rate=0.15) > 0:
        cost = np.random.lognormal(mean=np.log(15000), sigma=0.5)
        cost = np.clip(cost, 5000, 50000)
        events.append((year, cost))
```

**Applied in projection**: Added as `major_maintenance_cost` in affected years.

### Market Shocks (Low-Probability Events)

**Purpose**: Model rare disruptions (pandemic, economic downturn, regulatory changes).

**Process**:
- **Probability**: 3% per year (configurable)
- **Impact** (uniform distributions):
  - Occupancy: -30% to -50%
  - Daily Rate: -20% to -30%
  - Property Value: -10% to -20%
- **Recovery**: 1-3 years (random) with gradual return to normal

**Implementation**:

```python
if np.random.random() < 0.03:  # 3% probability
    occupancy_shock = np.random.uniform(-0.50, -0.30)
    rate_shock = np.random.uniform(-0.30, -0.20)
    value_shock = np.random.uniform(-0.20, -0.10)
    recovery_years = np.random.randint(1, 4)
```

**Applied in projection**: Multipliers applied to revenue and property value, with gradual recovery over `recovery_years`.

### Refinancing Opportunities

**Purpose**: Model refinancing when market rates drop below current rate.

**Process**:
- **Evaluation**: Every 3 years (years 3, 6, 9, 12, 15)
- **Trigger**: Market rate > 0.5% below current rate
- **Probability**: 70% chance of refinancing if trigger met
- **Cost**: 1.5% of loan balance
- **Benefit**: Lower interest rate for remaining years

**Implementation**:

```python
if year >= 3 and year % 3 == 0:
    market_rate = base_rate + np.random.normal(0, 0.005)
    if (current_rate - market_rate) > 0.005 and np.random.random() < 0.7:
        refinancing_cost = loan_balance * 0.015
        # Update interest rate for remaining years
```

**Applied in projection**: Updates `current_interest_rate` and adds `refinancing_cost` to expenses.

---

## Single Simulation Execution

### Step-by-Step Process

For each simulation `i` (out of `N` total):

#### 1. Extract Sampled Values

```python
occupancy = samples_dict['occupancy_rate'][i]
daily_rate = samples_dict['daily_rate'][i]
ota_booking_percentage = samples_dict['ota_booking_percentage'][i]
# ... etc for all stochastic parameters
```

**Fixed parameters** (use base config):
```python
interest_rate = base_config.financing.interest_rate
management_fee = base_config.expenses.property_management_fee_rate
owner_nights = base_config.rental.owner_nights_per_person
nubbing_costs_annual = base_config.expenses.nubbing_costs_annual
```

#### 2. Generate Time-Varying Series

```python
base_inflation = samples_dict['inflation_rate'][i]
base_appreciation = samples_dict['property_appreciation'][i]

inflation_series = generate_time_series(
    base_value=base_inflation,
    mean_reversion=0.8,
    innovation_std=0.005,
    num_years=15,
    bounds=(0.0, 0.03)
)

appreciation_series = generate_time_series(
    base_value=base_appreciation,
    mean_reversion=0.75,
    innovation_std=0.015,
    num_years=15,
    bounds=(-0.02, 0.09)
)
```

#### 3. Generate Events

```python
# Maintenance events (Poisson process)
maintenance_events = generate_maintenance_events(num_years=15, lambda_rate=0.15)
# Returns: [(year, cost), ...]

# Market shocks (low probability)
market_shocks = {}
for year in range(1, 16):
    shock = apply_market_shock(year, base_occupancy, base_rate, base_property_value)
    if shock['shock_occurred']:
        market_shocks[year] = shock

# Refinancing opportunities
refinancing_events = {}
for year in [3, 6, 9, 12, 15]:
    refi = evaluate_refinancing(...)
    if refi:
        refinancing_events[year] = refi
```

#### 4. Build Modified Configuration

```python
config = apply_enhanced_sensitivity(
    base_config,
    occupancy=occupancy,
    daily_rate=daily_rate,
    interest_rate=interest_rate,  # Fixed
    management_fee=management_fee,  # Fixed
    seasonal_occupancy=seasonal_occupancy,  # If use_seasonality
    seasonal_rates=seasonal_rates,  # If use_seasonality
    owner_nights=owner_nights,  # Fixed
    nubbing_costs_annual=nubbing_costs_annual,  # Fixed
    electricity_internet_annual=electricity_internet_annual,  # If use_expense_variation
    maintenance_rate=maintenance_rate  # If use_expense_variation
)
```

#### 5. Calculate Year 1 Cash Flows

```python
annual_result = compute_annual_cash_flows(
    config,
    ota_booking_percentage=ota_booking_percentage,
    ota_fee_rate=ota_fee_rate,
    average_length_of_stay=average_length_of_stay,
    avg_guests_per_night=avg_guests_per_night,
    cleaning_cost_per_stay=cleaning_cost_per_stay,
    marginal_tax_rate=marginal_tax_rate
)
```

#### 6. Calculate 15-Year Projection

```python
projection = compute_15_year_projection(
    config,
    start_year=2026,
    inflation_rate=base_inflation,  # Base for backward compatibility
    property_appreciation_rate=base_appreciation,  # Base for backward compatibility
    ota_booking_percentage=ota_booking_percentage,
    ota_fee_rate=ota_fee_rate,
    average_length_of_stay=average_length_of_stay,
    avg_guests_per_night=avg_guests_per_night,
    cleaning_cost_per_stay=cleaning_cost_per_stay,
    marginal_tax_rate=marginal_tax_rate,
    inflation_series=inflation_series.tolist(),  # Time-varying
    appreciation_series=appreciation_series.tolist(),  # Time-varying
    maintenance_events=maintenance_events,
    market_shocks=market_shocks,
    refinancing_events=refinancing_events
)
```

#### 7. Calculate NPV and IRR

```python
# IRR
irr_results = calculate_irrs_from_projection(
    projection,
    total_initial_investment_per_owner,
    final_property_value,
    final_loan_balance,
    num_owners,
    purchase_price
)

# NPV (using sampled discount_rate)
cash_flows = [year['cash_flow_per_owner'] for year in projection]
sale_proceeds_per_owner = (final_property_value - final_loan_balance) / num_owners

npv = -total_initial_investment_per_owner
for j, cf in enumerate(cash_flows):
    npv += cf / ((1 + discount_rate) ** (j + 1))
npv += sale_proceeds_per_owner / ((1 + discount_rate) ** len(cash_flows))
```

#### 8. Store Results

```python
result_row = {
    'simulation': i + 1,
    'occupancy_rate': occupancy,
    'daily_rate': daily_rate,
    'npv': npv,
    'irr_with_sale': irr_results['equity_irr_with_sale_pct'],
    'irr_without_sale': irr_results['equity_irr_without_sale_pct'],
    # ... all sampled parameters and metrics
}
```

---

## Parallel Processing

### Architecture

**Outer parallelization**: Process multiple simulations simultaneously across CPU cores.

**Inner parallelization**: Disabled when `run_single_simulation()` is called from a worker process (to avoid nested multiprocessing issues).

### Implementation

```python
# Determine number of workers
num_workers = max(1, cpu_count() - 1)  # Leave one core free

# Prepare arguments for each simulation
simulation_args = [
    (i, samples, base_config, use_seasonality, use_expense_variation)
    for i in range(num_simulations)
]

# Run in parallel pool
with Pool(processes=num_workers) as pool:
    results = []
    for result in pool.imap(run_single_simulation, simulation_args, chunksize=chunksize):
        results.append(result)
        # Progress tracking and convergence checking
```

### Performance

- **Speedup**: Typically 4-8x faster on multi-core systems
- **Scalability**: Linear scaling up to number of cores
- **Overhead**: Minimal for `num_simulations > 100`

### Fallback

If parallel processing fails (e.g., on Windows with certain configurations), the system automatically falls back to sequential processing.

---

## Convergence Checking

### Purpose

Stop early when statistics stabilize, reducing total runtime while maintaining accuracy.

### Method

**Tracked statistics**:
- NPV mean
- NPV standard deviation
- NPV P10 (10th percentile)
- NPV P90 (90th percentile)

**Convergence criterion**:
- Check every `convergence_check_interval` simulations (default: 5% of total or 500, whichever is larger)
- Calculate coefficient of variation (CV) of last 3 mean values: `CV = std(means) / abs(mean(means))`
- If `CV < 0.01` (1% threshold), statistics have stabilized

**Note**: Currently, convergence checking **monitors** but doesn't stop early (continues to `num_simulations`). This can be extended to stop early if desired.

### Implementation

```python
if check_convergence and completed >= 1000 and completed % convergence_check_interval == 0:
    df_temp = pd.DataFrame(results)
    convergence_stats['npv_mean'].append(df_temp['npv'].mean())
    convergence_stats['npv_std'].append(df_temp['npv'].std())
    # ... other stats

    if len(convergence_stats['npv_mean']) >= 3:
        recent_means = convergence_stats['npv_mean'][-3:]
        cv = np.std(recent_means) / (abs(np.mean(recent_means)) + 1e-6)
        if cv < 0.01:
            print(f"Convergence detected at {completed:,} simulations (CV={cv:.4f})")
```

---

## Result Aggregation

### Statistics Calculated

For each output metric (NPV, IRR, cash flows, etc.):

| Statistic | Description |
|-----------|-------------|
| **mean** | Average across all simulations |
| **median** | 50th percentile (robust to outliers) |
| **std** | Standard deviation (measure of uncertainty) |
| **min/max** | Extreme values |
| **p5, p10, p25, p75, p90, p95** | Percentiles (distribution shape) |
| **positive_prob** | Probability of positive value (for NPV) |

### Implementation

```python
def calc_stats(series: pd.Series) -> dict:
    return {
        'mean': series.mean(),
        'median': series.median(),
        'std': series.std(),
        'p10': series.quantile(0.10),
        'p90': series.quantile(0.90),
        'positive_prob': (series > 0).sum() / len(series)
    }

stats = {
    'npv': calc_stats(df['npv']),
    'irr_with_sale': calc_stats(df['irr_with_sale']),
    # ... etc
}
```

### Output Format

Results are returned as a **pandas DataFrame** with:
- One row per simulation
- Columns for all sampled parameters
- Columns for all calculated metrics (NPV, IRR, cash flows, etc.)

This allows:
- Statistical analysis (percentiles, correlations)
- Visualization (histograms, scatter plots)
- Export to JSON for dashboard

---

## Performance Optimizations

### 1. Vectorized Sampling

**Before**: Sample each parameter separately in a loop
**After**: Sample all parameters at once using vectorized operations

**Benefit**: 10-20x faster parameter sampling

### 2. Latin Hypercube Sampling

**Benefit**: 2-3x more efficient than random sampling (achieves same accuracy with fewer simulations)

**Trade-off**: Slightly more complex implementation, but worth it for large simulations

### 3. Parallel Processing

**Benefit**: 4-8x speedup on multi-core systems

**Implementation**: Uses Python `multiprocessing.Pool` with `imap` for progress tracking

### 4. Optimized Chunking

**Chunk size**: `max(1, num_simulations // (num_workers * 4))`

**Benefit**: Balances overhead vs. load balancing

### 5. Convergence Checking

**Benefit**: Can stop early when statistics stabilize (currently monitors only, but can be extended to stop)

**Trade-off**: Small overhead for tracking statistics

---

## Summary

The Monte Carlo engine is designed for **accuracy**, **efficiency**, and **realism**:

- **Accurate**: LHS sampling and correlations ensure good parameter space coverage
- **Efficient**: Parallel processing and vectorized operations provide 4-8x speedup
- **Realistic**: Time-varying parameters (AR(1)), events (maintenance, shocks, refinancing), and correlations capture real-world dynamics

**Key innovations**:
1. **LHS with correlations**: Better coverage than random sampling while preserving realistic relationships
2. **AR(1) processes**: Time-varying inflation and appreciation with mean reversion
3. **Event modeling**: Rare but impactful events (maintenance, market shocks, refinancing)
4. **Parallel architecture**: Efficient multi-core execution

For implementation details, see `engelberg/monte_carlo.py` (2,430+ lines).

---

**Created**: February 2, 2026
**Purpose**: Technical reference for Monte Carlo design and implementation
**Status**: Reference Documentation
