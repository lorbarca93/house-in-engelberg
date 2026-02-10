# Engelberg Property Investment Simulation

Financial modeling system for Swiss co-ownership vacation-rental investments (Engelberg focus), with deterministic and probabilistic analyses plus an interactive dashboard.

## Current Status (February 10, 2026)

- Active scenario set: `12` cases from `assumptions/`
- Dashboard views: `9`
- Data outputs per case: `7`
- Automated tests: `172 passed`
- System validation checks: `427 passed, 0 failed`

## What The Model Covers

- Deterministic base-case cash-flow and return modeling
- Balance-sheet vs cash-flow decomposition (equity build vs liquidity drag)
- Deterministic sensitivity analysis:
  - Equity IRR
  - Cash-on-cash
  - Monthly net cash flow
- Loan-structure sensitivity across SARON/fixed mixes with DSCR stress tests
- Monte Carlo simulation
- Monte Carlo sensitivity (NPV probability vs parameter changes)
- Scenario comparison across all configured cases

## Financial Logic and Calculation Order

Yearly operating flow (core ordering in `engelberg/core.py`):

1. Gross rental income (prorated for downtime months)
2. OTA platform fees
3. Net rental income
4. Cleaning cost (if separate)
5. Property management fee on revenue after OTA and cleaning
6. Tourist tax + VAT + fixed operating costs
7. Net operating income (NOI)
8. Debt service (interest + amortization)
9. Pre-tax cash flow
10. Tax shield from deductible interest
11. After-tax cash flow

Exit flow at sale:

1. Gross sale price
2. Selling costs (`selling_costs.total_rate`)
3. Capital gains tax (default `2%` on positive gain only)
4. Property transfer tax at sale (default `1.5%` on gross sale)
5. Net sale price
6. Net proceeds after loan payoff

Downtime modeling:

- Initial no-revenue ramp-up: default `3` months
- Recurring renovation no-revenue period: default `3` months every `5` years

## Quick Start

### 1) Install dependencies

```bash
# From repository root
pip install -r requirements.txt
```

### 2) Generate dashboard data (all cases)

Use this during normal iteration. It regenerates deterministic + Monte Carlo outputs and reuses existing Monte Carlo sensitivity files if they already exist.

```bash
python scripts/generate_all_data.py
```

### 3) (Optional) Regenerate Monte Carlo sensitivity in the same run

This is slower, but guarantees all Monte Carlo sensitivity JSON files are freshly produced.

```bash
python scripts/generate_all_data.py --include-mc-sensitivity
```

### 4) Run Monte Carlo sensitivity separately (recommended)

```bash
# Current assumptions file only
python scripts/analyze_monte_carlo_sensitivity.py

# Every assumptions file under assumptions/
python scripts/analyze_monte_carlo_sensitivity.py --all-cases

# Every case with a custom simulation count
python scripts/analyze_monte_carlo_sensitivity.py --all-cases --simulations 1500
```

### 5) Start the dashboard

```bash
cd website
python -m http.server 8080
```

Then open `http://localhost:8080/index.html`.

## CLI Scripts

| Script | Purpose |
| --- | --- |
| `scripts/analyze.py` | Single-case analysis runner |
| `scripts/generate_all_data.py` | Batch generation for all discovered cases |
| `scripts/analyze_monte_carlo_sensitivity.py` | Dedicated MC sensitivity runner |
| `scripts/validate_system.py` | Cross-file and cross-calculation validation |

Common commands:

```bash
# Run all analyses for the default assumptions file (assumptions/assumptions.json)
python scripts/analyze.py

# Run all analyses for a specific scenario
python scripts/analyze.py assumptions/assumptions_migros.json

# Run one analysis type only
python scripts/analyze.py --analysis base
python scripts/analyze.py --analysis sensitivity
python scripts/analyze.py --analysis monte_carlo
python scripts/analyze.py --analysis loan_structure_sensitivity
python scripts/analyze.py --analysis monte_carlo_sensitivity

# Increase Monte Carlo simulation count for the run
python scripts/analyze.py --simulations 5000
```

## Dashboard Views

