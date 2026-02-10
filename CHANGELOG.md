# Changelog

This document is the full historical log of plans, implementations, and outcomes for the Engelberg model.

Format per entry:

- `Plan / Intent`: Why the change was requested.
- `Implementation`: What was changed in code, data, and UI.
- `Outcome / Validation`: How the change was verified or what it enabled.

---

## [2025-01-XX] - Chart Library Upgrade (ApexCharts Era)

### Plan / Intent

- Improve report visual quality and interactivity beyond the original embedded chart setup.
- Deliver presentation-ready visuals for stakeholders.

### Implementation

- Introduced ApexCharts-driven chart rendering in the historical report flow.
- Updated chart styles, tooltips, currency formatting, and visual hierarchy.
- Added smoother interactions (hover, zoom, and clearer legends).

### Outcome / Validation

- Reports became easier to read and more suitable for investor communication.
- Established a pattern of chart-driven storytelling used in later dashboard work.

---

## [2025-01-XX] - Base Case Enhancements (Inflation, Appreciation, IRR, KPI clarity)

### Plan / Intent

- Fix KPI visualization issues.
- Add realistic long-horizon economics (inflation + appreciation).
- Introduce industry-standard return metrics.

### Implementation

- Added inflation and property appreciation support to projection logic.
- Added IRR calculations with and without sale.
- Expanded KPI and IRR reporting in generated outputs.
- Improved layout of KPI visual components.

### Outcome / Validation

- Long-term investment interpretation became materially stronger.
- Return metrics became comparable with alternative investment opportunities.

---

## [2025-01-XX] - Sensitivity Analysis Module (Initial large sensitivity suite)

### Plan / Intent

- Build structured sensitivity analysis around key operating, cost, and financing levers.
- Produce numeric and visual outputs that support decision-making.

### Implementation

- Implemented broad sensitivity scenarios for occupancy, ADR, costs, financing, and usage assumptions.
- Added export/report pathways for sensitivity results.

### Outcome / Validation

- Established parameter-impact ranking workflow that later evolved into tornado-style views.

---

## [2025-01-XX] - Base Case Update (Management fee model + 15-year projection)

### Plan / Intent

- Update operating-fee treatment to match manager contract logic.
- Extend analysis horizon from static annual view to 15-year performance.

### Implementation

- Updated property management fee assumptions and cleaning treatment.
- Added 15-year projection mechanics and debt amortization tracking.
- Extended output/report logic with long-term tables and charts.

### Outcome / Validation

- Model shifted from Year 1-only interpretation to lifecycle-level interpretation.

---

## [2025-12-01] - Dynamic Single-Page Dashboard Redesign

### Plan / Intent

- Move from many static reports to one interactive dashboard.
- Allow users to switch case and analysis instantly.

### Implementation

- Introduced single-page `website/index.html` with state-based rendering.
- Added `website/data/` JSON-driven architecture.
- Added centralized batch generation and case indexing model.
- Retired legacy static multi-report files.

### Outcome / Validation

- Large UX improvement: case and analysis switching became immediate.
- Clear separation emerged between modeling layer and rendering layer.

---

## [2025-12-03] - Code Consolidation and Monthly NCF Sensitivity

### Plan / Intent

- Reduce duplicated logic.
- Add explicit monthly net cash flow sensitivity perspective.

### Implementation

- Consolidated analysis pathways.
- Added dedicated monthly NCF sensitivity export and rendering pathway.

### Outcome / Validation

- Better maintainability and clearer sensitivity framing for owner affordability.

---

## [2025-12-03] - Tornado Chart Harmonization and Cleanup

### Plan / Intent

- Improve readability and consistency of tornado outputs.

### Implementation

- Harmonized tornado visuals and ordering conventions.
- Removed stale visual/report artifacts.

### Outcome / Validation

- Cross-analysis comparisons became easier and less error-prone.

---

## [2026-01-26] - Package Structure Reorganization

