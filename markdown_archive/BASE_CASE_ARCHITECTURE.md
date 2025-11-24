# Base Case Architecture - Single Source of Truth

## ⚠️ CRITICAL: Base Case Discipline

This codebase follows a **strict single source of truth** architecture. The base case scenario is defined **ONCE** in `simulation.py` and **ALL** other analyses must reference it.

## Architecture Principles

### 1. Base Case Definition
- **Location**: `simulation.py` → `create_base_case_config()`
- **Purpose**: Defines the single, authoritative base case scenario
- **Usage**: Called by `run_base_case.py` to generate the primary analysis

### 2. Analysis Scripts Must Reference Base Case
All analysis scripts (`run_sensitivity_analysis.py`, `run_monte_carlo.py`, etc.) **MUST**:
1. Call `create_base_case_config()` to get the base case
2. Use `apply_sensitivity()` to create variations
3. **NEVER** create their own base case configurations

### 3. Parameter Variations
- **Function**: `simulation.py` → `apply_sensitivity()`
- **Purpose**: Creates modified configurations from the base case
- **Preserves**: All base case parameters except those explicitly changed
- **Handles**: Seasonal parameters, financing, expenses, rental parameters

## File Structure

```
simulation.py
├── create_base_case_config()     ← SINGLE SOURCE OF TRUTH
└── apply_sensitivity()            ← Creates variations from base case

run_base_case.py
└── main()
    └── create_base_case_config()  ← Loads base case
    └── compute_annual_cash_flows()
    └── compute_15_year_projection()

run_sensitivity_analysis.py
└── main()
    └── create_base_case_config()  ← Loads base case
    └── apply_sensitivity()        ← Creates variations
    └── sensitivity_*() functions

run_monte_carlo.py
└── main()
    └── create_base_case_config()  ← Loads base case
    └── apply_sensitivity()        ← Creates variations
    └── run_monte_carlo_simulation()
```

## Rules for Adding New Analyses

When creating a new analysis script:

1. ✅ **DO**: Import and call `create_base_case_config()`
2. ✅ **DO**: Use `apply_sensitivity()` for parameter variations
3. ✅ **DO**: Reference base case results for comparison
4. ❌ **DON'T**: Create new `BaseCaseConfig` objects directly
5. ❌ **DON'T**: Define alternative base case parameters
6. ❌ **DON'T**: Hardcode configuration values

## Example: Correct Pattern

```python
from simulation import create_base_case_config, apply_sensitivity

# ✅ CORRECT: Load base case
base_config = create_base_case_config()

# ✅ CORRECT: Create variation
modified_config = apply_sensitivity(
    base_config,
    occupancy=0.6,
    daily_rate=350
)
```

## Example: Incorrect Pattern

```python
# ❌ WRONG: Don't create base case directly
config = BaseCaseConfig(
    financing=FinancingParams(...),
    rental=RentalParams(...),
    expenses=ExpenseParams(...)
)

# ❌ WRONG: Don't define alternative base case
def my_custom_base_case():
    return BaseCaseConfig(...)
```

## Benefits

1. **Consistency**: All analyses use the same base assumptions
2. **Maintainability**: Change base case once, all analyses update
3. **Traceability**: Easy to see what differs from base case
4. **Reliability**: No risk of inconsistent assumptions across analyses

## Verification

To verify your analysis follows this pattern:

1. Check that it calls `create_base_case_config()`
2. Check that it uses `apply_sensitivity()` for variations
3. Check that it doesn't create `BaseCaseConfig` directly
4. Check that it doesn't define alternative base case functions

## Current Status

✅ **Base Case**: Defined in `simulation.py`
✅ **Sensitivity Analysis**: Uses base case + `apply_sensitivity()`
✅ **Monte Carlo**: Uses base case + `apply_sensitivity()`
✅ **Seasonal Parameters**: Preserved by `apply_sensitivity()`

