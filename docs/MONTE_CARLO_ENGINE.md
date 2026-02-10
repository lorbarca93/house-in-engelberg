# Monte Carlo Engine

## Purpose

The Monte Carlo engine quantifies uncertainty around returns and cash flows by running many stochastic scenarios on top of the deterministic model.

Implementation lives in `engelberg/monte_carlo.py`.

## High-Level Workflow

1. Load base config (`BaseCaseConfig`).
2. Build distribution set (`get_default_distributions()`).
3. Select active variables based on flags:
   - `use_seasonality`
   - `use_expense_variation`
   - always-on core variables
4. Generate samples using:
   - Latin Hypercube Sampling (default) or
   - random/correlated sampling
5. Run each simulation (parallel or sequential):
   - apply sampled values to config
   - generate time series and events
   - compute annual + projection outputs
   - compute NPV and IRR metrics
6. Aggregate into DataFrame and summary statistics.

## Sampling and Distributions

### Distribution types supported

- `uniform`
- `normal`
- `triangular`
- `beta`
- `lognormal`

Each variable can define optional bounds for clipping.

### Active stochastic variables in main Monte Carlo run

Always active:

- occupancy rate
- daily rate
- OTA booking percentage
- OTA fee rate
- average length of stay
- average guests per night
- cleaning cost per stay
- marginal tax rate
- discount rate
- inflation rate
- property appreciation rate

Conditionally active:

- seasonal occupancy/rate variables (`use_seasonality=True`)
- electricity/internet and maintenance rate (`use_expense_variation=True`)

Fixed at base values in main MC run:

- interest rate
- management fee
- owner nights
- nubbing costs
- ramp-up months (unless explicitly sampled in upstream workflow)

## Correlation Model

- Supports correlated sampling via Gaussian-copula style transformation.
- Uses configured correlation matrix subset for currently active variables.

## Time-Varying Series

Within each simulation, inflation and appreciation are expanded into yearly paths using mean-reverting AR-style dynamics.

Effects:

- Revenue and cost inflation paths are not static constants.
- Property value path captures year-to-year variation.

## Event Modeling

### Major maintenance events

- Poisson-style occurrence process.
- Adds one-time maintenance costs to affected years.

### Market shock events

- Low probability occurrence.
- Applies temporary negative multipliers to occupancy/rates/value.
- Includes gradual recovery behavior.

### Refinancing opportunities

- Evaluated periodically.
- If refinance condition and probability trigger are met:
  - updates effective borrowing rate path
  - applies refinancing cost

## Single Simulation Path

Per simulation (`run_single_simulation`):

1. Extract sampled parameters.
2. Build modified config via `apply_enhanced_sensitivity`.
3. Compute Year 1 with sampled fee/tax assumptions.
4. Generate 15-year projection with time series + events.
5. Compute IRR outputs.
6. Compute NPV using sampled discount rate.
7. Return one result row.

## Parallelization Strategy

- Outer loop parallelization across simulations (`multiprocessing.Pool`).
- Inner nested parallelism disabled in worker-executed contexts to avoid daemon-process child spawning issues.
- Falls back to sequential mode if parallel setup fails.

## Convergence Monitoring

Optional convergence tracking (`check_convergence`) monitors stabilization of NPV stats during simulation progress.

Current behavior:

- Detects and logs convergence signals.
- Continues to configured simulation count rather than early stopping.

## Output Contract

`export_monte_carlo_to_json()` emits:

- `statistics`
- `sample_data`
- `total_simulations`
- `sample_size`
- `timestamp`

Typical usage:

- histogram/CDF/quantile interpretation in dashboard
- probability-of-positive-NPV decision support

## Performance Notes

- Default CLI simulation counts vary by entrypoint:
  - `analysis.main()` default `10000`
  - batch generation default `1000`
- LHS generally improves precision per simulation count vs naive random sampling.
- Parallel execution significantly improves throughput for larger runs.

## Practical Interpretation

Use Monte Carlo outputs to answer:

- How often does NPV remain positive?
- What is the downside tail (P10/P5)?
- How wide is return dispersion around the deterministic base case?

Then combine with:

- deterministic sensitivity (driver ranking)
- loan structure sensitivity (debt policy tradeoffs)
- balance sheet vs cash flow page (liquidity vs equity build)

---

Last updated: February 10, 2026

