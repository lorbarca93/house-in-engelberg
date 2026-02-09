# Sensitivity Calculations - Technical Reference

This document describes in detail how the **Model Sensitivity** (deterministic) and **Monte Carlo Sensitivity** (probabilistic) analyses are calculated in the Engelberg Property Investment Simulation.

---

## Table of Contents

1. [Overview](#overview)
2. [Model Sensitivity (Deterministic)](#model-sensitivity-deterministic)
3. [Parameter Ranges and Scaling](#parameter-ranges-and-scaling)
4. [Metric Calculations](#metric-calculations)
5. [Special Parameters (Projection-Only)](#special-parameters-projection-only)
6. [Monte Carlo Sensitivity (Probabilistic)](#mc-sensitivity-probabilistic)
7. [Configuration Modification](#configuration-modification)

---

## Overview

| Analysis                             | Type          | What it varies                    | What it measures                           | Time Horizon Support                  |
| ------------------------------------ | ------------- | --------------------------------- | ------------------------------------------ | ------------------------------------- |
| **Model Sensitivity - Equity IRR**   | Deterministic | 16 parameters (low / base / high) | Equity IRR and Monthly After-Tax Cash Flow | Horizon-aware (5-40 years) |
| **Model Sensitivity - Cash-on-Cash** | Deterministic | Same 16 parameters                | Year 1 cash flow / initial equity          | Year 1 only (horizon hidden in UI) |
| **Model Sensitivity - Monthly NCF**  | Deterministic | Same 16 parameters                | Annual cash flow per owner / 12            | Year 1 only (horizon hidden in UI) |
| **Monte Carlo Sensitivity**          | Probabilistic | 6 parameters x 10 values each     | NPV > 0 probability at each value          | Fixed 15-year model (horizon hidden in UI) |

Model Sensitivity uses **one parameter change at a time**: for each parameter we compute a **low** and **high** value (from the base), build a modified config, and recalculate the chosen metric. All other inputs stay at base case.

Monte Carlo Sensitivity **fixes one parameter at a chosen value** and runs a full **Monte Carlo** simulation (many random scenarios) to estimate the probability that NPV > 0; this is repeated for 10 values per parameter.

**NEW**: Ramp-up period (pre-operational months) is now included as a sensitivity parameter, allowing analysis of how different preparation timelines affect returns.

---

## Model Sensitivity (Deterministic)

### Flow

1. Load **base configuration** from the case assumptions file.
2. Compute **base metric(s)** (e.g. Equity IRR, and optionally Monthly After-Tax Cash Flow).
3. For each of the **16 parameters** (12 from config + 3 special):
   - Compute **low** and **high** values from the base value (see [Parameter Ranges and Scaling](#parameter-ranges-and-scaling)).
   - Build **low config** and **high config** by changing only that parameter (via `apply_sensitivity`).
   - Recompute the metric(s) for low config and high config.
   - Store base/low/high values and resulting metric(s).
4. **Sort** parameters by **impact** (e.g. |high_metric - low_metric|) for tornado charts.
5. Export results (e.g. to `{case}_sensitivity.json`, `{case}_sensitivity_coc.json`, `{case}_sensitivity_ncf.json`).

### Parameters Tested (13 config + 3 special = 16 total)

**Config parameters** (modified via `apply_sensitivity` on `BaseCaseConfig` or passed to projection functions):

| Key                  | Display Name             | Low Factor | High Factor | Clamp Min | Clamp Max | Notes                 |
| -------------------- | ------------------------ | ---------- | ----------- | --------- | --------- | --------------------- |
| `maintenance_rate`   | Maintenance Reserve Rate | 0.0        | 2.0         | 0         | -         | 0% to 2x base         |
| `management_fee`     | Property Management Fee  | 0.75       | 1.25        | 0         | 1         | 75%-125% of base      |
| `purchase_price`     | Purchase Price           | 0.90       | 1.10        | -         | -         | +/-10%                  |
| `occupancy`          | Occupancy Rate           | 0.90       | 1.10        | 0         | 1         | +/-10%                  |
| `average_daily_rate` | Average Daily Rate       | 0.80       | 1.20        | 0         | -         | +/-20%                  |
| `interest_rate`      | Interest Rate            | ~0.23      | ~1.77       | 0         | -         | ~+/-1% around 1.3% base |
| `ltv`                | Loan-to-Value (LTV)      | 0.90       | 1.10        | 0         | 0.95      | +/-10%, cap 95%         |
| `amortization`       | Amortization Rate        | 0.0        | 2.0         | 0         | -         | 0% to 2x base         |
| `cleaning_cost`      | Cleaning Cost per Stay   | 0.70       | 1.30        | 0         | -         | +/-30%                  |
| `length_of_stay`     | Average Length of Stay   | 0.70       | 1.30        | 0.1       | -         | +/-30%                  |
| `insurance_rate`     | Insurance Rate           | 0.75       | 1.25        | 0         | -         | +/-25%                  |
| `winter_occupancy`   | Winter Season Occupancy  | 0.85       | 1.15        | 0         | 0.95      | +/-15%, cap 95%         |
| `ramp_up_months`     | Ramp-Up Period           | 0.43       | 1.71        | 0         | 18        | 3-12 months           |

**Special parameters** (projection-only; not part of `BaseCaseConfig`; see [Special Parameters](#special-parameters-projection-only)):

- **Property Appreciation Rate** - factors (0.6, 1.4) on base rate -> affects IRR only.
- **Inflation Rate** - factors (0.50, 1.50) on base rate -> affects IRR only.
- **Selling Costs Rate** - factors (~0.74, ~1.26) on base rate, clamp min 5% -> affects IRR only.

---

## Parameter Ranges and Scaling

### Low/High From Base (Config Parameters)

For each config parameter, **low** and **high** are derived from the **case-specific base value**:

- `low_value = base_value x low_factor`
- `high_value = base_value x high_factor`

Then optional **clamps** are applied:

- If `clamp_min` is set: `low = max(low, clamp_min)`, `high = max(high, clamp_min)`.
- If `clamp_max` is set: `low = min(low, clamp_max)`, `high = min(high, clamp_max)`.

So every case (e.g. Migros, 3 Owners) uses **its own** base; the same **factors** and **clamps** are applied for consistency. Implemented in `scale_low_high()` in `engelberg/model_sensitivity.py`; factors and clamps come from `MODEL_SENSITIVITY_PARAMETER_CONFIG` in `engelberg/model_sensitivity_ranges.py`.

### Special Factors (Appreciation, Inflation, Selling Costs)

- **Property appreciation**: `low = base x 0.6`, `high = base x 1.4` (clamp 0-100%).
- **Inflation**: `low = base x 0.50`, `high = base x 1.50` (clamp min 0).
- **Selling costs**: `low = base x 0.743589`, `high = base x 1.256410` (clamp min 5%).

Defined in `MODEL_SENSITIVITY_SPECIAL_FACTORS` in `engelberg/model_sensitivity_ranges.py`.

---

## Metric Calculations

For each scenario (base, low, high), the metric is computed as follows. Only **one** parameter differs from base at a time.

### 1. Equity IRR (with sale)

- **Input**: Config (with optional overrides for appreciation/inflation/selling costs where applicable).
- **Steps**:
  1. `compute_annual_cash_flows(config)` -> Year 1 results.
  2. `compute_15_year_projection(config, start_year, inflation_rate, property_appreciation_rate)` -> 15-year projection.
  3. `calculate_irrs_from_projection(projection, initial_investment_per_owner, final_property_value, final_loan_balance, num_owners, purchase_price, selling_costs_rate, discount_rate)`.
- **Output**: `equity_irr_with_sale_pct` (annualised return on equity over 15 years including sale).

Used for **Model Sensitivity - Equity IRR**.

### 2. After-Tax Cash Flow per Person (monthly)

- **Input**: Same config as above (appreciation does not affect Year 1).
- **Steps**:
  1. `compute_annual_cash_flows(config)`.
  2. Take `after_tax_cash_flow_per_owner` (annual).
  3. Divide by 12.
- **Output**: Monthly after-tax cash flow per owner (CHF).

Reported alongside Equity IRR in the **Equity IRR** sensitivity (dual tornado).

### 3. Cash-on-Cash (Year 1)

- **Formula**: `(Year 1 cash flow per owner / equity per owner) x 100`.
- **Steps**:
  1. `compute_annual_cash_flows(config)`.
  2. `cash_flow_per_owner` (pre-tax) and `equity_per_owner` from results.
  3. CoC = `(cash_flow_per_owner / equity_per_owner) * 100`.
- **Output**: Percentage (e.g. -1.24).

Used for **Model Sensitivity - Cash-on-Cash**. Property appreciation and selling costs do not affect Year 1, so for those parameters the CoC result is unchanged (base = low = high).

**Time Horizon Note**: Cash-on-Cash is a **Year 1 metric only**. The `by_horizon` data in the JSON is duplicated across all horizons, and the dashboard UI hides the time horizon selector when viewing this analysis to avoid confusion.

### 4. Monthly NCF (Year 1)

- **Formula**: `Year 1 cash flow per owner / 12`.
- **Steps**:
  1. `compute_annual_cash_flows(config)`.
  2. `monthly_ncf = cash_flow_per_owner / 12`.
- **Output**: CHF per owner per month.

Used for **Model Sensitivity - Monthly NCF**. Again, appreciation and selling costs do not affect Year 1, so they show no impact on this metric.

**Time Horizon Note**: Monthly NCF is a **Year 1 metric only**. The `by_horizon` data in the JSON is duplicated across all horizons, and the dashboard UI hides the time horizon selector when viewing this analysis to avoid confusion.

### Impact and Sorting

- **Impact** for a parameter:
  `impact = |high_metric - low_metric|`
  (for Equity IRR and ATCF, impact can be defined per metric; for single-metric analyses it's the same idea).
- Parameters are **sorted by impact** (descending) for tornado charts and "top 5" summaries.

---

## Special Parameters (Projection-Only)

These three are not part of the main config; they only affect the **15-year projection** and thus **Equity IRR** (and optionally Project IRR), not Year 1 cash flow or CoC/Monthly NCF.

### Property Appreciation Rate

- Base comes from `get_projection_defaults(json_path)['property_appreciation_rate']`.
- Low/High: `scale_low_high(base, 0.6, 1.4, clamp_min=0, clamp_max=1)`.
- For **Equity IRR**: three full projections and IRR calculations with `property_appreciation_rate = base`, `low`, `high`; inflation and selling costs at base.
- For **Cash-on-Cash** and **Monthly NCF**: base = low = high (no impact), so the bar shows no change.

### Inflation Rate

- Base from `get_projection_defaults(json_path)['inflation_rate']`.
- Low/High: `scale_low_high(base, 0.50, 1.50, clamp_min=0)`.
- For **Equity IRR**: three projections with `inflation_rate = base`, `low`, `high`; appreciation and selling costs at base; then IRR from each projection.
- For **CoC / Monthly NCF**: no impact (base = low = high).

### Selling Costs Rate

- Base from `get_projection_defaults(json_path)['selling_costs_rate']`.
- Low/High: `scale_low_high(base, 0.743589, 1.256410, clamp_min=0.05)`.
- For **Equity IRR**: three projections (same inflation/appreciation); `calculate_irrs_from_projection` is called with `selling_costs_rate = base`, `low`, `high` (affects net sale proceeds at year 15).
- For **CoC / Monthly NCF**: no impact.

---

## Monte Carlo Sensitivity (Probabilistic)

Monte Carlo Sensitivity measures how **NPV > 0 probability** changes when **one** input is fixed at different values. For each value we run a full Monte Carlo simulation and count the fraction of runs with NPV > 0.

### Parameters and Ranges

Defined in `MC_SENSITIVITY_PARAMETER_CONFIG` in `engelberg/mc_sensitivity_ranges.py`:

| Parameter         | Base Source                             | Min Factor | Max Factor | Clamp Min | Clamp Max | Num Points |
| ----------------- | --------------------------------------- | ---------- | ---------- | --------- | --------- | ---------- |
| Amortization Rate | `config.financing.amortization_rate`    | 0.0        | 2.0        | 0         | 0.02      | 10         |
| Interest Rate     | `config.financing.interest_rate`        | 0.5        | 2.0        | 0.005     | 0.05      | 10         |
| Purchase Price    | `config.financing.purchase_price`       | 0.8        | 1.2        | -         | -         | 10         |
| Occupancy Rate    | `config.rental.occupancy_rate`          | 0.8        | 1.2        | 0         | 1         | 10         |
| Price per Night   | `config.rental.average_daily_rate`      | 0.7        | 1.3        | -         | -         | 10         |
| Ramp-Up Period    | `projection_defaults['ramp_up_months']` | 0.57       | 1.43       | 3         | 12        | 10         |

### Value Generation

For each parameter:

1. **Base value** = value from the case's base config (e.g. `get_base_value(base_config)`).
2. **Min/Max**:
   - `min_value = base_value x min_factor`
   - `max_value = base_value x max_factor`
   - Then apply `clamp_min` / `clamp_max` if defined (same idea as Model Sensitivity).
3. **10 points**: linear spacing between `min_value` and `max_value`:
   - `value[i] = min_value + (max_value - min_value) x i / 9` for `i = 0, ..., 9`.

Implemented in `generate_parameter_range()` in `engelberg/mc_sensitivity.py`.

### Probability Calculation

For **each** of the 10 values of **each** of the 6 parameters:

1. Build a **modified config** with that parameter set to the chosen value (all others at base). Same logic as Model Sensitivity (e.g. `apply_sensitivity(base_config, interest_rate=val)`).
2. Run **Monte Carlo** with that config:
   - `run_monte_carlo_simulation(modified_config, num_simulations=..., use_lhs=True, use_parallel=False)` (parallel is disabled when Monte Carlo Sensitivity runs parameter values in parallel).
3. From the simulation output, compute **statistics** (e.g. `calculate_statistics(df)`).
4. Take **NPV > 0 probability**: `positive_prob = (number of runs with NPV > 0) / total runs`.

Optional: **convergence checking** can stop before the full `num_simulations` if the estimated probability stabilises (see docstring of `run_mc_with_convergence`).

### Output and Impact

- For each parameter we get **10 (value, probability)** pairs.
- **Impact** for that parameter: `impact = max_probability - min_probability` (across the 10 values).
- Parameters are **ranked by impact** (descending) for the summary and charts.

Results are exported to e.g. `{case}_monte_carlo_sensitivity.json` and displayed as probability curves (one line per parameter) and impact table.

---

## Configuration Modification

Sensitivity analyses never mutate the base config; they build **new** configs with **one** (or in Monte Carlo Sensitivity, one at a time) parameter changed. That is done by `apply_sensitivity()` in `engelberg/core.py`.

### Signature (conceptually)

```text
apply_sensitivity(
    base_config,
    occupancy=..., daily_rate=..., management_fee=..., interest_rate=...,
    purchase_price=..., amortization_rate=..., maintenance_rate=...,
    cleaning_cost_per_stay=..., average_length_of_stay=..., insurance_rate=..., ltv=...
) -> BaseCaseConfig
```

Any argument that is `None` is left at the value from `base_config`. Only non-`None` arguments override.

### Behaviour

- **Financing**: New `FinancingParams` with overrides for purchase price, LTV, interest rate, amortization, and same `num_owners`.
- **Rental**:
  - If the base has **seasons**: each season's occupancy and daily rate are overridden when `occupancy` or `daily_rate` are passed. For `daily_rate`, the code applies a **proportional** multiplier to each season's rate so that the overall average matches the requested daily rate.
  - If no seasons: single overall occupancy and daily rate are overridden.
- **Expenses**: New `ExpenseParams` with overrides for management fee, cleaning cost per stay, length of stay, insurance (derived from `insurance_rate x purchase_price` if `insurance_rate` is set), maintenance rate, and property value (set to new purchase price if `purchase_price` is set).

So for Model Sensitivity, "low" and "high" scenarios are exactly **base config with one parameter replaced** by the scaled low/high value; for Monte Carlo Sensitivity, each of the 10 values per parameter is used the same way.

---

## Summary

- **Model Sensitivity** uses **deterministic** low/base/high (from factors and clamps) and recomputes **one** metric (Equity IRR, Cash-on-Cash, or Monthly NCF) per scenario; impact = |high - low|; 16 parameters (12 config + 3 projection-only).
- **Monte Carlo Sensitivity** uses **10 evenly spaced values** per parameter, runs a **Monte Carlo** at each value, and records **NPV > 0 probability**; impact = max_prob - min_prob; 6 parameters.
- Both rely on **single-parameter overrides** via `apply_sensitivity()` and the same core cash flow and projection functions; the only difference is whether the metric is a single deterministic number (IRR, CoC, NCF) or a probability from many stochastic runs (Monte Carlo Sensitivity).

For implementation details, see:

- `engelberg/model_sensitivity.py` - unified sensitivity loop, metric calculators, special handling.
- `engelberg/model_sensitivity_ranges.py` - config parameter factors and clamps; special factors.
- `engelberg/mc_sensitivity.py` - parameter ranges, value generation, Monte Carlo runs, probability and impact.
- `engelberg/mc_sensitivity_ranges.py` - Monte Carlo parameter definitions.
- `engelberg/core.py` - `apply_sensitivity`, `compute_annual_cash_flows`, `compute_15_year_projection`, `calculate_irrs_from_projection`.

---

**Created**: February 2, 2026
**Purpose**: Explain deterministic and Monte Carlo sensitivity calculations
**Status**: Reference Documentation
