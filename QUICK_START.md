# 🚀 Engelberg Property Investment - Quick Start Guide

## ⚡ Run Analysis in One Command

### Unified Analysis Script

```bash
python scripts/analyze.py                              # All analyses for base case
python scripts/analyze.py assumptions_migros.json      # All analyses for Migros
python scripts/analyze.py --analysis base              # Only base case
python scripts/analyze.py --analysis sensitivity       # Only sensitivity (all 3 types)
python scripts/analyze.py --analysis monte_carlo       # Only Monte Carlo
python scripts/analyze.py --simulations 5000           # Custom simulation count
python scripts/analyze.py --quiet                      # Minimal output
```

### Generate All Cases at Once

```bash
python scripts/generate_all_data.py  # Generates 5 cases × 5 analyses = 26 files
```

### Validate System

```bash
python scripts/validate_system.py    # 198 comprehensive checks
```

---

## 📊 View Results

**Start the server:**

```bash
cd website
python -m http.server 8080
```

**Open in browser**: http://localhost:8080/index.html

**Dashboard Features:**

- 🔄 Switch between 11 cases (Base, Migros, 3/5 Owners, Engelbergerstrasse 53 variants, and more)
- 📈 View 6 analysis types:
  - **Model** - Base case KPIs and 15-year projection
  - **Sensitivity - Equity IRR** - Dual tornado charts: Monthly After-Tax Cash Flow per Person and Equity IRR (15-year)
  - **Sensitivity - Cash-on-Cash** - Parameter impact on Year 1 yield
  - **Sensitivity - Monthly NCF** - Parameter impact on monthly cash
  - **Monte Carlo** - 1,000 probabilistic simulations
  - **Scenario Comparison** - Side-by-side comparison of all scenarios
- 🎨 Interactive Plotly tornado charts with:
  - Hover explanations with detailed information
  - Value annotations at bar ends showing final results
- 📋 Detailed data tables

---

## 🎯 Current Results (Base Case)

### Key Metrics

| Metric               | Value              |
| -------------------- | ------------------ |
| **Equity IRR (15Y)** | 4.63%              |
| **Project IRR**      | 2.53%              |
| **NPV @ 5%**         | -CHF 5,007         |
| **MOIC**             | 2.17×              |
| **Cash Flow/Owner**  | -CHF 2,870/year    |
| **Monthly NCF**      | -CHF 239/month     |
| **Payback Period**   | 15 years (at sale) |

### Economic Assumptions

| Parameter                   | Value      |
| --------------------------- | ---------- |
| **Inflation**               | 1.0%/year  |
| **Property Appreciation**   | 2.5%/year  |
| **Discount Rate**           | 5.0%       |
| **Maintenance Reserve**     | 0.5%/year  |
| **Selling Costs @ Year 15** | 7.8% total |

### Selling Costs Breakdown

- **Broker Fee**: 3.0%
- **Notary Fees**: 1.5%
- **Transfer Tax**: 3.3% (Canton Obwalden)

---

## 📁 File Structure

### Core Package Structure

| Location                                | Purpose                                    |
| --------------------------------------- | ------------------------------------------ |
| `engelberg/`                            | Main Python package                        |
| `engelberg/core.py`                     | Calculation engine (1,250+ lines)          |
| `engelberg/analysis.py`                 | Analysis orchestration (main entry point)  |
| `engelberg/model_sensitivity.py`        | Model Sensitivity analysis (deterministic) |
| `engelberg/model_sensitivity_ranges.py` | Model Sensitivity parameter ranges config  |
| `engelberg/mc_sensitivity.py`           | MC Sensitivity analysis (probabilistic)    |
| `engelberg/mc_sensitivity_ranges.py`    | MC Sensitivity parameter ranges config     |
| `engelberg/monte_carlo.py`              | Monte Carlo simulation (1,870+ lines)      |
| `scripts/analyze.py`                    | CLI entry point for analyses               |
| `scripts/generate_all_data.py`          | Batch data generator                       |
| `scripts/validate_system.py`            | System validator (198 checks)              |
| `assumptions/`                          | Assumptions files (10 cases)               |
| `tests/`                                | Test suite (unit, integration, regression) |

