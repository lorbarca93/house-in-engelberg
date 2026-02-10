# Bug Fix and Quality Summary

This document tracks major reliability, correctness, and quality hardening work.

## Scope

- Runtime safety fixes
- Calculation correctness fixes
- Data consistency and export integrity checks
- Cross-script and cross-output validation coverage

---

## 2026-02-02 Audit Hardening

### Fixed

1. Bare exception handling in `engelberg/core.py`

- Issue: `except:` could hide critical failures (`SystemExit`, `KeyboardInterrupt`).
- Fix: replaced with specific numeric-error exceptions.
- Impact: safer failure behavior and easier debugging.

2. Overly broad exception handling in `engelberg/model_sensitivity.py`

- Issue: broad catch without context obscured root causes.
- Fix: narrowed exception types and added warning context.
- Impact: failures remain non-fatal but observable.

3. Missing explicit file encoding in `scripts/validate_system.py`

- Issue: implicit encoding can break on Windows and mixed locale environments.
- Fix: standardized UTF-8 explicit reads.
- Impact: deterministic file handling across environments.

### Validation at the time

- Unit/integration tests passed.
- System validation checks passed.

---

## 2026-02-10 Consistency and Integration Hardening

### Added

1. Cross-script consistency suite (`tests/integration/test_cross_script_consistency.py`)

- Verifies `cases_index.json` integrity and linked file existence.
- Verifies assumptions-to-export consistency.
- Verifies accounting identities in base outputs:
  - `debt_service = interest + amortization`
  - `cash_flow_after_debt_service = NOI - debt_service`
  - owner-level after-tax rollups
- Verifies cross-analysis consistency (sensitivity/coc/ncf/loan structure).
- Verifies script-level parity between:
  - `engelberg.analysis.main()`
  - `scripts.generate_all_data.generate_case_data()`
- Uses stochastic tolerance rules for Monte Carlo comparisons.

2. Loan structure integration coverage (`tests/integration/test_loan_structure_sensitivity.py`)

- Checks required scenario presence.
- Checks tranche share normalization.
- Checks stress fields and fixed-only DSCR behavior.
- Checks recommendation and ranking consistency.

### Validation baseline now

- `python -m pytest -q` -> `172 passed`
- `python scripts/validate_system.py` -> `427 passed, 0 failed`

---

## Quality Principles Enforced

- No bare `except:` in core math paths
- Explicit UTF-8 file operations in validation and export pathways
- Output identity checks between related metrics
- Backward-compatible behavior where legacy single-rate financing is still supported
- Cross-entrypoint parity checks to prevent script drift

---

## Remaining Risk Areas to Monitor

1. Monte Carlo reproducibility across environments

- Controlled through tolerance-based assertions, not strict deterministic equality.

2. Stale generated data artifacts

- Some checks validate structure/consistency, but teams should regenerate data after model changes.

3. Documentation drift vs generated artifacts

- Keep `README.md`, `QUICK_START.md`, and `CHANGELOG.md` synchronized with regeneration and validation runs.

---

Last updated: February 10, 2026

