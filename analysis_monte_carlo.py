"""
Monte Carlo Analysis for Engelberg Property Investment
Analyzes uncertainty using the four most critical sensitivities:
1. Occupancy Rate
2. Average Daily Rate
3. Interest Rate
4. Property Management Fee Rate
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from simulation import (
    create_base_case_config,
    BaseCaseConfig,
    compute_annual_cash_flows,
    compute_15_year_projection,
    calculate_irrs_from_projection,
    apply_sensitivity  # Use the centralized sensitivity function
)
from datetime import datetime
import random


def run_monte_carlo_simulation(base_config: BaseCaseConfig, 
                                num_simulations: int = 10000,
                                discount_rate: float = 0.04) -> pd.DataFrame:
    """
    Run Monte Carlo simulation with random variations of key parameters.
    
    Args:
        base_config: Base case configuration
        num_simulations: Number of simulation runs
        discount_rate: Discount rate for NPV calculation
    
    Returns:
        DataFrame with simulation results
    """
    print(f"[*] Running {num_simulations:,} Monte Carlo simulations...")
    
    results = []
    
    # Define parameter distributions (uniform distributions for simplicity)
    # These can be changed to normal distributions or other distributions
    
    for i in range(num_simulations):
        if (i + 1) % 1000 == 0:
            print(f"  Progress: {i + 1:,} / {num_simulations:,} simulations ({100 * (i + 1) / num_simulations:.1f}%)")
        
        # Sample from uniform distributions
        # Occupancy Rate: 30% to 70% (base case ~61.5%)
        occupancy = np.random.uniform(0.30, 0.70)
        
        # Daily Rate: 200 to 400 CHF (base case ~324 CHF weighted average)
        daily_rate = np.random.uniform(200, 400)
        
        # Interest Rate: 1.2% to 3.5% (base case 1.3%)
        interest_rate = np.random.uniform(0.012, 0.035)
        
        # Management Fee: 20% to 35% (base case 20%)
        management_fee = np.random.uniform(0.20, 0.35)
        
        # Create modified configuration
        # IMPORTANT: Use apply_sensitivity() to ensure consistency with base case
        # This ensures all analyses reference the same base case structure
        config = apply_sensitivity(
            base_config,
            occupancy=occupancy,
            daily_rate=daily_rate,
            interest_rate=interest_rate,
            management_fee=management_fee
        )
        
        # Calculate annual cash flows
        annual_result = compute_annual_cash_flows(config)
        
        # Calculate 15-year projection
        projection = compute_15_year_projection(
            config, 
            start_year=2026, 
            inflation_rate=0.02, 
            property_appreciation_rate=0.02
        )
        
        # Get final values
        final_property_value = projection[-1]['property_value']
        final_loan_balance = projection[-1]['remaining_loan_balance']
        initial_equity = annual_result['equity_per_owner']
        
        # Calculate IRRs
        irr_results = calculate_irrs_from_projection(
            projection,
            initial_equity,
            final_property_value,
            final_loan_balance,
            config.financing.num_owners,
            purchase_price=config.financing.purchase_price
        )
        
        # Calculate NPV
        cash_flows = [year['cash_flow_per_owner'] for year in projection]
        sale_proceeds_per_owner = (final_property_value - final_loan_balance) / config.financing.num_owners
        
        npv = -initial_equity
        for j, cf in enumerate(cash_flows):
            npv += cf / ((1 + discount_rate) ** (j + 1))
        npv += sale_proceeds_per_owner / ((1 + discount_rate) ** len(cash_flows))
        
        # Store results
        results.append({
            'simulation': i + 1,
            'occupancy_rate': occupancy,
            'daily_rate': daily_rate,
            'interest_rate': interest_rate,
            'management_fee_rate': management_fee,
            'annual_cash_flow': annual_result['cash_flow_after_debt_service'],
            'cash_flow_per_owner': annual_result['cash_flow_per_owner'],
            'gross_rental_income': annual_result['gross_rental_income'],
            'net_operating_income': annual_result['net_operating_income'],
            'npv': npv,
            'irr_with_sale': irr_results['irr_with_sale_pct'],
            'irr_without_sale': irr_results['irr_without_sale_pct'],
            'final_property_value': final_property_value,
            'sale_proceeds_per_owner': sale_proceeds_per_owner
        })
    
    print(f"[+] Completed {num_simulations:,} simulations")
    
    return pd.DataFrame(results)


def calculate_statistics(df: pd.DataFrame) -> dict:
    """Calculate summary statistics from simulation results."""
    return {
        'npv': {
            'mean': df['npv'].mean(),
            'median': df['npv'].median(),
            'std': df['npv'].std(),
            'min': df['npv'].min(),
            'max': df['npv'].max(),
            'p5': df['npv'].quantile(0.05),
            'p10': df['npv'].quantile(0.10),
            'p25': df['npv'].quantile(0.25),
            'p75': df['npv'].quantile(0.75),
            'p90': df['npv'].quantile(0.90),
            'p95': df['npv'].quantile(0.95),
            'positive_prob': (df['npv'] > 0).sum() / len(df),
        },
        'irr_with_sale': {
            'mean': df['irr_with_sale'].mean(),
            'median': df['irr_with_sale'].median(),
            'std': df['irr_with_sale'].std(),
            'min': df['irr_with_sale'].min(),
            'max': df['irr_with_sale'].max(),
            'p5': df['irr_with_sale'].quantile(0.05),
            'p95': df['irr_with_sale'].quantile(0.95),
        },
        'annual_cash_flow': {
            'mean': df['annual_cash_flow'].mean(),
            'median': df['annual_cash_flow'].median(),
            'std': df['annual_cash_flow'].std(),
            'min': df['annual_cash_flow'].min(),
            'max': df['annual_cash_flow'].max(),
            'positive_prob': (df['annual_cash_flow'] > 0).sum() / len(df),
        }
    }


def create_monte_carlo_charts(df: pd.DataFrame, stats: dict) -> list:
    """Create visualization charts for Monte Carlo results."""
    charts = []
    
    # Chart 1: NPV Distribution Histogram
    fig1 = go.Figure()
    fig1.add_trace(go.Histogram(
        x=df['npv'],
        nbinsx=100,
        name='NPV Distribution',
        marker_color='#667eea',
        opacity=0.7
    ))
    
    # Add vertical lines for key statistics
    fig1.add_vline(x=stats['npv']['mean'], line_dash="dash", line_color="red", 
                   annotation_text=f"Mean: {stats['npv']['mean']:,.0f} CHF")
    fig1.add_vline(x=stats['npv']['median'], line_dash="dash", line_color="green",
                   annotation_text=f"Median: {stats['npv']['median']:,.0f} CHF")
    fig1.add_vline(x=0, line_dash="solid", line_color="black", line_width=2,
                   annotation_text="Break-even")
    
    fig1.update_layout(
        title="NPV Distribution - Monte Carlo Simulation",
        xaxis_title="NPV (CHF)",
        yaxis_title="Frequency",
        height=500,
        showlegend=False
    )
    charts.append(("npv_distribution", fig1))
    
    # Chart 2: IRR Distribution Histogram
    fig2 = go.Figure()
    fig2.add_trace(go.Histogram(
        x=df['irr_with_sale'],
        nbinsx=100,
        name='IRR Distribution',
        marker=dict(
            color=CHART_COLORS['success'],
            line=dict(color='#ffffff', width=1),
            opacity=0.75
        ),
        hovertemplate='<b>IRR Range</b><br>Value: %{x:.2f}%<br>Frequency: %{y}<extra></extra>'
    ))
    
    fig2.add_vline(
        x=stats['irr_with_sale']['mean'],
        line_dash="dash",
        line_color=CHART_COLORS['danger'],
        line_width=2,
        annotation_text=f"Mean: {stats['irr_with_sale']['mean']:.2f}%",
        annotation_position="top",
        annotation_font_size=11
    )
    fig2.add_vline(
        x=stats['irr_with_sale']['median'],
        line_dash="dash",
        line_color=CHART_COLORS['info'],
        line_width=2,
        annotation_text=f"Median: {stats['irr_with_sale']['median']:.2f}%",
        annotation_position="top",
        annotation_font_size=11
    )
    
    layout_updates = template.copy()
    layout_updates.update({
        'title': {
            'text': "IRR (with Sale) Distribution - Monte Carlo Simulation",
            'font': template['title_font'],
            'x': template['title_x'],
            'xanchor': template['title_xanchor'],
            'pad': template['title_pad']
        },
        'xaxis_title': "IRR (%)",
        'yaxis_title': "Frequency",
        'height': 550,
        'showlegend': False
    })
    fig2.update_layout(**layout_updates)
    charts.append(("irr_distribution", fig2))
    
    # Chart 3: Cumulative Probability Distribution (NPV)
    sorted_npv = np.sort(df['npv'])
    cumulative_prob = np.arange(1, len(sorted_npv) + 1) / len(sorted_npv)
    
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=sorted_npv,
        y=cumulative_prob * 100,
        mode='lines',
        name='Cumulative Probability',
        line=dict(color='#667eea', width=2)
    ))
    
    fig3.add_hline(y=50, line_dash="dash", line_color="gray",
                   annotation_text="50th Percentile (Median)")
    fig3.add_hline(y=90, line_dash="dash", line_color="orange",
                   annotation_text="90th Percentile")
    fig3.add_hline(y=10, line_dash="dash", line_color="orange",
                   annotation_text="10th Percentile")
    
    fig3.update_traces(
        line=dict(color=CHART_COLORS['gradient_start'], width=3),
        hovertemplate='<b>Cumulative Probability</b><br>NPV: %{x:,.0f} CHF<br>Probability: %{y:.1f}%<extra></extra>'
    )
    layout_updates = template.copy()
    layout_updates.update({
        'title': {
            'text': "NPV Cumulative Probability Distribution",
            'font': template['title_font'],
            'x': template['title_x'],
            'xanchor': template['title_xanchor'],
            'pad': template['title_pad']
        },
        'xaxis_title': "NPV (CHF)",
        'yaxis_title': "Probability (%)",
        'height': 550
    })
    fig3.update_layout(**layout_updates)
    charts.append(("npv_cumulative", fig3))
    
    # Chart 4: Scatter Plot - Occupancy vs Daily Rate (colored by NPV)
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=df['occupancy_rate'] * 100,
        y=df['daily_rate'],
        mode='markers',
        marker=dict(
            size=5,
            color=df['npv'],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="NPV (CHF)"),
            opacity=0.6
        ),
        text=[f"NPV: {n:,.0f} CHF<br>IRR: {i:.2f}%" 
              for n, i in zip(df['npv'], df['irr_with_sale'])],
        hovertemplate='Occupancy: %{x:.1f}%<br>Daily Rate: %{y:.0f} CHF<br>%{text}<extra></extra>',
        name='Simulations'
    ))
    
    fig4.update_traces(
        marker=dict(
            size=6,
            opacity=0.6,
            line=dict(width=0.5, color='rgba(255, 255, 255, 0.3)')
        ),
        hovertemplate='<b>Simulation</b><br>Occupancy: %{x:.1f}%<br>Daily Rate: %{y:.0f} CHF<br>%{text}<extra></extra>'
    )
    layout_updates = template.copy()
    layout_updates.update({
        'title': {
            'text': "NPV Sensitivity: Occupancy Rate vs Daily Rate",
            'font': template['title_font'],
            'x': template['title_x'],
            'xanchor': template['title_xanchor'],
            'pad': template['title_pad']
        },
        'xaxis_title': "Occupancy Rate (%)",
        'yaxis_title': "Daily Rate (CHF)",
        'height': 550,
        'showlegend': False
    })
    fig4.update_layout(**layout_updates)
    charts.append(("occupancy_daily_scatter", fig4))
    
    # Chart 5: Scatter Plot - Interest Rate vs Management Fee (colored by NPV)
    fig5_scatter = go.Figure()
    fig5_scatter.add_trace(go.Scatter(
        x=df['interest_rate'] * 100,
        y=df['management_fee_rate'] * 100,
        mode='markers',
        marker=dict(
            size=5,
            color=df['npv'],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="NPV (CHF)"),
            opacity=0.6
        ),
        text=[f"NPV: {n:,.0f} CHF<br>IRR: {i:.2f}%" 
              for n, i in zip(df['npv'], df['irr_with_sale'])],
        hovertemplate='Interest Rate: %{x:.2f}%<br>Management Fee: %{y:.1f}%<br>%{text}<extra></extra>',
        name='Simulations'
    ))
    
    fig5_scatter.update_traces(
        marker=dict(
            size=6,
            opacity=0.6,
            line=dict(width=0.5, color='rgba(255, 255, 255, 0.3)')
        ),
        hovertemplate='<b>Simulation</b><br>Interest Rate: %{x:.2f}%<br>Management Fee: %{y:.1f}%<br>%{text}<extra></extra>'
    )
    layout_updates = template.copy()
    layout_updates.update({
        'title': {
            'text': "NPV Sensitivity: Interest Rate vs Management Fee Rate",
            'font': template['title_font'],
            'x': template['title_x'],
            'xanchor': template['title_xanchor'],
            'pad': template['title_pad']
        },
        'xaxis_title': "Interest Rate (%)",
        'yaxis_title': "Management Fee Rate (%)",
        'height': 550,
        'showlegend': False
    })
    fig5_scatter.update_layout(**layout_updates)
    charts.append(("interest_management_scatter", fig5_scatter))
    
    # Chart 6: Box Plot - NPV by Parameter Quartiles
    fig6 = make_subplots(
        rows=2, cols=2,
        subplot_titles=('NPV by Occupancy Quartile', 'NPV by Daily Rate Quartile',
                        'NPV by Interest Rate Quartile', 'NPV by Management Fee Quartile'),
        vertical_spacing=0.12,
        horizontal_spacing=0.10
    )
    
    # Occupancy quartiles
    df['occ_quartile'] = pd.qcut(df['occupancy_rate'], q=4, labels=['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)'], duplicates='drop')
    for q in df['occ_quartile'].cat.categories:
        subset = df[df['occ_quartile'] == q]['npv']
        if len(subset) > 0:
            fig6.add_trace(go.Box(y=subset, name=str(q), showlegend=False), row=1, col=1)
    
    # Daily rate quartiles
    df['rate_quartile'] = pd.qcut(df['daily_rate'], q=4, labels=['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)'], duplicates='drop')
    for q in df['rate_quartile'].cat.categories:
        subset = df[df['rate_quartile'] == q]['npv']
        if len(subset) > 0:
            fig6.add_trace(go.Box(y=subset, name=str(q), showlegend=False), row=1, col=2)
    
    # Interest rate quartiles
    df['int_quartile'] = pd.qcut(df['interest_rate'], q=4, labels=['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)'], duplicates='drop')
    for q in df['int_quartile'].cat.categories:
        subset = df[df['int_quartile'] == q]['npv']
        if len(subset) > 0:
            fig6.add_trace(go.Box(y=subset, name=str(q), showlegend=False), row=2, col=1)
    
    # Management fee quartiles
    df['mgmt_quartile'] = pd.qcut(df['management_fee_rate'], q=4, labels=['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)'], duplicates='drop')
    for q in df['mgmt_quartile'].cat.categories:
        subset = df[df['mgmt_quartile'] == q]['npv']
        if len(subset) > 0:
            fig6.add_trace(go.Box(y=subset, name=str(q), showlegend=False), row=2, col=2)
    
    fig6.update_layout(
        height=800, 
        title_text="NPV Distribution by Parameter Quartiles", 
        showlegend=False,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    fig6.update_yaxes(title_text="NPV (CHF)", row=1, col=1)
    fig6.update_yaxes(title_text="NPV (CHF)", row=1, col=2)
    fig6.update_yaxes(title_text="NPV (CHF)", row=2, col=1)
    fig6.update_yaxes(title_text="NPV (CHF)", row=2, col=2)
    
    charts.append(("npv_by_quartiles", fig6))
    
    # Chart 7: Correlation Charts - NPV vs each key parameter
    fig7 = make_subplots(
        rows=2, cols=2,
        subplot_titles=('NPV vs Occupancy Rate', 'NPV vs Daily Rate',
                        'NPV vs Interest Rate', 'NPV vs Management Fee Rate'),
        vertical_spacing=0.12,
        horizontal_spacing=0.10
    )
    
    # NPV vs Occupancy Rate
    fig7.add_trace(go.Scatter(
        x=df['occupancy_rate'] * 100,
        y=df['npv'],
        mode='markers',
        marker=dict(size=3, opacity=0.5, color='#667eea'),
        name='Occupancy',
        showlegend=False
    ), row=1, col=1)
    
    # NPV vs Daily Rate
    fig7.add_trace(go.Scatter(
        x=df['daily_rate'],
        y=df['npv'],
        mode='markers',
        marker=dict(size=3, opacity=0.5, color='#2ecc71'),
        name='Daily Rate',
        showlegend=False
    ), row=1, col=2)
    
    # NPV vs Interest Rate
    fig7.add_trace(go.Scatter(
        x=df['interest_rate'] * 100,
        y=df['npv'],
        mode='markers',
        marker=dict(size=3, opacity=0.5, color='#e74c3c'),
        name='Interest Rate',
        showlegend=False
    ), row=2, col=1)
    
    # NPV vs Management Fee
    fig7.add_trace(go.Scatter(
        x=df['management_fee_rate'] * 100,
        y=df['npv'],
        mode='markers',
        marker=dict(size=3, opacity=0.5, color='#f39c12'),
        name='Management Fee',
        showlegend=False
    ), row=2, col=2)
    
    fig7.update_layout(
        height=600,
        title_text="NPV vs Key Parameters",
        showlegend=False,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    fig7.update_xaxes(title_text="Occupancy Rate (%)", row=1, col=1)
    fig7.update_xaxes(title_text="Daily Rate (CHF)", row=1, col=2)
    fig7.update_xaxes(title_text="Interest Rate (%)", row=2, col=1)
    fig7.update_xaxes(title_text="Management Fee Rate (%)", row=2, col=2)
    fig7.update_yaxes(title_text="NPV (CHF)", row=1, col=1)
    fig7.update_yaxes(title_text="NPV (CHF)", row=1, col=2)
    fig7.update_yaxes(title_text="NPV (CHF)", row=2, col=1)
    fig7.update_yaxes(title_text="NPV (CHF)", row=2, col=2)
    
    charts.append(("correlation_charts", fig7))
    
    return charts


def generate_monte_carlo_html(df: pd.DataFrame, stats: dict, charts: list, 
                              base_config: BaseCaseConfig, num_simulations: int,
                              output_path: str = "output/report_monte_carlo.html"):
    """Generate HTML report for Monte Carlo analysis."""
    
    def format_currency(value):
        return f"{value:,.0f} CHF"
    
    def format_percent(value):
        return f"{value:.2f}%"
    
    # Calculate base case for comparison
    from simulation import compute_annual_cash_flows, compute_15_year_projection, calculate_irrs_from_projection
    base_result = compute_annual_cash_flows(base_config)
    base_projection = compute_15_year_projection(base_config, start_year=2026, inflation_rate=0.02, property_appreciation_rate=0.02)
    base_final_value = base_projection[-1]['property_value']
    base_final_loan = base_projection[-1]['remaining_loan_balance']
    base_irr = calculate_irrs_from_projection(
        base_projection,
        base_result['equity_per_owner'],
        base_final_value,
        base_final_loan,
        base_config.financing.num_owners,
        purchase_price=base_config.financing.purchase_price
    )
    
    # Calculate base NPV
    discount_rate = 0.04
    base_cash_flows = [y['cash_flow_per_owner'] for y in base_projection]
    base_sale_proceeds = (base_final_value - base_final_loan) / base_config.financing.num_owners
    base_npv = -base_result['equity_per_owner']
    for i, cf in enumerate(base_cash_flows):
        base_npv += cf / ((1 + discount_rate) ** (i + 1))
    base_npv += base_sale_proceeds / ((1 + discount_rate) ** len(base_cash_flows))
    
    # Generate Plotly charts HTML - use to_html() directly for each chart
    charts_html = ""
    correlation_chart_html = ""  # Extract correlation chart separately
    plotly_js_parts = []
    first_chart = True
    correlation_fig = None  # Store correlation chart figure
    
    for chart_name, fig in charts:
        # Get chart title
        chart_title = chart_name.replace('_', ' ').title()
        if hasattr(fig.layout, 'title') and fig.layout.title:
            if hasattr(fig.layout.title, 'text'):
                chart_title = fig.layout.title.text
            elif isinstance(fig.layout.title, str):
                chart_title = fig.layout.title
        
        # Extract correlation chart separately for dedicated section
        if chart_name == "correlation_charts":
            # Store the figure for later use
            correlation_fig = fig
            continue  # Skip adding to main charts_html
        
        # Use to_html() directly - it handles everything including the script
        if first_chart:
            # First chart includes Plotly JS
            chart_html = fig.to_html(include_plotlyjs="cdn", div_id=chart_name, full_html=False)
            first_chart = False
        else:
            # Subsequent charts don't include Plotly JS
            chart_html = fig.to_html(include_plotlyjs=False, div_id=chart_name, full_html=False)
        
        # Wrap in container
        charts_html += f'''
        <div class="chart-container scroll-reveal">
            <div class="chart-title">{chart_title}</div>
            {chart_html}
        </div>
        '''
    
    # Generate correlation chart HTML
    if correlation_fig is not None:
        # Use to_html() to generate the chart HTML
        # Since Plotly JS is already loaded from first chart, we don't need to include it again
        correlation_chart_html = correlation_fig.to_html(include_plotlyjs=False, div_id="correlation_charts", full_html=False)
    
    # No need for separate plotly_js since it's embedded in the HTML
    plotly_js = ""
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monte Carlo Analysis - Engelberg Property Investment</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {{
            --primary: #1a1a2e;
            --secondary: #0f3460;
            --success: #28a745;
            --danger: #dc3545;
            --warning: #ffc107;
            --info: #17a2b8;
            --gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --shadow-sm: 0 2px 4px rgba(0,0,0,0.1);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.15);
            --shadow-lg: 0 10px 40px rgba(0,0,0,0.2);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            background: #0a0e27;
            color: #2c3e50;
            line-height: 1.6;
            overflow-x: hidden;
        }}
        
        .container {{
            max-width: 1920px;
            margin: 0 auto;
            background: white;
            min-height: 100vh;
        }}
        
        .header {{
            background: var(--gradient-1);
            color: white;
            padding: 60px 80px;
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -10%;
            width: 500px;
            height: 500px;
            background: rgba(255,255,255,0.1);
            border-radius: 50%;
            animation: float 20s infinite ease-in-out;
        }}
        
        @keyframes float {{
            0%, 100% {{ transform: translate(0, 0) rotate(0deg); }}
            50% {{ transform: translate(-30px, -30px) rotate(180deg); }}
        }}
        
        .header h1 {{
            font-size: 3.5em;
            font-weight: 700;
            margin-bottom: 15px;
            letter-spacing: -1px;
            position: relative;
            z-index: 1;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header .subtitle {{
            font-size: 1.4em;
            opacity: 0.95;
            margin-bottom: 10px;
            position: relative;
            z-index: 1;
        }}
        
        .header .meta {{
            font-size: 0.95em;
            opacity: 0.85;
            margin-top: 20px;
            position: relative;
            z-index: 1;
        }}
        
        .section {{
            padding: 50px 80px;
            background: white;
        }}
        
        .section:nth-child(even) {{
            background: #f8f9fa;
        }}
        
        .section h2 {{
            font-size: 2.2em;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid var(--secondary);
            letter-spacing: -0.5px;
        }}
        
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 50px;
        }}
        
        .kpi-card {{
            background: white;
            padding: 30px;
            border-radius: 16px;
            box-shadow: var(--shadow-md);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            border-left: 4px solid var(--primary);
        }}
        
        .kpi-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient-1);
            transform: scaleX(0);
            transform-origin: left;
            transition: transform 0.3s;
        }}
        
        .kpi-card:hover {{
            transform: translateY(-8px);
            box-shadow: var(--shadow-lg);
        }}
        
        .kpi-card:hover::before {{
            transform: scaleX(1);
        }}
        
        .kpi-label {{
            font-size: 0.85em;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        
        .kpi-value {{
            font-size: 2.5em;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 8px;
            letter-spacing: -1px;
        }}
        
        .kpi-value.positive {{
            color: var(--success);
        }}
        
        .kpi-value.negative {{
            color: var(--danger);
        }}
        
        .kpi-description {{
            font-size: 0.9em;
            color: #868e96;
            margin-top: 8px;
        }}
        
        .chart-container {{
            background: white;
            padding: 35px;
            border-radius: 16px;
            box-shadow: var(--shadow-md);
            transition: all 0.3s;
            margin-bottom: 30px;
        }}
        
        .chart-container:hover {{
            transform: translateY(-5px);
            box-shadow: var(--shadow-lg);
        }}
        
        .chart-title {{
            font-size: 1.3em;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e8ecef;
        }}
        
        .info-box {{
            background: linear-gradient(135deg, #e8f4f8 0%, #d1ecf1 100%);
            border-left: 4px solid var(--info);
            padding: 25px;
            border-radius: 12px;
            margin: 25px 0;
        }}
        
        .methodology-box {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 12px;
            border-left: 4px solid var(--primary);
            margin: 25px 0;
        }}
        
        .methodology-box h3 {{
            color: var(--primary);
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        
        .methodology-box ul {{
            margin-left: 20px;
            line-height: 2;
        }}
        
        .methodology-box li {{
            margin-bottom: 10px;
        }}
        
        .stats-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: var(--shadow-sm);
            margin: 20px 0;
        }}
        
        .stats-table th {{
            background: var(--gradient-1);
            color: white;
            padding: 18px 20px;
            text-align: left;
            font-weight: 600;
        }}
        
        .stats-table td {{
            padding: 15px 20px;
            border-bottom: 1px solid #e8ecef;
        }}
        
        .stats-table tr:hover td {{
            background: #f8f9fa;
        }}
        
        .scroll-reveal {{
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.6s ease-out;
        }}
        
        .scroll-reveal.revealed {{
            opacity: 1;
            transform: translateY(0);
        }}
        
        .footer {{
            background: var(--primary);
            color: white;
            padding: 40px 80px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-dice"></i> Monte Carlo Analysis</h1>
            <div class="subtitle">Engelberg Property Investment - Risk & Uncertainty Assessment</div>
            <div class="meta">Generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')} | {num_simulations:,} Simulations</div>
        </div>
        
        <!-- Executive Summary -->
        <div class="section">
            <h2><i class="fas fa-chart-line"></i> Executive Summary</h2>
            <div class="kpi-grid">
                <div class="kpi-card scroll-reveal">
                    <div class="kpi-label"><i class="fas fa-calculator"></i> Mean NPV</div>
                    <div class="kpi-value {'positive' if stats['npv']['mean'] >= 0 else 'negative'}">{format_currency(stats['npv']['mean'])}</div>
                    <div class="kpi-description">Average across all simulations</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <div class="kpi-label"><i class="fas fa-chart-bar"></i> Median NPV</div>
                    <div class="kpi-value {'positive' if stats['npv']['median'] >= 0 else 'negative'}">{format_currency(stats['npv']['median'])}</div>
                    <div class="kpi-description">50th percentile</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <div class="kpi-label"><i class="fas fa-percent"></i> Probability NPV > 0</div>
                    <div class="kpi-value">{stats['npv']['positive_prob']*100:.1f}%</div>
                    <div class="kpi-description">Chance of positive returns</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <div class="kpi-label"><i class="fas fa-trending-up"></i> Mean IRR</div>
                    <div class="kpi-value positive">{stats['irr_with_sale']['mean']:.2f}%</div>
                    <div class="kpi-description">Average IRR (with sale)</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <div class="kpi-label"><i class="fas fa-arrow-down"></i> 10th Percentile NPV</div>
                    <div class="kpi-value {'positive' if stats['npv']['p10'] >= 0 else 'negative'}">{format_currency(stats['npv']['p10'])}</div>
                    <div class="kpi-description">Worst case (90% better)</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <div class="kpi-label"><i class="fas fa-arrow-up"></i> 90th Percentile NPV</div>
                    <div class="kpi-value positive">{format_currency(stats['npv']['p90'])}</div>
                    <div class="kpi-description">Best case (10% better)</div>
                </div>
            </div>
            
            <div class="info-box">
                <h3 style="margin-bottom: 15px; color: var(--primary);">
                    <i class="fas fa-info-circle"></i> Key Insights
                </h3>
                <p style="font-size: 1.05em; line-height: 1.8;">
                    Based on {num_simulations:,} Monte Carlo simulations, the investment shows a 
                    <strong>{stats['npv']['positive_prob']*100:.1f}% probability</strong> of generating positive NPV. 
                    The mean NPV of <strong>{format_currency(stats['npv']['mean'])}</strong> indicates a favorable expected return, 
                    with a median of <strong>{format_currency(stats['npv']['median'])}</strong>. 
                    The 10th percentile (worst case) shows <strong>{format_currency(stats['npv']['p10'])}</strong>, 
                    while the 90th percentile (best case) reaches <strong>{format_currency(stats['npv']['p90'])}</strong>.
                </p>
            </div>
        </div>
        
        <!-- Methodology -->
        <div class="section">
            <h2><i class="fas fa-book"></i> Methodology</h2>
            <div class="methodology-box">
                <h3>Monte Carlo Simulation Approach</h3>
                <p style="margin-bottom: 20px; font-size: 1.05em; line-height: 1.8;">
                    This analysis uses Monte Carlo simulation to assess the uncertainty and risk associated with the Engelberg property investment. 
                    The simulation randomly varies four critical parameters across their plausible ranges to generate {num_simulations:,} different scenarios.
                </p>
                
                <h3 style="margin-top: 25px; margin-bottom: 15px;">Parameters Varied</h3>
                <ul style="font-size: 1.05em; line-height: 2;">
                    <li><strong>Occupancy Rate:</strong> Uniform distribution from 30% to 70% (base case: ~50% weighted average)</li>
                    <li><strong>Average Daily Rate:</strong> Uniform distribution from 200 to 400 CHF (base case: ~324 CHF weighted average)</li>
                    <li><strong>Interest Rate:</strong> Uniform distribution from 1.2% to 3.5% (base case: 1.3%)</li>
                    <li><strong>Property Management Fee Rate:</strong> Uniform distribution from 20% to 35% (base case: 20%)</li>
                </ul>
                
                <h3 style="margin-top: 25px; margin-bottom: 15px;">Simulation Process</h3>
                <ul style="font-size: 1.05em; line-height: 2;">
                    <li>For each simulation, random values are drawn from uniform distributions for all four parameters</li>
                    <li>A complete 15-year financial projection is calculated for each scenario</li>
                    <li>NPV and IRR are computed using a 4% discount rate</li>
                    <li>Results are aggregated to show probability distributions and key statistics</li>
                </ul>
                
                <h3 style="margin-top: 25px; margin-bottom: 15px;">Assumptions Held Constant</h3>
                <ul style="font-size: 1.05em; line-height: 2;">
                    <li>Property purchase price: {format_currency(base_config.financing.purchase_price)}</li>
                    <li>Loan-to-value ratio: {base_config.financing.ltv*100:.0f}%</li>
                    <li>Amortization rate: {base_config.financing.amortization_rate*100:.1f}%</li>
                    <li>Inflation rate: 2% per year</li>
                    <li>Property appreciation: 1% per year</li>
                    <li>Other operating expenses (insurance, utilities, maintenance reserve)</li>
                </ul>
            </div>
        </div>
        
        <!-- Statistical Summary -->
        <div class="section">
            <h2><i class="fas fa-table"></i> Statistical Summary</h2>
            <table class="stats-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Mean</th>
                        <th>Median</th>
                        <th>Std Dev</th>
                        <th>Min</th>
                        <th>Max</th>
                        <th>10th %ile</th>
                        <th>90th %ile</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>NPV (CHF)</strong></td>
                        <td>{format_currency(stats['npv']['mean'])}</td>
                        <td>{format_currency(stats['npv']['median'])}</td>
                        <td>{format_currency(stats['npv']['std'])}</td>
                        <td>{format_currency(stats['npv']['min'])}</td>
                        <td>{format_currency(stats['npv']['max'])}</td>
                        <td>{format_currency(stats['npv']['p10'])}</td>
                        <td>{format_currency(stats['npv']['p90'])}</td>
                    </tr>
                    <tr>
                        <td><strong>IRR with Sale (%)</strong></td>
                        <td>{stats['irr_with_sale']['mean']:.2f}%</td>
                        <td>{stats['irr_with_sale']['median']:.2f}%</td>
                        <td>{stats['irr_with_sale']['std']:.2f}%</td>
                        <td>{stats['irr_with_sale']['min']:.2f}%</td>
                        <td>{stats['irr_with_sale']['max']:.2f}%</td>
                        <td>{stats['irr_with_sale']['p5']:.2f}%</td>
                        <td>{stats['irr_with_sale']['p95']:.2f}%</td>
                    </tr>
                    <tr>
                        <td><strong>Annual Cash Flow (CHF)</strong></td>
                        <td>{format_currency(stats['annual_cash_flow']['mean'])}</td>
                        <td>{format_currency(stats['annual_cash_flow']['median'])}</td>
                        <td>{format_currency(stats['annual_cash_flow']['std'])}</td>
                        <td>{format_currency(stats['annual_cash_flow']['min'])}</td>
                        <td>{format_currency(stats['annual_cash_flow']['max'])}</td>
                        <td>-</td>
                        <td>-</td>
                    </tr>
                </tbody>
            </table>
            
            <div class="info-box" style="margin-top: 30px;">
                <h3 style="margin-bottom: 15px; color: var(--primary);">
                    <i class="fas fa-chart-pie"></i> Base Case Comparison
                </h3>
                <p style="font-size: 1.05em; line-height: 1.8;">
                    <strong>Base Case NPV:</strong> {format_currency(base_npv)} | 
                    <strong>Base Case IRR:</strong> {base_irr['irr_with_sale_pct']:.2f}%<br>
                    The base case falls at the <strong>{(df['npv'] <= base_npv).sum() / len(df) * 100:.1f}th percentile</strong> of the Monte Carlo distribution, 
                    meaning {(df['npv'] <= base_npv).sum() / len(df) * 100:.1f}% of simulations show worse results than the base case.
                </p>
            </div>
        </div>
        
        <!-- Visualizations -->
        <div class="section">
            <h2><i class="fas fa-chart-bar"></i> Results Visualization</h2>
            <p style="font-size: 1.1em; color: #555; margin-bottom: 30px;">
                The following charts show the distribution of outcomes from {num_simulations:,} Monte Carlo simulations.
                Each simulation randomly varies four key parameters (Occupancy Rate, Daily Rate, Interest Rate, Management Fee)
                to assess the range of possible investment outcomes.
            </p>
            {charts_html}
        </div>
        
        <!-- Additional Analysis: Key Sensitivity Correlations -->
        <div class="section">
            <h2><i class="fas fa-project-diagram"></i> Parameter Correlation Analysis</h2>
            <p style="font-size: 1.1em; color: #555; margin-bottom: 30px;">
                These charts show how different parameter combinations affect NPV and IRR outcomes.
            </p>
            <div class="chart-container scroll-reveal">
                <div class="chart-title">NPV vs Key Parameters</div>
                {correlation_chart_html if correlation_chart_html else '<div id="correlation_charts" style="min-height: 600px;"></div>'}
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p style="font-size: 1.1em; margin-bottom: 10px;">Engelberg Property Investment - Monte Carlo Analysis</p>
            <p>This analysis was generated automatically by the Engelberg Property Investment Simulation</p>
        </div>
    </div>
    
    <script>
        // Scroll reveal animation
        (function() {{
            const observerOptions = {{
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            }};
            
            const observer = new IntersectionObserver(function(entries) {{
                entries.forEach(entry => {{
                    if (entry.isIntersecting) {{
                        entry.target.classList.add('revealed');
                        observer.unobserve(entry.target);
                    }}
                }});
            }}, observerOptions);
            
            document.querySelectorAll('.scroll-reveal').forEach(el => {{
                observer.observe(el);
            }});
        }})();
        
        // Initialize Plotly charts
        {plotly_js}
        
    </script>
</body>
</html>
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"[+] HTML report generated: {output_path}")


def export_to_excel(df: pd.DataFrame, stats: dict, output_path: str = "monte_carlo_results.xlsx"):
    """Export Monte Carlo results to Excel."""
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Summary statistics
        summary_data = {
            'Metric': [
                'Mean NPV (CHF)',
                'Median NPV (CHF)',
                'Std Dev NPV (CHF)',
                'Min NPV (CHF)',
                'Max NPV (CHF)',
                '10th Percentile NPV (CHF)',
                '90th Percentile NPV (CHF)',
                'Probability NPV > 0 (%)',
                'Mean IRR with Sale (%)',
                'Median IRR with Sale (%)',
                'Mean Annual Cash Flow (CHF)',
                'Probability Positive Cash Flow (%)',
            ],
            'Value': [
                stats['npv']['mean'],
                stats['npv']['median'],
                stats['npv']['std'],
                stats['npv']['min'],
                stats['npv']['max'],
                stats['npv']['p10'],
                stats['npv']['p90'],
                stats['npv']['positive_prob'] * 100,
                stats['irr_with_sale']['mean'],
                stats['irr_with_sale']['median'],
                stats['annual_cash_flow']['mean'],
                stats['annual_cash_flow']['positive_prob'] * 100,
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary Statistics", index=False)
        
        # All simulation results (sample of 1000 for performance)
        sample_df = df.sample(min(1000, len(df))) if len(df) > 1000 else df
        sample_df.to_excel(writer, sheet_name="Simulation Results", index=False)
        
        # Parameter distributions
        param_stats = {
            'Parameter': ['Occupancy Rate', 'Daily Rate (CHF)', 'Interest Rate (%)', 'Management Fee Rate (%)'],
            'Min': [
                df['occupancy_rate'].min() * 100,
                df['daily_rate'].min(),
                df['interest_rate'].min() * 100,
                df['management_fee_rate'].min() * 100
            ],
            'Max': [
                df['occupancy_rate'].max() * 100,
                df['daily_rate'].max(),
                df['interest_rate'].max() * 100,
                df['management_fee_rate'].max() * 100
            ],
            'Mean': [
                df['occupancy_rate'].mean() * 100,
                df['daily_rate'].mean(),
                df['interest_rate'].mean() * 100,
                df['management_fee_rate'].mean() * 100
            ],
            'Std Dev': [
                df['occupancy_rate'].std() * 100,
                df['daily_rate'].std(),
                df['interest_rate'].std() * 100,
                df['management_fee_rate'].std() * 100
            ]
        }
        pd.DataFrame(param_stats).to_excel(writer, sheet_name="Parameter Distributions", index=False)
    
    print(f"[+] Excel file exported: {output_path}")


def main():
    """Main function to run Monte Carlo analysis."""
    print("=" * 70)
    print("Monte Carlo Analysis - Engelberg Property Investment")
    print("=" * 70)
    print()
    
    # Load base case configuration
    # IMPORTANT: This must use the SAME base case as analysis_base_case.py
    # All Monte Carlo simulations reference this single source of truth
    print("[*] Loading base case configuration...")
    base_config = create_base_case_config()
    
    # Run Monte Carlo simulation
    num_simulations = 10000
    print(f"[*] Running {num_simulations:,} Monte Carlo simulations...")
    print("     This may take several minutes...")
    print()
    
    df = run_monte_carlo_simulation(base_config, num_simulations=num_simulations)
    
    # Calculate statistics
    print("[*] Calculating statistics...")
    stats = calculate_statistics(df)
    
    # Create charts
    print("[*] Generating charts...")
    charts = create_monte_carlo_charts(df, stats)
    
    # Excel export disabled - user only uses HTML reports
    # print("[*] Exporting results to Excel...")
    # export_to_excel(df, stats)
    
    # Ensure output directory exists
    import os
    os.makedirs("output", exist_ok=True)
    
    # Generate HTML report
    print("[*] Generating HTML report...")
    generate_monte_carlo_html(df, stats, charts, base_config, num_simulations)
    
    print()
    print("=" * 70)
    print("[+] Monte Carlo analysis complete!")
    print("=" * 70)
    # print(f"[+] Excel file: monte_carlo_results.xlsx")  # Excel export disabled
    print(f"[+] HTML report: output/report_monte_carlo.html")
    print("=" * 70)
    print()
    print("KEY RESULTS:")
    print(f"  Mean NPV: {stats['npv']['mean']:>15,.0f} CHF")
    print(f"  Median NPV: {stats['npv']['median']:>13,.0f} CHF")
    print(f"  Probability NPV > 0: {stats['npv']['positive_prob']*100:>8.1f}%")
    print(f"  10th Percentile: {stats['npv']['p10']:>15,.0f} CHF")
    print(f"  90th Percentile: {stats['npv']['p90']:>15,.0f} CHF")
    print("=" * 70)


if __name__ == "__main__":
    main()

