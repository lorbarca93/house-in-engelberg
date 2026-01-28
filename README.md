# Engelberg Property Investment Simulation

A professional-grade toolkit for analyzing co-ownership rental investments in Engelberg, Switzerland. The codebase features a **dynamic single-page dashboard** that loads all analyses dynamically from JSON data files, providing a unified, interactive experience.

## Overview

- **Single Source of Truth**: All assumptions are centralized in `assumptions.json` (and case-specific `assumptions_*.json` files)
- **Dynamic Dashboard**: Single interactive HTML page (`website/index.html`) that loads data dynamically
- **JSON Data Export**: All analyses export structured JSON data to `website/data/` for the dashboard
- **Unified Analysis Script**: Single `analyze.py` script handles all analysis types
- **Case Management**: Easy creation of new scenarios by adding `assumptions_*.json` files
- **Comprehensive Validation**: 198 automated checks ensure system integrity

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate Data for Dashboard

**Option A: Generate All Cases Automatically** (Recommended)

```bash
python scripts/generate_all_data.py
```

This script:

- Auto-detects all `assumptions_*.json` files
- Generates base case, sensitivity (3 types), and Monte Carlo data for each case
- Creates `website/data/cases_index.json` with metadata
- Produces 50 JSON data files (10 cases × 5 analyses each)

**Option B: Run Individual Analyses**

```bash
python scripts/analyze.py                              # All analyses for base case
python scripts/analyze.py assumptions_migros.json      # All analyses for Migros
python scripts/analyze.py --analysis base                      # Only base case analysis
python scripts/analyze.py --analysis sensitivity               # Only Model Sensitivity analysis
python scripts/analyze.py --analysis monte_carlo               # Only Monte Carlo
python scripts/analyze.py --analysis monte_carlo_sensitivity    # Only MC Sensitivity
python scripts/analyze.py --quiet                              # Minimal output
```

### 3. Open the Dashboard

**Using a Local Web Server** (Recommended - required for JSON loading):

```bash
cd website
python -m http.server 8080
# Then open: http://localhost:8080/index.html
```

**Or directly** (may have CORS limitations):

- Open `website/index.html` in your browser
- Note: Some browsers block local file access for security reasons

### 4. Validate the System

```bash
python scripts/validate_system.py    # 198 comprehensive checks
```

## Dynamic Dashboard Features

The dashboard (`website/index.html`) provides:

- **Top Navigation Bar**: Case selector dropdown (11 available cases)
- **Left Sidebar**: Analysis type selector with 7 options:
  - **Model** (Simulation KPIs): Base case metrics and 15-year projection
  - **Model Sensitivity - Equity IRR**: Dual tornado charts showing:
    - Monthly After-Tax Cash Flow per Person (monthly cash flow impact)
    - Equity IRR (15-year return impact)
  - **Model Sensitivity - Cash-on-Cash**: How parameters affect Year 1 cash yield
  - **Model Sensitivity - Monthly NCF**: How parameters affect monthly cash flow
  - **Monte Carlo**: Probabilistic simulation with 1,000+ scenarios
  - **MC Sensitivity**: Shows how NPV > 0 probability changes with parameter variations (5 parameters × 10 values × 2,000 sims)
  - **Scenario Comparison**: Side-by-side comparison of all scenarios with key metrics
- **Dynamic Content Area**:
  - KPI cards with key metrics (12+ per page)
  - Interactive Plotly.js tornado charts
  - Data tables with detailed analysis
  - Responsive design for mobile devices

### Dashboard Workflow

1. Select a case from the dropdown (e.g., "Base Case", "Migros")
2. Select an analysis type from the sidebar
3. View dynamically loaded charts, KPIs, and data tables
4. Switch between cases and analyses instantly without page reloads

## Available Cases

The system supports 10 investment scenarios:

