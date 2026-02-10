# Development Guide

## Prerequisites

- Python `3.8+`
- `pip`
- Browser for dashboard verification

## Local Setup

1. Install runtime dependencies:

```bash
pip install -r requirements.txt
```

2. Install dev dependencies:

```bash
pip install -r requirements-dev.txt
```

3. Validate environment:

```bash
python -m pytest -q
python scripts/validate_system.py
```

Expected baseline:

- `172 passed`
- `427 passed, 0 failed`

## Core Workflow

1. Update modeling or UI code.
2. Add/update tests.
3. Run focused tests first.
4. Run full test suite.
5. Regenerate data if output schema or calculations changed.
6. Run system validation.
7. Verify dashboard behavior manually.
8. Update documentation and changelog.

## High-Value Commands

Run all tests:

```bash
python -m pytest -q
```

Run only integration tests:

```bash
python -m pytest -q tests/integration
```

Run cross-consistency suite:

```bash
python -m pytest -q tests/integration/test_cross_script_consistency.py
```

Run full validator:

```bash
python scripts/validate_system.py
```

Regenerate data:

```bash
python scripts/generate_all_data.py
```

Regenerate MC sensitivity only:

```bash
python scripts/analyze_monte_carlo_sensitivity.py --all-cases --simulations 1000
```

## Code Areas and Ownership

- `engelberg/core.py`
  - primary financial logic and export contract
- `engelberg/analysis.py`
  - orchestration and CLI-facing analysis entrypoints
- `engelberg/model_sensitivity*.py`
  - deterministic sensitivity
- `engelberg/monte_carlo.py`
  - simulation engine
- `engelberg/mc_sensitivity*.py`
  - probabilistic sensitivity
- `website/index.html`
  - all dashboard rendering and UX logic
- `scripts/*.py`
  - execution orchestration and validation

## Test Strategy

### Unit tests

Use for:

- formula correctness
- dataclass behavior
- edge-case math

### Integration tests

Use for:

- end-to-end analysis output shape
- cross-module behavior
- script entrypoint consistency

### Regression tests

Use for:

- known-value guardrails
- drift detection

## Adding Features Safely

### Add new analysis output

1. Add computation function.
2. Add JSON export mapping.
3. Wire script orchestration.
4. Wire dashboard loading and renderer.
5. Add tests:
  - output schema
  - numerical sanity
  - integration path
6. Add validator checks.
7. Update docs.

### Add new assumptions field

1. Parse in `load_assumptions_from_json()` and `create_base_case_config()`.
2. Validate type/range and default behavior.
3. Propagate to compute functions.
4. Expose in exports where relevant.
5. Add unit and integration tests.

### Add a new dashboard page

1. Add menu item with `data-analysis="..."`.
2. Add data loader route in `DataManager.loadCaseData()`.
3. Add render function in `ChartRenderer`.
4. Add controller dispatch in `Controller.loadAnalysis()`.
5. Define horizon visibility behavior in `HorizonResolver`.
6. Add validator presence checks.

## Data and Consistency Rules

- Always treat `assumptions/*.json` as source of truth.
- Keep `cases_index.json` synchronized with generated outputs.
- Preserve accounting identities in output:
  - debt service decomposition
  - NOI to cash-flow linkage
  - owner-level after-tax rollups
- For Monte Carlo comparisons across flows, use tolerance-based checks (stochastic).

## Quality Checklist Before Push

- `python -m pytest -q` passes
- `python scripts/validate_system.py` passes
- Regenerated outputs when schema/calculations changed
- Dashboard loads and renders for at least:
  - one base case
  - one non-base scenario
  - loan structure page
  - balance-sheet vs cash-flow page
- Documentation updated (`README`, `QUICK_START`, `CHANGELOG`, relevant `docs/*`)

## Troubleshooting

### Dashboard shows missing data

- Run `python scripts/generate_all_data.py`
- Verify `website/data/cases_index.json`
- Confirm referenced files exist

### Tests fail after schema changes

- Update integration assertions and fixtures
- Re-run cross-consistency suite
- Ensure export keys remain backward-compatible where required

### MC sensitivity too slow during development

- Lower simulations for iteration:

```bash
python scripts/analyze_monte_carlo_sensitivity.py --all-cases --simulations 300
```

### Cross-script mismatch detected

- Compare outputs from:
  - `engelberg.analysis.main()`
  - `scripts.generate_all_data.generate_case_data()`
- Use `tests/integration/test_cross_script_consistency.py` as reference contract.

---

Last updated: February 10, 2026

