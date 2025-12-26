# 🚀 Engelberg Property Investment - Quick Start Guide

## ⚡ Run Analysis in One Command

### Unified Analysis Script

```bash
python analyze.py                              # All analyses for base case
python analyze.py assumptions_migros.json      # All analyses for Migros
python analyze.py --analysis base              # Only base case
python analyze.py --analysis sensitivity       # Only sensitivity (all 3 types)
python analyze.py --analysis monte_carlo       # Only Monte Carlo
python analyze.py --simulations 5000           # Custom simulation count
python analyze.py --quiet                      # Minimal output
```

### Generate All Cases at Once

```bash
python generate_all_data.py  # Generates 5 cases × 5 analyses = 26 files
```

### Validate System

```bash
python validate_system.py    # 198 comprehensive checks
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

- 🔄 Switch between 11 cases (Base, 900K House, SARON Mortgage, Migros, 3/4/5 Owners, 90-Day Restriction, Climate Risk, Early Exit, Interest Rate Spike)
- 📈 View 3 analysis types:
  - **Model** - Base case KPIs and 15-year projection
  - **sensitivity.html** - Monthly NCF sensitivity analysis with tornado charts
  - **monte_carlo.html** - Monte Carlo risk analysis with distribution charts
- 🎨 Interactive Plotly tornado charts with hover explanations
- 📋 Detailed data tables

---

## 🎯 Current Results (Base Case)

### Key Metrics

| Metric                | Value              |
| --------------------- | ------------------ |
| **Equity IRR (15Y)**  | 6.2%               |
| **After-tax IRR**     | 6.9%               |
| **Project IRR**       | 3.7%               |
| **NPV @ 5%**          | CHF 32,009         |
| **MOIC**              | 3.23×              |
| **Cash Flow/Owner**   | -CHF 3,013/year    |
| **Tax Benefit/Owner** | CHF 3,572/year     |
| **After-tax CF**      | -CHF 2,120/year    |
| **Payback Period**    | 15 years (at sale) |

### Economic Assumptions

| Parameter                   | Value      |
| --------------------------- | ---------- |
| **Inflation**               | 1.0%/year  |
| **Property Appreciation**   | 3.0%/year  |
| **Discount Rate**           | 4.0%       |
| **Maintenance Reserve**     | 0.4%/year  |
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
| `validate_system.py`    | System validator (198 checks)          |

### New Scenarios Added

**SARON Variable Rate Mortgage** (`assumptions_saron_mortgage.json`)

- Variable interest rate using Swiss SARON benchmark + 0.9% spread
- Rate fluctuates between 1.5% and 2.2% over 15 years
- Tests interest rate risk vs. potential savings

**900K House Price** (`assumptions_900k_house.json`)

- More affordable CHF 900,000 property (vs CHF 1.3M base)
- Same financing structure, lower equity requirement
- Tests impact of property price on returns

**90-Day Airbnb Restriction** (`assumptions_90day_restriction.json`)

- Local regulation limits Airbnb to 90 days/year
- Increased owner usage (30 nights vs 5 per owner)
- Tests regulatory risk impact

**Climate Risk Scenario** (`assumptions_climate_risk.json`)

- Warmer winters: -25% winter occupancy
- Warmer summers: +10% summer occupancy
- Tests climate change impact on tourism patterns

**Early Exit Scenario** (`assumptions_early_exit.json`)

- Poor performance leads to 6-year exit (vs 15-year hold)
- Tests downside risk and early termination costs

**Interest Rate Spike** (`assumptions_interest_rate_spike.json`)

- Rate increases from 1.3% to 3.5% after 5 years
- Tests refinancing risk and rate shock scenarios

### Configuration (11 scenarios)

| File                                   | Description                                  |
| -------------------------------------- | -------------------------------------------- |
| `assumptions.json`                     | Base case (4 owners, 75% LTV, 1.3% interest) |
| `assumptions_900k_house.json`          | 900K property (4 owners, 75% LTV, 1.3%)      |
| `assumptions_saron_mortgage.json`      | SARON variable rate (4 owners, 75% LTV)      |
| `assumptions_migros.json`              | Migros financing (60% LTV, 1.8%, no amort)   |
| `assumptions_3_owners.json`            | 3 owners scenario                            |
| `assumptions_4_owners.json`            | 4 owners scenario (matches base case)        |
| `assumptions_5_owners.json`            | 5 owners scenario                            |
| `assumptions_90day_restriction.json`   | 90-day Airbnb limit (4 owners)               |
| `assumptions_climate_risk.json`        | Climate change impact (4 owners)             |
| `assumptions_early_exit.json`          | 6-year exit scenario (4 owners)              |
| `assumptions_interest_rate_spike.json` | Interest rate spike (4 owners)               |

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
python generate_all_data.py
```

---

## 📈 Sensitivity Analysis Overview

### Monthly Net Cash Flow per Owner Sensitivity

This analysis shows how different parameters affect your **monthly cash flow per owner**. This is the most relevant metric for ongoing investment viability, as it represents the actual money you need to contribute each month to keep the investment running.

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
Revenue:          CHF  48,783
- Expenses:       CHF  29,765
= NOI:            CHF  19,018
- Debt Service:   CHF  22,696
= Cash Flow:      CHF  -3,678
+ Tax Benefits:   CHF   3,572  (from interest deduction)
= After-tax CF:   CHF    -106
÷ 4 owners:       CHF     -27/year per owner (after-tax)
```

### But You're Building Wealth:

```
Pre-tax Cash:     -CHF   3,678/year
+ Tax Benefits:   +CHF   3,572/year (interest deduction)
= After-tax Cash: -CHF     106/year
+ Equity Buildup: +CHF   2,437/year (amortization)
+ Appreciation:   +CHF   8,125/year (2.5% × CHF 325k share)
+ Personal Use:   +CHF   1,000/year (5 nights @ CHF 200)
= Economic Value: +CHF  13,456/year  ✅ VERY POSITIVE!
```

---

## 💰 Tax Benefits Explanation

**Tax Benefits: CHF 3,572 per owner per year**

The system now includes Swiss tax benefits for interest payments on investment properties:

- **Marginal Tax Rate**: 21% (combined federal + cantonal)
- **Depreciation**: 2% annually on property value
- **Interest Deduction**: Mortgage interest is fully deductible
- **Net Effect**: Tax savings offset most of the negative cash flow

**Why This Matters:**

- Tax benefits represent real cash flow savings to owners
- In Switzerland, investment property debt is tax-advantaged
- This makes leveraged real estate much more attractive
- The effective cost of borrowing is reduced by the tax rate

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
python validate_system.py
```

Expected output:

```
[SUCCESS] SYSTEM VALIDATION PASSED
[PASS] Passed:  198
[FAIL] Failed:  0
```

---

**Created**: December 3, 2025
**Last Updated**: December 25, 2025
**Status**: Production Ready ✅
**Validation**: All systems operational

**Questions?** See README.md for full documentation.