| Case                              | File                                                    | LTV | Interest | Amort | Owners |
| --------------------------------- | ------------------------------------------------------- | --- | -------- | ----- | ------ |
| **Base Case**                     | `assumptions/assumptions.json`                          | 75% | 1.3%     | 1%    | 4      |
| **Migros**                        | `assumptions/assumptions_migros.json`                   | 60% | 1.8%     | 0%    | 4      |
| **3 Owners**                      | `assumptions/assumptions_3_owners.json`                 | 75% | 1.3%     | 1%    | 3      |
| **5 Owners**                      | `assumptions/assumptions_5_owners.json`                 | 75% | 1.3%     | 1%    | 5      |
| **90-Day Restriction**            | `assumptions/assumptions_90day_restriction.json`        | 75% | 1.3%     | 1%    | 4      |
| **Climate Risk**                  | `assumptions/assumptions_climate_risk.json`             | 75% | 1.3%     | 1%    | 4      |
| **Early Exit**                    | `assumptions/assumptions_early_exit.json`               | 75% | 1.3%     | 1%    | 4      |
| **Engelbergerstrasse 53**         | `assumptions/assumptions_engelbergerstrasse53.json`     | 75% | 1.8%     | 1.33% | 4      |
| **Engelbergerstrasse 53 (1.45%)** | `assumptions/assumptions_engelbergerstrasse53_145.json` | 75% | 1.45%    | 1.33% | 4      |
| **Interest Rate Spike**           | `assumptions/assumptions_interest_rate_spike.json`      | 75% | 2.5%     | 1%    | 4      |

## Tax Treatment

The model implements proper Swiss tax treatment for rental property investments:

- **Only interest payments are tax-deductible** (principal repayments are not)
- **30% uniform marginal tax rate** applied across all cases
- **Tax savings** = Interest Payment × 30%
- **After-tax cash flow** = Pre-tax cash flow + Tax savings

**Example Calculation** (Base Case):

- Interest payment: 12,675 CHF/year
- Tax savings: 12,675 × 30% = 3,802.50 CHF/year (total)
- Tax savings per owner: 3,802.50 / 4 = 950.63 CHF/year (~79 CHF/month)
- Pre-tax cash flow per owner: -1,183.71 CHF/year
- After-tax cash flow per owner: -1,183.71 + 950.63 = -233.08 CHF/year

The dashboard displays both **Pre-Tax Cashflow** and **After-Tax Cashflow** metrics, allowing investors to see the impact of tax savings on their returns.

## Key Metrics (Base Case)

| Metric              | Value           | Description                    |
| ------------------- | --------------- | ------------------------------ |
| **Equity IRR**      | 4.63%           | Return on equity over 15 years |
| **Project IRR**     | 2.53%           | Unlevered return (no debt)     |
| **NPV @ 5%**        | -CHF 5,007      | Present value at 5% discount   |
| **MOIC**            | 2.17×           | Multiple on invested capital   |
| **Cash Flow/Owner** | -CHF 2,870/year | Annual net cash flow           |
| **Payback Period**  | 15 years        | With property sale             |

## Repository Structure

```
.
├── engelberg/                       # Main Python package
│   ├── __init__.py                  # Package initialization and exports
│   ├── core.py                      # Core calculation engine (1,250+ lines)
│   ├── analysis.py                  # Analysis orchestration (main entry point)
│   ├── model_sensitivity.py         # Model Sensitivity analysis (deterministic)
│   ├── model_sensitivity_ranges.py  # Model Sensitivity parameter ranges config
│   ├── mc_sensitivity.py           # MC Sensitivity analysis (probabilistic)
│   ├── mc_sensitivity_ranges.py     # MC Sensitivity parameter ranges config
│   └── monte_carlo.py               # Monte Carlo simulation engine (1,870+ lines)
├── scripts/                         # Entry point scripts (CLI)
│   ├── analyze.py                   # Main analysis CLI script
│   ├── generate_all_data.py         # Master data generator (auto-discovers cases)
│   └── validate_system.py           # System validation (198 checks)
├── assumptions/                     # Assumptions files (JSON configs)
│   ├── assumptions.json              # Base case assumptions (single source of truth)
│   └── assumptions_*.json           # Case-specific assumption overrides (9 files)
├── tests/                           # Test suite
│   ├── unit/                        # Unit tests
│   ├── integration/                 # Integration tests
│   ├── regression/                  # Regression tests
│   └── fixtures/                    # Test fixtures
├── website/
│   ├── index.html                   # Dynamic single-page dashboard
│   └── data/                        # JSON data files (50 files: 10 cases × 5 analyses)
│       ├── cases_index.json         # Master index of all cases
│       ├── {case}_base_case_analysis.json
│       ├── {case}_sensitivity.json
│       ├── {case}_sensitivity_coc.json
│       ├── {case}_sensitivity_ncf.json
│       └── {case}_monte_carlo.json
├── requirements.txt                 # Python dependencies
├── requirements-dev.txt              # Development dependencies (pytest, etc.)
├── README.md                        # Project guide (this file)
├── QUICK_START.md                   # Quick start guide
└── CHANGELOG.md                     # Detailed implementation history
```

