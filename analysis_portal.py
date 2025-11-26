"""
Summary Portal Generator
Creates a unified HTML dashboard summarizing all analyses:
- Base Case
- Alternative Scenarios
- Sensitivity Analysis
- Monte Carlo Simulation
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from simulation import (
    create_base_case_config,
    compute_annual_cash_flows,
    compute_15_year_projection,
    calculate_irrs_from_projection,
    BaseCaseConfig
)

# Import analysis modules
import analysis_base_case as base_case_module
import analysis_sensitivity as sensitivity_module
import analysis_monte_carlo as monte_carlo_module
import analysis_alternative_scenarios as scenarios_module


def get_base_case_summary() -> Dict:
    """Extract key metrics from base case analysis."""
    config = create_base_case_config()
    results = compute_annual_cash_flows(config)
    projection = compute_15_year_projection(
        config, start_year=2026, inflation_rate=0.02, property_appreciation_rate=0.02
    )
    
    final_value = projection[-1]['property_value']
    final_loan = projection[-1]['remaining_loan_balance']
    irr_results = calculate_irrs_from_projection(
        projection,
        results['equity_per_owner'],
        final_value,
        final_loan,
        config.financing.num_owners,
        purchase_price=config.financing.purchase_price
    )
    
    return {
        'purchase_price': config.financing.purchase_price,
        'num_owners': config.financing.num_owners,
        'ltv': config.financing.ltv,
        'interest_rate': config.financing.interest_rate,
        'gross_rental_income': results['gross_rental_income'],
        'net_operating_income': results['net_operating_income'],
        'cash_flow_after_debt': results['cash_flow_after_debt_service'],
        'cash_flow_per_owner': results['cash_flow_per_owner'],
        'monthly_cash_flow_per_owner': results['cash_flow_per_owner'] / 12.0,
        'cap_rate': results['cap_rate_pct'],
        'cash_on_cash': results['cash_on_cash_return_pct'],
        'debt_coverage_ratio': results['debt_coverage_ratio'],
        'occupancy_rate': results['rented_nights'] / results['rentable_nights'] * 100,
        'average_daily_rate': results['gross_rental_income'] / results['rented_nights'] if results['rented_nights'] > 0 else 0,
        'irr_with_sale': irr_results.get('equity_irr_with_sale_pct', irr_results.get('irr_with_sale_pct', 0)),
        'irr_without_sale': irr_results.get('equity_irr_without_sale_pct', irr_results.get('irr_without_sale_pct', 0)),
        'final_property_value': final_value,
        'final_loan_balance': final_loan,
        'equity_per_owner': results['equity_per_owner']
    }


def get_sensitivity_summary() -> Dict:
    """Extract key insights from sensitivity analysis."""
    config = create_base_case_config()
    
    # Run key sensitivities to get tornado data
    sensitivities = {}
    
    # Occupancy sensitivity
    df_occ = sensitivity_module.sensitivity_occupancy_rate(config)
    sensitivities['Occupancy Rate'] = {
        'worst_cf': df_occ['Cash Flow After Debt (CHF)'].min(),
        'best_cf': df_occ['Cash Flow After Debt (CHF)'].max(),
        'base_cf': df_occ.loc[df_occ['Occupancy Rate (%)'] == config.rental.occupancy_rate * 100, 'Cash Flow After Debt (CHF)'].values[0] if len(df_occ.loc[df_occ['Occupancy Rate (%)'] == config.rental.occupancy_rate * 100]) > 0 else df_occ['Cash Flow After Debt (CHF)'].median()
    }
    
    # Daily rate sensitivity
    df_rate = sensitivity_module.sensitivity_daily_rate(config)
    sensitivities['Daily Rate'] = {
        'worst_cf': df_rate['Cash Flow After Debt (CHF)'].min(),
        'best_cf': df_rate['Cash Flow After Debt (CHF)'].max(),
        'base_cf': df_rate.loc[df_rate['Average Daily Rate (CHF)'] == config.rental.average_daily_rate, 'Cash Flow After Debt (CHF)'].values[0] if len(df_rate.loc[df_rate['Average Daily Rate (CHF)'] == config.rental.average_daily_rate]) > 0 else df_rate['Cash Flow After Debt (CHF)'].median()
    }
    
    # Interest rate sensitivity
    df_int = sensitivity_module.sensitivity_interest_rate(config)
    sensitivities['Interest Rate'] = {
        'worst_cf': df_int['Cash Flow After Debt (CHF)'].min(),
        'best_cf': df_int['Cash Flow After Debt (CHF)'].max(),
        'base_cf': df_int.loc[df_int['Interest Rate (%)'] == config.financing.interest_rate * 100, 'Cash Flow After Debt (CHF)'].values[0] if len(df_int.loc[df_int['Interest Rate (%)'] == config.financing.interest_rate * 100]) > 0 else df_int['Cash Flow After Debt (CHF)'].median()
    }
    
    return sensitivities


def get_monte_carlo_summary() -> Dict:
    """Extract key statistics from Monte Carlo simulation."""
    config = create_base_case_config()
    
    # Run a smaller simulation for the portal (faster)
    df = monte_carlo_module.run_monte_carlo_simulation(config, num_simulations=5000)
    stats = monte_carlo_module.calculate_statistics(df)
    
    # Calculate IRR percentiles that aren't in stats
    irr_p10 = df['irr_with_sale'].quantile(0.10)
    irr_p90 = df['irr_with_sale'].quantile(0.90)
    prob_positive_irr = (df['irr_with_sale'] > 0).sum() / len(df) * 100
    
    return {
        'mean_npv': stats['npv']['mean'],
        'median_npv': stats['npv']['median'],
        'std_npv': stats['npv']['std'],
        'p10_npv': stats['npv']['p10'],
        'p90_npv': stats['npv']['p90'],
        'prob_positive_npv': stats['npv']['positive_prob'] * 100,
        'mean_irr': stats['irr_with_sale']['mean'],
        'median_irr': stats['irr_with_sale']['median'],
        'p10_irr': irr_p10,
        'p90_irr': irr_p90,
        'prob_positive_irr': prob_positive_irr,
        'mean_cash_flow': stats['annual_cash_flow']['mean'],
        'median_cash_flow': stats['annual_cash_flow']['median']
    }


def get_alternative_scenarios_summary() -> List[Dict]:
    """Extract summaries from alternative scenarios."""
    scenarios = []
    
    # 3 owners scenario
    try:
        config_3 = scenarios_module.create_scenario_config(1_300_000, 3)
        results_3 = compute_annual_cash_flows(config_3)
        scenarios.append({
            'name': '3 Owners',
            'num_owners': 3,
            'purchase_price': 1_300_000,
            'cash_flow_per_owner': results_3['cash_flow_per_owner'],
            'monthly_cash_flow_per_owner': results_3['cash_flow_per_owner'] / 12.0,
            'equity_per_owner': results_3['equity_per_owner']
        })
    except:
        pass
    
    # 5 owners scenario
    try:
        config_5 = scenarios_module.create_scenario_config(1_300_000, 5)
        results_5 = compute_annual_cash_flows(config_5)
        scenarios.append({
            'name': '5 Owners',
            'num_owners': 5,
            'purchase_price': 1_300_000,
            'cash_flow_per_owner': results_5['cash_flow_per_owner'],
            'monthly_cash_flow_per_owner': results_5['cash_flow_per_owner'] / 12.0,
            'equity_per_owner': results_5['equity_per_owner']
        })
    except:
        pass
    
    # Lower price scenarios
    for price in [1_100_000, 1_000_000]:
        try:
            config_low = scenarios_module.create_scenario_config(price, 4)
            results_low = compute_annual_cash_flows(config_low)
            scenarios.append({
                'name': f'CHF {price/1_000_000:.1f}M (4 Owners)',
                'num_owners': 4,
                'purchase_price': price,
                'cash_flow_per_owner': results_low['cash_flow_per_owner'],
                'monthly_cash_flow_per_owner': results_low['cash_flow_per_owner'] / 12.0,
                'equity_per_owner': results_low['equity_per_owner']
            })
        except:
            pass
    
    return scenarios


def format_currency(value: float) -> str:
    """Format value as Swiss currency."""
    return f"{value:,.0f} CHF"


def format_percent(value: float) -> str:
    """Format value as percentage."""
    return f"{value:.2f}%"


def generate_portal_html(
    base_case: Dict,
    sensitivity: Dict,
    monte_carlo: Dict,
    scenarios: List[Dict],
    output_path: str = "output/report_portal.html"
) -> str:
    """Generate unified portal HTML dashboard."""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Engelberg Investment Analysis Portal</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary: #1a1a2e;
            --secondary: #0f3460;
            --success: #2ecc71;
            --danger: #e74c3c;
            --warning: #f39c12;
            --info: #3498db;
            --light: #f8f9fa;
            --dark: #2c3e50;
            --border: #dee2e6;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: var(--dark);
            background: #f5f6fa;
        }}
        
        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            padding: 40px 80px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        
        .nav-tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            border-bottom: 2px solid var(--border);
            flex-wrap: wrap;
        }}
        
        .nav-tab {{
            padding: 15px 30px;
            background: white;
            border: none;
            border-bottom: 3px solid transparent;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
            color: var(--dark);
            transition: all 0.3s;
        }}
        
        .nav-tab:hover {{
            background: var(--light);
            color: var(--primary);
        }}
        
        .nav-tab.active {{
            color: var(--primary);
            border-bottom-color: var(--primary);
            background: white;
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        .section {{
            background: white;
            padding: 40px;
            margin-bottom: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        
        .section h2 {{
            color: var(--primary);
            font-size: 1.8em;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid var(--secondary);
        }}
        
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .kpi-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        
        .kpi-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}
        
        .kpi-card.positive {{
            background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
        }}
        
        .kpi-card.negative {{
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        }}
        
        .kpi-card.info {{
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        }}
        
        .kpi-card .label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .kpi-card .value {{
            font-size: 2em;
            font-weight: 700;
            margin-bottom: 5px;
        }}
        
        .kpi-card .subvalue {{
            font-size: 0.85em;
            opacity: 0.8;
        }}
        
        .summary-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        .summary-table th {{
            background: var(--primary);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        .summary-table td {{
            padding: 15px;
            border-bottom: 1px solid var(--border);
        }}
        
        .summary-table tr:hover {{
            background: var(--light);
        }}
        
        .comparison-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .scenario-card {{
            background: white;
            border: 2px solid var(--border);
            border-radius: 8px;
            padding: 25px;
            transition: all 0.3s;
        }}
        
        .scenario-card:hover {{
            border-color: var(--primary);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        
        .scenario-card h3 {{
            color: var(--primary);
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        
        .stat-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid var(--border);
        }}
        
        .stat-row:last-child {{
            border-bottom: none;
        }}
        
        .stat-label {{
            color: var(--dark);
            font-weight: 500;
        }}
        
        .stat-value {{
            color: var(--primary);
            font-weight: 600;
        }}
        
        .stat-value.positive {{
            color: var(--success);
        }}
        
        .stat-value.negative {{
            color: var(--danger);
        }}
        
        .sensitivity-item {{
            background: var(--light);
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 6px;
            border-left: 4px solid var(--primary);
        }}
        
        .sensitivity-item h4 {{
            color: var(--primary);
            margin-bottom: 10px;
        }}
        
        .range-bar {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 10px;
        }}
        
        .range-bar .bar {{
            flex: 1;
            height: 30px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 0.9em;
        }}
        
        .range-bar .worst {{
            background: var(--danger);
        }}
        
        .range-bar .best {{
            background: var(--success);
        }}
        
        .link-box {{
            background: var(--light);
            padding: 20px;
            border-radius: 6px;
            margin-top: 20px;
        }}
        
        .link-box a {{
            color: var(--primary);
            text-decoration: none;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        
        .link-box a:hover {{
            text-decoration: underline;
        }}
        
        @media (max-width: 768px) {{
            .header {{
                padding: 30px 20px;
            }}
            
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .container {{
                padding: 20px 10px;
            }}
            
            .section {{
                padding: 20px;
            }}
            
            .kpi-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1><i class="fas fa-chart-line"></i> Engelberg Investment Analysis Portal</h1>
        <p>Comprehensive summary of all financial analyses • Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="container">
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('base-case')">Base Case</button>
            <button class="nav-tab" onclick="showTab('scenarios')">Alternative Scenarios</button>
            <button class="nav-tab" onclick="showTab('sensitivity')">Sensitivity Analysis</button>
            <button class="nav-tab" onclick="showTab('monte-carlo')">Monte Carlo</button>
        </div>
        
        <!-- Base Case Tab -->
        <div id="base-case" class="tab-content active">
            <div class="section">
                <h2><i class="fas fa-home"></i> Base Case Overview</h2>
                
                <div class="kpi-grid">
                    <div class="kpi-card {'positive' if base_case['cash_flow_per_owner'] >= 0 else 'negative'}">
                        <div class="label">Monthly Cash Flow per Owner</div>
                        <div class="value">{format_currency(base_case['monthly_cash_flow_per_owner'])}</div>
                        <div class="subvalue">Annual: {format_currency(base_case['cash_flow_per_owner'])}</div>
                    </div>
                    
                    <div class="kpi-card info">
                        <div class="label">IRR (with Sale)</div>
                        <div class="value">{format_percent(base_case['irr_with_sale'])}</div>
                        <div class="subvalue">15-year equity return</div>
                    </div>
                    
                    <div class="kpi-card info">
                        <div class="label">IRR (without Sale)</div>
                        <div class="value">{format_percent(base_case['irr_without_sale'])}</div>
                        <div class="subvalue">Cash flow only</div>
                    </div>
                    
                    <div class="kpi-card">
                        <div class="label">Cap Rate</div>
                        <div class="value">{format_percent(base_case['cap_rate'])}</div>
                        <div class="subvalue">Unlevered yield</div>
                    </div>
                    
                    <div class="kpi-card">
                        <div class="label">Cash-on-Cash Return</div>
                        <div class="value">{format_percent(base_case['cash_on_cash'])}</div>
                        <div class="subvalue">Levered return</div>
                    </div>
                    
                    <div class="kpi-card">
                        <div class="label">Debt Coverage Ratio</div>
                        <div class="value">{base_case['debt_coverage_ratio']:.2f}x</div>
                        <div class="subvalue">NOI / Debt Service</div>
                    </div>
                </div>
                
                <table class="summary-table">
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Purchase Price</strong></td>
                            <td>{format_currency(base_case['purchase_price'])}</td>
                        </tr>
                        <tr>
                            <td><strong>Number of Owners</strong></td>
                            <td>{base_case['num_owners']}</td>
                        </tr>
                        <tr>
                            <td><strong>Loan-to-Value</strong></td>
                            <td>{format_percent(base_case['ltv'] * 100)}</td>
                        </tr>
                        <tr>
                            <td><strong>Interest Rate</strong></td>
                            <td>{format_percent(base_case['interest_rate'] * 100)}</td>
                        </tr>
                        <tr>
                            <td><strong>Gross Rental Income</strong></td>
                            <td>{format_currency(base_case['gross_rental_income'])}</td>
                        </tr>
                        <tr>
                            <td><strong>Net Operating Income</strong></td>
                            <td>{format_currency(base_case['net_operating_income'])}</td>
                        </tr>
                        <tr>
                            <td><strong>Cash Flow After Debt</strong></td>
                            <td class="{'positive' if base_case['cash_flow_after_debt'] >= 0 else 'negative'}">{format_currency(base_case['cash_flow_after_debt'])}</td>
                        </tr>
                        <tr>
                            <td><strong>Occupancy Rate</strong></td>
                            <td>{format_percent(base_case['occupancy_rate'])}</td>
                        </tr>
                        <tr>
                            <td><strong>Average Daily Rate</strong></td>
                            <td>{format_currency(base_case['average_daily_rate'])}</td>
                        </tr>
                        <tr>
                            <td><strong>Final Property Value (Year 15)</strong></td>
                            <td>{format_currency(base_case['final_property_value'])}</td>
                        </tr>
                        <tr>
                            <td><strong>Final Loan Balance (Year 15)</strong></td>
                            <td>{format_currency(base_case['final_loan_balance'])}</td>
                        </tr>
                        <tr>
                            <td><strong>Equity per Owner</strong></td>
                            <td>{format_currency(base_case['equity_per_owner'])}</td>
                        </tr>
                    </tbody>
                </table>
                
                <div class="link-box">
                    <a href="report_base_case.html"><i class="fas fa-external-link-alt"></i> View Detailed Base Case Report</a>
                </div>
            </div>
        </div>
        
        <!-- Alternative Scenarios Tab -->
        <div id="scenarios" class="tab-content">
            <div class="section">
                <h2><i class="fas fa-exchange-alt"></i> Alternative Scenarios Comparison</h2>
                
                <div class="comparison-grid">
                    <div class="scenario-card">
                        <h3>Base Case (4 Owners)</h3>
                        <div class="stat-row">
                            <span class="stat-label">Purchase Price</span>
                            <span class="stat-value">{format_currency(base_case['purchase_price'])}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Monthly CF per Owner</span>
                            <span class="stat-value {'positive' if base_case['monthly_cash_flow_per_owner'] >= 0 else 'negative'}">{format_currency(base_case['monthly_cash_flow_per_owner'])}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Equity per Owner</span>
                            <span class="stat-value">{format_currency(base_case['equity_per_owner'])}</span>
                        </div>
                    </div>
"""
    
    # Add scenario cards
    for scenario in scenarios:
        html += f"""
                    <div class="scenario-card">
                        <h3>{scenario['name']}</h3>
                        <div class="stat-row">
                            <span class="stat-label">Purchase Price</span>
                            <span class="stat-value">{format_currency(scenario['purchase_price'])}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Monthly CF per Owner</span>
                            <span class="stat-value {'positive' if scenario['monthly_cash_flow_per_owner'] >= 0 else 'negative'}">{format_currency(scenario['monthly_cash_flow_per_owner'])}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Equity per Owner</span>
                            <span class="stat-value">{format_currency(scenario['equity_per_owner'])}</span>
                        </div>
                    </div>
"""
    
    html += """
                </div>
                
                <div class="link-box">
                    <a href="report_scenarios_overview.html"><i class="fas fa-external-link-alt"></i> View Detailed Scenario Comparison</a>
                </div>
            </div>
        </div>
        
        <!-- Sensitivity Analysis Tab -->
        <div id="sensitivity" class="tab-content">
            <div class="section">
                <h2><i class="fas fa-sliders-h"></i> Sensitivity Analysis Summary</h2>
                <p style="margin-bottom: 25px; color: #555; line-height: 1.8;">
                    The following shows how key parameters impact cash flow. Each sensitivity tests a range of values to identify 
                    which factors most significantly affect investment performance.
                </p>
"""
    
    # Add sensitivity items
    for sens_name, sens_data in sensitivity.items():
        worst = sens_data['worst_cf']
        best = sens_data['best_cf']
        base = sens_data['base_cf']
        range_total = best - worst
        
        html += f"""
                <div class="sensitivity-item">
                    <h4>{sens_name}</h4>
                    <div class="range-bar">
                        <div class="bar worst" style="flex: {abs(worst - base) / range_total if range_total != 0 else 0.5}">
                            Worst: {format_currency(worst)}
                        </div>
                        <div class="bar" style="background: #95a5a6; flex: 0.1; min-width: 80px;">
                            Base: {format_currency(base)}
                        </div>
                        <div class="bar best" style="flex: {abs(best - base) / range_total if range_total != 0 else 0.5}">
                            Best: {format_currency(best)}
                        </div>
                    </div>
                </div>
"""
    
    html += """
                <div class="link-box">
                    <a href="report_sensitivity.html"><i class="fas fa-external-link-alt"></i> View Detailed Sensitivity Analysis with Tornado Charts</a>
                </div>
            </div>
        </div>
        
        <!-- Monte Carlo Tab -->
        <div id="monte-carlo" class="tab-content">
            <div class="section">
                <h2><i class="fas fa-dice"></i> Monte Carlo Simulation Summary</h2>
                <p style="margin-bottom: 25px; color: #555; line-height: 1.8;">
                    Probabilistic analysis based on 5,000 simulations with varying occupancy, rates, and costs. 
                    Shows the distribution of possible outcomes and risk metrics.
                </p>
                
                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="label">Mean NPV</div>
                        <div class="value">{format_currency(monte_carlo['mean_npv'])}</div>
                        <div class="subvalue">Average outcome</div>
                    </div>
                    
                    <div class="kpi-card">
                        <div class="label">Median NPV</div>
                        <div class="value">{format_currency(monte_carlo['median_npv'])}</div>
                        <div class="subvalue">50th percentile</div>
                    </div>
                    
                    <div class="kpi-card {'positive' if monte_carlo['prob_positive_npv'] >= 50 else 'negative'}">
                        <div class="label">Probability NPV > 0</div>
                        <div class="value">{format_percent(monte_carlo['prob_positive_npv'])}</div>
                        <div class="subvalue">Chance of positive return</div>
                    </div>
                    
                    <div class="kpi-card">
                        <div class="label">10th Percentile</div>
                        <div class="value">{format_currency(monte_carlo['p10_npv'])}</div>
                        <div class="subvalue">Worst case (10%)</div>
                    </div>
                    
                    <div class="kpi-card">
                        <div class="label">90th Percentile</div>
                        <div class="value">{format_currency(monte_carlo['p90_npv'])}</div>
                        <div class="subvalue">Best case (90%)</div>
                    </div>
                    
                    <div class="kpi-card">
                        <div class="label">Mean IRR</div>
                        <div class="value">{format_percent(monte_carlo['mean_irr'])}</div>
                        <div class="subvalue">Average return</div>
                    </div>
                </div>
                
                <table class="summary-table" style="margin-top: 30px;">
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>NPV Statistics</strong></td>
                            <td></td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Mean</td>
                            <td>{format_currency(monte_carlo['mean_npv'])}</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Median</td>
                            <td>{format_currency(monte_carlo['median_npv'])}</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Standard Deviation</td>
                            <td>{format_currency(monte_carlo['std_npv'])}</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">10th Percentile</td>
                            <td>{format_currency(monte_carlo['p10_npv'])}</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">90th Percentile</td>
                            <td>{format_currency(monte_carlo['p90_npv'])}</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Probability NPV > 0</td>
                            <td>{format_percent(monte_carlo['prob_positive_npv'])}</td>
                        </tr>
                        <tr>
                            <td><strong>IRR Statistics</strong></td>
                            <td></td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Mean</td>
                            <td>{format_percent(monte_carlo['mean_irr'])}</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Median</td>
                            <td>{format_percent(monte_carlo['median_irr'])}</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">10th Percentile</td>
                            <td>{format_percent(monte_carlo['p10_irr'])}</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">90th Percentile</td>
                            <td>{format_percent(monte_carlo['p90_irr'])}</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Probability IRR > 0</td>
                            <td>{format_percent(monte_carlo['prob_positive_irr'])}</td>
                        </tr>
                        <tr>
                            <td><strong>Cash Flow Statistics</strong></td>
                            <td></td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Mean Annual Cash Flow</td>
                            <td>{format_currency(monte_carlo['mean_cash_flow'])}</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Median Annual Cash Flow</td>
                            <td>{format_currency(monte_carlo['median_cash_flow'])}</td>
                        </tr>
                    </tbody>
                </table>
                
                <div class="link-box">
                    <a href="report_monte_carlo.html"><i class="fas fa-external-link-alt"></i> View Detailed Monte Carlo Report with Distributions</a>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function showTab(tabName) {{
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.classList.remove('active');
            }});
            
            // Remove active class from all nav buttons
            document.querySelectorAll('.nav-tab').forEach(btn => {{
                btn.classList.remove('active');
            }});
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked button
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>"""
    
    return html


def main():
    """Generate the summary portal."""
    print("=" * 70)
    print("Engelberg Investment Analysis Portal Generator")
    print("=" * 70)
    print()
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    print("[*] Gathering base case summary...")
    base_case = get_base_case_summary()
    
    print("[*] Gathering sensitivity analysis summary...")
    sensitivity = get_sensitivity_summary()
    
    print("[*] Running Monte Carlo simulation (5,000 iterations)...")
    monte_carlo = get_monte_carlo_summary()
    
    print("[*] Gathering alternative scenarios summary...")
    scenarios = get_alternative_scenarios_summary()
    
    print("[*] Generating portal HTML...")
    html = generate_portal_html(base_case, sensitivity, monte_carlo, scenarios)
    
    output_path = "output/report_portal.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print()
    print("=" * 70)
    print("[+] Portal generated successfully!")
    print("=" * 70)
    print(f"[+] Portal: {output_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()