### Configuration (5 scenarios)

| File                        | Description                                  |
| --------------------------- | -------------------------------------------- |
| `assumptions.json`          | Base case (4 owners, 75% LTV, 1.3% interest) |
| `assumptions_migros.json`   | Migros financing (60% LTV, 1.8%, no amort)   |
| `assumptions_3_owners.json` | 3 owners scenario                            |
| `assumptions_5_owners.json` | 5 owners scenario                            |
| `assumptions_6_owners.json` | 6 owners scenario                            |

### Output

- `website/index.html` - Dynamic dashboard
- `website/data/*.json` - 26 data files

---

## 🔧 Modify Assumptions

Edit `assumptions.json`:

```json
{
  "financing": {
    "purchase_price": 1300000.0,
    "ltv": 0.75,
    "interest_rate": 0.013,
    "amortization_rate": 0.01,
    "num_owners": 4
  },
  "projection": {
    "inflation_rate": 0.01,
    "property_appreciation_rate": 0.025,
    "discount_rate": 0.05,
    "selling_costs": {
      "total_rate": 0.078
    }
  }
}
```

Then regenerate:

```bash
python scripts/generate_all_data.py
```

---

## 📈 Sensitivity Analysis Overview

### Top 5 Most Impactful Parameters (Equity IRR)

1. **Property Appreciation** (±4.09% IRR impact)
2. **Interest Rate** (±3.52% IRR impact)
3. **Average Daily Rate** (±2.94% IRR impact)
4. **Maintenance Reserve** (±2.93% IRR impact)
5. **Loan-to-Value** (±1.21% IRR impact)

### Top 5 for Monthly Cash Flow

1. **Interest Rate** (±CHF 406/month)
2. **Amortization Rate** (±CHF 406/month)
3. **Average Daily Rate** (±CHF 225/month)
4. **Occupancy Rate** (±CHF 160/month)
5. **Purchase Price** (±CHF 140/month)

---

## 🎓 Understanding Negative Cash Flow

**Monthly Cash Flow: -CHF 239/month per owner**

This means you contribute ~CHF 240/month. Why?

### The Math:

```
Revenue:          CHF  51,360
- Expenses:       CHF  40,413
= NOI:            CHF  10,946
- Debt Service:   CHF  22,426  (2× higher than NOI!)
= Cash Flow:      CHF -11,479
÷ 4 owners:       CHF  -2,870/year
÷ 12 months:      CHF    -239/month
```

### But You're Building Wealth:

```
Negative Cash:    -CHF   2,870/year
+ Equity Buildup: +CHF   2,437/year (amortization)
+ Appreciation:   +CHF   8,125/year (2.5% × CHF 325k share)
+ Personal Use:   +CHF   1,000/year (5 nights @ CHF 200)
= Economic Value: +CHF   8,692/year  ✅ POSITIVE!
```

---

## ⚠️ Key Metrics Explained

| Metric           | Description                                     |
| ---------------- | ----------------------------------------------- |
| **Equity IRR**   | Return on your equity investment over 15 years  |
| **Project IRR**  | Return if you bought with 100% cash (no debt)   |
| **Cash-on-Cash** | Year 1 cash flow ÷ Initial equity               |
| **Monthly NCF**  | Actual CHF hitting your bank account monthly    |
| **NPV**          | Present value of all cash flows at 5% discount  |
| **MOIC**         | Total cash returned ÷ Initial investment        |
| **Payback**      | Years until cumulative cash flow turns positive |

---

## 🔍 Validation

Run 198 comprehensive checks:

```bash
python scripts/validate_system.py
```

Expected output:

```
[SUCCESS] SYSTEM VALIDATION PASSED
[PASS] Passed:  198
[FAIL] Failed:  0
```

---

**Created**: December 3, 2025  
**Last Updated**: January 26, 2026  
**Status**: Production Ready ✅  
**Validation**: 198/198 checks passing

**Questions?** See README.md for full documentation.
