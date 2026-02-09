# Quick Start

Fast operator guide for running analyses, generating dashboard data, and validating outputs.

## 1) Install

```bash
pip install -r requirements.txt
```

## 2) Generate Data

### Fast all-cases batch (recommended during normal iteration)

```bash
python scripts/generate_all_data.py
```

Behavior:
- Discovers all assumptions files
- Generates base case, sensitivity, and Monte Carlo JSONs
- Reuses existing MC sensitivity JSON (does not regenerate by default)

### Full all-cases batch (slow)

```bash
python scripts/generate_all_data.py --include-mc-sensitivity
```

### Run MC sensitivity separately (recommended)

```bash
python scripts/analyze_monte_carlo_sensitivity.py
python scripts/analyze_monte_carlo_sensitivity.py --all-cases
python scripts/analyze_monte_carlo_sensitivity.py --all-cases --simulations 1500
```

## 3) Run Single Case

```bash
python scripts/analyze.py
python scripts/analyze.py assumptions/assumptions_migros.json
python scripts/analyze.py --analysis base
python scripts/analyze.py --analysis sensitivity
python scripts/analyze.py --analysis monte_carlo
python scripts/analyze.py --analysis monte_carlo_sensitivity
python scripts/analyze.py --simulations 5000
```

## 4) Open Dashboard

```bash
cd website
python -m http.server 8080
```

Open `http://localhost:8080/index.html`.

## 5) Validate

```bash
python scripts/validate_system.py
python -m pytest tests -v
```

Expected on current branch:
- `validate_system.py`: `403 passed, 0 failed`
- `pytest`: `154 passed`

## Dashboard Summary

- Cases in dropdown: 12
- Analysis views: 8
- Time horizon selector options: `5, 10, 15, 20, 25, 30, 35, 40`

Horizon selector policy:
- Visible: `base_case`, `sensitivity`
- Hidden: `sensitivity_coc`, `sensitivity_ncf`, `monte_carlo`, `monte_carlo_sensitivity`, `scenario_comparison`

## Current Base Case Snapshot

From `website/data/base_case_base_case_analysis.json`:

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

## Files You Will Touch Most

- `assumptions/` for scenario inputs
- `scripts/generate_all_data.py` for batch generation
- `scripts/analyze_monte_carlo_sensitivity.py` for isolated MC sensitivity runs
- `website/index.html` for dashboard rendering
- `website/data/` for generated JSON artifacts

## Common Issues

### "No cases available" in dashboard

Run:

```bash
python scripts/generate_all_data.py
```

Confirm `website/data/cases_index.json` exists.

### Slow iteration loop

Use fast batch + separate MC sensitivity:

```bash
python scripts/generate_all_data.py
python scripts/analyze_monte_carlo_sensitivity.py --all-cases --simulations 300
```

### Sanity check before commit

```bash
python scripts/validate_system.py
python -m pytest tests -v
```

---

Last updated: February 9, 2026
