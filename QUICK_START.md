# Quick Start Guide

Get the Engelberg Property Investment Simulation running in a few steps. For full documentation, see [README.md](README.md).

---

## Contents

- [Run analysis](#run-analysis)
- [View results](#view-results)
- [Key metrics](#current-results-base-case)
- [File structure](#file-structure)
- [Modify assumptions](#modify-assumptions)
- [Sensitivity overview](#sensitivity-analysis-overview)
- [Understanding metrics](#key-metrics-explained)
- [Validation](#validation)

---

## Run analysis

**Single case (base or named file):**

```bash
python scripts/analyze.py                              # Base case, all analyses
python scripts/analyze.py assumptions_migros.json     # Migros case
python scripts/analyze.py --analysis base              # Base case only
python scripts/analyze.py --analysis sensitivity      # All 3 sensitivity types
python scripts/analyze.py --analysis monte_carlo      # Monte Carlo only
python scripts/analyze.py --simulations 5000           # Custom simulation count
python scripts/analyze.py --quiet                      # Minimal output
```

**All cases at once:**

```bash
python scripts/generate_all_data.py   # 11 cases × 6 analyses → 66+ files
```

**Validate:**

```bash
python scripts/validate_system.py      # 352 checks
```

---

## View results

1. Start a local server:

   ```bash
   cd website
   python -m http.server 8080
   ```

2. Open **http://localhost:8080/index.html** in your browser.

**Dashboard:** Switch between 11 cases and 7 analysis types (Model, Sensitivity ×3, Monte Carlo, MC Sensitivity, Scenario Comparison). Charts and tables load from JSON.

---

## Current results (base case)

| Metric               | Value                |
| -------------------- | -------------------- |
| Equity IRR (15Y)     | 7.92%                |
| Project IRR          | 3.97%                |
| NPV @ 5%             | CHF 45,630           |
| MOIC                 | 3.27×                |
| Cash Flow/Owner      | -CHF 1,007/year      |
| Monthly NCF (AT)     | ~CHF -5/month        |
| Payback Period       | 15 years (at sale)   |

**Assumptions:** Inflation 1.0%/year, appreciation 2.5%/year, discount 5.0%, maintenance 0.5%/year, selling costs 7.8% (broker 3%, notary 1.5%, transfer tax 3.3%).

---

## File structure

| Path                    | Purpose                    |
| ----------------------- | -------------------------- |
| `engelberg/`            | Core package (core, analysis, monte_carlo, sensitivity) |
| `scripts/`              | CLI: analyze, generate_all_data, validate_system        |
| `assumptions/`          | JSON configs (11 cases)    |
| `website/`              | Dashboard + `data/*.json`   |
| `tests/`                | Unit, integration, regression |

**Cases (11):** Base, Migros, 3/5 Owners, 90-Day Restriction, Climate Risk, Early Exit, Engelbergerstrasse 53 (×3), Interest Rate Spike.

---

## Modify assumptions


Edit `assumptions/assumptions.json` (base case) or add `assumptions/assumptions_mycase.json` (new case):

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

Then run `python scripts/generate_all_data.py` and refresh the dashboard.

---

## Sensitivity analysis overview

Sensitivity analysis shows which parameters have the biggest impact on your investment returns. Focus optimization efforts on high-impact parameters.

### Top 5 Most Impactful Parameters (Equity IRR - 15-Year Return)

1. **Property Appreciation** (±4.09% IRR impact)
   - Long-term value driver
   - Hard to control, but critical for returns
2. **Interest Rate** (±3.52% IRR impact)
   - Negotiate best mortgage rate possible
   - Consider refinancing opportunities
3. **Average Daily Rate** (±2.94% IRR impact)
   - Pricing strategy directly affects returns
   - Test different rate levels in sensitivity
4. **Maintenance Reserve** (±2.93% IRR impact)
   - Budget for unexpected repairs
   - Higher reserve = more conservative
5. **Loan-to-Value** (±1.21% IRR impact)
   - More equity = lower leverage = lower returns (but less risk)

### Top 5 for Monthly Cash Flow (What Hits Your Bank Account)

1. **Interest Rate** (±CHF 406/month)
   - Biggest monthly cash flow driver
   - Small rate changes = big monthly impact
2. **Amortization Rate** (±CHF 406/month)
   - Faster paydown = more monthly cash out
   - But builds equity faster
3. **Average Daily Rate** (±CHF 225/month)
   - Revenue driver
   - Test pricing strategies
4. **Occupancy Rate** (±CHF 160/month)
   - Fill vacant nights
   - Marketing and property quality matter
5. **Purchase Price** (±CHF 140/month)
   - Negotiate purchase price
   - Lower price = better cash flow

---

## Understanding negative cash flow

**Current Base Case: -CHF 1,007/year per owner (~CHF -84/month)**

This means you contribute cash each month. Why?

### The Math:

```
Gross Rental Income:    CHF  48,783
- Operating Expenses:   CHF  28,487
= Net Operating Income: CHF  12,978  ✅ POSITIVE!

- Debt Service:         CHF  17,008  (interest + principal)
= Cash Flow:            CHF  -4,029
÷ 4 owners:             CHF  -1,007/year
÷ 12 months:             CHF     -84/month
```

**Key Insight**: The property generates positive NOI, but debt service exceeds it. This is common in leveraged real estate investments.

### But You're Building Wealth:

```
Negative Cash Flow:     -CHF   1,007/year
+ Tax Savings:          +CHF     951/year (interest deduction)
+ Equity Buildup:       +CHF   1,083/year (principal payments)
+ Property Appreciation:+CHF   8,125/year (2.5% × CHF 325k share)
+ Personal Use Value:   +CHF   1,000/year (5 nights @ market rate)
─────────────────────────────────────────────────────
= Total Economic Value: +CHF  10,152/year  ✅ POSITIVE!
```

**The investment is profitable when you account for all value creation, not just cash flow!**

---

## Key metrics explained

| Metric           | Description                                                                 | Good Value        |
| ---------------- | --------------------------------------------------------------------------- | ----------------- |
| **Equity IRR**   | Annualized return on your equity investment over 15 years (includes sale)   | > 7%              |
| **Project IRR**  | Return if you bought with 100% cash (no debt) - shows property fundamentals | > 3%              |
| **Cash-on-Cash** | Year 1 cash flow ÷ Initial equity - immediate yield                        | > 0% (positive)   |
| **Monthly NCF**  | Actual CHF hitting your bank account monthly (after-tax)                    | > 0 (positive)    |
| **NPV**          | Present value of all cash flows at 5% discount - value creation            | > 0 (positive)    |
| **MOIC**         | Total cash returned ÷ Initial investment - wealth multiplier               | > 2×              |
| **Payback**      | Years until cumulative cash flow turns positive (with sale)                | < 15 years        |

### Quick Interpretation Guide

- **IRR > 7%**: Strong return, beats most fixed-income investments
- **NPV > 0**: Investment creates value at 5% discount rate
- **MOIC > 3×**: Excellent wealth creation over 15 years
- **Negative Cash Flow**: Normal for leveraged investments; focus on total returns

---

## Validation

Run 352 comprehensive checks:

```bash
python scripts/validate_system.py
```

Expected output:

```
[SUCCESS] SYSTEM VALIDATION PASSED
[PASS] Passed:  352
[FAIL] Failed:  0
```

---

**Created**: December 3, 2025  
**Last Updated**: January 28, 2026  
**Status**: Production Ready ✅  
**Validation**: 352/352 checks passing

## Pro tips

1. **Start with Base Case**: Understand the base scenario before exploring alternatives
2. **Use Scenario Comparison**: Quickly identify best-performing scenarios across all metrics
3. **Focus on High-Impact Parameters**: Use sensitivity analysis to prioritize optimization efforts
4. **Monte Carlo for Risk**: Understand probability distributions, not just point estimates
5. **After-Tax Cash Flow**: Most practical metric for monthly budgeting
6. **IRR for Comparison**: Best metric for comparing to other investments

## See also

- **[README.md](README.md)** — Full documentation, analysis types, troubleshooting
- **[CHANGELOG.md](CHANGELOG.md)** — Version history and implementation notes
- **Validation** — `python scripts/validate_system.py` (352 checks)
