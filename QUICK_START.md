# Quick Start

Operator runbook for generating data, opening the dashboard, and validating consistency.

## 1) Install

```bash
# From repository root
pip install -r requirements.txt
```

Optional developer tooling:

```bash
pip install -r requirements-dev.txt
```

## 2) Generate Dashboard Data

Fast default (recommended):

```bash
# Standard fast path
python scripts/generate_all_data.py
```

This generates all case outputs except fresh MC sensitivity regeneration (it reuses existing files when available).

Full regeneration including MC sensitivity:

```bash
# Use this when you need completely fresh MC sensitivity output
python scripts/generate_all_data.py --include-mc-sensitivity
```

### Run MC sensitivity separately (recommended)

```bash
# Current assumptions file only
python scripts/analyze_monte_carlo_sensitivity.py

# Every assumptions file under assumptions/
python scripts/analyze_monte_carlo_sensitivity.py --all-cases

# Every case with a custom simulation count
python scripts/analyze_monte_carlo_sensitivity.py --all-cases --simulations 1500
```

## 3) Run Single Case

```bash
# Default assumptions file: assumptions/assumptions.json
python scripts/analyze.py

# Specific assumptions file
python scripts/analyze.py assumptions/assumptions_migros.json

# Run one analysis type only
python scripts/analyze.py --analysis base
python scripts/analyze.py --analysis sensitivity
python scripts/analyze.py --analysis monte_carlo
python scripts/analyze.py --analysis loan_structure_sensitivity
python scripts/analyze.py --analysis monte_carlo_sensitivity

# Override Monte Carlo simulation count for this run
python scripts/analyze.py --simulations 5000
```

## 4) Refresh MC Sensitivity Only

```bash
python scripts/analyze_monte_carlo_sensitivity.py
python scripts/analyze_monte_carlo_sensitivity.py --all-cases
python scripts/analyze_monte_carlo_sensitivity.py --all-cases --simulations 1500
```

## 5) Start Dashboard

```bash
cd website
python -m http.server 8080
```

Open: `http://localhost:8080/index.html`

Tip: If the page loads but has empty charts, regenerate data and refresh the browser.

## 6) Validate System

```bash
python -m pytest -q
python scripts/validate_system.py
```

Current expected results:

- `172 passed` (pytest)
- `427 passed, 0 failed` (validator)

## Dashboard Behavior Notes

- Cases available: `12`
- Views available: `9`
- Horizon selector visible for:
  - `base_case`
  - `balance_sheet_cashflow`
  - `sensitivity`
- Horizon selector hidden for:
  - `loan_structure_sensitivity`
  - `sensitivity_coc`
  - `sensitivity_ncf`
  - `monte_carlo`
  - `monte_carlo_sensitivity`
  - `scenario_comparison`

## Common Issues

No cases in dropdown:

```bash
python scripts/generate_all_data.py
```

MC sensitivity too slow during iteration:

```bash
python scripts/generate_all_data.py
python scripts/analyze_monte_carlo_sensitivity.py --all-cases --simulations 300
```

Unexpected output drift:

```bash
python scripts/validate_system.py
python -m pytest -q tests/integration/test_cross_script_consistency.py
```

---

Last updated: February 10, 2026
