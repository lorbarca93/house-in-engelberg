# Changelog

All notable changes to the Engelberg Property Investment Simulation will be documented in this file.

## [2025-11-26] - UI/UX Overhaul: Sidebar Navigation, Tornado Charts, and Terminology Updates

### Prompt Context

The user requested several major improvements to enhance the professional appearance and usability of all HTML reports:

1. **Sidebar Navigation & Toolbar**: Add fixed sidebar navigation and top toolbar to all HTML reports for better navigation
2. **Tornado Charts Enhancement**: Ensure tornado charts are clean and functional, and add cap rate and monthly cash flow per investor metrics
3. **Terminology Consistency**: Update all references from "per Owner" to "per Investor" for clarity
4. **Portal Updates**: Update the analysis portal to reflect new metrics and features
5. **Alternative Scenario Reports**: Update all alternative scenario reports with consistent terminology and new metrics

### Why These Changes Were Requested

- **Navigation**: As reports became more complex with multiple sections, users needed better navigation to quickly jump between sections
- **Professional Presentation**: Sidebar and toolbar provide a more professional, dashboard-like experience
- **Tornado Charts**: Cap rate and monthly cash flow per investor are critical metrics that needed to be prominently displayed
- **Terminology**: "Investor" is more accurate and professional than "Owner" for financial reporting
- **Consistency**: All reports should use the same terminology and design language

### Changes Implemented

#### 1. Sidebar Navigation & Top Toolbar System

- **Files**: All `analysis_*.py` files
  - Created shared layout functions: `generate_top_toolbar()`, `generate_sidebar_navigation()`, `generate_shared_layout_css()`, `generate_shared_layout_js()`
  - Implemented fixed sidebar (250px width) with section navigation
  - Added fixed top toolbar (60px height) with "Back to Home" button
  - Integrated smooth scrolling and active section highlighting using Intersection Observer API
  - Added responsive design (sidebar collapses on mobile)

- **Reports Updated**:
  - `analysis_base_case.py` - Base case report
  - `analysis_sensitivity.py` - Sensitivity analysis report
  - `analysis_monte_carlo.py` - Monte Carlo simulation report
  - `analysis_alternative_scenarios.py` - Scenario comparison dashboard
  - `analysis_validation.py` - Validation report
  - `analysis_portal.py` - Unified portal dashboard
  - `website/index.html` - Homepage (toolbar only, no sidebar needed)

- **Features**:
  - Fixed sidebar with section navigation
  - Active section highlighting as user scrolls
  - Smooth scroll to sections on click
  - "Back to Home" button in toolbar
  - Responsive mobile design
  - Consistent styling across all reports

#### 2. Tornado Charts Enhancement

- **File**: `analysis_sensitivity.py`
  - Updated tornado chart titles and labels to use "per Investor" terminology
  - Enhanced chart formatting:
    - Improved margins and spacing
    - White background for cleaner appearance
    - Better grid lines and zero line visibility
    - Enhanced hover tooltips with detailed parameter information
  - Verified both tornado charts are functional:
    - **Monthly Cash Flow per Investor**: Shows monthly impact in CHF per investor
    - **Cap Rate (Unlevered)**: Shows cap rate impact in percentage points
  - Charts now display with proper sorting by impact magnitude
  - Interactive hover tooltips show parameter ranges and resulting values

#### 3. Terminology Updates: "per Owner" → "per Investor"

- **Files Updated**:
  - `analysis_base_case.py`: Updated all HTML labels, chart titles, table headers
  - `analysis_sensitivity.py`: Updated tornado chart labels and descriptions
  - `analysis_alternative_scenarios.py`: Updated comparison dashboard and scenario cards
  - `analysis_portal.py`: Updated portal metrics and descriptions
  - `analysis_monte_carlo.py`: Already using correct terminology

- **Changes**:
  - "Cash Flow per Owner" → "Cash Flow per Investor"
  - "Monthly Cash per Owner" → "Monthly Cash Flow per Investor"
  - "Equity per Owner" → "Equity per Investor"
  - Chart labels, table headers, KPI cards, and descriptions updated
  - Print statements updated for consistency

#### 4. Portal Updates

- **File**: `analysis_portal.py`
  - Updated terminology to "per Investor"
  - Added description mentioning tornado charts for monthly cash flow per investor and cap rate
  - Enhanced Monte Carlo section to include cap rate and monthly cash flow statistics (if available)
  - Updated link text to reference new tornado chart features
  - Added monthly cash flow per investor to scenario comparison cards

#### 5. Alternative Scenario Reports Updates

- **File**: `analysis_alternative_scenarios.py`
  - Updated comparison dashboard terminology
  - Added "Monthly Cash Flow per Investor" metric to comparison table
  - Added monthly cash flow to scenario cards
  - Updated section IDs for proper sidebar navigation
  - Fixed CSS variable for gradient-1
  - Individual scenario reports automatically updated via base case report function

- **Reports Updated**:
  - Comparison dashboard: `report_scenarios_overview.html`
  - All 6 individual scenario reports (inherit updates from base case)

#### 6. Homepage Updates

- **File**: `website/index.html`
  - Added top toolbar matching other reports
  - Consistent gradient styling
  - Responsive design improvements
  - Enhanced card hover effects

### Technical Implementation Details

#### Shared Layout Functions

All reports now use shared layout functions that can be imported from `analysis_sensitivity.py`:

- `generate_top_toolbar(report_title, back_link, subtitle)`: Creates fixed toolbar HTML
- `generate_sidebar_navigation(sections)`: Creates sidebar with section links
- `generate_shared_layout_css()`: Returns CSS for layout components
- `generate_shared_layout_js()`: Returns JavaScript for smooth scrolling and active highlighting

#### Sidebar Navigation

- Sections are defined with `id`, `title`, and optional `icon`
- JavaScript uses Intersection Observer API to detect visible sections
- Active section is highlighted in sidebar as user scrolls
- Smooth scrolling with proper offset for fixed toolbar

#### Tornado Charts

- Monthly Cash Flow per Investor: Calculated as annual cash flow / 12
- Cap Rate: Calculated as NOI / Purchase Price (unlevered metric)
- Charts sorted by maximum absolute impact
- Top 10 factors displayed
- Red bars (left) = worst case, Green bars (right) = best case

### Files Modified

1. `analysis_base_case.py` - Terminology updates, sidebar/toolbar integration
2. `analysis_sensitivity.py` - Tornado chart enhancements, sidebar/toolbar, terminology
3. `analysis_monte_carlo.py` - Sidebar/toolbar integration
4. `analysis_alternative_scenarios.py` - Terminology, metrics, sidebar/toolbar
5. `analysis_validation.py` - Sidebar/toolbar integration, layout functions
6. `analysis_portal.py` - Terminology, metrics, sidebar/toolbar
7. `website/index.html` - Toolbar addition, styling improvements

### Benefits

- **Better Navigation**: Users can quickly jump to any section in long reports
- **Professional Appearance**: Sidebar and toolbar give reports a modern dashboard feel
- **Consistent Terminology**: "Investor" is more accurate and professional
- **Enhanced Metrics**: Cap rate and monthly cash flow per investor prominently displayed
- **Improved UX**: Smooth scrolling, active highlighting, responsive design
- **Unified Design**: All reports share the same navigation system and styling

### Testing Notes

- All reports generate successfully with sidebar and toolbar
- Navigation works correctly on all pages
- "Back to Home" button functions on all reports
- Tornado charts display correctly with proper formatting
- Terminology is consistent across all reports
- Responsive design works on mobile devices
- Active section highlighting functions as expected
- All links and navigation elements are functional

---

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
