# System Architecture

## Purpose

This document describes how the Engelberg modeling stack is structured across:

- Core financial logic (`engelberg/`)
- Script orchestration (`scripts/`)
- Generated JSON artifacts (`website/data/`)
- Interactive dashboard (`website/index.html`)
- Validation and tests (`scripts/validate_system.py`, `tests/`)

## Architecture Overview

```text
assumptions/*.json
   -> engelberg.core (config + financial engine)
   -> engelberg.analysis / model_sensitivity / monte_carlo / mc_sensitivity
   -> scripts/*.py (single-case + batch orchestration)
   -> website/data/*.json outputs
   -> website/index.html (interactive rendering)
```

## Layer Breakdown

### 1) Assumptions Layer

Location: `assumptions/`

- Base assumptions plus case-specific overrides.
- Includes:
  - financing (single-rate fallback + tranche structure)
  - rental and seasonal configuration
  - expense parameters
  - projection parameters (inflation, appreciation, ramp-up, renovation downtime)
  - sale costs and sale tax rates

### 2) Core Engine Layer

Location: `engelberg/core.py`

Primary responsibilities:

- Parse and validate assumptions into dataclasses.
- Execute deterministic cash-flow, projection, and return calculations.
- Support both financing modes:
  - legacy single interest rate
  - tranche-based fixed/SARON blended financing
- Apply stress testing for SARON shock scenarios.
- Export JSON-ready structures used by downstream analysis and UI.

Key dataclasses:

- `LoanTranche`
- `FinancingParams`
- `RentalParams`
- `ExpenseParams`
- `ProjectionParams`
- `BaseCaseConfig`

Key engine functions:

- `create_base_case_config()`
- `get_projection_defaults()`
- `compute_annual_cash_flows()`
- `compute_15_year_projection()`
- `calculate_irrs_from_projection()`
- `apply_sensitivity()`

### 3) Analysis Layer

Location: `engelberg/analysis.py` and related modules

- `run_base_case_analysis()`
- `run_sensitivity_analysis()` (from `engelberg/model_sensitivity.py`)
- `run_cash_on_cash_sensitivity_analysis()`
- `run_monthly_ncf_sensitivity_analysis()`
- `run_monte_carlo_analysis()`
- `run_monte_carlo_sensitivity_analysis()` (from `engelberg/mc_sensitivity.py`)
- `run_loan_structure_sensitivity_analysis()`

This layer orchestrates calculations and writes canonical JSON payloads into `website/data/`.

### 4) Script Layer

Location: `scripts/`

- `analyze.py`
  - single-case CLI wrapper around analysis layer
- `generate_all_data.py`
  - discovers all assumptions files and generates all case outputs
  - writes `website/data/cases_index.json`
- `analyze_monte_carlo_sensitivity.py`
  - focused MC sensitivity generation for one/all cases
- `validate_system.py`
  - repository-wide structural and numeric consistency checks

### 5) Presentation Layer

Location: `website/index.html`

- Single-page dashboard with stateful analysis switching.
- Loads JSON on demand via `DataManager`.
- Renders charts/tables via `ChartRenderer` using Plotly.
- Controls view logic via `UIManager` and `Controller`.

Current analysis views:

1. `base_case`
2. `balance_sheet_cashflow`
3. `loan_structure_sensitivity`
4. `sensitivity`
5. `sensitivity_coc`
6. `sensitivity_ncf`
7. `monte_carlo`
8. `monte_carlo_sensitivity`
9. `scenario_comparison`

## Core Financial Flow

### Annual flow (`compute_annual_cash_flows`)

1. Revenue (downtime-adjusted)
2. OTA fee deduction
3. Cleaning and management-fee base determination
4. Operating expenses
5. NOI
6. Interest + amortization (tranche-aware if configured)
7. Pre-tax cash flow
8. Interest tax shield
9. After-tax cash flow
10. Stress outputs (base, +150 bps, +250 bps)

### Projection flow (`compute_15_year_projection`)

For each year:

- Resolve operational months from:
  - initial ramp-up
  - recurring renovation downtime
- Apply inflation/appreciation factor (or MC time series)
- Recompute revenue and variable costs with occupancy/rate effects
- Apply market shocks/refinancing/maintenance events when present
- Recompute debt service on current balance
- Compute yearly after-tax cash flow and stress metrics
- Roll forward loan balance

### Exit flow (`calculate_irrs_from_projection`)

- Starts with gross sale price.
- Deducts selling costs (`selling_costs_rate`).
- Deducts capital gains tax (`capital_gains_tax_rate`, gain-only).
- Deducts sale transfer tax (`property_transfer_tax_sale_rate`, gross basis).
- Computes net sale price and owner-level proceeds after loan payoff.
- Calculates equity/project IRR, NPV, MOIC, and payback period.

## Output Contracts

### Base case JSON (`{case}_base_case_analysis.json`)

Top-level keys:

- `config`
- `annual_results`
- `projection_15yr`
- `irr_results`
- `kpis`
- `timestamp`
- `by_horizon`

Notable fields:

- tranche configuration and stress policy in `config.financing`
- downtime metadata in `annual_results` and each projection year
- sale-tax fields in `irr_results`

### Loan structure sensitivity JSON (`{case}_loan_structure_sensitivity.json`)

Top-level keys:

- `analysis_type`
- `case_name`
- `projection_years`
- `assumptions`
- `stress_policy`
- `recommended_scenario_id`
- `ranking`
- `scenarios`

Each scenario contains:

- tranche mix
- year-1 liquidity/stress KPIs
- long-term return KPIs
- first-5-year equity-build decomposition

### Cases index (`website/data/cases_index.json`)

- Case metadata and data-file mapping used by dashboard selectors.
- Includes per-case file references for all analysis types.

## Horizon Routing Model

Handled in `website/index.html` via `HorizonResolver`.

Horizon-aware analyses:

- `base_case`
- `balance_sheet_cashflow`
- `sensitivity`

Horizon-hidden analyses:

- `loan_structure_sensitivity`
- `sensitivity_coc`
- `sensitivity_ncf`
- `monte_carlo`
- `monte_carlo_sensitivity`
- `scenario_comparison`

## Testing and Validation Architecture

### Test suite (`tests/`)

- Unit tests: core formulas and helper behavior
- Integration tests: analysis workflows and exports
- Regression tests: known-value protections
- New cross-consistency integration coverage:
  - index integrity
  - input/output alignment
  - cross-analysis identity checks
  - script entrypoint parity checks

Current status: `172 passed`

### Validator (`scripts/validate_system.py`)

Covers:

- file/module existence
- assumptions sanity
- output shape and presence
- cross-calculation consistency
- KPI range safety
- dashboard component checks
- end-to-end file naming and linkage

Current status: `427 passed, 0 failed`

## Extension Points

### Add new analysis type

1. Implement analysis function in `engelberg/`
2. Add export/write pathway
3. Wire into `scripts/analyze.py` and `scripts/generate_all_data.py`
4. Add JSON mapping + renderer in `website/index.html`
5. Add validator checks and integration tests

### Add new scenario

1. Add assumptions file under `assumptions/`
2. Run `python scripts/generate_all_data.py`
3. Confirm new entry in `website/data/cases_index.json`

### Add new sensitivity driver

1. Register parameter and range config
2. Implement modifier pathway
3. Validate output ordering and impact metrics
4. Add integration/unit assertions

---

Last updated: February 10, 2026

