# Waterfall Charts - Revenue vs Expenses

## Overview

The Waterfall (Revenue vs Expenses) view provides a visual cash flow bridge showing how gross rental income flows through various deductions to arrive at the final after-tax cash flow per owner.

## Chart Types

### 1. Yearly Waterfall

Shows annual values for all cash flow components:

```
Gross Rental Income
  v (- OTA Platform Fees)
Net Rental Income
  v (- Operating Expenses)
Net Operating Income (NOI)
  v (- Debt Service: Interest + Principal)
Pre-Tax Cash Flow
  v (+ Tax Savings from Interest Deduction)
After-Tax Cash Flow
```

### 2. Monthly Waterfall

Shows monthly values (annual / 12) for practical budgeting:

- Same structure as yearly waterfall
- All values divided by 12 for monthly perspective
- Useful for understanding monthly cash requirements

## Color Coding

- **Green bars**: Revenue items and positive adjustments (e.g., Gross Rental Income, Tax Savings)
- **Red bars**: Expense items and negative adjustments (e.g., OTA Fees, Operating Expenses, Debt Service)
- **Blue bars**: Cumulative totals at key stages (e.g., Net Rental Income, NOI, Pre-Tax CF, After-Tax CF)

## Data Source

Waterfall charts use data from the **base case analysis**:

- **Data file**: `website/data/{case}_base_case_analysis.json`
- **Data section**: `annual_results` (Year 1 values)
- **Alternative**: `projection[0]` if `annual_results` is not available

## Key Metrics Displayed

| Stage | Metric | Description |
|-------|--------|-------------|
| **Start** | Gross Rental Income | Total revenue from all bookings |
| **Stage 1** | Net Rental Income | After deducting OTA platform fees |
| **Stage 2** | Net Operating Income (NOI) | After deducting all operating expenses |
| **Stage 3** | Pre-Tax Cash Flow | After deducting debt service (interest + principal) |
| **Final** | After-Tax Cash Flow | After adding tax savings from interest deduction |

## Interpretation

### Why Waterfall Charts?

Waterfall charts are particularly useful for understanding:

1. **Where revenue goes**: See the impact of each expense category
2. **Biggest cash drains**: Identify which expenses have the most impact
3. **Tax benefit**: Visualize how tax savings improve cash flow
4. **Monthly budgeting**: Monthly view shows actual monthly cash requirements

### Example Insights

From Base Case waterfall:

- **OTA Fees**: Take ~15% of gross rental income (platform commissions)
- **Operating Expenses**: Consume most of the net rental income
- **Debt Service**: Largest single outflow (interest + principal payments)
- **Tax Savings**: Partially offset debt service through interest deduction
- **Final Result**: Negative cash flow, but you're building equity through principal payments

### Comparing Scenarios

Use waterfall charts to:

- Compare expense structures across scenarios (e.g., 3 owners vs 4 owners)
- See how different financing affects cash flow (e.g., higher LTV vs lower LTV)
- Understand impact of operational changes (e.g., higher occupancy, different pricing)

## Technical Details

### Implementation

**Location**: `website/index.html`, lines 5415-5533

**Function**: `ChartRenderer.renderWaterfall(data)`

**Features**:
- Robust error handling for missing or invalid data
- Currency formatting with CHF symbol
- Responsive layout for different screen sizes
- Plotly.js interactive features (zoom, hover, export)

### Error Handling

If cash flow data is missing or invalid:
- Displays: "No cash flow data available for this case."
- Prevents rendering empty/broken charts
- User-friendly error messaging

### Data Validation

The function checks for required fields:
- `gross_rental_income`
- `ota_platform_fees`
- `net_rental_income`
- `total_operating_expenses`
- `noi`
- `total_debt_service`
- `pre_tax_cash_flow_total`
- `tax_savings_total`
- `after_tax_cash_flow_total`

If any are missing or non-numeric, an error message is displayed.

## Usage Tips

1. **Start with yearly view**: Understand the full annual picture first
2. **Check monthly view**: See practical monthly cash requirements
3. **Compare stages**: Identify which stage has the biggest impact
4. **Use hover tooltips**: See exact values for each component
5. **Export chart**: Use Plotly toolbar to export as PNG for presentations

## Related Analyses

- **Base Case**: Shows detailed breakdowns for each component
- **Sensitivity Analysis**: Shows how parameters affect each stage
- **Scenario Comparison**: Compare waterfall structures across scenarios

---

**Created**: February 2, 2026
**Purpose**: Explain waterfall chart data and interpretation
**Status**: Production Ready
