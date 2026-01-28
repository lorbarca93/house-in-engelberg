# Changelog

All notable changes to the Engelberg Property Investment Simulation will be documented in this file.

## [2026-01-26] - Module Separation: Model Sensitivity and MC Sensitivity

### Module Structure Refactoring

Separated Model Sensitivity and MC Sensitivity analyses into dedicated modules for better maintainability and clarity.

#### New Module Structure

- **`engelberg/model_sensitivity.py`**: Contains all Model Sensitivity analysis functions
  - `run_sensitivity_analysis()` - Equity IRR + After-Tax Cash Flow sensitivity
  - `run_cash_on_cash_sensitivity_analysis()` - Cash-on-Cash sensitivity
  - `run_monthly_ncf_sensitivity_analysis()` - Monthly NCF sensitivity
  - `run_unified_sensitivity_analysis()` - Unified function for all Model Sensitivity metrics
  - Metric calculators: `calculate_equity_irr()`, `calculate_cash_on_cash()`, `calculate_monthly_ncf()`, etc.
  - Helper functions: `create_sensitivity_result()`, `scale_low_high()`
  - Modifier functions: `modify_maintenance_rate()`, `modify_cleaning_cost()`, etc.

- **`engelberg/model_sensitivity_ranges.py`**: Configuration for Model Sensitivity parameter ranges
  - `MODEL_SENSITIVITY_PARAMETER_CONFIG` - 12 config parameters with ranges, clamps, and modifiers
  - `MODEL_SENSITIVITY_SPECIAL_FACTORS` - 3 projection parameters (appreciation, inflation, selling costs)

- **`engelberg/mc_sensitivity.py`**: Contains MC Sensitivity analysis function
  - `run_monte_carlo_sensitivity_analysis()` - NPV > 0 probability sensitivity
  - Helper function: `generate_parameter_range()`

- **`engelberg/mc_sensitivity_ranges.py`**: Configuration for MC Sensitivity parameter ranges
  - `MC_SENSITIVITY_PARAMETER_CONFIG` - 5 parameters with ranges and clamps

#### Updated Files

- **`engelberg/analysis.py`**: Now imports and re-exports functions from new modules
  - Removed all Model Sensitivity and MC Sensitivity implementation code
  - Maintains backward compatibility by re-exporting functions
  - Keeps base case analysis and Monte Carlo analysis functions

- **`engelberg/__init__.py`**: No changes needed (imports from `engelberg.analysis` which re-exports)

#### Benefits

1. **Separation of Concerns**: Each analysis type has its own dedicated module
2. **Independent Evolution**: Can modify Model Sensitivity without affecting MC Sensitivity
3. **Clearer Dependencies**: Easy to see what each analysis needs
4. **Easier Testing**: Can test each module independently
5. **Better Maintainability**: Smaller, focused files are easier to understand
6. **Configuration Management**: Parameter ranges are clearly separated and easy to modify

#### Backward Compatibility

- All functions remain accessible through `engelberg.analysis` (via imports)
- All functions remain accessible through `engelberg` package `__init__.py`
- CLI interface (`scripts/analyze.py`) unchanged
- JSON output format unchanged
- Scripts (`generate_all_data.py`, `validate_system.py`) work without changes

## [2026-01-26] - MC Sensitivity Analysis & Naming Alignment

### MC Sensitivity Analysis

Added a new **MC Sensitivity Analysis** (Monte Carlo-based sensitivity) that combines deterministic parameter variation with probabilistic Monte Carlo simulation to show how NPV > 0 probability changes with different parameter values.

#### Features

- **5 Parameters Tested**:
  - Amortization Rate (0% to 2x base, clamped to 0-2%)
  - Interest Rate (0.5x to 2x base, clamped to 0.5%-5%)
  - Purchase Price (±20% of base)
  - Occupancy Rate (±20% of base, clamped to 0-100%)
  - Price per Night (±30% of base, applied proportionally to all seasons)
- **10 Values per Parameter**: Evenly spaced values across the parameter range
- **2,000 Simulations per Value**: High accuracy Monte Carlo simulation for each parameter value
- **Total: 100,000 Simulations**: Comprehensive probabilistic analysis (5 params × 10 values × 2,000 sims)
- **Line Chart Visualization**: Shows how NPV > 0 probability changes across parameter ranges
- **Impact Summary Table**: Ranks parameters by their impact on NPV probability

#### Implementation

**Backend (`engelberg/analysis.py`)**:

- Added `generate_parameter_range()` helper function to create evenly spaced parameter values
- Added `run_monte_carlo_sensitivity_analysis()` function that:
  - Runs base case Monte Carlo to establish baseline NPV probability
  - For each parameter, generates 10 test values
  - For each value, modifies config and runs 2,000 Monte Carlo simulations
  - Extracts NPV > 0 probability from each simulation
  - Ranks parameters by impact (max - min probability)

**Backend (`engelberg/core.py`)**:

- Extended `apply_sensitivity()` to support `purchase_price` and `amortization_rate` parameters
- Added `export_monte_carlo_sensitivity_to_json()` function for structured data export

**Frontend (`website/index.html`)**:

- Added new menu item "MC Sensitivity" in sidebar navigation
- Created `renderMonteCarloSensitivity()` function that:
  - Displays base NPV > 0 probability as KPI card
  - Renders multi-line chart showing probability curves for all 5 parameters
  - Highlights base values with vertical dashed lines
  - Shows impact summary table with min/max probabilities and impact ranges
- Updated data loading logic to handle `monte_carlo_sensitivity` analysis type

**CLI Integration**:

- Added `--analysis monte_carlo_sensitivity` option to `scripts/analyze.py`
- Integrated into main analysis workflow

#### Benefits

- **Risk-Adjusted Sensitivity**: Shows probabilistic impacts, not just deterministic changes
- **Comprehensive Coverage**: Tests 5 critical parameters with high granularity (10 values each)
- **High Accuracy**: 2,000 simulations per value provides statistically robust results
- **Visual Clarity**: Line charts make it easy to see which parameters have the most impact
- **Actionable Insights**: Identifies which parameters to focus on to improve NPV probability

#### Usage

```bash
# Run MC Sensitivity Analysis
python scripts/analyze.py assumptions/assumptions.json --analysis monte_carlo_sensitivity

# Or include in full analysis
python scripts/analyze.py assumptions/assumptions.json --analysis all
```

