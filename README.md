# Engelberg Property Investment Simulation

A comprehensive financial simulation tool for analyzing real estate investment opportunities in Engelberg, Switzerland.

## Features

- **Financial Modeling**: Complete cash flow analysis with detailed revenue and expense breakdowns
- **Excel Export**: Multi-sheet Excel workbook with comprehensive results
- **Interactive HTML Report**: Beautiful, interactive dashboard with charts and KPIs
- **Key Performance Indicators**: Cap rate, cash-on-cash return, debt coverage ratio, and more

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the base case analysis:

```bash
python run_base_case.py
```

This will generate:

- `base_case_results.xlsx` - Excel workbook with detailed results across multiple sheets
- `base_case_report.html` - Interactive HTML report with charts and visualizations

## Output Files

### Excel Workbook (`base_case_results.xlsx`)

Contains 5 sheets:

1. **KPIs** - Key performance indicators summary
2. **Revenue & Expenses** - Detailed income statement
3. **Rental Metrics** - Occupancy and rental statistics
4. **Financing** - Loan and equity details
5. **Assumptions** - All input parameters

### HTML Report (`base_case_report.html`)

Interactive dashboard featuring:

- Key Performance Indicators cards
- Financial summary table
- Revenue vs Expenses comparison charts
- Operating expenses breakdown (pie and bar charts)
- Cash flow waterfall chart
- KPI gauge charts (Cap Rate, Cash-on-Cash Return, Debt Coverage Ratio, Operating Expense Ratio)

## Base Case Parameters

- **Purchase Price**: CHF 1,300,000
- **Loan-to-Value**: 75%
- **Interest Rate**: 1.9% annually
- **Amortization Rate**: 1% of initial loan
- **Number of Owners**: 4
- **Owner Nights per Person**: 5 nights/year
- **Occupancy Rate**: 60%
- **Average Daily Rate**: CHF 280
- **Property Management Fee**: 25% of gross rental income

## Project Structure

```
.
├── simulation.py          # Core simulation logic and data classes
├── run_base_case.py       # Main script to run analysis and generate outputs
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Customization

To modify the base case parameters, edit the `create_base_case_config()` function in `simulation.py`.

## Dependencies

- `pandas` - Data manipulation and Excel export
- `openpyxl` - Excel file generation
- `plotly` - Interactive charts and visualizations
