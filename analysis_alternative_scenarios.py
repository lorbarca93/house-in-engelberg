"""
Generate reports for alternative scenarios:
- 3 owners
- 5 owners
- Lower purchase prices
"""

import os
from simulation import (
    create_base_case_config,
    compute_annual_cash_flows,
    compute_15_year_projection,
    calculate_irrs_from_projection,
    BaseCaseConfig,
    FinancingParams,
    RentalParams,
    ExpenseParams,
    SeasonalParams
)
import analysis_base_case as base_case_report
from typing import List, Dict


def create_scenario_config(
    purchase_price: float,
    num_owners: int,
    base_config: BaseCaseConfig = None
) -> BaseCaseConfig:
    """
    Create a configuration for an alternative scenario.
    
    Args:
        purchase_price: Purchase price for this scenario
        num_owners: Number of owners for this scenario
        base_config: Base configuration to use as template (uses create_base_case_config if None)
    
    Returns:
        BaseCaseConfig for the alternative scenario
    """
    if base_config is None:
        base_config = create_base_case_config()
    
    # Get seasonal parameters from base config
    seasons = base_config.rental.seasons
    
    # Adjust owner nights distribution based on number of owners
    # Keep same total owner nights per season proportionally
    owner_nights_per_person = 5
    total_owner_nights = owner_nights_per_person * num_owners
    
    # Distribute proportionally: Winter 40%, Summer 35%, Off-peak 25%
    owner_nights_winter = int(total_owner_nights * 0.40)
    owner_nights_summer = int(total_owner_nights * 0.35)
    owner_nights_offpeak = total_owner_nights - owner_nights_winter - owner_nights_summer
    
    # Days per month
    days_per_month = {
        1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
        7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
    }
    
    winter_months = [12, 1, 2, 3]
    summer_months = [6, 7, 8, 9]
    offpeak_months = [4, 5, 10, 11]
    
    winter_nights = sum(days_per_month[m] for m in winter_months)
    summer_nights = sum(days_per_month[m] for m in summer_months)
    offpeak_nights = sum(days_per_month[m] for m in offpeak_months)
    
    # Calculate rentable nights per season
    rentable_winter = winter_nights - owner_nights_winter
    rentable_summer = summer_nights - owner_nights_summer
    rentable_offpeak = offpeak_nights - owner_nights_offpeak
    
    # Create seasonal parameters (same rates as base case)
    winter_season = SeasonalParams(
        name="Winter Peak (Ski Season)",
        months=winter_months,
        occupancy_rate=seasons[0].occupancy_rate,
        average_daily_rate=seasons[0].average_daily_rate,
        nights_in_season=rentable_winter
    )
    
    summer_season = SeasonalParams(
        name="Summer Peak (Hiking Season)",
        months=summer_months,
        occupancy_rate=seasons[1].occupancy_rate,
        average_daily_rate=seasons[1].average_daily_rate,
        nights_in_season=rentable_summer
    )
    
    offpeak_season = SeasonalParams(
        name="Off-Peak (Shoulder Seasons)",
        months=offpeak_months,
        occupancy_rate=seasons[2].occupancy_rate,
        average_daily_rate=seasons[2].average_daily_rate,
        nights_in_season=rentable_offpeak
    )
    
    # Create financing parameters
    financing = FinancingParams(
        purchase_price=purchase_price,
        ltv=base_config.financing.ltv,  # Keep same LTV
        interest_rate=base_config.financing.interest_rate,  # Keep same interest rate
        amortization_rate=base_config.financing.amortization_rate,  # Keep same amortization
        num_owners=num_owners
    )
    
    # Create rental parameters
    rental = RentalParams(
        owner_nights_per_person=owner_nights_per_person,
        num_owners=num_owners,
        occupancy_rate=base_config.rental.occupancy_rate,
        average_daily_rate=base_config.rental.average_daily_rate,
        seasons=[winter_season, summer_season, offpeak_season]
    )
    
    # Create expense parameters (adjust property value for maintenance)
    expenses = ExpenseParams(
        property_management_fee_rate=base_config.expenses.property_management_fee_rate,
        cleaning_cost_per_stay=base_config.expenses.cleaning_cost_per_stay,
        average_length_of_stay=base_config.expenses.average_length_of_stay,
        tourist_tax_per_person_per_night=base_config.expenses.tourist_tax_per_person_per_night,
        avg_guests_per_night=base_config.expenses.avg_guests_per_night,
        insurance_annual=base_config.expenses.insurance_annual,
        utilities_annual=base_config.expenses.utilities_annual,
        maintenance_rate=base_config.expenses.maintenance_rate,
        property_value=purchase_price  # Use scenario purchase price
    )
    
    return BaseCaseConfig(
        financing=financing,
        rental=rental,
        expenses=expenses
    )


