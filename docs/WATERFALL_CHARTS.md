# Waterfall and Wealth-Bridge Views

This guide covers two related dashboard perspectives:

1. Base-case cash-flow waterfall
2. Balance-sheet-vs-cash-flow wealth bridge

Both are designed to explain why cash flow can be negative while equity still builds.

## 1) Base Cash-Flow Waterfall

Source: `ChartRenderer.renderBaseCase()` in `website/index.html`

### Purpose

Show how gross revenue is transformed into after-tax owner cash flow.

### Bridge sequence

1. Gross rental income
2. OTA fees
3. Operating costs
4. Debt service
5. Tax shield
6. After-tax cash flow

### Monthly owner bridge

A monthly-per-owner waterfall is also rendered to support liquidity planning.

### Interpretation

- Large negative debt-service bars indicate financing burden.
- Tax shield partially offsets financing cost.
- Final monthly after-tax value is the practical affordability signal.

## 2) Balance Sheet vs Cash Flow Page

Source: `ChartRenderer.renderBalanceSheetCashFlow()` in `website/index.html`

### Purpose

Provide a second lens for the same investment:

- Liquidity lens: monthly/annual cash drag
- Balance-sheet lens: equity build from amortization + appreciation

### Year 1 KPI block

Per owner:

- Monthly after-tax cash flow
- Monthly debt service
- Monthly operating expenses
- Year 1 net wealth change
- Year 1 equity build

### Wealth decomposition logic (first 5 years)

For each year:

- after-tax cash flow per owner
- amortization equity per owner
- appreciation equity per owner
- net wealth delta per owner
- cumulative wealth per owner

### Main charts

1. Year 1 cash-to-wealth waterfall
2. First-5-years stacked wealth components + cumulative line
3. Cumulative wealth trajectory
4. Property value vs loan balance vs equity trajectory

### Key interpretation metrics

- Cash drag coverage: how much Year 1 cash drag is offset by equity build
- First positive cumulative wealth year (if reached)
- 5-year equity mix: amortization share vs appreciation share

## 3) Data Inputs Used

Primary data source:

- `website/data/{case}_base_case_analysis.json`

Key fields consumed:

- `annual_results.*`
- `projection_15yr[]` or horizon-resolved `by_horizon[h].projection[]`
- `config.financing.*`

## 4) Horizon Behavior

- This page is horizon-aware.
- When `by_horizon` data is available, selected horizon drives projection slicing and derived 5-year windows.

## 5) Common Misreadings to Avoid

1. Negative cash flow does not imply negative wealth creation.

- Amortization and appreciation can offset or exceed cash drag over time.

2. Year 1 outcome alone is incomplete.

- Ramp-up and renovation downtime can distort Year 1 liquidity.
- Multi-year wealth bridge is required for full interpretation.

3. Equity creation is not purely appreciation.

- Loan principal reduction is an explicit, mechanical equity driver.

## 6) Decision Use

Use this page before financing decisions to answer:

- Is monthly liquidity burden acceptable?
- Is the burden compensated by sufficient equity build?
- How long before cumulative wealth turns positive for each owner?

Then pair findings with:

- `Loan Structure Sensitivity`
- deterministic and Monte Carlo sensitivity pages

---

Last updated: February 10, 2026