## Analysis Types

### 1. Model (Base Case Analysis)

- **12 KPI cards**: IRR, NPV, MOIC, Payback, Cash Flow, etc.
- **Main Assumptions Summary**: Financing, rental, projection parameters
- **15-Year Projection Table**: Revenue, expenses, debt service, equity

### 2. Model Sensitivity Analysis - Equity IRR

- **15 parameters tested**: Property appreciation, interest rate, occupancy, etc.
- **Two tornado charts**:
  - **Monthly After-Tax Cash Flow per Person**: Shows monthly cash flow impact (what hits your bank account each month)
  - **Equity IRR**: Shows 15-year return impact (long-term investment performance)
- **End-of-bar annotations**: Final values displayed at the ends of each bar for quick reference
- **Data table**: Low/base/high scenarios with results
- **Hover tooltips**: Detailed explanations for each parameter with formatted values
- **Ranked by impact**: Parameters sorted by their effect on each metric

### 3. Model Sensitivity Analysis - Cash-on-Cash

- **Year 1 cash yield focus**: How parameters affect first-year returns
- **Filters out zero-impact params**: Property appreciation, selling costs
- **Same 15 parameters**: Different metric focus

### 4. Model Sensitivity Analysis - Monthly NCF

- **Monthly cash flow per owner**: Practical "what hits your bank account"
- **CHF values**: Shows actual monthly impact in Swiss Francs
- **Filters non-monthly impacts**: Appreciation, inflation, selling costs

### 5. Monte Carlo Simulation

- **1,000 probabilistic scenarios**: Tests uncertainty in key parameters
- **Statistical outputs**: Mean, median, percentiles for NPV and IRR
- **Distribution charts**: Histograms showing range of possible outcomes

### 6. MC Sensitivity Analysis

- **Risk-adjusted parameter impacts**: Shows how NPV > 0 probability changes with parameter variations
- **5 parameters tested**: Amortization Rate, Interest Rate, Purchase Price, Occupancy Rate, Price per Night
- **10 values per parameter**: Evenly spaced across parameter ranges
- **2,000 simulations per value**: High accuracy probabilistic analysis
- **Line chart visualization**: Shows probability curves for all parameters

### 7. Scenario Comparison

- **Comprehensive comparison table**: All scenarios side-by-side with key metrics
- **After-Tax Cash Flow chart**: Horizontal bar chart showing monthly cash flow per person for all scenarios
- **Key metrics compared**:
  - Monthly After-Tax Cash Flow per Person (primary metric)
  - Equity IRR
  - Cash-on-Cash Return
  - MOIC (Multiple on Invested Capital)
  - Initial Investment per Person
  - Interest Rate
  - Number of Owners
- **Summary KPIs**: Best performers highlighted for each metric
- **Sorted by cash flow**: Scenarios ranked from best to worst cash flow

- **1,000+ simulations**: Probabilistic outcomes
- **Statistics**: Mean, median, std dev, percentiles
- **Distribution charts**: NPV and IRR histograms
- **Risk metrics**: Probability of negative NPV, VaR

