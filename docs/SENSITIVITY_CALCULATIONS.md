# Sensitivity Calculations

This document explains how deterministic model sensitivity and Monte Carlo sensitivity are computed.

## 1) Analysis Types

### Deterministic sensitivity (`*_sensitivity*.json`)

- Varies one parameter at a time (low/base/high).
- Recomputes deterministic outputs.
- Produces impact-ranked tornado payloads.

Supported deterministic views:

- Equity IRR sensitivity (`{case}_sensitivity.json`)
- Cash-on-cash sensitivity (`{case}_sensitivity_coc.json`)
- Monthly NCF sensitivity (`{case}_sensitivity_ncf.json`)

### Monte Carlo sensitivity (`*_monte_carlo_sensitivity.json`)

- Selects one parameter.
- Sweeps 10 values across configured range.
- Runs full Monte Carlo at each value.
- Tracks `NPV > 0` probability curve and impact range.

## 2) Deterministic Sensitivity Mechanics

Implemented primarily in `engelberg/model_sensitivity.py` with ranges from `engelberg/model_sensitivity_ranges.py`.

### 2.1 Low/high generation

For each parameter with base value `x`:

- `low = x * low_factor`
- `high = x * high_factor`

Then clamp if configured:

- `low = max(low, clamp_min)` and/or `min(low, clamp_max)`
- `high = max(high, clamp_min)` and/or `min(high, clamp_max)`

### 2.2 Core parameter set

Config-driven parameters (16):

1. Maintenance reserve rate
2. Property management fee
3. Purchase price
4. Occupancy rate
5. Average daily rate
6. Interest rate
7. SARON share
8. Fixed 10Y share
9. SARON margin
10. Loan-to-value
11. Amortization rate
12. Cleaning cost per stay
13. Average length of stay
14. Insurance rate
15. Winter occupancy
16. Ramp-up months

Projection/sale special parameters (3):

1. Property appreciation rate
2. Inflation rate
3. Selling costs rate

Notes:

- When tranche-specific parameters are not active in a given generated dataset, outputs may contain a reduced subset.
- Engine support includes the full set above.

### 2.3 Metrics and formulas

#### Equity IRR

- Uses `compute_15_year_projection()` and `calculate_irrs_from_projection()`.
- Includes sale proceeds net of costs and sale taxes.
- Impact = `abs(high_irr - low_irr)`.

#### After-tax cash flow per owner (monthly)

- Uses Year 1 after-tax cash flow / 12.
- If Year 1 has downtime (ramp-up or renovation), calculation uses projection Year 1.

#### Cash-on-cash (Year 1)

- `cash_on_cash = (year1_cash_flow_per_owner / initial_equity_per_owner) * 100`
- Year 1 metric by definition.

#### Monthly NCF (Year 1)

- `monthly_ncf = year1_cash_flow_per_owner / 12`
- Year 1 metric by definition.

### 2.4 Horizon behavior in deterministic outputs

- Equity IRR sensitivity computes per horizon and writes `by_horizon`.
- CoC and Monthly NCF are Year 1 metrics.
  - Their `by_horizon` blocks duplicate Year 1 results for UI contract consistency.
  - Dashboard hides horizon selector for those views.

### 2.5 Projection-only effects

- Appreciation, inflation, and selling-cost parameters affect long-horizon return metrics.
- They do not change Year 1 cash-flow metrics materially.

## 3) Monte Carlo Sensitivity Mechanics

Implemented in `engelberg/mc_sensitivity.py` using parameter configs from `engelberg/mc_sensitivity_ranges.py`.

### 3.1 Parameter set (current config)

1. Amortization rate
2. Interest rate
3. Purchase price
4. Occupancy rate
5. Price per night
6. Ramp-up period

Each parameter is evaluated over:

- `10` evenly spaced values between min and max (after factor scaling and clamps)

### 3.2 Workflow

For each parameter value:

1. Apply one-parameter override to base config.
2. Run Monte Carlo simulation (`run_monte_carlo_simulation`).
3. Compute statistics (`calculate_statistics`).
4. Extract `npv.positive_prob`.

Then for each parameter:

- `min_probability`
- `max_probability`
- `impact = max_probability - min_probability`

### 3.3 Convergence and performance

- Uses parallel processing across parameter-value tasks where possible.
- Includes convergence-aware helper pathway for probability stabilization checks.
- Uses Latin Hypercube Sampling for simulation efficiency.

## 4) Output Structures

### Deterministic IRR sensitivity output

Main keys:

- `base_irr`
- `base_atcf` (when included)
- `sensitivities`
- `by_horizon`
- `analysis_type`

Each `sensitivities[]` item includes:

- `parameter`
- `base_value`
- `low.value`, `low.irr`
- `high.value`, `high.irr`
- `impact`
- optional ATCF low/high blocks

### CoC/NCF sensitivity outputs

- `base_coc` or `base_ncf`
- `sensitivities`
- `by_horizon` (duplicated Year 1 payloads)

### MC sensitivity output

Main keys:

- `case_name`
- `base_npv_probability`
- `sensitivities`
- `analysis_type` (`mc_sensitivity`)
- `metric` (`NPV > 0 Probability`)

Each `sensitivities[]` item includes:

- `parameter`
- `base_value`
- `values[]` (`value`, `npv_probability`)
- `min_probability`
- `max_probability`
- `impact`

## 5) Interpretation Guidance

- Use deterministic sensitivity to rank directional drivers quickly.
- Use MC sensitivity to evaluate risk-adjusted robustness of each driver.
- For financing decisions, combine:
  - deterministic IRR sensitivity
  - loan-structure sensitivity view
  - DSCR stress outputs

---

Last updated: February 10, 2026

