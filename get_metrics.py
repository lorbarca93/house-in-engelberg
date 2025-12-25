import json

# Load latest base case data
with open('website/data/base_case_base_case_analysis.json', 'r') as f:
    data = json.load(f)

annual = data['annual_results']
irr = data['irr_results']

print('=== LATEST BASE CASE METRICS ===')
print('Equity IRR (15Y):', f"{irr['equity_irr_with_sale_pct']:.1f}%")
print('After-tax Equity IRR:', f"{irr['after_tax_equity_irr_with_sale_pct']:.1f}%")
print('Project IRR:', f"{irr['project_irr_with_sale_pct']:.1f}%")
print('NPV @ 5%:', f"CHF {irr['npv_at_5pct']:,.0f}")
print('MOIC:', f"{irr['moic']:.2f}x")
print('Cash Flow/Owner:', f"CHF {annual['cash_flow_per_owner']:,.0f}/year")
print('Monthly NCF:', f"CHF {annual['cash_flow_per_owner']//12:,.0f}/month")
print('Payback Period:', f"{irr['payback_period_years']} years")
print('Tax Benefit/Owner:', f"CHF {annual.get('tax_benefit', 0):,.0f}/year")