## Creating New Cases

To create a new investment scenario:

1. **Create an assumptions file**: `assumptions_mycase.json`

   ```json
   {
     "_case_metadata": {
       "display_name": "My Case",
       "description": "Description of this scenario",
       "enabled": true
     },
     "financing": {
       "purchase_price": 1300000.0,
       "num_owners": 4,
       "ltv": 0.7,
       "interest_rate": 0.015
     }
   }
   ```

2. **Run the generator**:

   ```bash
   python generate_all_data.py
   ```

3. **The new case will appear** in the dashboard dropdown automatically!

## Assumptions Management

### Current Economic Assumptions

| Parameter                 | Value     | Description                    |
| ------------------------- | --------- | ------------------------------ |
| **Inflation**             | 1.0%/year | Revenue and expense growth     |
| **Property Appreciation** | 2.5%/year | Annual property value increase |
| **Discount Rate**         | 5.0%      | NPV calculation rate           |
| **Maintenance Reserve**   | 0.5%/year | Of property value              |
| **Selling Costs**         | 7.8%      | Broker + notary + transfer tax |

### Selling Costs Breakdown (7.8% total)

| Component    | Rate | Description          |
| ------------ | ---- | -------------------- |
| Broker Fee   | 3.0% | Agent commission     |
| Notary Fees  | 1.5% | Legal documentation  |
| Transfer Tax | 3.3% | Canton Obwalden rate |

### Modifying Assumptions

**To change base case assumptions:**

1. Edit `assumptions.json`
2. Run `python generate_all_data.py`

**To create a new scenario:**

1. Create `assumptions_mycase.json` with only changed parameters
2. Run `python generate_all_data.py`

## System Validation

Run the comprehensive validation script:

```bash
python validate_system.py
```

**198 checks across 12 categories:**

- ✅ File structure and existence
- ✅ Python module imports
- ✅ Assumptions file structure
- ✅ Cross-dependencies
- ✅ Generated data files
- ✅ Calculation consistency
- ✅ Cross-validation (assumptions ↔ data)
- ✅ Sensitivity analysis
- ✅ Monte Carlo simulation
- ✅ Dashboard components
- ✅ Script integration
- ✅ End-to-end consistency

**Example Output:**

```
[SUCCESS] SYSTEM VALIDATION PASSED
[PASS] Passed:  198
[FAIL] Failed:  0
[WARN] Warnings: 0
```

## Troubleshooting

### Dashboard Shows "No cases available"

**Solution**: Run `python generate_all_data.py` to generate all data files.

### Dashboard Shows "Failed to load data"

**Solutions**:

1. Run `python generate_all_data.py` to regenerate data
2. Use a web server: `cd website && python -m http.server 8080`
3. Check browser console (F12) for specific errors
4. Run `python validate_system.py` to diagnose issues

### JSON Files Not Generated

**Check**:

1. Verify `website/data/` directory exists
2. Check script output for error messages
3. Ensure dependencies: `pip install -r requirements.txt`
4. Run `python validate_system.py`

## Technical Notes

- **Python Version**: 3.8+ required
- **Dependencies**: pandas, numpy, plotly (see `requirements.txt`)
- **Browser**: Modern browser with JavaScript enabled
- **Data Format**: All outputs in JSON for easy consumption
- **IRR Calculation**: Binary search method for numerical stability

## Development

### Adding a New Analysis Type

1. Create analysis function in `analyze.py`
2. Add JSON export to `website/data/{case}_myanalysis.json`
3. Update `generate_all_data.py` to call new function
4. Add render function in `website/index.html`
5. Add sidebar menu item

### Modifying the Dashboard

The dashboard (`website/index.html`) uses:

- **DataManager**: JSON file loading via Fetch API
- **ChartRenderer**: Plotly.js chart rendering
- **UIManager**: UI state management
- **Controller**: Main orchestration

---

**Last Updated**: January 26, 2026  
**Status**: Production Ready ✅  
**Validation**: 198/198 checks passing