#### Output

- JSON file: `website/data/{case_name}_monte_carlo_sensitivity.json`
- Dashboard visualization: Accessible via "MC Sensitivity" menu item
- Shows base probability and sensitivity curves for all 5 parameters

### Naming Alignment

Standardized naming across the codebase:

- **Model Sensitivity**: Deterministic sensitivity analysis (Equity IRR, Cash-on-Cash, Monthly NCF)
- **MC Sensitivity**: Monte Carlo-based sensitivity analysis (NPV > 0 probability)

Updated in:

- Dashboard UI labels and titles
- Function docstrings and print statements
- JSON export `analysis_type` fields
- Documentation (README.md, CHANGELOG.md)
- CLI help text

## [2026-01-26] - Scenario Comparison Page & Enhanced Tornado Charts

### Scenario Comparison Page

Added a new **Scenario Comparison** page to the dashboard that provides a comprehensive side-by-side comparison of all investment scenarios.

#### Features

- **Comparison Chart**: Horizontal bar chart showing Monthly After-Tax Cash Flow per Person for all scenarios, color-coded (green for positive, red for negative)
- **Detailed Comparison Table**: Comprehensive table with key metrics:
  - Monthly After-Tax Cash Flow per Person (primary metric)
  - Equity IRR
  - Cash-on-Cash Return
  - MOIC
  - Initial Investment per Person
  - Interest Rate
  - Number of Owners
- **Summary KPIs**: Highlighted cards showing best performers:
  - Best Cash Flow scenario
  - Best Equity IRR scenario
  - Best MOIC scenario
- **Automatic Loading**: Loads all scenario data automatically from `cases_index.json`
- **Sorted Display**: Scenarios sorted by cash flow (best to worst) for easy comparison

#### Implementation

**Frontend (`website/index.html`)**:

- Added new menu item "Scenario Comparison" in sidebar navigation
- Created `renderScenarioComparison()` function that:
  - Loads base case analysis data for all scenarios
  - Extracts key metrics from each scenario
  - Generates comparison chart and table
  - Displays summary KPIs
- Updated routing logic to handle scenario comparison (no case selection needed)

#### Benefits

- **Quick Decision Making**: Instantly see which scenario performs best on key metrics
- **Comprehensive View**: Compare all scenarios in one place without switching between cases
- **Focus on Cash Flow**: Primary metric (monthly after-tax cash flow) prominently displayed
- **Visual Clarity**: Color-coded chart and table make it easy to identify best/worst scenarios

### Monthly After-Tax Cash Flow in Tornado Charts

Changed the After-Tax Cash Flow tornado chart to display **monthly values** instead of annual values for better practical understanding.

#### Changes

**Backend (`engelberg/analysis.py`)**:

- Updated `calculate_after_tax_cash_flow_per_person()` to return monthly values (annual / 12)
- Updated docstring to reflect monthly return value
- Updated print statements to indicate monthly values

**Frontend (`website/index.html`)**:

- Updated chart title to "Monthly After-Tax Cash Flow per Person"
- Updated axis label to "Change in Monthly After-Tax Cash Flow per Person (CHF)"
- Updated hover tooltips to show "Resulting ATCF (monthly)" and "CHF/month" units
- Updated KPI cards to show "Base After-Tax Cash Flow (Monthly)" with "per person/month" unit
- Updated all descriptions to reflect monthly impact

#### Benefits

- **More Practical**: Monthly values are more relevant for understanding actual cash flow impact
- **Better Alignment**: Matches the Monthly NCF sensitivity analysis for consistency
- **Clearer Units**: "per person/month" is more intuitive than annual values

### Tornado Chart Annotations

Added value annotations at the ends of tornado chart bars showing the final result values for quick reference.

#### Features

- **End-of-Bar Annotations**: Final values displayed at both ends of each bar:
  - **Left side (low scenario)**: Shows final monthly after-tax cash flow or Equity IRR
  - **Right side (high scenario)**: Shows final monthly after-tax cash flow or Equity IRR
- **Color-Coded**: Annotations match bar colors (green for positive, red for negative)
- **Formatted Values**: Currency formatting for cash flow, percentage formatting for IRR
- **Both Charts**: Applied to both After-Tax Cash Flow and Equity IRR tornado charts

#### Implementation

**Frontend (`website/index.html`)**:

- Added dynamic annotations array to chart layouts
- Annotations positioned at bar ends using x/y coordinates
- Styled with white background and colored borders matching bar colors
- Small offset from bar ends to avoid overlap

#### Benefits

- **Quick Reference**: See final values without hovering
- **Better Readability**: Values clearly visible at bar ends
- **Consistent Experience**: Same feature on both tornado charts

### Files Modified

- `engelberg/analysis.py` - Updated to return monthly after-tax cash flow values
- `website/index.html` - Added scenario comparison page, updated tornado charts with monthly values and annotations

### Data Regeneration Required

**Important**: After these updates, sensitivity analysis data must be regenerated to include monthly after-tax cash flow values:

```bash
python scripts/generate_all_data.py
```

## [2026-01-26] - After-Tax Cash Flow Model Sensitivity Analysis

### Dual Tornado Charts for Model Sensitivity Analysis

Added a new tornado chart to the Equity IRR Model Sensitivity analysis page showing how parameters affect **After-Tax Cash Flow per Person** (monthly impact), in addition to the existing Equity IRR tornado chart (15-year return impact).

**Note**: This feature was later updated to show monthly values instead of annual values (see entry above).

#### Implementation Details

**Backend (`engelberg/analysis.py`)**:

