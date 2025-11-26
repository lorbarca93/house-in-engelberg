# Engelberg Property Investment Simulation

A professional-grade toolkit for analysing co-ownership rental investments in Engelberg, Switzerland. The code base produces harmonised HTML dashboards for the base case, sensitivity analysis, Monte Carlo simulation, scenario comparisons, and validation checks.

## Overview

- **Single Source of Truth**: `simulation.py` defines the calibrated Engelberg base case (63 % occupancy, 200 CHF ADR, ≈46 k CHF annual revenue).
- **Modular Analyses**: Each script focuses on a specific deliverable while reusing the same configuration pipeline.
- **HTML-First Reporting**: All scripts save reports into `website/` using the `report_*.html` naming convention. Open `website/index.html` in a browser to access all reports.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the desired analysis:
   ```bash
   python analysis_base_case.py              # Base case KPI dashboard
   python analysis_sensitivity.py            # Tornado tables & parameter write-ups
   python analysis_monte_carlo.py            # Probabilistic risk view
   python analysis_alternative_scenarios.py # Ownership & pricing lab
   python analysis_validation.py             # Automated checks + QA dashboard
   python analysis_portal.py                 # Unified summary dashboard
   ```

## Key Reports

| Script                              | Purpose                                                                     | HTML Output                                                                |
| ----------------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `analysis_base_case.py`             | Executive dashboard, KPI gauges, 15-year projection                         | `website/report_base_case.html`                                            |
| `analysis_sensitivity.py`           | Tornado charts (Monthly CF per Investor & Cap Rate), break-even, elasticity | `website/report_sensitivity.html`                                          |
| `analysis_monte_carlo.py`           | Enhanced Monte Carlo with advanced distributions, correlations, seasonality | `website/report_monte_carlo.html`                                          |
| `analysis_alternative_scenarios.py` | 3/5-investor cases, lower purchase prices, scenario comparison              | `website/report_scenario_*.html`, `website/report_scenarios_overview.html` |
| `analysis_validation.py`            | Automated regression tests and monitoring dashboard                         | `website/report_validation.html`                                           |
| `analysis_portal.py`                | Unified summary dashboard combining all analyses                            | `website/report_portal.html`                                               |

All reports share a compact visual system (fonts, colour palette, hover styles) for a cohesive experience. Each report includes:

- **Fixed Sidebar Navigation**: Quick access to all major sections with active highlighting
- **Top Toolbar**: "Back to Home" button and report title
- **Smooth Scrolling**: Clicking sidebar items smoothly scrolls to the target section
- **Active Section Detection**: Sidebar automatically highlights the currently visible section
- **Responsive Design**: Sidebar collapses on mobile devices for optimal viewing

## Base Case Snapshot

- **Purchase Price**: 1 300 000 CHF
- **Financing**: 75 % LTV, 1.3 % interest, 1 % amortisation
- **Investors**: 4 investors, 5 personal nights each
- **Calibrated Inputs** (Airbnb market data):
  - Average occupancy: **63 %**
  - Average nightly rate: **200 CHF**
  - Annual revenue: **≈44.9 k CHF** after owner nights
- **Operating Model**: 20 % management fee (cleaning separate), variable expenses inflated annually, maintenance at 1 % of property value

Adjustments to assumptions should be made in `create_base_case_config()` inside `simulation.py`.

## Repository Structure

```
.
├── analysis_base_case.py              # Base case dashboard generator
├── analysis_sensitivity.py            # Sensitivity toolkit + report builder
├── analysis_monte_carlo.py            # Monte Carlo simulation + report
├── analysis_alternative_scenarios.py  # Ownership & pricing scenario lab
├── analysis_validation.py             # Automated calculations QA + dashboard
├── analysis_portal.py                 # Unified summary dashboard
├── simulation.py                      # Data classes + shared financial logic
├── website/                           # HTML reports and homepage
│   ├── index.html                     # Homepage with links to all reports
│   └── *.html                         # Individual analysis reports
├── markdown_archive/                   # Legacy documentation
├── CHANGELOG.md                       # Detailed implementation history
└── README.md                          # Project guide (this file)
```

