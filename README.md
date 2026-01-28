# Engelberg Property Investment Simulation

A toolkit for analyzing co-ownership short-term rental investments in Engelberg, Switzerland. Run base-case and sensitivity analyses, Monte Carlo simulations, and view results in a single-page dashboard.

---

## Table of Contents

- [What is this?](#what-is-this)
- [Features](#features)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Dashboard](#dashboard)
- [Scenarios](#scenarios)
- [Key Metrics & Logic](#key-metrics--logic)
- [Analysis Types](#analysis-types)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

---

## What is this?

This repository models a co-owned vacation property (e.g. holiday flat) in Engelberg: financing, rental income, operating expenses, tax treatment, and a 15-year projection. It supports multiple scenarios (different financing, owner counts, restrictions) and provides:

- **Deterministic base case** – IRR, NPV, MOIC, cash flow, 15-year projection  
- **Sensitivity analysis** – tornado charts for Equity IRR, Cash-on-Cash, and monthly NCF  
- **Monte Carlo** – probabilistic NPV/IRR with stochastic parameters and events  
- **MC Sensitivity** – how NPV > 0 probability varies with key inputs  
- **Scenario comparison** – side-by-side metrics across all cases  

Results are exported as JSON and viewed in a single HTML dashboard (no backend required).

## Features

| Feature | Description |
|--------|-------------|
| **Single source of truth** | All inputs in `assumptions/assumptions.json` (and case-specific `assumptions_*.json`) |
| **Unified CLI** | One script: `scripts/analyze.py` for base, sensitivity, Monte Carlo, MC sensitivity |
| **Batch generation** | `scripts/generate_all_data.py` discovers cases and generates all analyses |
| **Interactive dashboard** | `website/index.html` loads JSON and renders KPIs, tornado charts, tables |
| **Validation** | `scripts/validate_system.py` runs 352 checks (structure, calculations, data, E2E) |

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
- Generates base case, sensitivity (3 types), Monte Carlo, and MC Sensitivity data for each case
- Creates `website/data/cases_index.json` with metadata
- Produces 66+ JSON data files (11 cases × 6 analyses each)

**Option B: Run Individual Analyses**

```bash
python scripts/analyze.py                              # All analyses for base case
python scripts/analyze.py assumptions_migros.json      # All analyses for Migros
python scripts/analyze.py --analysis base                      # Only base case analysis
python scripts/analyze.py --analysis sensitivity               # Only Model Sensitivity analysis
python scripts/analyze.py --analysis monte_carlo               # Only Monte Carlo
python scripts/analyze.py --analysis monte_carlo_sensitivity   # Only MC Sensitivity
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
python scripts/validate_system.py
```

## Documentation

| Document | Purpose |
|----------|---------|
| **[QUICK_START.md](QUICK_START.md)** | Commands, file layout, key metrics, and tips |
| **[docs/SENSITIVITY_CALCULATIONS.md](docs/SENSITIVITY_CALCULATIONS.md)** | How Model and MC sensitivity analyses are calculated |
| **[docs/MONTE_CARLO_ENGINE.md](docs/MONTE_CARLO_ENGINE.md)** | Monte Carlo simulation design, engineering, and execution |
| **[CHANGELOG.md](CHANGELOG.md)** | Version history and implementation notes |

---

## Dashboard

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
4. Switch between cases and analyses instantly without page reloads.

---

## Scenarios

The system supports 11 investment scenarios:

| Case                                   | File                                                          | LTV | Interest | Amort | Owners |
| -------------------------------------- | ------------------------------------------------------------- | --- | -------- | ----- | ------ |
| **Base Case**                          | `assumptions/assumptions.json`                                | 75% | 1.3%     | 1%    | 4      |
| **Migros**                             | `assumptions/assumptions_migros.json`                         | 60% | 1.8%     | 0%    | 4      |
| **3 Owners**                           | `assumptions/assumptions_3_owners.json`                       | 75% | 1.3%     | 1%    | 3      |
| **5 Owners**                           | `assumptions/assumptions_5_owners.json`                       | 75% | 1.3%     | 1%    | 5      |
| **90-Day Restriction**                 | `assumptions/assumptions_90day_restriction.json`              | 75% | 1.3%     | 1%    | 4      |
| **Climate Risk**                       | `assumptions/assumptions_climate_risk.json`                   | 75% | 1.3%     | 1%    | 4      |
| **Early Exit**                         | `assumptions/assumptions_early_exit.json`                     | 75% | 1.3%     | 1%    | 4      |
| **Engelbergerstrasse 53**              | `assumptions/assumptions_engelbergerstrasse53.json`           | 75% | 1.8%     | 1.33% | 4      |
| **Engelbergerstrasse 53 (1.45%)**      | `assumptions/assumptions_engelbergerstrasse53_145.json`        | 75% | 1.45%    | 1.33% | 4      |
| **Engelbergerstrasse 53 (Long-Term)**  | `assumptions/assumptions_engelbergerstrasse53_longterm.json`   | 75% | 1.8%     | 1.33% | 4      |
| **Interest Rate Spike**               | `assumptions/assumptions_interest_rate_spike.json`             | 75% | 2.5%     | 1%    | 4      |

---

## Key Metrics & Logic

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

The dashboard shows both **Pre-Tax** and **After-Tax** cash flow so you can see the effect of tax savings.

### Fee and Expense Logic

- **Cleaning fee**: Applied only at the end of each short-term guest stay. Cost = (rented nights ÷ average length of stay) × cleaning cost per stay (CHF). This is a direct operating expense.
- **Property management fee**: Applied on **revenue after deducting OTA platform fees and cleaning fees**. Base = gross rental income − OTA fees − cleaning cost; management cost = base × management fee rate. This ensures the manager’s percentage is on net rental revenue, not gross.

### Key Metrics (Base Case)

| Metric              | Value             | Description                                                                 |
| ------------------- | ----------------- | --------------------------------------------------------------------------- |
| **Equity IRR**      | 7.92%             | Annualized return on your equity investment over 15 years (includes sale)   |
| **Project IRR**     | 3.97%             | Unlevered return if purchased with 100% cash (no debt financing)            |
| **NPV @ 5%**        | CHF 45,630        | Net Present Value at 5% discount rate (positive = good investment)        |
| **MOIC**            | 3.27×             | Multiple on Invested Capital: total cash returned ÷ initial investment      |
| **Cash Flow/Owner** | -CHF 1,007/year   | Annual net cash flow per owner (negative = you contribute cash)             |
| **After-Tax CF**    | -CHF 57/year      | Annual cash flow after tax savings (interest deduction)                    |
| **Payback Period**  | 15 years          | Years until cumulative cash flow turns positive (with property sale)        |

### Understanding Negative Cash Flow

**Why is cash flow negative?**

The property generates positive Net Operating Income (NOI), but debt service (interest + principal) exceeds NOI:

```
NOI:              CHF 12,978/year
Debt Service:     CHF 17,008/year  (interest + amortization)
Cash Flow:        CHF -4,029/year
Per Owner (÷4):    CHF -1,007/year
```

**But you're building wealth through:**
- **Equity buildup**: Principal payments reduce loan balance (~CHF 4,333/year)
- **Property appreciation**: 2.5% annual growth on your CHF 325k share (~CHF 8,125/year)
- **Tax savings**: Interest deduction saves ~CHF 951/year per owner
- **Personal use value**: 5 nights × market rate (~CHF 1,000/year)

**Total economic value**: Positive despite negative cash flow.

---

## Project Structure

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
│   └── validate_system.py           # System validation (352 checks)
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
│   └── data/                        # JSON data files (66+ files: 11 cases × 6 analyses)
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
└── CHANGELOG.md                     # Change history
```

---

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

A sophisticated probabilistic analysis that models uncertainty across multiple dimensions:

#### Core Features

- **1,000+ scenarios**: Latin Hypercube Sampling (LHS) ensures uniform coverage of parameter space, reducing variance compared to random sampling
- **Correlation modeling**: Gaussian copula approach captures realistic relationships between parameters (e.g., high occupancy correlates with higher rates)
- **Parallel processing**: Multi-threaded execution for faster results

#### Stochastic Parameters (Sampled Each Simulation)

| Parameter | Distribution | Bounds | Description |
|-----------|-------------|--------|-------------|
| **Occupancy Rate** | Beta (α=2.5, β=1.8) | 30-75% | Overall property occupancy |
| **Daily Rate** | Lognormal (μ=ln(300), σ=0.25) | 150-450 CHF | Average nightly rate |
| **OTA Booking %** | Beta (α=3, β=3) | 30-70% | Share of bookings through platforms |
| **OTA Fee Rate** | Triangular (min=25%, mode=30%, max=35%) | 25-35% | Platform commission rate |
| **Length of Stay** | Lognormal (μ=ln(1.7), σ=0.15) | 1.0-3.0 nights | Average guest stay duration |
| **Guests per Night** | Normal (μ=2.0, σ=0.3) | 1.0-4.0 | Average number of guests |
| **Cleaning Cost** | Normal (μ=100, σ=15) | 60-130 CHF | Cost per stay |
| **Tax Rate** | Triangular (min=25%, mode=30%, max=35%) | 25-35% | Marginal tax rate |
| **Discount Rate** | Normal (μ=3%, σ=0.5%) | 2-5% | NPV discount rate |
| **Inflation** | Normal (μ=1.5%, σ=0.75%) | 0-3% | Annual inflation (time-varying) |
| **Property Appreciation** | Normal (μ=3.5%, σ=2.75%) | -2% to 9% | Annual appreciation (time-varying) |
| **Maintenance Rate** | Normal (μ=1%, σ=0.3%) | 0.5-2.0% | Annual maintenance as % of value |
| **Utilities** | Lognormal (μ=ln(2000), σ=0.20) | 1,200-3,500 CHF | Annual utilities cost |

#### Fixed Parameters (Not Sampled)

- **Interest Rate**: Uses base case value (e.g., 1.3%)
- **Management Fee Rate**: Uses base case value (e.g., 20%)
- **Owner Nights**: Uses base case value (e.g., 5 nights per person)
- **Nubbing Costs**: Uses base case value (e.g., 2,000 CHF/year)

#### Time-Varying Parameters

- **Inflation**: AR(1) mean-reverting process over 15 years (bounds 0-3%)
  - Year-to-year changes follow: `inflation[t] = mean + ρ × (inflation[t-1] - mean) + innovation`
  - Captures economic cycles and volatility clustering
- **Property Appreciation**: AR(1) process (bounds -2% to 9%)
  - Allows for market downturns and recovery periods
  - More realistic than constant appreciation

#### Event Modeling

- **Major Maintenance**: Poisson process (~1 event per 5-7 years)
  - Cost: Lognormal distribution (mean 15,000 CHF, bounded 5,000-50,000 CHF)
  - Examples: roof replacement, heating system, major renovations
- **Market Shocks**: Low probability (2-5% per year) of major disruptions
  - Impact: Occupancy -30% to -50%, rates -20% to -30%, property value -10% to -20%
  - Recovery: Gradual return to normal over 1-3 years
  - Examples: pandemic, economic downturn, regulatory changes
- **Refinancing**: Evaluated every 2-3 years
  - Triggered when market rate drops >0.5% below current rate
  - Includes refinancing costs (1-2% of loan balance)
  - Updates loan terms for remaining years

#### Statistical Outputs

- **NPV**: Mean, median, standard deviation, percentiles (P10, P25, P50, P75, P90)
- **IRR**: Distribution statistics for both with-sale and without-sale scenarios
- **Distribution Charts**: Histograms showing range of possible outcomes
- **Risk Metrics**: Probability of negative NPV, Value at Risk (VaR)

### 6. MC Sensitivity Analysis

Combines deterministic parameter variation with probabilistic Monte Carlo simulation to show risk-adjusted impacts:

- **Risk-adjusted parameter impacts**: Shows how NPV > 0 probability changes with parameter variations
- **5 parameters tested**: Amortization Rate, Interest Rate, Purchase Price, Occupancy Rate, Price per Night
- **10 values per parameter**: Evenly spaced across parameter ranges
- **2,000 simulations per value**: High accuracy probabilistic analysis (100,000 total simulations)
- **Line chart visualization**: Shows probability curves for all parameters
- **Interpretation**: Higher probability = lower risk; steeper curve = more sensitive parameter

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
- **Sorted by cash flow**: Scenarios ranked from best to worst cash flow.

---

## Configuration

### Creating New Cases

1. Add `assumptions/assumptions_mycase.json` with only the parameters you want to override (see [Modifying Assumptions](#modifying-assumptions) for JSON format).
2. Run `python scripts/generate_all_data.py`.
3. The new case appears in the dashboard dropdown.

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

1. Edit `assumptions/assumptions.json`
2. Run `python scripts/generate_all_data.py`
3. Refresh the dashboard to see updated results

**To create a new scenario:**

1. Create `assumptions/assumptions_mycase.json` with only changed parameters:
   ```json
   {
     "_case_metadata": {
       "display_name": "My Custom Scenario",
       "description": "Testing different financing terms",
       "enabled": true
     },
     "financing": {
       "interest_rate": 0.02,  // 2% instead of 1.3%
       "ltv": 0.70             // 70% instead of 75%
     }
   }
   ```
2. Run `python scripts/generate_all_data.py`
3. The new case appears automatically in the dashboard dropdown

**Note**: Only include parameters you want to change. All other values inherit from `assumptions.json`.

### System Validation

Run the comprehensive validation script:

```bash
python scripts/validate_system.py
```

**352 checks across 12 categories:**

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
[PASS] Passed:  352
[FAIL] Failed:  0
[WARN] Warnings: 0
```

---

## Troubleshooting

### Dashboard Shows "No cases available"

**Causes**:
- Data files not generated yet
- `cases_index.json` missing or corrupted

**Solutions**:
1. Run `python scripts/generate_all_data.py` to generate all data files
2. Verify `website/data/cases_index.json` exists and contains case entries
3. Check browser console (F12) for loading errors

### Dashboard Shows "Failed to load data"

**Solutions**:

1. Run `python scripts/generate_all_data.py` to regenerate data
2. Use a web server: `cd website && python -m http.server 8080`
3. Check browser console (F12) for specific errors
4. Run `python scripts/validate_system.py` to diagnose issues

### JSON Files Not Generated

**Common Causes**:

1. **Missing dependencies**: Run `pip install -r requirements.txt`
2. **Python version**: Requires Python 3.8+ (check with `python --version`)
3. **Path issues**: Run scripts from project root directory
4. **Permission errors**: Ensure write access to `website/data/` directory

**Diagnostic Steps**:

1. Verify `website/data/` directory exists (created automatically)
2. Check script output for error messages (remove `--quiet` flag)
3. Run `python scripts/validate_system.py` to identify specific issues
4. Check Python path: `python -c "import engelberg; print(engelberg.__file__)"`

### Monte Carlo Takes Too Long

**Optimization Tips**:

- Reduce simulation count: `python scripts/analyze.py --simulations 500`
- Disable parallel processing (if causing issues): Modify `run_monte_carlo_simulation()` in `engelberg/monte_carlo.py`
- Use `--quiet` flag to reduce console output overhead
- For development: Use smaller simulation counts (100-500) for faster iteration.

---

## Understanding the Results

### Interpreting IRR

- **Equity IRR > 5%**: Good return, beats typical savings accounts and bonds
- **Equity IRR > 7%**: Strong return, competitive with stock market averages
- **Equity IRR > 10%**: Excellent return for real estate investment
- **Project IRR**: Lower than Equity IRR because leverage amplifies returns (debt magnifies gains)

### Interpreting NPV

- **NPV > 0**: Investment creates value at the given discount rate
- **NPV < 0**: Investment destroys value (but may still be worthwhile for other reasons)
- **Higher discount rate**: More conservative, requires better returns to be positive

### Interpreting Monte Carlo Results

- **Mean NPV**: Expected value across all scenarios
- **P10/P90**: 10th and 90th percentiles show range of likely outcomes
  - P10: 10% chance of worse result
  - P90: 10% chance of better result
- **Standard Deviation**: Higher = more uncertainty/risk
- **Probability of Negative NPV**: Risk metric showing chance of losing money

### Scenario Comparison Tips

- **Monthly After-Tax Cash Flow**: Most practical metric (what hits your bank account)
- **Equity IRR**: Best for comparing long-term returns across scenarios
- **MOIC**: Shows total wealth creation (includes appreciation and equity buildup).

### Technical Notes

- **Python Version**: 3.8+ required
- **Dependencies**: pandas, numpy, plotly, scipy (see `requirements.txt`)
- **Browser**: Modern browser with JavaScript enabled (Chrome, Firefox, Safari, Edge)
- **Data Format**: All outputs in JSON for easy consumption and programmatic access
- **IRR Calculation**: Binary search method for numerical stability (handles negative cash flows)
- **Monte Carlo**: Uses Latin Hypercube Sampling for better coverage than random sampling
- **Correlations**: Gaussian copula method preserves realistic parameter relationships.

---

## Development

### Adding a New Analysis Type

1. Create analysis function in `engelberg/analysis.py`
2. Add JSON export to `website/data/{case}_myanalysis.json`
3. Update `scripts/generate_all_data.py` to call new function
4. Add render function in `website/index.html`
5. Add sidebar menu item

### Modifying the Dashboard

The dashboard (`website/index.html`) uses:

- **DataManager**: JSON file loading via Fetch API
- **ChartRenderer**: Plotly.js chart rendering
- **UIManager**: UI state management
- **Controller**: Main orchestration.

---

**Last updated**: January 2026 · **Validation**: 352/352 checks passing