1. `Simulation KPIs`
2. `Balance Sheet vs Cash Flow`
3. `Loan Structure Sensitivity`
4. `Model Sensitivity - Equity IRR`
5. `Model Sensitivity - Cash-on-Cash`
6. `Model Sensitivity - Monthly NCF`
7. `Monte Carlo`
8. `Monte Carlo Sensitivity`
9. `Scenario Comparison`

Horizon selector behavior:

- Visible: `base_case`, `balance_sheet_cashflow`, `sensitivity`
- Hidden: `loan_structure_sensitivity`, `sensitivity_coc`, `sensitivity_ncf`, `monte_carlo`, `monte_carlo_sensitivity`, `scenario_comparison`

## Scenario Catalog (from `website/data/cases_index.json`)

1. `base_case` - Base Case
2. `3_owners` - 3 Owners
3. `5_owners` - 5 Owners
4. `90day_restriction` - 90-Day Airbnb Restriction
5. `climate_risk` - Climate Risk Scenario
6. `early_exit` - Early Exit (Poor Performance)
7. `engelbergerstrasse53` - Engelbergerstrasse 53
8. `engelbergerstrasse53_145` - Engelbergerstrasse 53 (1.45%)
9. `engelbergerstrasse53_850_success` - Engelbergerstrasse 53 (850k Success)
10. `engelbergerstrasse53_longterm` - Engelbergerstrasse 53 (Long-Term Rental)
11. `interest_rate_spike` - Interest Rate Spike
12. `migros` - Migros Scenario

## Base Case Snapshot (Current Branch Data)

Source: `website/data/base_case_base_case_analysis.json`

- Equity IRR (with sale): `5.97%`
- Project IRR (with sale): `3.59%`
- MOIC: `2.58x`
- Annual pre-tax cash flow per owner: `CHF -3,019`
- Annual after-tax cash flow per owner: `CHF -2,076`
- Monthly after-tax cash flow per owner: `CHF -173`
- Payback period: `15 years`
- Year 1 operational months: `9` (`3` ramp-up months)

## Project Layout

```text
.
|-- engelberg/                # Core package (model + analysis)
|-- scripts/                  # CLI orchestration
|-- assumptions/              # Case assumptions JSON files
|-- website/
|   |-- index.html            # Dashboard UI
|   `-- data/                 # Generated analysis JSON
|-- tests/                    # Unit/integration/regression
|-- docs/                     # Technical documentation
|-- README.md
|-- QUICK_START.md
|-- CHANGELOG.md
`-- BUG_FIX_SUMMARY.md
```

## Quality Gates

Run before release or major changes:

```bash
python -m pytest -q
python scripts/validate_system.py
```

Expected currently:

- `172 passed`
- `427 passed, 0 failed`

## Documentation Map

- `QUICK_START.md`: operator runbook
- `CHANGELOG.md`: full historical timeline (plans + implementations)
- `BUG_FIX_SUMMARY.md`: quality and bug-fix history
- `docs/README.md`: complete docs index
- `docs/ARCHITECTURE.md`: system architecture and data flow
- `docs/SENSITIVITY_CALCULATIONS.md`: deterministic and MC sensitivity math
- `docs/MONTE_CARLO_ENGINE.md`: Monte Carlo internals
- `docs/WATERFALL_CHARTS.md`: balance-sheet and waterfall interpretation
- `docs/DEVELOPMENT.md`: developer workflow and contribution standards

## Troubleshooting

No case data in dashboard:

```bash
python scripts/generate_all_data.py
```

Check that `website/data/cases_index.json` exists and contains the generated cases list.

### Monte Carlo sensitivity is slow

Use separated execution:

```bash
python scripts/generate_all_data.py        # fast path (skips MC sensitivity regeneration)
python scripts/analyze_monte_carlo_sensitivity.py --all-cases
```

Lower simulation count while iterating:

```bash
python scripts/generate_all_data.py
python scripts/analyze_monte_carlo_sensitivity.py --all-cases --simulations 300
```

Full integrity check:

```bash
python scripts/validate_system.py
python -m pytest -q
```

---

Last updated: February 10, 2026