### Plan / Intent

- Reorganize project into a cleaner package-oriented architecture.
- Enable scalable module growth.

### Implementation

- Consolidated modeling logic under `engelberg/` package.
- Standardized script entry points in `scripts/`.
- Updated imports, paths, and integration points.

### Outcome / Validation

- Better modularity and clearer dependency structure.
- Enabled later module split and advanced testing work.

---

## [2026-01-26] - System Verification, Cleanup, and Documentation Update

### Plan / Intent

- Increase repository hygiene and consistency.

### Implementation

- Cleanup of stale files and inconsistencies.
- Expanded verification and documentation alignment.

### Outcome / Validation

- Lower maintenance friction and fewer hidden integration issues.

---

## [2026-01-26] - Tax Treatment Refinement and Tax Savings Integration

### Plan / Intent

- Improve realism of after-tax cash flow calculations.

### Implementation

- Refined tax treatment to ensure interest-based tax shield is integrated into cash flow outputs.
- Added explicit tax fields in annual/projection outputs.

### Outcome / Validation

- After-tax metrics became first-class outputs instead of side calculations.

---

## [2026-01-26] - After-Tax Cash Flow Model Sensitivity

### Plan / Intent

- Show how drivers impact both long-term returns and owner cash burden.

### Implementation

- Added dual-metric sensitivity framing for IRR plus after-tax cash flow.
- Enhanced sensitivity outputs to support dual-axis interpretation.

### Outcome / Validation

- Decisions can now balance return optimization vs affordability constraints.

---

## [2026-01-26] - Scenario Comparison Page and Enhanced Tornado Context

### Plan / Intent

- Add cross-scenario navigation and improve interpretation clarity.

### Implementation

- Added scenario comparison workflow in dashboard.
- Improved explanatory context in sensitivity views.

### Outcome / Validation

- Faster cross-case decision loops and clearer scenario storytelling.

---

## [2026-01-26] - Monte Carlo Sensitivity and Naming Alignment

### Plan / Intent

- Add a probabilistic sensitivity layer (beyond deterministic tornado analysis).

### Implementation

- Implemented MC sensitivity: parameter sweeps where each point runs Monte Carlo and tracks NPV>0 probability.
- Aligned naming and output conventions across analyses.

### Outcome / Validation

- Added risk-adjusted sensitivity viewpoint for parameter prioritization.

---

## [2026-01-26] - Module Separation (Model Sensitivity vs MC Sensitivity)

### Plan / Intent

- Separate deterministic and probabilistic sensitivity modules for maintainability.

### Implementation

- Split into dedicated modules:
  - `engelberg/model_sensitivity.py`
  - `engelberg/model_sensitivity_ranges.py`
  - `engelberg/mc_sensitivity.py`
  - `engelberg/mc_sensitivity_ranges.py`
- Kept backward-compatible exports through `engelberg.analysis`.

### Outcome / Validation

- Cleaner module ownership and easier targeted testing.

---

## [2026-01-28] - Calculation Rigor and Monte Carlo Engine Enhancements

### Plan / Intent

- Tighten economic logic and improve Monte Carlo realism.

### Implementation

- Standardized fee logic: management fee base = revenue after platform and cleaning costs.
- Expanded stochastic parameter set and improved distribution calibration.
- Added time-varying AR(1)-style inflation/appreciation behavior in MC engine.
- Added event modeling (maintenance events, market shocks, refinancing opportunities).
- Updated projection logic for consistency under shocks and variable occupancy/rates.

### Outcome / Validation

- Better consistency between deterministic and stochastic pathways.
- Improved scenario realism under uncertainty.

---

## [2026-02-02] - Ramp-Up, Renovation Downtime, Waterfall Views, and Robustness Fixes

### Plan / Intent

- Reflect no-revenue startup periods and planned renovation outages.
- Improve explanation of cash-flow bridges.
- Fix reliability issues and horizon UX confusion.