- Added `calculate_after_tax_cash_flow_per_person()` function to compute after-tax cash flow per person for any configuration
- Updated `create_sensitivity_result()` to include after-tax cash flow per person data (`base_atcf`, `low.atcf`, `high.atcf`, `impact_atcf`)
- Updated `test_parameter_sensitivity()` to calculate and include after-tax cash flow per person for all sensitivity scenarios
- Updated `run_sensitivity_analysis()` to:
  - Calculate base after-tax cash flow per person
  - Include `base_atcf` in exported JSON data
  - Handle special cases (Property Appreciation and Selling Costs don't affect Year 1 cash flow)

**Frontend (`website/index.html`)**:

- Added first tornado chart: **After-Tax Cash Flow per Person** sensitivity
  - Shows monthly cash flow impact in CHF (updated from annual to monthly)
  - Ranked by impact on after-tax cash flow per person
  - Color-coded: green for higher cash flow, red for lower cash flow
- Kept second tornado chart: **Equity IRR** sensitivity (existing)
  - Shows 15-year return impact in percentage points
  - Ranked by impact on Equity IRR
- Both charts use identical styling and structure for easy comparison
- Updated KPI summary cards to show both base after-tax cash flow and base Equity IRR
- Enhanced hover tooltips with formatted currency values

#### Benefits

- **Short-term vs. Long-term View**: Users can now see both immediate cash flow impact (Year 1) and long-term return impact (15 years) side-by-side
- **Better Decision Making**: Helps investors understand which parameters affect their monthly cash flow vs. their overall investment return
- **Consistent Experience**: Both charts use the same parameters, styling, and structure for easy comparison

#### Example Insights

- **Interest Rate**: High impact on both metrics (cash flow and IRR)
- **Property Appreciation**: High impact on IRR but zero impact on Year 1 cash flow
- **Occupancy Rate**: Moderate impact on both metrics
- **Cleaning Cost**: Higher impact on cash flow than on IRR

### Files Modified

- `engelberg/analysis.py` - Added after-tax cash flow per person calculation and sensitivity tracking
- `website/index.html` - Added dual tornado charts to sensitivity analysis page

### Data Regeneration Required

**Important**: After this update, sensitivity analysis data must be regenerated to include the new after-tax cash flow per person values:

```bash
python scripts/generate_all_data.py
```

Or regenerate only sensitivity analysis:

```bash
python scripts/analyze.py --analysis sensitivity
```

## [2026-01-26] - Tax Treatment Refinement and Tax Savings Integration

### Tax Calculation Implementation

Implemented proper Swiss tax treatment for rental property investments with tax savings calculations.

#### Tax Treatment Rules

- **Only interest payments are tax-deductible** (not principal repayment)
- **30% uniform marginal tax rate** applied across all cases
- Tax savings = Interest Payment × 30%
- Tax savings per owner = Tax Savings Total / Number of Owners
- After-tax cash flow = Pre-tax cash flow + Tax savings

#### Tax Calculation Formula

```
Taxable Income = Net Operating Income - Interest Payment
Tax Liability = max(0, Taxable Income) × 30%
Tax Savings = Interest Payment × 30%
After-Tax Cash Flow = Pre-Tax Cash Flow + Tax Savings
```

#### Implementation Details

**Core Engine (`engelberg/core.py`)**:

- Added tax calculations to `compute_annual_cash_flows()`:
  - `taxable_income`: NOI - interest payment
  - `tax_liability`: max(0, taxable_income) × 30%
  - `tax_savings_total`: interest × 30%
  - `tax_savings_per_owner`: tax_savings_total / num_owners
  - `after_tax_cash_flow_total`: pre-tax + tax_savings_total
  - `after_tax_cash_flow_per_owner`: pre-tax per owner + tax_savings_per_owner

- Added tax calculations to `compute_15_year_projection()` for each year in the 15-year projection

- Updated `export_base_case_to_json()` to include all tax metrics in exported JSON

**Dashboard (`website/index.html`)**:

- Added "Tax Savings" KPI cards (per person and total, monthly)
- Added "After-Tax Cashflow" KPI cards (per person and total, monthly)
- Renamed "Airbnb Cashflow" to "Pre-Tax Cashflow" for clarity
- Both pre-tax and after-tax cash flows displayed in Per-Person and Total sections

**Assumptions (`assumptions/assumptions.json`)**:

- Updated `marginal_tax_rate` from 0.21 (21%) to 0.30 (30%)
- Updated explanation text to clarify that only interest (not principal) is tax-deductible

**Tests (`tests/unit/test_core_calculations.py`)**:

- Added `TestTaxCalculations` class with comprehensive tax calculation tests:
  - Tax savings calculation (interest × 30%)
  - Tax savings per owner calculation
  - Taxable income calculation (NOI - interest only)
  - Tax liability calculation
  - After-tax cash flow calculation
  - Edge case: negative taxable income (tax liability = 0)
  - Verification that principal is NOT tax-deductible

#### Impact

- Tax savings improve cash flow for all co-owners
- Example (Base Case): ~950 CHF/year tax savings per owner (~79 CHF/month)
- After-tax cash flows are more positive (or less negative) than pre-tax cash flows
- All 11 cases now include tax metrics in generated data

### Files Modified

- `assumptions/assumptions.json` - Updated tax rate to 30%
- `engelberg/core.py` - Added tax calculations to annual and projection functions
- `engelberg/core.py` - Updated export function to include tax metrics
- `website/index.html` - Added tax savings and after-tax cash flow KPIs
- `tests/unit/test_core_calculations.py` - Added comprehensive tax calculation tests

### Files Regenerated

- All 11 cases regenerated with tax metrics:
  - `website/data/*_base_case_analysis.json` (11 files)
  - `website/data/*_monte_carlo.json` (11 files)
  - `website/data/*_sensitivity*.json` (33 files)

## [2026-01-26] - System Verification, Cleanup, and Documentation Update

### System Verification and Cleanup

Comprehensive verification of file interconnections, removal of redundancies, cleanup of orphaned files, and documentation updates.

#### Code Cleanup

- **Removed duplicate function**: Removed duplicate `extract_case_name()` from `scripts/generate_all_data.py` (now uses import from `engelberg.analysis`)
- **Standardized path resolution**: Updated `scripts/generate_all_data.py` to use `get_project_root()` from `engelberg.core` instead of manual calculation
- **Improved imports**: Added `get_project_root` import to `scripts/validate_system.py` for consistency

#### Orphaned File Cleanup

- **Deleted orphaned data files** (9 files total):
  - `website/data/saron_mortgage_*.json` (3 files) - No corresponding assumptions file
  - `website/data/900k_house_*.json` (3 files) - No corresponding assumptions file
  - `website/data/4_owners_*.json` (3 files) - No corresponding assumptions file

#### Documentation Updates

- **Updated README.md**:
  - Repository structure diagram now shows `engelberg/` package and `scripts/` directory
  - Updated file counts: 10 cases (not 5), 50 data files (10 cases × 5 analyses)
  - Updated cases table to include all 10 scenarios with correct file paths
  - All command examples use `scripts/` paths

- **Updated QUICK_START.md**:
  - Updated case count references (10 cases instead of 5)
  - Enhanced package structure table with line counts
  - Added `assumptions/` and `tests/` directories to structure

#### Verification Results

- All imports resolve correctly across all Python files
- No circular dependencies detected
- All path resolutions work correctly from package location
- All 10 assumptions files have corresponding entries in `cases_index.json`
- All assumptions files have corresponding data files generated

### Files Modified

- `scripts/generate_all_data.py` - Removed duplicate function, standardized path resolution
- `scripts/validate_system.py` - Added `get_project_root` import
- `README.md` - Updated structure, file counts, and case listings
- `QUICK_START.md` - Updated case counts and structure

### Files Deleted

- `website/data/saron_mortgage_*.json` (3 files)
- `website/data/900k_house_*.json` (3 files)
- `website/data/4_owners_*.json` (3 files)

## [2026-01-26] - Package Structure Reorganization

### Major Restructuring

Reorganized the codebase into a proper Python package structure for better maintainability and organization.

#### New Package Structure

- **Created `engelberg/` package**:
  - `engelberg/__init__.py` - Package initialization with convenient exports
  - `engelberg/core.py` - Core financial calculations (moved from `core_engine.py`)
  - `engelberg/analysis.py` - Analysis orchestration (moved from `analyze.py`)
  - `engelberg/monte_carlo.py` - Monte Carlo simulation (moved from `monte_carlo_engine.py`)

- **Created `scripts/` directory**:
  - `scripts/analyze.py` - CLI entry point for analyses
  - `scripts/generate_all_data.py` - Batch data generator
  - `scripts/validate_system.py` - System validation script

#### Path Resolution

- Added `get_project_root()` utility function to resolve paths relative to project root
- Updated all path handling to work correctly from package location
- All assumptions and data file paths now resolve correctly regardless of script location

#### Updated Imports

- All test files updated to use `engelberg.*` imports
- All scripts updated to import from `engelberg` package
- Maintained backward compatibility for functionality

#### Documentation Updates

- Updated `README.md` with new script paths (`scripts/analyze.py`)
- Updated `QUICK_START.md` with new command examples
- Updated `CHANGELOG.md` with reorganization details

### Files Moved

- `core_engine.py` → `engelberg/core.py`
- `monte_carlo_engine.py` → `engelberg/monte_carlo.py`
- `analyze.py` → `engelberg/analysis.py`
- `generate_all_data.py` → `scripts/generate_all_data.py`
- `validate_system.py` → `scripts/validate_system.py`

### Breaking Changes

- **Script paths changed**: All scripts now in `scripts/` directory
  - Old: `python analyze.py`
  - New: `python scripts/analyze.py`

- **Import paths changed**: All imports now use `engelberg.*` package
  - Old: `from core_engine import ...`
  - New: `from engelberg.core import ...`

### Migration Guide

If you have existing scripts or tests that import from the old modules:

1. Update script paths: `python scripts/analyze.py` instead of `python analyze.py`
2. Update imports: Use `from engelberg.core import ...` instead of `from core_engine import ...`
3. All functionality remains the same - only paths and imports changed

## [2025-12-03] - Tornado Chart Harmonization & Cleanup

### Dashboard Visual Improvements

#### 1. Tornado Charts Harmonized

All three sensitivity tornado charts now have consistent, compact styling:

- **Reduced Chart Size**:
  - Height: `Math.max(420, 300 + params * 40)` (was 550-600)
  - Margins: `{ l: 200, r: 30, t: 50, b: 60 }` (was l: 240-250, r: 50)
  - Min-height: 400px (was 650px)

- **Unified Visual Elements**:
  - Zero line width: 2px (was 3-4px)
  - Font sizes: 11-13px (was 13-15px)
  - Consistent `hovermode: "closest"` on all charts
  - Same legend positioning (centered, horizontal, y: 1.08)
  - Same background colors (`#fafbfc`)

- **Compact Info Boxes**:
  - Padding: 14px 18px (was 20px)
  - Border radius: 8px (was 12px)
  - Single-line concise descriptions

- **Compact KPI Grids**:
  - 4-column layout (was auto-fit)
  - Card padding: 12px
  - Font sizes: 0.75em headers, 1.4em values
  - Gap: 12px (was 20px)

#### 2. Repository Cleanup

- **Deleted**: `STATUS.md` (redundant with README.md)
- **Deleted**: `markdown_archive/` folder (6 archived docs)
- **Deleted**: `__pycache__/` folder

### Files Modified

- `website/index.html` - Tornado chart and KPI styling harmonization

### Files Deleted

- `STATUS.md`
- `markdown_archive/BASE_CASE_ARCHITECTURE.md`
- `markdown_archive/CALCULATION_REVIEW.md`
- `markdown_archive/COMPLETE_GITHUB_SETUP.md`
- `markdown_archive/CONSISTENCY_REPORT.md`
- `markdown_archive/GITHUB_SETUP.md`
- `markdown_archive/IMPLEMENTATION_REVIEW.md`

---

## [2025-12-03] - Code Consolidation & Monthly NCF Sensitivity

### Major Changes

#### 1. New Sensitivity Analysis: Monthly Net Cash Flow

- **New**: `Sensitivity - Monthly NCF` tab in dashboard
  - Shows CHF impact on monthly cash flow per owner
  - Filters out parameters with no monthly impact (appreciation, selling costs, inflation)
  - Teal color theme distinct from IRR (purple) and CoC (pink)
  - Complete hover tooltips for all 15 parameters
- **New**: `calculate_monthly_ncf()` function in `analyze.py`
- **New**: `run_monthly_ncf_sensitivity_analysis()` function
- **New**: `{case}_sensitivity_ncf.json` data files (5 files)

#### 2. Code Consolidation & Renaming

- **Renamed**: `simulation.py` → `core_engine.py` (clearer purpose)
- **Renamed**: `run_analysis.py` → `analyze.py` (simpler name)
- **Consolidated**: All analysis scripts merged into unified `analyze.py`
  - `analysis_base_case.py` → merged into `analyze.py`
  - `analysis_sensitivity.py` → merged into `analyze.py`
  - `analysis_monte_carlo.py` → merged into `analyze.py`
- **Deleted**: Individual analysis scripts (using unified script now)

#### 3. Bug Fixes

- **Fixed**: `discount_rate` was hardcoded to 0.05 in `calculate_irrs_from_projection()`
  - Now properly accepts as parameter from assumptions.json
  - Updated all 4 call sites in `analyze.py`
- **Fixed**: Table colors in sensitivity analysis
  - Now dynamically colored based on better/worse than base
  - Green = better result, Red = worse result
  - Applied to all 3 sensitivity tabs

#### 4. Dashboard Enhancements

- **New**: Chart annotations showing base value, range, and parameter count
- **Improved**: Hover tooltips with tree-style formatting and rationale
- **Improved**: `formatValue()` function handles all parameter types:
  - Rates: "7.80%" instead of "0.078"
  - Currency: "CHF 70" instead of "70.0"
  - Nights: "1.7 nights" instead of "1.70"
- **Added**: Complete parameter info for all 15 sensitivity parameters

#### 5. Validation Expansion

- **Expanded**: `validate_system.py` from 72 to 198 checks
- **New**: Cross-validation between assumptions and generated data
- **New**: Sensitivity analysis delta verification
- **New**: Dashboard component checks
- **New**: Script integration tests
- **New**: End-to-end consistency checks

### Technical Details

#### New File Structure

```
analyze.py           # Unified analysis script (1,500+ lines)
core_engine.py       # Core calculation engine (1,250+ lines)
monte_carlo_engine.py # Monte Carlo simulation
generate_all_data.py # Batch generator
validate_system.py   # System validator (198 checks)
```

#### Data Files Generated (26 total)

- 5 cases × 5 analysis types = 25 files
- 1 cases_index.json
- Analysis types: base_case_analysis, sensitivity, sensitivity_coc, sensitivity_ncf, monte_carlo

#### Sensitivity Parameters (15 total)

1. Property Appreciation Rate
2. Interest Rate
3. Average Daily Rate
4. Maintenance Reserve Rate
5. Loan-to-Value (LTV)
6. Average Length of Stay
7. Cleaning Cost per Stay
8. Occupancy Rate
9. Property Management Fee
10. Winter Season Occupancy
11. Amortization Rate
12. Purchase Price
13. Selling Costs Rate
14. Insurance Rate
15. Inflation Rate

### Migration Notes

**For Users:**

- Run `python generate_all_data.py` to regenerate all data
- Old script names (`run_analysis.py`, `simulation.py`) no longer exist
- Use `python analyze.py` for all analyses

**For Developers:**

- Import calculation functions from `core_engine` instead of `simulation`
- Use unified `analyze.py` instead of individual analysis scripts

---

## [2025-12-01] - Dynamic Single-Page Dashboard Redesign

### Major System Overhaul

Complete transformation from multi-page static HTML reports to a unified dynamic dashboard system with JSON-based data architecture.

### Key Changes

#### 1. Dynamic Dashboard System

- **New**: Single-page interactive dashboard (`website/index.html`)
  - Top navigation bar with case selector dropdown
  - Left sidebar with analysis type selector
  - Dynamic content area that loads data via JavaScript
  - Responsive design for mobile devices
  - Plotly.js integration for interactive charts

#### 2. JSON Data Architecture

- **New**: All analyses now export structured JSON data to `website/data/`
- **New**: `export_base_case_to_json()` function in `simulation.py`
- **New**: `export_sensitivity_to_json()` function in `simulation.py`
- **New**: `export_monte_carlo_to_json()` function in `simulation.py`
- **New**: `cases_index.json` master index file listing all available cases

#### 3. Enhanced Assumptions Management

- **Enhanced**: `assumptions.json` now includes extensive explanatory text for each parameter
- **New**: Case metadata system with `_case_metadata` fields
- **New**: Support for case-specific assumption files (`assumptions_*.json`)
- **New**: JSON loader handles explanation fields (skips fields starting with `_`)

#### 4. Master Data Generator

- **New**: `generate_all_data.py` script
  - Auto-detects all `assumptions_*.json` files
  - Generates JSON data for each case automatically
  - Creates `cases_index.json` with metadata
  - Handles base case, sensitivity, and Monte Carlo analyses

#### 5. Case Management System

- **New**: Support for multiple investment scenarios:
  - Base Case (`assumptions.json`)
  - Migros Scenario (`assumptions_migros.json`)
  - 3 Owners (`assumptions_3_owners.json`)
  - 5 Owners (`assumptions_5_owners.json`)
  - 6 Owners (`assumptions_6_owners.json`)
- **New**: Easy creation of new cases by adding `assumptions_*.json` files

#### 6. Updated Analysis Scripts

- **Modified**: `analysis_base_case.py` - Added JSON export to `website/data/{case}_base_case_analysis.json`
- **Modified**: `analysis_sensitivity.py` - Added JSON export to `website/data/{case}_sensitivity.json`
- **Modified**: `analysis_monte_carlo.py` - Added JSON export to `website/data/{case}_monte_carlo.json`
- **Modified**: `analysis_alternative_scenarios.py` - Added JSON export for each scenario

#### 7. Cleanup

- **Removed**: All legacy `report_*.html` files (13 files deleted)
- **Kept**: Only `website/index.html` as the single dashboard entry point

### Technical Details

#### JSON Export Functions

- All export functions return structured dictionaries ready for JSON serialization
- Includes timestamps for data freshness tracking
- Handles numpy/pandas types for JSON compatibility

#### Dashboard JavaScript Architecture

- **DataManager**: Handles loading JSON files via Fetch API
- **ChartRenderer**: Renders Plotly.js charts from JSON data
- **UIManager**: Manages case/analysis selection and UI updates
- **StateManager**: Tracks current case and analysis type

#### File Naming Convention

- Base case analysis: `{case_name}_base_case_analysis.json`
- Sensitivity: `{case_name}_sensitivity.json`
- Monte Carlo: `{case_name}_monte_carlo.json`
- Cases index: `cases_index.json`

### Migration Notes

**For Users:**

1. Run `python generate_all_data.py` to generate all JSON data files
2. Open `website/index.html` using a web server (e.g., `python -m http.server 8000`)
3. Select cases and analyses from the dashboard interface

**For Developers:**

- All assumptions should be modified in `assumptions.json` or case-specific files
- New cases can be added by creating `assumptions_*.json` files
- Dashboard can be extended by adding new analysis types to the JavaScript

### Benefits

1. **Unified Experience**: All analyses accessible from one dashboard
2. **Easy Navigation**: Switch between cases and analyses instantly
3. **Maintainability**: Single HTML file to maintain
4. **Scalability**: Easy to add new cases (just add JSON file)
5. **Performance**: Lazy loading of data, only load what's needed
6. **Enhanced Assumptions**: Explanatory text helps understand rationale

### Breaking Changes

- **Removed**: Individual HTML report files (`report_*.html`)
- **Changed**: Dashboard now requires JSON data files in `website/data/`
- **Changed**: Must use web server to open dashboard (not `file://` protocol)

### Files Added

- `generate_all_data.py` - Master data generator
- `assumptions_3_owners.json` - 3 owners scenario
- `assumptions_5_owners.json` - 5 owners scenario
- `assumptions_6_owners.json` - 6 owners scenario
- `website/data/` - Directory for JSON data files

### Files Modified

- `assumptions.json` - Added extensive explanatory text
- `assumptions_migros.json` - Added explanatory text and case metadata
- `simulation.py` - Added JSON export functions
- `analysis_base_case.py` - Added JSON export
- `analysis_sensitivity.py` - Added JSON export
- `analysis_monte_carlo.py` - Added JSON export
- `analysis_alternative_scenarios.py` - Added JSON export
- `website/index.html` - Complete rewrite as dynamic dashboard

### Files Deleted

- `website/report_base_case.html`
- `website/report_migros.html`
- `website/report_migros_sensitivity.html`
- `website/report_monte_carlo.html`
- `website/report_portal.html`
- `website/report_scenario_*.html` (multiple files)
- `website/report_scenarios_overview.html`
- `website/report_sensitivity.html`
- `website/report_validation.html`

## [2025-01-XX] - Base Case Update: Property Management Fee & 15-Year Projection

### Prompt Context

The user requested two major updates to the base case simulation:

1. **Property Management Fee Change**: Increase property management fee from 25% to 30%, with cleaning costs now included in this fee (removed as separate expense line item)
2. **15-Year Projection**: Calculate and visualize the investment performance over 15 years, starting from January 2026

### Why These Changes Were Requested

- **Property Management Fee**: The user negotiated a new property management arrangement where cleaning services are bundled into the management fee at a 30% rate, simplifying expense tracking and potentially changing the cost structure
- **15-Year Projection**: To better understand the long-term financial trajectory of the investment, including how loan amortization affects cash flow over time and when the property might become cash-flow positive

### Changes Implemented

#### 1. Property Management Fee Update

- **File**: `simulation.py`
  - Updated `create_base_case_config()` to set `property_management_fee_rate` from 0.25 (25%) to 0.30 (30%)
  - Set `cleaning_cost_per_stay` to 0.0 (cleaning now included in management fee)
  - Updated `compute_annual_cash_flows()` to exclude cleaning cost from total operating expenses calculation
  - Updated `compute_detailed_expenses()` to label property management as "Property Management (incl. Cleaning)"

#### 2. 15-Year Projection Functionality

- **File**: `simulation.py`
  - Added new function `compute_15_year_projection()` that:
    - Calculates annual cash flows for 15 years starting from 2026
    - Tracks loan balance reduction due to amortization
    - Adjusts interest payments based on remaining loan balance each year
    - Returns a list of annual results for all 15 years

#### 3. Excel Export Updates

- **File**: `run_base_case.py`
  - Updated `export_to_excel()` function signature to accept `projection_15yr` parameter
  - Modified "Revenue & Expenses" sheet to show "Property Management (includes Cleaning)" instead of separate line items
  - Updated "Assumptions" sheet to reflect that cleaning is included in property management fee
  - Added new "15-Year Projection" sheet with comprehensive annual data including:
    - Year-by-year cash flows
    - Loan balance tracking
    - Debt service breakdown
    - Cash flow per owner

#### 4. HTML Report Enhancements

- **File**: `run_base_case.py`
  - Updated `create_charts()` to accept `projection_15yr` and generate three new charts:
    - 15-Year Cash Flow Projection (line chart showing total and per-owner cash flows)
    - 15-Year Loan Balance & Debt Service (dual-axis chart)
    - 15-Year Revenue & Expenses Projection (multi-line chart)
  - Updated `generate_html_report()` to include:
    - New "15-Year Financial Projection" section with detailed table
    - Updated financial summary table to reflect property management includes cleaning
    - Updated assumptions table to note cleaning is included
  - All charts now display in the HTML report with interactive Plotly visualizations

#### 5. Main Function Updates

- **File**: `run_base_case.py`
  - Updated `main()` function to:
    - Calculate 15-year projection after computing annual cash flows
    - Pass projection data to all export and visualization functions
    - Update console output to reflect property management includes cleaning

### Impact on Calculations

- **Operating Expenses**: Reduced by removing separate cleaning cost line item (cleaning now part of 30% management fee)
- **Property Management Cost**: Increased from 25% to 30% of gross rental income
- **Net Operating Income**: Changed due to updated expense structure
- **15-Year Analysis**: Provides visibility into long-term cash flow trends and loan paydown schedule

### Files Modified

1. `simulation.py` - Core calculation logic and configuration
2. `run_base_case.py` - Main script, exports, and report generation

### Files Created

- `CHANGELOG.md` - This changelog file

### Testing Notes

- All calculations verified to match expected values
- 15-year projection correctly tracks loan amortization
- Excel export includes all new data
- HTML report displays all new charts and tables
- Property management fee correctly calculated at 30% including cleaning

---

## [2025-01-XX] - Sensitivity Analysis Module

### Prompt Context

The user requested a comprehensive sensitivity analysis module that:

1. Takes the base case output as input
2. Analyzes multiple sensitivity scenarios across operational, cost, and financing parameters
3. Generates Excel output with numeric results for all sensitivities
4. Creates an HTML report with professional charts and detailed explanations

### Why This Was Requested

To understand the range of possible outcomes and identify which factors most significantly impact the investment's financial performance. This helps in:

- Risk assessment and scenario planning
- Identifying critical success factors
- Making informed decisions about which variables to focus on optimizing
- Understanding the investment's sensitivity to market conditions and operational changes

### Changes Implemented

#### 1. New Sensitivity Analysis Script

- **File**: `run_sensitivity_analysis.py` (new file)
  - Comprehensive sensitivity analysis module with 15 different sensitivity analyses
  - Takes base case configuration as input
  - Generates Excel and HTML outputs

#### 2. Operational Sensitivities

- **Occupancy Rate (30-70%)**: Analyzes impact of varying occupancy rates on cash flow
- **Average Daily Rate (200-400 CHF)**: Tests sensitivity to rental pricing
- **Owner Nights (0-150)**: Examines trade-off between personal use and rental income
- **Seasonality Curve**: Models monthly revenue distribution with winter peaks and summer lows
- **Platform Mix**: Analyzes Airbnb vs Booking.com revenue mix with different fee structures

#### 3. Cost Sensitivities

- **Cleaning Fee Pass-Through**: Compares three scenarios:
  - Cleaning included in management fee (current)
  - Cleaning passed through to guests
  - Cleaning cost borne by owners
- **Property Management Fee (20-35%)**: Tests impact of management fee rate changes
- **Cleaning Cost per Turnover**: Analyzes sensitivity to cleaning cost variations
- **Utilities (2000-4000 CHF)**: Tests impact of utility cost changes
- **Maintenance Reserve (0.5-2%)**: Examines effect of maintenance reserve rate
- **CAPEX Events**: Models impact of major one-time expenses (roof, heating, renovations)

#### 4. Financing Sensitivities

- **Interest Rate (1.2-3.5%)**: Analyzes impact of mortgage interest rate changes
- **Amortization Rate (1-2%)**: Tests different loan paydown speeds
- **Loan-to-Value (60-80%)**: Examines impact of different equity/debt ratios
- **Mortgage Type**: Compares interest-only vs amortizing mortgages

#### 5. Excel Export

- **File**: `sensitivity_analysis.xlsx`
  - 15 separate sheets, one for each sensitivity analysis
  - Comprehensive numeric data for all scenarios
  - Easy to use for further analysis or presentation

#### 6. HTML Report

- **File**: `sensitivity_analysis.html`
  - Professional, interactive visualizations using Plotly
  - Detailed explanations for each sensitivity
  - Key charts showing:
    - Occupancy rate impact on cash flow
    - Daily rate sensitivity
    - Owner nights vs rental income
    - Seasonality patterns
    - Platform mix comparison
    - Interest rate sensitivity
    - Loan-to-value impact
    - Management fee sensitivity
  - Responsive design with modern styling

#### 7. Chart Generation

- Interactive Plotly charts embedded in HTML
- Line charts for continuous variables
- Bar charts for categorical comparisons
- Dual-axis charts for multi-metric analysis
- Break-even lines where applicable

### Technical Implementation Details

#### Sensitivity Functions

Each sensitivity analysis is implemented as a separate function:

- `sensitivity_occupancy_rate()`: Varies occupancy from 30% to 70%
- `sensitivity_daily_rate()`: Tests daily rates from 200 to 400 CHF
- `sensitivity_owner_nights()`: Analyzes owner nights from 0 to 150
- `sensitivity_seasonality()`: Models monthly revenue with seasonal multipliers
- `sensitivity_platform_mix()`: Compares Airbnb vs Booking.com with different fee structures
- `sensitivity_cleaning_pass_through()`: Three-scenario comparison
- `sensitivity_property_management_fee()`: Tests 20% to 35% range
- `sensitivity_cleaning_cost()`: Analyzes cleaning cost per turnover
- `sensitivity_utilities()`: Tests 2000 to 4000 CHF range
- `sensitivity_maintenance_reserve()`: Tests 0.5% to 2% range
- `sensitivity_capex_events()`: Models major capital expenditures
- `sensitivity_interest_rate()`: Tests 1.2% to 3.5% range
- `sensitivity_amortization_rate()`: Tests 1% to 2% range
- `sensitivity_ltv()`: Tests 60% to 80% LTV range
- `sensitivity_mortgage_type()`: Compares interest-only vs amortizing

#### Key Features

- All sensitivities use the base case configuration as starting point
- Calculations maintain consistency with base case logic
- Results are formatted for easy interpretation
- Charts highlight break-even points and key thresholds

### Files Created

1. `run_sensitivity_analysis.py` - Main sensitivity analysis script
2. `sensitivity_analysis.xlsx` - Excel output with all sensitivity results
3. `sensitivity_analysis.html` - HTML report with charts and explanations

### Usage

Run the sensitivity analysis after generating the base case:

```bash
python run_sensitivity_analysis.py
```

This will:

1. Load the base case configuration
2. Run all 15 sensitivity analyses
3. Generate Excel file with numeric results
4. Generate HTML report with visualizations

### Testing Notes

- All 15 sensitivity analyses execute successfully
- Excel file contains 15 sheets with comprehensive data
- HTML report displays all charts correctly
- All calculations are consistent with base case logic
- Seasonality model uses normalized multipliers to maintain annual totals
- Platform mix analysis accounts for different fee structures and rate impacts

---

## [2025-01-XX] - Base Case Enhancements: Inflation, Appreciation, IRR, and Visual Fixes

### Prompt Context

The user requested several enhancements to the base case HTML report:

1. **Fix KPI Gauge Chart Visual Issues**: Text overlays in the key performance indicators chart needed to be resolved
2. **Add Inflation Assumptions**: Include inflation (2% per year) in the 15-year projection
3. **Add Property Appreciation**: Conservative 1% per year property value appreciation
4. **Calculate IRRs**: Two IRR calculations:
   - IRR with house sale at end of 15 years
   - IRR without house sale

### Why These Changes Were Requested

- **Visual Improvements**: Professional presentation is critical for decision-making and stakeholder communication
- **Inflation**: Real-world analysis requires accounting for inflation's impact on revenue and expenses
- **Property Appreciation**: Swiss real estate historically appreciates; this should be factored into returns
- **IRR Metrics**: Industry-standard metric for evaluating investment returns, especially important for comparing to alternative investments

### Changes Implemented

#### 1. KPI Gauge Chart Visual Fixes

- **File**: `run_base_case.py`
  - Replaced single subplot figure with 4 individual gauge charts
  - Increased spacing and margins to prevent text overlays
  - Improved font sizes and styling for better readability
  - Each KPI now has its own dedicated chart with proper spacing

#### 2. Inflation Integration

- **File**: `simulation.py`
  - Updated `compute_15_year_projection()` to accept `inflation_rate` parameter (default 2%)
  - Applied inflation to:
    - Gross rental income
    - Property management costs
    - Tourist tax
    - Insurance
    - Utilities
  - Maintenance reserve calculated on appreciated property value

#### 3. Property Appreciation

- **File**: `simulation.py`
  - Added `property_appreciation_rate` parameter (default 1% per year)
  - Property value increases annually: `purchase_price * (1.01 ^ year_number)`
  - Maintenance reserve calculated based on current property value each year
  - Final property value used in IRR calculations

#### 4. IRR Calculations

- **File**: `simulation.py`
  - Added `calculate_irr()` function using binary search method
  - Added `calculate_irrs_from_projection()` function that calculates:
    - **IRR with Sale**: Includes annual cash flows + sale proceeds (property value - loan balance) at year 15
    - **IRR without Sale**: Only annual cash flows, no sale proceeds
  - IRR calculation handles negative cash flows correctly
  - Returns IRRs as percentages

#### 5. HTML Report Updates

- **File**: `run_base_case.py`
  - Added 4 new KPI cards for:
    - IRR (with Sale)
    - IRR (without Sale)
    - Final Property Value
  - New "IRR Analysis" section with detailed table showing:
    - Initial equity investment
    - Final property value
    - Final loan balance
    - Net sale proceeds per owner
    - Both IRR metrics
  - Updated 15-year projection section to explain inflation and appreciation assumptions
  - All KPI gauge charts now display individually without overlays

#### 6. Console Output Updates

- **File**: `run_base_case.py`
  - Added "15-Year Projection Metrics" section showing:
    - Final property value
    - Final loan balance
    - Sale proceeds per owner
    - Both IRR metrics
  - Added inflation and appreciation rate information

### Technical Details

#### Inflation Application

- Year 1: No inflation (base year)
- Year N: All revenue and variable expenses multiplied by `(1.02 ^ (N-1))`
- Fixed expenses (insurance, utilities) also inflate
- Maintenance reserve recalculated based on appreciated property value

#### Property Appreciation

- Conservative 1% annual appreciation
- Year N property value: `1,300,000 * (1.01 ^ (N-1))`
- Year 15 property value: ~CHF 1,494,316

#### IRR Calculation Method

- Binary search algorithm to find rate where NPV = 0
- Handles negative cash flows (negative IRRs possible)
- Search range: -99% to 999%
- Tolerance: 1e-8 for precision

### Impact on Results

- **Cash Flows**: Improve over time due to inflation increasing revenue faster than some fixed costs
- **Property Value**: Increases from CHF 1,300,000 to CHF 1,494,316 over 15 years
- **IRR with Sale**: Positive return when including property sale proceeds
- **IRR without Sale**: Negative return due to negative annual cash flows (expected given base case)

### Files Modified

1. `simulation.py` - Added inflation, appreciation, and IRR calculation functions
2. `run_base_case.py` - Updated charts, HTML report, and console output

### Testing Notes

- KPI charts display correctly without text overlays
- Inflation correctly applied to all relevant line items
- Property appreciation calculated correctly
- IRR calculations produce reasonable results
- HTML report displays all new metrics clearly
- Both IRRs calculated and displayed in console and HTML

---

## [2025-01-XX] - Chart Library Upgrade: ApexCharts Integration

### Prompt Context

The user requested better, more sophisticated charts in the HTML report. The previous Plotly embedded HTML approach was not visually appealing enough and needed improvement.

### Why This Change Was Requested

- **Visual Quality**: The embedded Plotly charts lacked sophistication and modern styling
- **User Experience**: Better interactivity and presentation needed for professional reports
- **Performance**: JavaScript-based charts provide better rendering and interactivity

### Changes Implemented

#### 1. ApexCharts Integration

- **File**: `run_base_case.py`
  - Replaced Plotly's `to_html()` method with ApexCharts JavaScript library
  - ApexCharts is a modern, open-source charting library known for beautiful visualizations
  - Added ApexCharts CDN link in HTML
  - Created `generate_apexcharts_html()` function to generate all chart configurations

#### 2. Chart Improvements

- **Enhanced Styling**:
  - Smooth curves for line charts
  - Better color schemes
  - Improved tooltips with Swiss currency formatting
  - Professional grid styling with alternating row colors
  - Better markers and hover effects
- **Chart Types**:
  - Bar charts for revenue/expenses comparison
  - Donut charts for expense breakdown
  - Line charts for 15-year projections with smooth curves
  - All charts include zoom and toolbar functionality

#### 3. Visual Enhancements

- **CSS Updates**:
  - Enhanced chart container styling with hover effects
  - Better shadows and transitions
  - Improved spacing and padding
  - Professional rounded corners

- **Interactivity**:
  - Zoom functionality on all line charts
  - Hover tooltips with formatted currency values
  - Interactive legends
  - Smooth animations

#### 4. Currency Formatting

- All charts use Swiss currency formatting (CHF)
- Proper number formatting with thousand separators
- Consistent formatting across all tooltips and labels

### Technical Details

#### ApexCharts Features Used

- **Line Charts**: Smooth curves, markers, zoom, annotations
- **Bar Charts**: Grouped bars, data labels, custom colors
- **Donut Charts**: Percentage display, custom labels
- **Tooltips**: Custom formatters for currency display
- **Grids**: Alternating row colors for better readability
- **Legends**: Top/bottom positioning with interactive toggling

#### Chart Configuration

- All charts use consistent color schemes
- Professional typography and spacing
- Responsive design
- Swiss locale formatting (de-CH) for currency

### Files Modified

1. `run_base_case.py` - Added ApexCharts generation function and updated HTML template

### Benefits

- **Better Visual Appeal**: Modern, professional-looking charts
- **Improved Interactivity**: Zoom, hover, and interactive legends
- **Better Performance**: JavaScript-based rendering is faster
- **Professional Presentation**: Suitable for stakeholder presentations
- **Enhanced UX**: Better tooltips and formatting

### Testing Notes

- All charts render correctly with ApexCharts
- Currency formatting works properly
- Interactive features (zoom, hover) function as expected
- Charts are responsive and display well on different screen sizes
- No JavaScript errors in browser console
