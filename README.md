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
python generate_all_data.py
```

This script:

- Auto-detects all `assumptions_*.json` files
- Generates base case, sensitivity (3 types), and Monte Carlo data for each case
- Creates `website/data/cases_index.json` with metadata
- Produces 26 JSON data files

**Option B: Run Individual Analyses**

```bash
python analyze.py                              # All analyses for base case
python analyze.py assumptions_migros.json      # All analyses for Migros
python analyze.py --analysis base              # Only base case analysis
python analyze.py --analysis sensitivity       # Only sensitivity analysis
python analyze.py --analysis monte_carlo       # Only Monte Carlo
python analyze.py --quiet                      # Minimal output
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
python validate_system.py    # 198 comprehensive checks
```

## Dynamic Dashboard Features

The dashboard (`website/index.html`) provides:

- **Top Navigation Bar**: Case selector dropdown (Base Case, Migros, 3 Owners, 4 Owners, 5 Owners)
- **Left Sidebar**: Analysis type selector with 3 options:
  - **Model** (Simulation KPIs): Base case metrics and 15-year projection
  - **Sensitivity - Monthly NCF**: How parameters affect monthly cash flow per owner
  - **Monte Carlo**: Probabilistic simulation with 10,000 scenarios (integrated)
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

The system supports 11 investment scenarios:

| Case                 | File                            | LTV | Interest     | Amort  | Owners | Description |
| -------------------- | ------------------------------- | --- | ------------ | ------ | ------ | ----------- |
| **Base Case**        | `assumptions.json`              | 75% | 1.3% fixed   | 0.444% | 4      | Standard financing |
| **900K House**       | `assumptions_900k_house.json`   | 75% | 1.3% fixed   | 0.444% | 4      | More affordable property |
| **SARON Mortgage**   | `assumptions_saron_mortgage.json` | 75% | SARON +0.9%  | 0.444% | 4      | Variable rate mortgage |
| **Migros**           | `assumptions_migros.json`       | 60% | 1.8% fixed   | 0%     | 4      | Alternative lender |
| **3 Owners**         | `assumptions_3_owners.json`     | 75% | 1.3% fixed   | 0.444% | 3      | Smaller ownership group |
| **4 Owners**         | `assumptions_4_owners.json`     | 75% | 1.3% fixed   | 0.444% | 4      | Matches base case |
| **5 Owners**         | `assumptions_5_owners.json`     | 75% | 1.3% fixed   | 0.444% | 5      | Larger ownership group |
| **90-Day Restriction** | `assumptions_90day_restriction.json` | 75% | 1.3% fixed | 0.444% | 4      | Airbnb regulation impact |
| **Climate Risk**     | `assumptions_climate_risk.json` | 75% | 1.3% fixed   | 0.444% | 4      | Weather change impact |
| **Early Exit**       | `assumptions_early_exit.json`   | 75% | 1.3% fixed   | 0.444% | 4      | Poor performance exit |
| **Interest Rate Spike** | `assumptions_interest_rate_spike.json` | 75% | 1.3→3.5%     | 0.444% | 4      | Rate increase risk |

## Key Metrics (Base Case)

| Metric              | Value            | Description                    |
| ------------------- | ---------------- | ------------------------------ |
| **Equity IRR**      | 7.5%             | Return on equity over 15 years |
| **After-tax IRR**   | 8.2%             | IRR after tax benefits         |
| **Project IRR**     | 3.7%             | Unlevered return (no debt)     |
| **NPV @ 5%**        | CHF 39,172       | Present value at 5% discount   |
| **MOIC**            | 3.23×            | Multiple on invested capital   |
| **Cash Flow/Owner** | CHF -3,678/year  | Annual net cash flow           |
| **Tax Benefit/Owner**| CHF 3,572/year   | Annual tax savings from debt   |
| **After-tax CF/Owner**| CHF -106/year   | Cash flow after tax benefits   |
| **Payback Period**  | 15 years         | With property sale             |

## Repository Structure

```
.
├── assumptions.json                 # Base case assumptions (single source of truth)
├── assumptions_*.json               # Case-specific assumption overrides (10 files)
├── analyze.py                       # 🆕 Unified analysis script (1,500+ lines)
├── core_engine.py                   # 🆕 Core calculation engine (1,250+ lines)
├── monte_carlo_engine.py            # Monte Carlo simulation engine (1,870+ lines)
├── generate_all_data.py             # Master data generator (auto-discovers cases)
├── validate_system.py               # System validation (comprehensive checks)
├── requirements.txt                 # Python dependencies
├── website/
│   ├── index.html                   # Dynamic single-page dashboard
│   └── data/                        # JSON data files (56 files)
│       ├── cases_index.json         # Master index of all cases
│       ├── {case}_base_case_analysis.json
│       ├── {case}_sensitivity.json
│       ├── {case}_sensitivity_coc.json
│       ├── {case}_sensitivity_ncf.json
│       └── {case}_monte_carlo.json
├── README.md                        # Project guide (this file)
├── QUICK_START.md                   # Quick start guide
└── CHANGELOG.md                     # Detailed implementation history
```

## Analysis Types

### 1. Model (Base Case Analysis)

- **12 KPI cards**: IRR, NPV, MOIC, Payback, Cash Flow, etc.
- **Main Assumptions Summary**: Financing, rental, projection parameters
- **15-Year Projection Table**: Revenue, expenses, debt service, equity

### 2. Sensitivity Analysis - Equity IRR

- **15 parameters tested**: Property appreciation, interest rate, occupancy, etc.
- **Tornado chart**: Visual impact ranking
- **Data table**: Low/base/high scenarios with results
- **Hover tooltips**: Detailed explanations for each parameter

### 3. Sensitivity Analysis - Cash-on-Cash

- **Year 1 cash yield focus**: How parameters affect first-year returns
- **Filters out zero-impact params**: Property appreciation, selling costs
- **Same 15 parameters**: Different metric focus

### 4. Sensitivity Analysis - Monthly NCF

- **Monthly cash flow per owner**: Practical "what hits your bank account"
- **CHF values**: Shows actual monthly impact in Swiss Francs
- **Filters non-monthly impacts**: Appreciation, inflation, selling costs

### 5. Monte Carlo Simulation

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
| **Property Appreciation** | 3.0%/year | Annual property value increase |
| **Discount Rate**         | 4.0%      | NPV calculation rate           |
| **Maintenance Reserve**   | 0.4%/year | Of property value              |
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

**Comprehensive validation across multiple categories:**

- ✅ File structure and existence
- ✅ Python module imports and dependencies
- ✅ Assumptions file structure (11 complete scenarios)
- ✅ Cross-dependencies and parameter consistency
- ✅ Generated data files (66 JSON + 11 HTML reports)
- ✅ Financial calculation consistency across scenarios
- ✅ Tax benefit calculations and IRR accuracy
- ✅ SARON variable rate mortgage implementation
- ✅ Monte Carlo simulation and HTML report generation
- ✅ Dashboard components and case loading
- ✅ Script integration and data flow
- ✅ End-to-end consistency and error handling

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

**Last Updated**: December 25, 2025
**Status**: Production Ready ✅
**Validation**: All systems operational (Monte Carlo integrated)