### Implementation

- Added ramp-up period modeling and recurring renovation downtime modeling.
- Added operational/downtime metadata to annual and projection outputs.
- Introduced waterfall visual pathways and improved horizon visibility rules by analysis type.
- Fixed broad/bare exception handling patterns.
- Standardized explicit UTF-8 file encoding in validation pathways.

### Outcome / Validation

- Year 1 and periodic downtime behavior became explicit and measurable.
- Dashboard navigation and interpretation became more predictable.

---

## [2026-02-09] - Documentation and Workflow Clarification Refresh

### Plan / Intent

- Align documentation with the then-current code and operating workflow.

### Implementation

- Updated top-level docs and technical docs.
- Clarified fast-path vs slow-path generation (`generate_all_data.py` vs standalone MC sensitivity runner).

### Outcome / Validation

- Reduced operator confusion for routine data refresh cycles.

---

## [2026-02-10] - Financing Structure Expansion, Sale Taxes, New Decision Pages, and Cross-Consistency Testing

### Plan / Intent

- Model realistic financing strategy tradeoffs for debt-service control.
- Add sale-stage taxes explicitly.
- Reflect startup and recurring renovation downtime in all analysis paths.
- Add a decision view separating liquidity from wealth creation.
- Add stronger cross-script and cross-output consistency tests.

### Implementation

Core engine:

- Added tranche-capable financing schema:
  - `loan_tranches` with `fixed` and `saron` support
  - `saron_base_rate`
  - stress policy block (`saron_shocks_bps`, DSCR thresholds)
- Added blended tranche interest calculations and per-tranche annual interest outputs.
- Added SARON shock stress evaluation and stress pass/fail outputs.
- Added sale taxes in IRR/exit logic:
  - `capital_gains_tax_rate` (default `2%` on positive gain)
  - `property_transfer_tax_sale_rate` (default `1.5%` on gross sale)
- Integrated downtime schedule support end-to-end:
  - initial ramp-up months
  - recurring renovation downtime months every configured frequency

Analysis layer:

- Added `run_loan_structure_sensitivity_analysis()` with scenario set:
  - `100% SARON`
  - `100% Fixed 10Y`
  - `Staggered Fixed`
  - `Mixed 50/50`
  - `Mixed 60/40 laddered`
  - `Mixed 70/30`
- Added ranking and recommendation logic with stress gating.
- Added 5-year wealth decomposition outputs by scenario.

Dashboard/UI:

- Added `Balance Sheet vs Cash Flow` page:
  - Year-1 cash-to-wealth bridge waterfall
  - 5-year wealth decomposition charts
  - cumulative wealth and equity trajectory views
- Added `Loan Structure Sensitivity` page:
  - cash flow, DSCR stress, rate-vs-IRR, and wealth decomposition visuals
  - narrative guidance and recommendation context

Automation/data:

- Updated batch generation to include loan-structure outputs for all cases.
- Updated `cases_index.json` to include `loan_structure_sensitivity` data references.

Testing:

- Added loan-structure integration tests.
- Added `tests/integration/test_cross_script_consistency.py` to validate:
  - assumptions-to-output consistency
  - cross-analysis identity checks
  - script entry-point consistency (`analysis.main` vs `generate_case_data`)
  - stochastic tolerance-aware MC consistency rules

### Outcome / Validation

- Model now supports mixed SARON/fixed financing in core calculations and reporting.
- Sale taxes are included explicitly at disposition.
- Downtime assumptions are modeled consistently in annual and projection outputs.
- New pages provide better decision framing: short-term liquidity vs medium-term equity creation.
- Validation baseline reached:
  - `172 passed` tests
  - `427 passed, 0 failed` system checks

---

## Current Baseline (Reference)

As of February 10, 2026:

- `12` active cases
- `9` dashboard views
- `7` analysis outputs per case
- Full coverage across deterministic, probabilistic, financing-structure, and scenario-comparison workflows


