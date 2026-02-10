# Engelberg Property Investment Simulation

Financial modeling toolkit for co-ownership short-term rental investments in Engelberg, Switzerland.

It combines:
- Deterministic base-case analysis
- Deterministic sensitivity analysis (Equity IRR, Cash-on-Cash, Monthly NCF)
- Probabilistic Monte Carlo analysis
- Probabilistic Monte Carlo sensitivity analysis
- Interactive dashboard visualizations (single-page HTML + JSON data)

## What You Get

- Core Python package in `engelberg/` for all calculations
- CLI scripts in `scripts/` for single-case and batch runs
- Scenario assumptions in `assumptions/`
- Dashboard in `website/index.html`
- Automated checks:
1. `python -m pytest tests -v` (154 tests)
2. `python scripts/validate_system.py` (403 validation checks)

## Quick Start

### 1) Install dependencies

```bash
# From repository root
pip install -r requirements.txt
```

### 2) Generate dashboard data (all cases)

Use this during normal iteration. It regenerates deterministic + Monte Carlo outputs and reuses existing Monte Carlo sensitivity files if they already exist.

```bash
python scripts/generate_all_data.py
```

### 3) (Optional) Regenerate Monte Carlo sensitivity in the same run

This is slower, but guarantees all Monte Carlo sensitivity JSON files are freshly produced.

```bash
python scripts/generate_all_data.py --include-mc-sensitivity
```

### 4) Run Monte Carlo sensitivity separately (recommended)

```bash
# Current assumptions file only
python scripts/analyze_monte_carlo_sensitivity.py

# Every assumptions file under assumptions/
python scripts/analyze_monte_carlo_sensitivity.py --all-cases

# Every case with a custom simulation count
python scripts/analyze_monte_carlo_sensitivity.py --all-cases --simulations 1500
```

### 5) Start the dashboard

```bash
cd website
python -m http.server 8080
```

Then open `http://localhost:8080/index.html`.

## Core Scripts

| Script | Purpose |
| --- | --- |
| `scripts/analyze.py` | Run analyses for one assumptions file |
| `scripts/generate_all_data.py` | Batch generation across all discovered cases |
| `scripts/analyze_monte_carlo_sensitivity.py` | Dedicated MC sensitivity runner |
| `scripts/validate_system.py` | Structural, data, and consistency validation |

### `analyze.py` examples

```bash
# Run all analyses for the default assumptions file (assumptions/assumptions.json)
python scripts/analyze.py

# Run all analyses for a specific scenario
python scripts/analyze.py assumptions/assumptions_migros.json

# Run one analysis type only
python scripts/analyze.py --analysis base
python scripts/analyze.py --analysis sensitivity
python scripts/analyze.py --analysis monte_carlo
python scripts/analyze.py --analysis monte_carlo_sensitivity

# Increase Monte Carlo simulation count for the run
python scripts/analyze.py --simulations 5000
```

## Dashboard Analysis Views

The sidebar contains 8 analysis views:

1. Model (base case)
2. Model Sensitivity - Equity IRR
3. Model Sensitivity - Cash-on-Cash
4. Model Sensitivity - Monthly NCF
5. Monte Carlo
6. Monte Carlo Sensitivity
7. Waterfall (Revenue vs Expenses)
8. Scenario Comparison

## Time Horizon Behavior

Supported horizon options in UI: `5, 10, 15, 20, 25, 30, 35, 40`.

Horizon selector visibility policy:
- `base_case`: shown, uses `by_horizon[h]`
- `sensitivity` (Equity IRR): shown, uses `by_horizon[h]`
- `sensitivity_coc`: hidden (Year 1 metric)
- `sensitivity_ncf`: hidden (Year 1 metric)
- `monte_carlo`: hidden (fixed 15-year model)
- `monte_carlo_sensitivity`: hidden (fixed 15-year model)
- `scenario_comparison`: hidden

## Scenario Set

Current repository includes 12 scenarios:

1. `assumptions/assumptions.json` (`base_case`)
2. `assumptions/assumptions_3_owners.json`
3. `assumptions/assumptions_5_owners.json`
4. `assumptions/assumptions_90day_restriction.json`
5. `assumptions/assumptions_climate_risk.json`
6. `assumptions/assumptions_early_exit.json`
7. `assumptions/assumptions_engelbergerstrasse53.json`
8. `assumptions/assumptions_engelbergerstrasse53_145.json`
9. `assumptions/assumptions_engelbergerstrasse53_850_success.json`
10. `assumptions/assumptions_engelbergerstrasse53_longterm.json`
11. `assumptions/assumptions_interest_rate_spike.json`
12. `assumptions/assumptions_migros.json`

## Base Case Snapshot

From `website/data/base_case_base_case_analysis.json` generated on this branch:

| Metric | Value |
| --- | --- |
| Equity IRR (with sale) | 6.07% |
| Project IRR (with sale) | 3.66% |
| NPV @ 5% | CHF 18,319 |
| MOIC | 2.62x |
| Annual Cash Flow per Owner (pre-tax) | CHF -4,408 |
| Annual Cash Flow per Owner (after-tax) | CHF -3,458 |
| Monthly Cash Flow per Owner (after-tax) | CHF -288 |
| Payback Period | 15 years |

## Project Structure

```text
.
|-- engelberg/                        # Core calculation and analysis package
|-- scripts/                          # CLI entry points
|-- assumptions/                      # Base and scenario assumptions
|-- website/
|   |-- index.html                    # Dashboard UI
|   `-- data/                         # Generated JSON data
|-- tests/                            # Unit, integration, regression
|-- docs/                             # Technical documentation
|-- QUICK_START.md
|-- CHANGELOG.md
`-- BUG_FIX_SUMMARY.md
```

## Documentation

- `QUICK_START.md`: operator-focused commands and validation flow
- `docs/ARCHITECTURE.md`: system architecture and data flow
- `docs/DEVELOPMENT.md`: development workflow and testing practices
- `docs/SENSITIVITY_CALCULATIONS.md`: deterministic and MC sensitivity methodology
- `docs/MONTE_CARLO_ENGINE.md`: Monte Carlo engine internals
- `docs/WATERFALL_CHARTS.md`: interpretation of waterfall views
- `CHANGELOG.md`: chronological change history

## Troubleshooting

### Dashboard has no data

Run:

```bash
python scripts/generate_all_data.py
```

Check that `website/data/cases_index.json` exists and contains the generated cases list.

### Monte Carlo sensitivity is slow

Use separated execution:

```bash
python scripts/generate_all_data.py        # fast path (skips MC sensitivity regeneration)
python scripts/analyze_monte_carlo_sensitivity.py --all-cases
```

Lower simulation count while iterating:

```bash
python scripts/analyze_monte_carlo_sensitivity.py --all-cases --simulations 300
```

### Verify system integrity

```bash
python scripts/validate_system.py
python -m pytest tests -v
```

Expected on current branch:
- Validation: `403 passed, 0 failed`
- Tests: `154 passed`

---

Last updated: February 9, 2026
