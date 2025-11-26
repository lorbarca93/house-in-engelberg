# Engelberg Property Investment Simulation

A professional-grade toolkit for analysing co-ownership rental investments in Engelberg, Switzerland. The code base produces harmonised HTML dashboards for the base case, sensitivity analysis, Monte Carlo simulation, scenario comparisons, and validation checks.

## Overview

- **Single Source of Truth**: `simulation.py` defines the calibrated Engelberg base case (63 % occupancy, 200 CHF ADR, ≈46 k CHF annual revenue).
- **Modular Analyses**: Each script focuses on a specific deliverable while reusing the same configuration pipeline.
- **HTML-First Reporting**: All scripts save reports into `output/` using the `report_*.html` naming convention.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the desired analysis:
   ```bash
   python analysis_base_case.py         # Base case KPI dashboard
   python analysis_sensitivity.py       # Tornado tables & parameter write-ups
   python analysis_monte_carlo.py       # Probabilistic risk view
   python analysis_alternative_scenarios.py  # Ownership & pricing lab
   python analysis_validation.py        # Automated checks + QA dashboard
   ```

## Key Reports

| Script | Purpose | HTML Output |
| --- | --- | --- |
| `analysis_base_case.py` | Executive dashboard, KPI gauges, 15-year projection | `output/report_base_case.html` |
| `analysis_sensitivity.py` | Tornado charts plus parameter-specific tables | `output/report_sensitivity.html` |
| `analysis_monte_carlo.py` | Distribution plots, statistics, correlation grids | `output/report_monte_carlo.html` |
| `analysis_alternative_scenarios.py` | 3/5-owner cases, lower purchase prices, scenario comparison | `output/report_scenario_*.html`, `output/report_scenarios_overview.html` |
| `analysis_validation.py` | Automated regression tests and monitoring dashboard | `output/report_validation.html` |

All reports share a compact visual system (fonts, colour palette, hover styles) for a cohesive experience.

## Base Case Snapshot

- **Purchase Price**: 1 300 000 CHF
- **Financing**: 75 % LTV, 1.3 % interest, 1 % amortisation
- **Owners**: 4 owners, 5 personal nights each
- **Calibrated Inputs** (Airbnb market data):
  - Average occupancy: **63 %**
  - Average nightly rate: **200 CHF**
  - Annual revenue: **≈44.9 k CHF** after owner nights
- **Operating Model**: 20 % management fee (cleaning separate), variable expenses inflated annually, maintenance at 1 % of property value

Adjustments to assumptions should be made in `create_base_case_config()` inside `simulation.py`.

## Repository Structure

```
.
├── analysis_base_case.py           # Base case dashboard generator
├── analysis_sensitivity.py         # Sensitivity toolkit + report builder
├── analysis_monte_carlo.py         # Monte Carlo simulation + report
├── analysis_alternative_scenarios.py  # Ownership & pricing scenario lab
├── analysis_validation.py          # Automated calculations QA + dashboard
├── simulation.py                   # Data classes + shared financial logic
├── scripts/                        # Helper PowerShell utilities
├── output/                         # Generated HTML reports (gitignored)
├── CHANGELOG.md                    # Detailed implementation history
└── README.md                       # Project guide (this file)
```

## Notes

- Excel exports have been disabled to keep the repository light-weight; HTML reports are the single source of deliverables.
- Tests can be launched via `analysis_validation.py`. The script runs 24+ checks and updates `output/report_validation.html`.
- Legacy documentation lives under `markdown_archive/` for historical reference. Some files may mention deprecated script names; the active naming scheme is `analysis_*.py` and `report_*.html`.

---
*Last updated: Test push to verify GitHub integration*