## Monte Carlo Enhancements

The Monte Carlo simulation (`analysis_monte_carlo.py`) has been enhanced with sophisticated modeling capabilities:

### Advanced Distributions

- **Beta distribution** for occupancy rates (captures realistic bounded patterns)
- **Lognormal distribution** for daily rates and utilities (models positive-skewed uncertainty)
- **Triangular distribution** for management fees and seasonal parameters (expert-estimated ranges)
- **Normal distribution** for interest rates, inflation, and appreciation (standard financial modeling)

### Correlation Structure

Parameters are sampled with realistic correlations using a Gaussian copula approach:

- Revenue correlations: Occupancy and ADR positively correlated (ρ=0.4-0.5)
- Seasonal correlations: Peak seasons show moderate positive correlation
- Financial correlations: Interest rates negatively correlate with property appreciation (ρ=-0.3)
- Expense correlations: Utilities and maintenance correlate with inflation (ρ=0.3-0.4)

### Expanded Stochastic Inputs

Beyond the original four parameters (occupancy, ADR, interest, management fee), the simulation now varies:

- **Seasonal parameters**: Independent occupancy and ADR for Winter, Summer, and Off-Peak seasons
- **Expense drivers**: Owner nights, utilities, and maintenance rate
- **Projection parameters**: Inflation rate and property appreciation rate (varies per simulation)

### Methodology

The simulation uses Cholesky decomposition of a correlation matrix to generate correlated standard normals, which are then transformed to target distributions via inverse CDF. This ensures realistic parameter relationships while maintaining distributional accuracy.

## Key Features

### Navigation System

All HTML reports feature a unified navigation system:

- **Fixed Sidebar**: Lists all major sections with icons for quick navigation
- **Top Toolbar**: Contains report title and "Back to Home" button
- **Active Highlighting**: Sidebar automatically highlights the section currently in view
- **Smooth Scrolling**: Clicking sidebar items smoothly scrolls to the target section
- **Responsive**: Sidebar collapses on mobile devices (< 768px width)

### Sensitivity Analysis Features

The sensitivity analysis report includes:

- **Tornado Charts**: Visual representation of parameter impact on:
  - Monthly Cash Flow per Investor (most practical metric)
  - Cap Rate (unlevered yield metric)
  - Cash-on-Cash Return (levered return metric)
  - NPV and IRR impacts
- **Break-Even Analysis**: Identifies parameter values where cash flow reaches zero
- **Elasticity Metrics**: Measures sensitivity of outputs to input changes
- **Two-Way Sensitivity**: Analyzes interactions between parameter pairs
- **Scenario Analysis**: Optimistic, pessimistic, base, and stressed scenarios
- **Statistical Measures**: Coefficient of variation, confidence intervals, threshold analysis

### Monte Carlo Simulation Features

The Monte Carlo simulation includes:

- **Advanced Distributions**: Beta, lognormal, triangular, and normal distributions
- **Correlation Structure**: Realistic parameter correlations using Gaussian copula
- **Key Metrics**: NPV, IRR, Cap Rate, Monthly Cash Flow per Investor
- **Risk Metrics**: Percentiles, probability distributions, confidence intervals
- **Visualizations**: Distribution charts, correlation analysis, parameter quartiles

## Notes

- Excel exports have been disabled to keep the repository light-weight; HTML reports are the single source of deliverables.
- Tests can be launched via `analysis_validation.py`. The script runs 43+ checks and updates `website/report_validation.html`.
- Open `website/index.html` in a web browser to access the homepage with links to all reports. Each report includes a "Back to Home" button in the top toolbar.
- All reports use "per Investor" terminology for consistency and clarity.
- Legacy documentation lives under `markdown_archive/` for historical reference. Some files may mention deprecated script names; the active naming scheme is `analysis_*.py` and `report_*.html`.
