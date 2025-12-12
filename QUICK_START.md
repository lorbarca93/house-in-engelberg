# 🚀 Engelberg Property Investment - Quick Start Guide

## ⚡ Run Analysis in One Command

### Unified Analysis Script

```bash
python analyze.py                              # All analyses for base case
python analyze.py assumptions/assumptions_migros.json      # All analyses for Migros
python analyze.py --analysis base              # Only base case
python analyze.py --analysis sensitivity       # Only sensitivity (all 3 types)
python analyze.py --analysis monte_carlo       # Only Monte Carlo
python analyze.py --simulations 5000           # Custom simulation count
python analyze.py --quiet                      # Minimal output
```

### Generate All Cases at Once

```bash
python generate_all_data.py  # Generates 9 cases × 5 analyses = 45+ files
```

### Validate System

```bash
python validate_system.py    # 285+ comprehensive checks
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

- 🔄 Switch between 9 cases (Base, Migros, 3/5/6 Owners, 90-Day Restriction, Climate Risk, Interest Rate Spike, Early Exit)
- 📈 View 5 analysis types:
  - **Model** - Base case KPIs and 15-year projection
  - **Sensitivity - Equity IRR** - Parameter impact on IRR
  - **Sensitivity - Cash-on-Cash** - Parameter impact on Year 1 yield
  - **Sensitivity - Monthly NCF** - Parameter impact on monthly cash
  - **Monte Carlo** - 10,000 probabilistic simulations with comprehensive statistics and 4 interactive charts
- 🎨 Interactive Plotly tornado charts with hover explanations
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
| **Property Appreciation**   | 4.0%/year  |
| **Discount Rate**           | 5.0%       |
| **Maintenance Reserve**     | 0.5%/year  |
| **Selling Costs @ Year 15** | 7.8% total |

### Selling Costs Breakdown

- **Broker Fee**: 3.0%
- **Notary Fees**: 1.5%
- **Transfer Tax**: 3.3% (Canton Obwalden)

---

## 📁 File Structure

### Core Scripts

| File                    | Purpose                                |
| ----------------------- | -------------------------------------- |
| `analyze.py`            | Unified analysis script (all analyses) |
| `core_engine.py`        | Calculation engine (1,250 lines)       |
| `monte_carlo_engine.py` | Monte Carlo simulation                 |
| `generate_all_data.py`  | Batch data generator                   |
| `validate_system.py`    | System validator (285+ checks)         |

### Configuration (9 scenarios)

| File                                               | Description                                                |
| -------------------------------------------------- | ---------------------------------------------------------- |
| `assumptions/assumptions.json`                     | Base case (6 owners, 70% LTV, 1.3% interest)               |
| `assumptions/assumptions_migros.json`              | Migros financing (60% LTV, 1.8%, no amort)                 |
| `assumptions/assumptions_3_owners.json`            | 3 owners scenario                                          |
| `assumptions/assumptions_5_owners.json`            | 5 owners scenario                                          |
| `assumptions/assumptions_6_owners.json`            | 6 owners scenario                                          |
| `assumptions/assumptions_90day_restriction.json`   | 90-day Airbnb restriction (25% occupancy)                  |
| `assumptions/assumptions_climate_risk.json`        | Climate change impact (winter -25%, summer +10% occupancy) |
| `assumptions/assumptions_interest_rate_spike.json` | Refinancing risk (1.3% → 3.5% at year 6)                   |
| `assumptions/assumptions_early_exit.json`          | Poor performance exit (40% occupancy, 6-year exit)         |

### Output

- `website/index.html` - Dynamic dashboard
- `website/data/*.json` - 45+ data files (9 cases × 5 analyses)

---

## 🔧 Modify Assumptions

Edit `assumptions/assumptions.json`:

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
    "property_appreciation_rate": 0.04,
    "discount_rate": 0.05,
    "selling_costs": {
      "total_rate": 0.078
    }
  }
}
```

Then regenerate:

```bash
python generate_all_data.py
```

---

## 📈 Sensitivity Analysis Overview

### Top 5 Most Impactful Parameters (Equity IRR)

1. **Property Appreciation** (±6.06% IRR impact)
2. **Interest Rate** (±2.91% IRR impact)
3. **Average Daily Rate** (±2.60% IRR impact)
4. **Maintenance Reserve** (±2.64% IRR impact)
5. **Loan-to-Value** (±1.32% IRR impact)

### Top 5 for Monthly Cash Flow

1. **Interest Rate** (largest CHF/month swing)
2. **Amortization Rate** (principal paydown hits cash)
3. **Average Daily Rate**
4. **Occupancy Rate**
5. **Purchase Price**

---

## 🎓 Understanding Negative Cash Flow

**Monthly Cash Flow: ~-CHF 350/month per owner**

This means you contribute ~CHF 350/month. Why?

### The Math:

```
Revenue:          CHF  41,610
- Expenses:       CHF  45,867
= NOI:            CHF  -4,257
- Debt Service:   CHF  20,930
= Cash Flow:      CHF -25,187
÷ 6 owners:       CHF  -4,198/year
÷ 12 months:      CHF    -350/month
```

### But You're Building Wealth:

```
Negative Cash:    -CHF   4,198/year
+ Equity Buildup: +CHF   1,517/year (amortization)
+ Appreciation:   +CHF  15,600/year (4% × CHF 390k share)
+ Personal Use:   +CHF     600/year (3 nights @ CHF 200)
= Economic Value: +CHF  13,519/year  ✅ POSITIVE!
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

Run 285+ comprehensive checks:

```bash
python validate_system.py
```

Expected output:

```
[SUCCESS] SYSTEM VALIDATION PASSED
[PASS] Passed:  285+
[FAIL] Failed:  0
```

---

**Created**: December 3, 2025  
**Last Updated**: December 9, 2025  
**Status**: Production Ready ✅  
**Validation**: 285+/285+ checks passing  
**Scenarios**: 9 investment cases available

**Questions?** See README.md for full documentation.