def generate_scenario_report(config: BaseCaseConfig, scenario_name: str, scenario_description: str):
    """
    Generate a complete report for a scenario.
    
    Args:
        config: Configuration for the scenario
        scenario_name: Name of the scenario (for file naming)
        scenario_description: Description of the scenario
    """
    print(f"\n{'='*80}")
    print(f"Generating Report: {scenario_name}")
    print(f"{'='*80}")
    print(f"Description: {scenario_description}")
    print(f"Purchase Price: {config.financing.purchase_price:,.0f} CHF")
    print(f"Number of Owners: {config.financing.num_owners}")
    print(f"Equity per Owner: {config.financing.equity_per_owner:,.0f} CHF")
    print()
    
    # Compute annual cash flows
    print("[*] Computing annual cash flows...")
    results = compute_annual_cash_flows(config)
    
    # Add purchase price to results
    results['purchase_price'] = config.financing.purchase_price
    
    # Compute 15-year projection
    print("[*] Computing 15-year projection...")
    projection_15yr = compute_15_year_projection(
        config,
        start_year=2026,
        inflation_rate=0.02,
        property_appreciation_rate=0.02
    )
    
    # Calculate IRRs
    print("[*] Calculating IRRs...")
    final_property_value = projection_15yr[-1]['property_value']
    final_loan_balance = projection_15yr[-1]['remaining_loan_balance']
    irr_results = calculate_irrs_from_projection(
        projection_15yr,
        results['equity_per_owner'],
        final_property_value,
        final_loan_balance,
        config.financing.num_owners,
        purchase_price=config.financing.purchase_price
    )
    
    # Create charts
    print("[*] Creating charts...")
    charts = base_case_report.create_charts(results, config, projection_15yr)
    
    # Generate HTML report with scenario-specific title
    scenario_slug = scenario_name.lower().replace(" ", "_")
    output_path = f"output/report_scenario_{scenario_slug}.html"
    print(f"[*] Generating HTML report: {output_path}")
    
    # Modify the HTML generation to include scenario info
    base_case_report.generate_html_report(
        results,
        config,
        charts,
        projection_15yr,
        irr_results,
        output_path=output_path
    )
    
    # Print summary
    print(f"\n[+] Report generated: {output_path}")
    print(f"    Cap Rate: {results['cap_rate_pct']:.2f}%")
    print(f"    Cash-on-Cash Return: {results['cash_on_cash_return_pct']:.2f}%")
    print(f"    Debt Coverage Ratio: {results['debt_coverage_ratio']:.2f}x")
    print(f"    IRR with Sale: {irr_results['irr_with_sale_pct']:.2f}%")
    print(f"    Annual Cash Flow per Owner: {results['cash_flow_per_owner']:,.0f} CHF")
    
    return {
        'scenario_name': scenario_name,
        'config': config,
        'results': results,
        'irr_results': irr_results,
        'output_path': output_path
    }


