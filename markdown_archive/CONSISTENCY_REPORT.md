# Consistency Verification Report

## Date: December 2024

## Summary
All scripts have been verified and updated to ensure complete consistency across:
- `run_base_case.py`
- `run_sensitivity_analysis.py`
- `run_monte_carlo.py`

## Verified Parameters

### Base Case Configuration
All scripts use `create_base_case_config()` from `simulation.py`:
- ✅ **Purchase Price**: 1,300,000 CHF
- ✅ **Interest Rate**: 1.3% (0.013)
- ✅ **LTV**: 75%
- ✅ **Amortization Rate**: 1.0%
- ✅ **Number of Owners**: 4
- ✅ **Management Fee**: 20%
- ✅ **Cleaning Cost per Stay**: 80 CHF
- ✅ **Average Length of Stay**: 1.7 nights

### Projection Parameters
All scripts use the same projection parameters:
- ✅ **Start Year**: 2026
- ✅ **Inflation Rate**: 2% (0.02)
- ✅ **Property Appreciation**: 2% (0.02)
- ✅ **Discount Rate (NPV)**: 4% (0.04)

### Calculation Methods
All scripts use the same calculation functions:
- ✅ `compute_annual_cash_flows()` - from `simulation.py`
- ✅ `compute_15_year_projection()` - from `simulation.py`
- ✅ `calculate_irrs_from_projection()` - from `simulation.py`
- ✅ `apply_sensitivity()` - from `simulation.py` (for variations)

## Fixes Applied

### 1. Interest Rate Documentation
- **Fixed**: Updated comments and descriptions from 1.9% to 1.3%
- **Files**: `run_sensitivity_analysis.py`, `run_monte_carlo.py`

### 2. Management Fee Documentation
- **Fixed**: Updated comments from 30% to 20%
- **Files**: `run_monte_carlo.py`

### 3. Discount Rate Documentation
- **Fixed**: Updated docstring from 5% to 4%
- **Files**: `run_sensitivity_analysis.py`, `run_monte_carlo.py`

### 4. IRR Calculation Consistency
- **Fixed**: Added `purchase_price` parameter to all `calculate_irrs_from_projection()` calls
- **Files**: `run_sensitivity_analysis.py`, `run_monte_carlo.py`
- **Impact**: Ensures Project IRR (unlevered) is calculated correctly

### 5. Property Appreciation Documentation
- **Fixed**: Updated HTML text from 1% to 2%
- **Files**: `run_monte_carlo.py`

## Architecture Compliance

All scripts follow the **Single Source of Truth** architecture:

1. ✅ **Base Case**: All scripts call `create_base_case_config()`
2. ✅ **Variations**: All scripts use `apply_sensitivity()` for parameter changes
3. ✅ **No Hardcoding**: No scripts create `BaseCaseConfig` directly
4. ✅ **Consistent Calculations**: All use the same calculation functions

## Verification Results

### Base Case Values (Verified)
```
Purchase Price: 1,300,000 CHF
Interest Rate: 1.30%
Management Fee: 20%
Annual Cash Flow: -4,240 CHF
Cash Flow per Owner: -1,060 CHF
```

### 15-Year Projection (Verified)
```
Year 1 (2026):
  Gross Income: 55,396 CHF
  Cash Flow per Owner: -1,060 CHF
  Loan Balance End: 965,250 CHF

Year 15 (2040):
  Gross Income: 73,094 CHF
  Cash Flow per Owner: 836 CHF
  Loan Balance End: 828,750 CHF
  Property Value: 1,715,322 CHF
```

### IRR Results (Verified)
```
Equity IRR (with sale): 6.68%
Equity IRR (without sale): -22.73%
Project IRR (with sale): 3.28%
Project IRR (without sale): -13.67%
```

### NPV (Verified with 4% discount rate)
```
NPV: 39,138 CHF
```

## Script Execution Status

All scripts execute successfully:
- ✅ `run_base_case.py` - Complete
- ✅ `run_sensitivity_analysis.py` - Complete
- ✅ `run_monte_carlo.py` - Complete

## Conclusion

All scripts are now **fully consistent** and use the same:
- Base case configuration
- Calculation methods
- Projection parameters
- IRR calculation approach

The codebase maintains a **single source of truth** architecture, ensuring all analyses are comparable and consistent.