def generate_comparison_dashboard(scenario_reports: List[Dict]):
    """Generate a comparison dashboard showing all scenarios side by side."""
    print(f"\n{'='*80}")
    print("Generating Comparison Dashboard")
    print(f"{'='*80}")
    
    # Create comparison HTML
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scenario Comparison Dashboard</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #0a0e27;
            color: #2c3e50;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1920px;
            margin: 0 auto;
            background: #ffffff;
            min-height: 100vh;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 60px 80px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 3.5em;
            margin-bottom: 15px;
        }}
        
        .header .subtitle {{
            font-size: 1.4em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 50px 80px;
        }}
        
        .section {{
            margin-bottom: 50px;
        }}
        
        .section h2 {{
            font-size: 2.2em;
            color: #1a1a2e;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
        }}
        
        .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            margin-bottom: 30px;
        }}
        
        .comparison-table thead {{
            background: linear-gradient(135deg, #0f3460 0%, #1a1a2e 100%);
            color: white;
        }}
        
        .comparison-table th {{
            padding: 20px;
            text-align: left;
            font-weight: 600;
            font-size: 1.1em;
        }}
        
        .comparison-table td {{
            padding: 15px 20px;
            border-bottom: 1px solid #e8ecef;
        }}
        
        .comparison-table tbody tr:hover {{
            background: #f8f9fa;
        }}
        
        .comparison-table tbody tr:last-child td {{
            border-bottom: none;
        }}
        
        .metric-label {{
            font-weight: 600;
            color: #495057;
        }}
        
        .metric-value {{
            font-weight: 600;
            color: #1a1a2e;
        }}
        
        .positive {{
            color: #2ecc71;
        }}
        
        .negative {{
            color: #e74c3c;
        }}
        
        .scenario-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-top: 30px;
        }}
        
        .scenario-card {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .scenario-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        }}
        
        .scenario-card h3 {{
            font-size: 1.5em;
            color: #1a1a2e;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #667eea;
        }}
        
        .scenario-card .metric {{
            margin-bottom: 15px;
        }}
        
        .scenario-card .metric-label {{
            font-size: 0.9em;
            color: #6c757d;
            margin-bottom: 5px;
        }}
        
        .scenario-card .metric-value {{
            font-size: 1.3em;
            color: #1a1a2e;
        }}
        
        .scenario-link {{
            display: inline-block;
            margin-top: 20px;
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            transition: opacity 0.3s ease;
        }}
        
        .scenario-link:hover {{
            opacity: 0.9;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 40px 80px;
            text-align: center;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-chart-line"></i> Scenario Comparison Dashboard</h1>
            <div class="subtitle">Compare different investment scenarios side by side</div>
        </div>
        
        <div class="content">
            <div class="section">
                <h2><i class="fas fa-table"></i> Key Metrics Comparison</h2>
                <table class="comparison-table">
                    <thead>
                        <tr>
                            <th>Metric</th>
"""
    
    # Add scenario columns
    for report in scenario_reports:
        html += f"<th>{report['scenario_name']}</th>"
    
    html += """
                        </tr>
                    </thead>
                    <tbody>
"""
    
    # Define metrics to compare
    metrics = [
        ('Purchase Price', lambda r: f"{r['config'].financing.purchase_price:,.0f} CHF"),
        ('Number of Owners', lambda r: f"{r['config'].financing.num_owners}"),
        ('Loan Amount', lambda r: f"{r['config'].financing.loan_amount:,.0f} CHF"),
        ('Equity per Owner', lambda r: f"{r['config'].financing.equity_per_owner:,.0f} CHF"),
        ('Gross Rental Income', lambda r: f"{r['results']['gross_rental_income']:,.0f} CHF"),
        ('Net Operating Income', lambda r: f"{r['results']['net_operating_income']:,.0f} CHF"),
        ('Annual Cash Flow', lambda r: f"{r['results']['cash_flow_after_debt_service']:,.0f} CHF"),
        ('Cash Flow per Owner', lambda r: f"{r['results']['cash_flow_per_owner']:,.0f} CHF"),
        ('Cap Rate', lambda r: f"{r['results']['cap_rate_pct']:.2f}%"),
        ('Cash-on-Cash Return', lambda r: f"{r['results']['cash_on_cash_return_pct']:.2f}%"),
        ('Debt Coverage Ratio', lambda r: f"{r['results']['debt_coverage_ratio']:.2f}x"),
        ('IRR with Sale', lambda r: f"{r['irr_results']['irr_with_sale_pct']:.2f}%"),
        ('IRR without Sale', lambda r: f"{r['irr_results']['irr_without_sale_pct']:.2f}%"),
    ]
    
    for metric_name, metric_func in metrics:
        html += f"""
                        <tr>
                            <td class="metric-label">{metric_name}</td>
"""
        for report in scenario_reports:
            value = metric_func(report)
            # Add color coding for certain metrics
            if 'Cash Flow' in metric_name:
                cash_flow = report['results'].get('cash_flow_after_debt_service', 0) if 'per Owner' not in metric_name else report['results'].get('cash_flow_per_owner', 0)
                color_class = 'positive' if cash_flow >= 0 else 'negative'
                html += f"<td class='metric-value {color_class}'>{value}</td>"
            else:
                html += f"<td class='metric-value'>{value}</td>"
        
        html += """
                        </tr>
"""
    
    html += """
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2><i class="fas fa-file-alt"></i> Individual Scenario Reports</h2>
                <div class="scenario-cards">
"""
    
    # Add scenario cards
    for report in scenario_reports:
        config = report['config']
        results = report['results']
        irr = report['irr_results']
        filename = report['output_path'].split('/')[-1]
        
        html += f"""
                    <div class="scenario-card">
                        <h3>{report['scenario_name']}</h3>
                        <div class="metric">
                            <div class="metric-label">Purchase Price</div>
                            <div class="metric-value">{config.financing.purchase_price:,.0f} CHF</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Number of Owners</div>
                            <div class="metric-value">{config.financing.num_owners}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Equity per Owner</div>
                            <div class="metric-value">{config.financing.equity_per_owner:,.0f} CHF</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Cap Rate</div>
                            <div class="metric-value">{results['cap_rate_pct']:.2f}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Cash-on-Cash Return</div>
                            <div class="metric-value">{results['cash_on_cash_return_pct']:.2f}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">IRR with Sale</div>
                            <div class="metric-value">{irr['irr_with_sale_pct']:.2f}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Annual Cash Flow per Owner</div>
                            <div class="metric-value {'positive' if results['cash_flow_per_owner'] >= 0 else 'negative'}">{results['cash_flow_per_owner']:,.0f} CHF</div>
                        </div>
                        <a href="{filename}" class="scenario-link" target="_blank">
                            <i class="fas fa-external-link-alt"></i> View Full Report
                        </a>
                    </div>
"""
    
    html += """
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Engelberg Property Investment Simulation</p>
            <p>Compare different scenarios to find the best investment structure</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Write comparison dashboard
    output_path = "output/report_scenarios_overview.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"[+] Comparison dashboard generated: {output_path}")


def main():
    """Generate reports for all alternative scenarios."""
    print("="*80)
    print("ALTERNATIVE SCENARIOS REPORT GENERATOR")
    print("="*80)
    print()
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Get base configuration
    base_config = create_base_case_config()
    base_price = base_config.financing.purchase_price
    base_owners = base_config.financing.num_owners
    
    scenario_reports = []
    
    # Scenario 1: 3 Owners (same price)
    print("\n[*] Scenario 1: 3 Owners")
    config_3_owners = create_scenario_config(
        purchase_price=base_price,
        num_owners=3,
        base_config=base_config
    )
    report_3 = generate_scenario_report(
        config_3_owners,
        "3 Owners",
        f"Same purchase price ({base_price:,.0f} CHF) with 3 owners instead of {base_owners}"
    )
    scenario_reports.append(report_3)
    
    # Scenario 2: 5 Owners (same price)
    print("\n[*] Scenario 2: 5 Owners")
    config_5_owners = create_scenario_config(
        purchase_price=base_price,
        num_owners=5,
        base_config=base_config
    )
    report_5 = generate_scenario_report(
        config_5_owners,
        "5 Owners",
        f"Same purchase price ({base_price:,.0f} CHF) with 5 owners instead of {base_owners}"
    )
    scenario_reports.append(report_5)
    
    # Scenario 3: Lower Price - 1,100,000 CHF (4 owners)
    print("\n[*] Scenario 3: Lower Price (1,100,000 CHF)")
    config_lower_1 = create_scenario_config(
        purchase_price=1_100_000.0,
        num_owners=4,
        base_config=base_config
    )
    report_lower_1 = generate_scenario_report(
        config_lower_1,
        "Lower Price 1.1M",
        "Lower purchase price of 1,100,000 CHF with 4 owners"
    )
    scenario_reports.append(report_lower_1)
    
    # Scenario 4: Lower Price - 1,000,000 CHF (4 owners)
    print("\n[*] Scenario 4: Lower Price (1,000,000 CHF)")
    config_lower_2 = create_scenario_config(
        purchase_price=1_000_000.0,
        num_owners=4,
        base_config=base_config
    )
    report_lower_2 = generate_scenario_report(
        config_lower_2,
        "Lower Price 1.0M",
        "Lower purchase price of 1,000,000 CHF with 4 owners"
    )
    scenario_reports.append(report_lower_2)
    
    # Scenario 5: Lower Price - 1,100,000 CHF (3 owners)
    print("\n[*] Scenario 5: Lower Price (1,100,000 CHF) with 3 Owners")
    config_lower_3_owners = create_scenario_config(
        purchase_price=1_100_000.0,
        num_owners=3,
        base_config=base_config
    )
    report_lower_3 = generate_scenario_report(
        config_lower_3_owners,
        "Lower Price 1.1M - 3 Owners",
        "Lower purchase price of 1,100,000 CHF with 3 owners"
    )
    scenario_reports.append(report_lower_3)
    
    # Scenario 6: Lower Price - 1,000,000 CHF (5 owners)
    print("\n[*] Scenario 6: Lower Price (1,000,000 CHF) with 5 Owners")
    config_lower_5_owners = create_scenario_config(
        purchase_price=1_000_000.0,
        num_owners=5,
        base_config=base_config
    )
    report_lower_5 = generate_scenario_report(
        config_lower_5_owners,
        "Lower Price 1.0M - 5 Owners",
        "Lower purchase price of 1,000,000 CHF with 5 owners"
    )
    scenario_reports.append(report_lower_5)
    
    # Generate comparison dashboard
    generate_comparison_dashboard(scenario_reports)
    
    print("\n" + "="*80)
    print("ALL SCENARIOS GENERATED SUCCESSFULLY")
    print("="*80)
    print(f"\nGenerated {len(scenario_reports)} scenario reports:")
    for report in scenario_reports:
        print(f"  - {report['scenario_name']}: {report['output_path']}")
    print(f"\nComparison dashboard: output/report_scenarios_overview.html")
    print("="*80)


if __name__ == "__main__":
    main()

