"""
Main script to run the base case simulation and generate outputs:
- XLSX file with detailed results
- HTML report with charts and KPIs
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from simulation import (
    create_base_case_config,
    compute_annual_cash_flows,
    compute_detailed_expenses,
    compute_15_year_projection,
    calculate_irrs_from_projection
)
from datetime import datetime
import os


def export_to_excel(results: dict, config, projection_15yr: List[dict], irr_results: dict = None, output_path: str = "base_case_results.xlsx"):
    """Export results to Excel with multiple sheets including 15-year projection."""
    
    # Create Excel writer
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        
        # Sheet 1: Executive Summary
        summary_data = {
            "Category": [
                "Property Location",
                "Purchase Price",
                "Number of Owners",
                "Owner Nights per Person",
                "Total Owner Nights",
                "Rentable Nights",
                "Occupancy Rate",
                "Rented Nights",
                "Average Daily Rate",
                "Gross Rental Income",
                "Net Operating Income",
                "Cash Flow After Debt Service",
                "Cash Flow per Owner",
                "",
                "Key Insight",
            ],
            "Value": [
                "Engelberg, Switzerland",
                f"{results['purchase_price']:,.0f} CHF",
                f"{config.financing.num_owners}",
                f"{config.rental.owner_nights_per_person}",
                f"{results['total_owner_nights']:.0f}",
                f"{results['rentable_nights']:.0f}",
                f"{results.get('overall_occupancy_rate', config.rental.occupancy_rate)*100:.1f}%",
                f"{results['rented_nights']:.0f}",
                f"{results.get('average_daily_rate', config.rental.average_daily_rate):.0f} CHF",
                f"{results['gross_rental_income']:,.0f} CHF",
                f"{results['net_operating_income']:,.0f} CHF",
                f"{results['cash_flow_after_debt_service']:,.0f} CHF",
                f"{results['cash_flow_per_owner']:,.0f} CHF",
                "",
                f"Each owner contributes {abs(results['cash_flow_per_owner']):,.0f} CHF annually, but receives 5 nights of personal use plus potential property appreciation and tax benefits." if results['cash_flow_after_debt_service'] < 0 else f"Each owner receives {results['cash_flow_per_owner']:,.0f} CHF annually plus 5 nights of personal use.",
            ]
        }
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name="Executive Summary", index=False)
        
        # Sheet 2: Summary KPIs
        kpi_data = {
            "Metric": [
                "Purchase Price (CHF)",
                "Loan Amount (CHF)",
                "Equity Total (CHF)",
                "Equity per Owner (CHF)",
                "Gross Rental Income (CHF)",
                "Net Operating Income (CHF)",
                "Cash Flow After Debt Service (CHF)",
                "Cash Flow per Owner (CHF)",
                "Cap Rate (%)",
                "Levered Cash-on-Cash Return (%)",
                "Debt Coverage Ratio",
                "Operating Expense Ratio (%)",
            ],
            "Value": [
                results["purchase_price"],
                results["loan_amount"],
                results["equity_total"],
                results["equity_per_owner"],
                results["gross_rental_income"],
                results["net_operating_income"],
                results["cash_flow_after_debt_service"],
                results["cash_flow_per_owner"],
                results["cap_rate_pct"],
                results["cash_on_cash_return_pct"],
                results["debt_coverage_ratio"],
                results["operating_expense_ratio_pct"],
            ]
        }
        df_kpis = pd.DataFrame(kpi_data)
        df_kpis.to_excel(writer, sheet_name="KPIs", index=False)
        
        # Sheet 2b: IRR Metrics (if provided)
        if irr_results:
            irr_data = {
                "Metric": [
                    "Equity IRR (with Sale) (%)",
                    "Equity IRR (without Sale) (%)",
                    "Project IRR - Unlevered (with Sale) (%)",
                    "Project IRR - Unlevered (without Sale) (%)",
                    "Levered Cash-on-Cash Return (%)",
                ],
                "Value": [
                    irr_results.get('equity_irr_with_sale_pct', irr_results.get('irr_with_sale_pct', 0)),
                    irr_results.get('equity_irr_without_sale_pct', irr_results.get('irr_without_sale_pct', 0)),
                    irr_results.get('project_irr_with_sale_pct', 0),
                    irr_results.get('project_irr_without_sale_pct', 0),
                    results["cash_on_cash_return_pct"],
                ]
            }
            df_irr = pd.DataFrame(irr_data)
            df_irr.to_excel(writer, sheet_name="IRR Metrics", index=False)
        
        # Sheet 3: Revenue & Expenses
        revenue_expenses_data = {
            "Category": [
                "Gross Rental Income",
                "",
                "Operating Expenses:",
                "  Property Management (includes Cleaning)",
                "  Tourist Tax",
                "  Insurance",
                "  Utilities",
                "  Maintenance Reserve",
                "Total Operating Expenses",
                "",
                "Net Operating Income",
                "",
                "Debt Service:",
                "  Interest Payment",
                "  Amortization Payment",
                "Total Debt Service",
                "",
                "Cash Flow After Debt Service",
            ],
            "Amount (CHF)": [
                results["gross_rental_income"],
                "",
                "",
                results["property_management_cost"],
                results["tourist_tax"],
                results["insurance"],
                results["utilities"],
                results["maintenance_reserve"],
                results["total_operating_expenses"],
                "",
                results["net_operating_income"],
                "",
                "",
                results["interest_payment"],
                results["amortization_payment"],
                results["debt_service"],
                "",
                results["cash_flow_after_debt_service"],
            ]
        }
        df_revenue_expenses = pd.DataFrame(revenue_expenses_data)
        df_revenue_expenses.to_excel(writer, sheet_name="Revenue & Expenses", index=False)
        
        # Sheet 4: Rental Metrics
        rental_data = {
            "Metric": [
                "Days per Year",
                "Total Owner Nights",
                "Rentable Nights",
                "Rented Nights",
                "Overall Occupancy Rate (%)",
                "Weighted Average Daily Rate (CHF)",
                "Average Length of Stay (nights)",
                "Average Guests per Night",
            ],
            "Value": [
                config.rental.days_per_year,
                results["total_owner_nights"],
                results["rentable_nights"],
                results["rented_nights"],
                results.get('overall_occupancy_rate', config.rental.occupancy_rate) * 100,
                results.get('average_daily_rate', config.rental.average_daily_rate),
                config.expenses.average_length_of_stay,
                config.expenses.avg_guests_per_night,
            ]
        }
        df_rental = pd.DataFrame(rental_data)
        df_rental.to_excel(writer, sheet_name="Rental Metrics", index=False)
        
        # Sheet 4b: Seasonal Breakdown (if seasons are defined)
        if 'seasonal_breakdown' in results and results['seasonal_breakdown']:
            seasonal_rows = []
            for season_name, season_data in results['seasonal_breakdown'].items():
                seasonal_rows.append({
                    "Season": season_name,
                    "Available Nights": season_data['available_nights'],
                    "Rented Nights": season_data['nights'],
                    "Occupancy Rate (%)": season_data['occupancy'] * 100,
                    "Average Daily Rate (CHF)": season_data['rate'],
                    "Season Income (CHF)": season_data['income'],
                })
            df_seasonal = pd.DataFrame(seasonal_rows)
            df_seasonal.to_excel(writer, sheet_name="Seasonal Breakdown", index=False)
        
        # Sheet 5: Financing Details
        financing_data = {
            "Parameter": [
                "Purchase Price (CHF)",
                "Loan-to-Value Ratio (%)",
                "Loan Amount (CHF)",
                "Equity Total (CHF)",
                "Number of Owners",
                "Equity per Owner (CHF)",
                "Interest Rate (%)",
                "Annual Interest Payment (CHF)",
                "Amortization Rate (%)",
                "Annual Amortization Payment (CHF)",
                "Total Annual Debt Service (CHF)",
            ],
            "Value": [
                config.financing.purchase_price,
                config.financing.ltv * 100,
                config.financing.loan_amount,
                config.financing.equity_total,
                config.financing.num_owners,
                config.financing.equity_per_owner,
                config.financing.interest_rate * 100,
                config.financing.annual_interest,
                config.financing.amortization_rate * 100,
                config.financing.annual_amortization,
                config.financing.annual_debt_service,
            ]
        }
        df_financing = pd.DataFrame(financing_data)
        df_financing.to_excel(writer, sheet_name="Financing", index=False)
        
        # Sheet 6: Assumptions
        assumptions_data = {
            "Category": [
                "Financing",
                "",
                "",
                "",
                "",
                "Rental",
                "",
                "",
                "",
                "Expenses",
                "",
                "",
                "",
                "",
                "",
                "",
            ],
            "Parameter": [
                "Purchase Price",
                "Loan-to-Value",
                "Interest Rate",
                "Amortization Rate",
                "Number of Owners",
                "Owner Nights per Person",
                "Occupancy Rate",
                "Average Daily Rate",
                "Days per Year",
                "Property Management Fee Rate (includes Cleaning)",
                "Average Length of Stay",
                "Tourist Tax per Person per Night",
                "Average Guests per Night",
                "Insurance Annual",
                "Utilities Annual",
                "Maintenance Rate",
            ],
            "Value": [
                f"{config.financing.purchase_price:,.0f} CHF",
                f"{config.financing.ltv*100:.1f}%",
                f"{config.financing.interest_rate*100:.2f}%",
                f"{config.financing.amortization_rate*100:.1f}%",
                f"{config.financing.num_owners}",
                f"{config.rental.owner_nights_per_person}",
                f"{config.rental.occupancy_rate*100:.1f}%",
                f"{config.rental.average_daily_rate:.0f} CHF",
                f"{config.rental.days_per_year}",
                f"{config.expenses.property_management_fee_rate*100:.1f}% (cleaning included)",
                f"{config.expenses.average_length_of_stay:.1f}",
                f"{config.expenses.tourist_tax_per_person_per_night:.0f} CHF",
                f"{config.expenses.avg_guests_per_night:.1f}",
                f"{config.expenses.insurance_annual:,.0f} CHF",
                f"{config.expenses.utilities_annual:,.0f} CHF",
                f"{config.expenses.maintenance_rate*100:.1f}%",
            ]
        }
        df_assumptions = pd.DataFrame(assumptions_data)
        df_assumptions.to_excel(writer, sheet_name="Assumptions", index=False)
        
        # Sheet 7: 15-Year Projection
        projection_data = []
        for year_data in projection_15yr:
            projection_data.append({
                "Year": year_data['year'],
                "Gross Rental Income (CHF)": year_data['gross_rental_income'],
                "Operating Expenses (CHF)": year_data['total_operating_expenses'],
                "Net Operating Income (CHF)": year_data['net_operating_income'],
                "Interest Payment (CHF)": year_data['interest_payment'],
                "Amortization Payment (CHF)": year_data['amortization_payment'],
                "Total Debt Service (CHF)": year_data['debt_service'],
                "Cash Flow After Debt (CHF)": year_data['cash_flow_after_debt_service'],
                "Cash Flow per Owner (CHF)": year_data['cash_flow_per_owner'],
                "Remaining Loan Balance (CHF)": year_data['remaining_loan_balance'],
                "Debt Coverage Ratio": year_data['debt_coverage_ratio'],
            })
        df_projection = pd.DataFrame(projection_data)
        df_projection.to_excel(writer, sheet_name="15-Year Projection", index=False)
    
    print(f"[+] Excel file exported: {output_path}")


def create_charts(results: dict, config, projection_15yr: List[dict]) -> List[go.Figure]:
    """Create all charts for the HTML report including 15-year projections."""
    charts = []
    
    # Chart 1: Revenue vs Expenses Breakdown
    fig1 = go.Figure()
    
    # Revenue
    fig1.add_trace(go.Bar(
        name="Gross Rental Income",
        x=["Revenue"],
        y=[results["gross_rental_income"]],
        marker_color='#2ecc71',
        text=[f"{results['gross_rental_income']:,.0f}"],
        textposition='auto',
    ))
    
    # Expenses
    expenses_breakdown = compute_detailed_expenses(config)
    expense_names = list(expenses_breakdown.keys())
    expense_values = list(expenses_breakdown.values())
    
    fig1.add_trace(go.Bar(
        name="Total Operating Expenses",
        x=["Expenses"],
        y=[results["total_operating_expenses"]],
        marker_color='#e74c3c',
        text=[f"{results['total_operating_expenses']:,.0f}"],
        textposition='auto',
    ))
    
    fig1.add_trace(go.Bar(
        name="Debt Service",
        x=["Debt Service"],
        y=[results["debt_service"]],
        marker_color='#f39c12',
        text=[f"{results['debt_service']:,.0f}"],
        textposition='auto',
    ))
    
    fig1.update_layout(
        title="Revenue vs Expenses vs Debt Service",
        yaxis_title="Amount (CHF)",
        barmode='group',
        height=400,
        showlegend=True,
    )
    charts.append(("revenue_expenses", fig1))
    
    # Chart 2: Operating Expenses Breakdown (Pie Chart)
    fig2 = go.Figure(data=[go.Pie(
        labels=expense_names,
        values=expense_values,
        hole=0.4,
        textinfo='label+percent',
        texttemplate='%{label}<br>%{value:,.0f} CHF<br>(%{percent})',
    )])
    fig2.update_layout(
        title="Operating Expenses Breakdown",
        height=400,
    )
    charts.append(("expenses_pie", fig2))
    
    # Chart 3: Cash Flow Waterfall
    fig3 = go.Figure(go.Waterfall(
        name="Cash Flow",
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["Gross Rental<br>Income", "Operating<br>Expenses", "Debt<br>Service", "Cash Flow<br>After Debt"],
        textposition="outside",
        text=[
            f"{results['gross_rental_income']:,.0f}",
            f"-{results['total_operating_expenses']:,.0f}",
            f"-{results['debt_service']:,.0f}",
            f"{results['cash_flow_after_debt_service']:,.0f}",
        ],
        y=[
            results["gross_rental_income"],
            -results["total_operating_expenses"],
            -results["debt_service"],
            results["cash_flow_after_debt_service"],
        ],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))
    fig3.update_layout(
        title="Cash Flow Waterfall",
        yaxis_title="Amount (CHF)",
        height=400,
        showlegend=False,
    )
    charts.append(("cashflow_waterfall", fig3))
    
    # Chart 4: Key Performance Indicators (Gauge Charts)
    # Use individual figures to avoid text overlay issues
    fig4a = go.Figure(go.Indicator(
        mode="gauge+number",
        value=results["cap_rate_pct"],
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "<b>Cap Rate (%)</b>", 'font': {'size': 16}},
        number={'font': {'size': 24}},
        gauge={
            'axis': {'range': [None, 10], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#2ecc71"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 3], 'color': "#e74c3c"},
                {'range': [3, 6], 'color': "#f39c12"},
                {'range': [6, 10], 'color': "#2ecc71"}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 5
            }
        }
    ))
    fig4a.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    charts.append(("kpi_cap_rate", fig4a))
    
    fig4b = go.Figure(go.Indicator(
        mode="gauge+number",
        value=results["cash_on_cash_return_pct"],
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "<b>Cash-on-Cash Return (%)</b>", 'font': {'size': 16}},
        number={'font': {'size': 24}},
        gauge={
            'axis': {'range': [None, 20], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#3498db"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 5], 'color': "#e74c3c"},
                {'range': [5, 10], 'color': "#f39c12"},
                {'range': [10, 20], 'color': "#2ecc71"}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 10
            }
        }
    ))
    fig4b.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    charts.append(("kpi_cash_on_cash", fig4b))
    
    fig4c = go.Figure(go.Indicator(
        mode="gauge+number",
        value=results["debt_coverage_ratio"],
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "<b>Debt Coverage Ratio</b>", 'font': {'size': 16}},
        number={'font': {'size': 24}},
        gauge={
            'axis': {'range': [0, 3], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#9b59b6"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 1], 'color': "#e74c3c"},
                {'range': [1, 1.5], 'color': "#f39c12"},
                {'range': [1.5, 3], 'color': "#2ecc71"}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 1.25
            }
        }
    ))
    fig4c.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    charts.append(("kpi_debt_coverage", fig4c))
    
    fig4d = go.Figure(go.Indicator(
        mode="gauge+number",
        value=results["operating_expense_ratio_pct"],
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "<b>Operating Expense Ratio (%)</b>", 'font': {'size': 16}},
        number={'font': {'size': 24}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#e67e22"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': "#2ecc71"},
                {'range': [50, 70], 'color': "#f39c12"},
                {'range': [70, 100], 'color': "#e74c3c"}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 60
            }
        }
    ))
    fig4d.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    charts.append(("kpi_operating_expense", fig4d))
    
    # Chart 5: Operating Expenses Bar Chart
    fig5 = go.Figure()
    fig5.add_trace(go.Bar(
        x=expense_names,
        y=expense_values,
        marker_color='#3498db',
        text=[f"{v:,.0f}" for v in expense_values],
        textposition='auto',
    ))
    fig5.update_layout(
        title="Operating Expenses Breakdown",
        xaxis_title="Expense Category",
        yaxis_title="Amount (CHF)",
        height=400,
    )
    charts.append(("expenses_bar", fig5))
    
    # Chart 6: 15-Year Cash Flow Projection
    years = [y['year'] for y in projection_15yr]
    cash_flows = [y['cash_flow_after_debt_service'] for y in projection_15yr]
    cash_flows_per_owner = [y['cash_flow_per_owner'] for y in projection_15yr]
    
    fig6 = go.Figure()
    fig6.add_trace(go.Scatter(
        x=years,
        y=cash_flows,
        mode='lines+markers',
        name='Total Cash Flow',
        line=dict(color='#3498db', width=3),
        marker=dict(size=8),
    ))
    fig6.add_trace(go.Scatter(
        x=years,
        y=cash_flows_per_owner,
        mode='lines+markers',
        name='Cash Flow per Owner',
        line=dict(color='#2ecc71', width=3),
        marker=dict(size=8),
    ))
    fig6.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Break-even")
    fig6.update_layout(
        title="15-Year Cash Flow Projection",
        xaxis_title="Year",
        yaxis_title="Cash Flow (CHF)",
        height=500,
        hovermode='x unified',
    )
    charts.append(("cashflow_15yr", fig6))
    
    # Chart 7: 15-Year Loan Balance and Debt Service
    loan_balances = [y['remaining_loan_balance'] for y in projection_15yr]
    debt_services = [y['debt_service'] for y in projection_15yr]
    
    fig7 = make_subplots(specs=[[{"secondary_y": True}]])
    fig7.add_trace(
        go.Scatter(x=years, y=loan_balances, name="Remaining Loan Balance", line=dict(color='#e74c3c', width=3)),
        secondary_y=False,
    )
    fig7.add_trace(
        go.Scatter(x=years, y=debt_services, name="Debt Service", line=dict(color='#f39c12', width=3)),
        secondary_y=True,
    )
    fig7.update_xaxes(title_text="Year")
    fig7.update_yaxes(title_text="Loan Balance (CHF)", secondary_y=False)
    fig7.update_yaxes(title_text="Debt Service (CHF)", secondary_y=True)
    fig7.update_layout(
        title="15-Year Loan Balance & Debt Service",
        height=500,
        hovermode='x unified',
    )
    charts.append(("loan_15yr", fig7))
    
    # Chart 8: 15-Year Revenue vs Expenses
    revenues = [y['gross_rental_income'] for y in projection_15yr]
    expenses = [y['total_operating_expenses'] for y in projection_15yr]
    noi = [y['net_operating_income'] for y in projection_15yr]
    
    fig8 = go.Figure()
    fig8.add_trace(go.Scatter(x=years, y=revenues, mode='lines+markers', name='Gross Rental Income', line=dict(color='#2ecc71', width=3)))
    fig8.add_trace(go.Scatter(x=years, y=expenses, mode='lines+markers', name='Operating Expenses', line=dict(color='#e74c3c', width=3)))
    fig8.add_trace(go.Scatter(x=years, y=noi, mode='lines+markers', name='Net Operating Income', line=dict(color='#3498db', width=3)))
    fig8.update_layout(
        title="15-Year Revenue & Expenses Projection",
        xaxis_title="Year",
        yaxis_title="Amount (CHF)",
        height=500,
        hovermode='x unified',
    )
    charts.append(("revenue_expenses_15yr", fig8))
    
    return charts


def generate_apexcharts_html(results: dict, config, projection_15yr: List[dict]) -> str:
    """Generate ApexCharts HTML for all visualizations with proper JavaScript formatting."""
    import json
    
    # Chart 1: Revenue vs Expenses vs Debt Service
    revenue_expenses_data = json.dumps({
        "chart": {"type": "bar", "height": 400, "toolbar": {"show": True}},
        "plotOptions": {"bar": {"horizontal": False, "columnWidth": "60%", "dataLabels": {"position": "top"}}},
        "dataLabels": {"enabled": True},
        "series": [{
            "name": "Gross Rental Income",
            "data": [results["gross_rental_income"]]
        }, {
            "name": "Operating Expenses",
            "data": [results["total_operating_expenses"]]
        }, {
            "name": "Debt Service",
            "data": [results["debt_service"]]
        }],
        "xaxis": {"categories": ["Financial Summary"]},
        "colors": ["#2ecc71", "#e74c3c", "#f39c12"],
        "title": {"text": "Revenue vs Expenses vs Debt Service", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
        "legend": {"position": "top"}
    })
    
    # Chart 2: Operating Expenses Pie
    expenses_breakdown = compute_detailed_expenses(config)
    expenses_pie_data = json.dumps({
        "chart": {"type": "donut", "height": 400, "toolbar": {"show": True}},
        "labels": list(expenses_breakdown.keys()),
        "series": list(expenses_breakdown.values()),
        "dataLabels": {"enabled": True},
        "colors": ["#3498db", "#9b59b6", "#e67e22", "#1abc9c", "#f39c12", "#e74c3c"],
        "title": {"text": "Operating Expenses Breakdown", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
        "legend": {"position": "bottom"}
    })
    
    # Chart 3: Cash Flow Waterfall
    waterfall_data = json.dumps({
        "chart": {"type": "bar", "height": 400, "toolbar": {"show": True}},
        "plotOptions": {"bar": {"horizontal": False, "columnWidth": "60%"}},
        "dataLabels": {"enabled": True},
        "series": [{
            "name": "Cash Flow",
            "data": [
                results["gross_rental_income"],
                -results["total_operating_expenses"],
                -results["debt_service"],
                results["cash_flow_after_debt_service"]
            ]
        }],
        "xaxis": {"categories": ["Gross Rental Income", "Operating Expenses", "Debt Service", "Cash Flow After Debt"]},
        "colors": ["#3498db"],
        "title": {"text": "Cash Flow Waterfall", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}}
    })
    
    # Chart 4: 15-Year Cash Flow Projection
    years = [str(y['year']) for y in projection_15yr]
    cash_flows = [y['cash_flow_after_debt_service'] for y in projection_15yr]
    cash_flows_per_owner = [y['cash_flow_per_owner'] for y in projection_15yr]
    
    cashflow_15yr_data = json.dumps({
        "chart": {"type": "line", "height": 500, "toolbar": {"show": True}, "zoom": {"enabled": True}},
        "stroke": {"curve": "smooth", "width": 3},
        "markers": {"size": 5, "hover": {"size": 8}},
        "series": [{
            "name": "Total Cash Flow",
            "data": cash_flows
        }, {
            "name": "Cash Flow per Owner",
            "data": cash_flows_per_owner
        }],
        "xaxis": {"categories": years, "title": {"text": "Year"}},
        "yaxis": {"title": {"text": "Cash Flow (CHF)"}},
        "colors": ["#3498db", "#2ecc71"],
        "title": {"text": "15-Year Cash Flow Projection", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
        "legend": {"position": "top"},
        "grid": {"borderColor": "#e7e7e7", "row": {"colors": ["#f3f3f3", "transparent"], "opacity": 0.5}},
        "annotations": {"yaxis": [{"y": 0, "borderColor": "#999", "strokeDashArray": 5, "label": {"text": "Break-even", "style": {"color": "#999", "background": "#fff"}}}]}
    })
    
    # Chart 5: 15-Year Loan Balance & Debt Service
    loan_balances = [y['remaining_loan_balance'] for y in projection_15yr]
    debt_services = [y['debt_service'] for y in projection_15yr]
    
    loan_data = json.dumps({
        "chart": {"type": "line", "height": 500, "toolbar": {"show": True}, "zoom": {"enabled": True}},
        "stroke": {"curve": "smooth", "width": 3},
        "markers": {"size": 5, "hover": {"size": 8}},
        "series": [{
            "name": "Remaining Loan Balance",
            "data": loan_balances
        }, {
            "name": "Debt Service",
            "data": debt_services
        }],
        "xaxis": {"categories": years, "title": {"text": "Year"}},
        "yaxis": {"title": {"text": "Amount (CHF)"}},
        "colors": ["#e74c3c", "#f39c12"],
        "title": {"text": "15-Year Loan Balance & Debt Service", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
        "legend": {"position": "top"},
        "grid": {"borderColor": "#e7e7e7", "row": {"colors": ["#f3f3f3", "transparent"], "opacity": 0.5}}
    })
    
    # Chart 6: 15-Year Revenue & Expenses
    revenues = [y['gross_rental_income'] for y in projection_15yr]
    expenses = [y['total_operating_expenses'] for y in projection_15yr]
    noi = [y['net_operating_income'] for y in projection_15yr]
    
    revenue_expenses_15yr_data = json.dumps({
        "chart": {"type": "line", "height": 500, "toolbar": {"show": True}, "zoom": {"enabled": True}},
        "stroke": {"curve": "smooth", "width": 3},
        "markers": {"size": 5, "hover": {"size": 8}},
        "series": [{
            "name": "Gross Rental Income",
            "data": revenues
        }, {
            "name": "Operating Expenses",
            "data": expenses
        }, {
            "name": "Net Operating Income",
            "data": noi
        }],
        "xaxis": {"categories": years, "title": {"text": "Year"}},
        "yaxis": {"title": {"text": "Amount (CHF)"}},
        "colors": ["#2ecc71", "#e74c3c", "#3498db"],
        "title": {"text": "15-Year Revenue & Expenses Projection", "align": "left", "style": {"fontSize": "18px", "fontWeight": "600"}},
        "legend": {"position": "top"},
        "grid": {"borderColor": "#e7e7e7", "row": {"colors": ["#f3f3f3", "transparent"], "opacity": 0.5}}
    })
    
    # Generate HTML with ApexCharts - enhanced for dashboard layout
    charts_html = f"""
    <!-- Revenue vs Expenses Chart -->
    <div class="chart-container scroll-reveal">
        <div class="chart-title"><i class="fas fa-chart-bar"></i> Revenue vs Expenses vs Debt Service</div>
        <div id="revenueExpensesChart" style="min-height: 400px;"></div>
    </div>
    
    <!-- Operating Expenses Pie Chart -->
    <div class="chart-container scroll-reveal">
        <div class="chart-title"><i class="fas fa-chart-pie"></i> Operating Expenses Breakdown</div>
        <div id="expensesPieChart" style="min-height: 400px;"></div>
    </div>
    
    <!-- Cash Flow Waterfall Chart -->
    <div class="chart-container scroll-reveal">
        <div class="chart-title"><i class="fas fa-water"></i> Cash Flow Waterfall</div>
        <div id="waterfallChart" style="min-height: 400px;"></div>
    </div>
    
    <!-- 15-Year Cash Flow Chart -->
    <div class="chart-container full-width scroll-reveal">
        <div class="chart-title"><i class="fas fa-chart-line"></i> 15-Year Cash Flow Projection</div>
        <div id="cashflow15yrChart" style="min-height: 500px;"></div>
    </div>
    
    <!-- 15-Year Loan Balance Chart -->
    <div class="chart-container scroll-reveal">
        <div class="chart-title"><i class="fas fa-credit-card"></i> Loan Balance & Debt Service</div>
        <div id="loanChart" style="min-height: 500px;"></div>
    </div>
    
    <!-- 15-Year Revenue & Expenses Chart -->
    <div class="chart-container scroll-reveal">
        <div class="chart-title"><i class="fas fa-chart-area"></i> Revenue & Expenses Projection</div>
        <div id="revenueExpenses15yrChart" style="min-height: 500px;"></div>
    </div>
    
    <!-- ApexCharts Initialization Script -->
    <script>
        // Wait for ApexCharts library to load
        function initCharts() {{
            if (typeof ApexCharts === 'undefined') {{
                console.log('Waiting for ApexCharts library to load...');
                setTimeout(initCharts, 100);
                return;
            }}
            
            console.log('ApexCharts loaded, initializing charts...');
            
            // Currency formatter function
            function formatCHF(val) {{
                return new Intl.NumberFormat('de-CH', {{style: 'currency', currency: 'CHF', maximumFractionDigits: 0}}).format(val);
            }}
            
            try {{
                // Chart 1: Revenue vs Expenses
                var revenueExpensesOptions = {revenue_expenses_data};
                revenueExpensesOptions.dataLabels.formatter = formatCHF;
                revenueExpensesOptions.yaxis = revenueExpensesOptions.yaxis || {{}};
                revenueExpensesOptions.yaxis.labels = {{formatter: formatCHF}};
                revenueExpensesOptions.tooltip = {{y: {{formatter: formatCHF}}}};
                var revenueExpensesChart = new ApexCharts(document.querySelector("#revenueExpensesChart"), revenueExpensesOptions);
                revenueExpensesChart.render();
                
                // Chart 2: Operating Expenses Pie
                var expensesPieOptions = {expenses_pie_data};
                expensesPieOptions.dataLabels.formatter = function(val, opts) {{
                    var label = opts.w.config.labels[opts.seriesIndex];
                    var value = formatCHF(opts.w.globals.series[opts.seriesIndex]);
                    var percent = opts.w.globals.seriesPercent[opts.seriesIndex][0].toFixed(1);
                    return label + '\\n' + value + ' (' + percent + '%)';
                }};
                expensesPieOptions.tooltip = {{y: {{formatter: formatCHF}}}};
                var expensesPieChart = new ApexCharts(document.querySelector("#expensesPieChart"), expensesPieOptions);
                expensesPieChart.render();
                
                // Chart 3: Cash Flow Waterfall
                var waterfallOptions = {waterfall_data};
                waterfallOptions.dataLabels.formatter = formatCHF;
                waterfallOptions.yaxis = waterfallOptions.yaxis || {{}};
                waterfallOptions.yaxis.labels = {{formatter: formatCHF}};
                waterfallOptions.tooltip = {{y: {{formatter: formatCHF}}}};
                var waterfallChart = new ApexCharts(document.querySelector("#waterfallChart"), waterfallOptions);
                waterfallChart.render();
                
                // Chart 4: 15-Year Cash Flow
                var cashflow15yrOptions = {cashflow_15yr_data};
                cashflow15yrOptions.yaxis = cashflow15yrOptions.yaxis || {{}};
                cashflow15yrOptions.yaxis.labels = {{formatter: formatCHF}};
                cashflow15yrOptions.tooltip = {{y: {{formatter: formatCHF}}}};
                var cashflow15yrChart = new ApexCharts(document.querySelector("#cashflow15yrChart"), cashflow15yrOptions);
                cashflow15yrChart.render();
                
                // Chart 5: 15-Year Loan Balance
                var loanOptions = {loan_data};
                loanOptions.yaxis = loanOptions.yaxis || {{}};
                loanOptions.yaxis.labels = {{formatter: formatCHF}};
                loanOptions.tooltip = {{y: {{formatter: formatCHF}}}};
                var loanChart = new ApexCharts(document.querySelector("#loanChart"), loanOptions);
                loanChart.render();
                
                // Chart 6: 15-Year Revenue & Expenses
                var revenueExpenses15yrOptions = {revenue_expenses_15yr_data};
                revenueExpenses15yrOptions.yaxis = revenueExpenses15yrOptions.yaxis || {{}};
                revenueExpenses15yrOptions.yaxis.labels = {{formatter: formatCHF}};
                revenueExpenses15yrOptions.tooltip = {{y: {{formatter: formatCHF}}}};
                var revenueExpenses15yrChart = new ApexCharts(document.querySelector("#revenueExpenses15yrChart"), revenueExpenses15yrOptions);
                revenueExpenses15yrChart.render();
            }} catch (error) {{
                console.error('Error initializing charts:', error);
            }}
        }}
        
        // Initialize when both DOM and ApexCharts are ready
        function startInit() {{
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', function() {{
                    setTimeout(initCharts, 200); // Give library time to load
                }});
            }} else {{
                setTimeout(initCharts, 200); // Give library time to load
            }}
        }}
        
        // Start initialization
        startInit();
    </script>
    """
    
    return charts_html


def generate_html_report(results: dict, config, charts: List, projection_15yr: List[dict], irr_results: dict, output_path: str = "output/base_case_report.html"):
    """Generate HTML report with charts, KPIs, 15-year projection, and IRRs."""
    
    # Format numbers for display
    def format_currency(value):
        return f"{value:,.0f} CHF"
    
    def format_percent(value):
        return f"{value:.2f}%"
    
    # Generate ApexCharts HTML
    charts_html = generate_apexcharts_html(results, config, projection_15yr)
    
    # Helper function for seasonal breakdown HTML
    def generate_seasonal_breakdown_html(results_dict, format_func):
        """Generate HTML for seasonal breakdown table."""
        if 'seasonal_breakdown' not in results_dict or not results_dict['seasonal_breakdown']:
            return ''
        
        seasonal_rows = ''.join([
            f'''
                            <tr>
                                <td><strong>{name}</strong></td>
                                <td>{data["available_nights"]:.0f}</td>
                                <td>{data["nights"]:.1f}</td>
                                <td>{data["occupancy"]*100:.1f}%</td>
                                <td>{data["rate"]:.0f}</td>
                                <td><strong>{format_func(data["income"])}</strong></td>
                            </tr>
            ''' for name, data in results_dict['seasonal_breakdown'].items()
        ])
        
        return f'''
                <div style="background: #e8f4f8; padding: 25px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #17a2b8;">
                    <h3 style="color: #1a1a2e; margin-bottom: 20px; font-size: 1.3em;"><i class="fas fa-calendar-alt"></i> Seasonal Breakdown - Engelberg Tourism Patterns</h3>
                    <p style="font-size: 1.05em; line-height: 1.8; margin-bottom: 20px;">
                        Engelberg experiences distinct tourism seasons, each with different demand patterns and pricing:
                    </p>
                    <table class="summary-table" style="margin-top: 15px;">
                        <thead>
                            <tr>
                                <th>Season</th>
                                <th>Available Nights</th>
                                <th>Rented Nights</th>
                                <th>Occupancy Rate</th>
                                <th>Daily Rate (CHF)</th>
                                <th>Season Income (CHF)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {seasonal_rows}
                        </tbody>
                    </table>
                    <p style="font-size: 0.95em; line-height: 1.6; margin-top: 20px; color: #495057; font-style: italic;">
                        <strong>Note:</strong> Winter Peak (Dec-Mar) represents the ski season with highest demand and premium rates. 
                        Summer Peak (Jun-Sep) covers the hiking and mountain activities season. 
                        Off-Peak periods (Apr-May, Oct-Nov) are shoulder seasons with lower demand and discounted rates.
                    </p>
                </div>
        '''
    
    # HTML template with enhanced dashboard design
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Engelberg Property - Base Case Analysis</title>
    <!-- ApexCharts Library -->
    <script src="https://cdn.jsdelivr.net/npm/apexcharts@3.44.0"></script>
    <!-- Font Awesome for icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary: #1a1a2e;
            --secondary: #0f3460;
            --accent: #16213e;
            --success: #28a745;
            --danger: #dc3545;
            --warning: #ffc107;
            --info: #17a2b8;
            --light: #f8f9fa;
            --dark: #212529;
            --gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --shadow-sm: 0 2px 4px rgba(0,0,0,0.1);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.15);
            --shadow-lg: 0 10px 40px rgba(0,0,0,0.2);
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
            background: #ffffff;
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
        
        .content {{
            padding: 50px 80px;
        }}
        
        .dashboard {{
            padding: 50px 80px;
            background: #f5f7fa;
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
        
        .kpi-card h3 {{
            font-size: 0.85em;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        
        .kpi-card .value {{
            font-size: 2.5em;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 8px;
            letter-spacing: -1px;
        }}
        
        .kpi-card .value.positive {{
            color: var(--success);
        }}
        
        .kpi-card .value.negative {{
            color: var(--danger);
        }}
        
        .kpi-card .description {{
            font-size: 0.9em;
            color: #868e96;
            margin-top: 8px;
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
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 30px;
            margin-bottom: 50px;
        }}
        
        .chart-container {{
            background: white;
            padding: 35px;
            border-radius: 16px;
            box-shadow: var(--shadow-md);
            transition: all 0.3s;
            position: relative;
        }}
        
        .chart-container:hover {{
            transform: translateY(-5px);
            box-shadow: var(--shadow-lg);
        }}
        
        .chart-container.full-width {{
            grid-column: 1 / -1;
        }}
        
        .chart-title {{
            font-size: 1.3em;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e8ecef;
        }}
        
        .chart-container > div {{
            width: 100%;
        }}
        
        .summary-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: var(--shadow-sm);
        }}
        
        .summary-table th {{
            background: var(--gradient-1);
            color: white;
            padding: 18px 20px;
            text-align: left;
            font-weight: 600;
            font-size: 0.95em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .summary-table td {{
            padding: 15px 20px;
            border-bottom: 1px solid #e8ecef;
            transition: background 0.2s;
        }}
        
        .summary-table tr:hover td {{
            background: #f8f9fa;
        }}
        
        .summary-table tr:last-child td {{
            border-bottom: none;
        }}
        
        .footer {{
            background: var(--primary);
            color: white;
            padding: 40px 80px;
            text-align: center;
        }}
        
        .positive {{
            color: var(--success);
            font-weight: bold;
        }}
        
        .negative {{
            color: var(--danger);
            font-weight: bold;
        }}
        
        .info-box {{
            background: linear-gradient(135deg, #e8f4f8 0%, #d1ecf1 100%);
            border-left: 4px solid var(--info);
            padding: 25px;
            border-radius: 12px;
            margin: 25px 0;
        }}
        
        .info-box.warning {{
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            border-left-color: var(--warning);
        }}
        
        .info-box.success {{
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border-left-color: var(--success);
        }}
        
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .fade-in-up {{
            animation: fadeInUp 0.6s ease-out;
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
        
        @media (max-width: 1400px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-mountain"></i> Engelberg Property Investment</h1>
            <div class="subtitle">Base Case Financial Analysis Dashboard</div>
            <div class="meta">Generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}</div>
        </div>
        
        <!-- Dashboard Section -->
        <div class="dashboard">
            <h2 style="font-size: 2em; margin-bottom: 30px; color: var(--primary);">Executive Dashboard</h2>
            
            <!-- Key Metrics Grid - IRR and Return Metrics First -->
            <div class="kpi-grid">
                <div class="kpi-card scroll-reveal" style="border-left: 4px solid var(--success);">
                    <h3><i class="fas fa-trending-up"></i> Equity IRR (with Sale)</h3>
                    <div class="value positive">{irr_results['equity_irr_with_sale_pct']:.2f}%</div>
                    <div class="description">Levered return on equity</div>
                </div>
                
                <div class="kpi-card scroll-reveal" style="border-left: 4px solid var(--info);">
                    <h3><i class="fas fa-chart-line"></i> Project IRR (Unlevered)</h3>
                    <div class="value positive">{irr_results['project_irr_with_sale_pct']:.2f}%</div>
                    <div class="description">100% equity, with sale</div>
                </div>
                
                <div class="kpi-card scroll-reveal" style="border-left: 4px solid var(--warning);">
                    <h3><i class="fas fa-chart-pie"></i> Levered Cash-on-Cash</h3>
                    <div class="value {('positive' if results['cash_on_cash_return_pct'] >= 0 else 'negative')}">{format_percent(results['cash_on_cash_return_pct'])}</div>
                    <div class="description">Annual return on equity</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <h3><i class="fas fa-chart-area"></i> Equity IRR (no Sale)</h3>
                    <div class="value {('positive' if irr_results['equity_irr_without_sale_pct'] >= 0 else 'negative')}">{irr_results['equity_irr_without_sale_pct']:.2f}%</div>
                    <div class="description">Operating returns only</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <h3><i class="fas fa-chart-bar"></i> Project IRR (no Sale)</h3>
                    <div class="value {('positive' if irr_results['project_irr_without_sale_pct'] >= 0 else 'negative')}">{irr_results['project_irr_without_sale_pct']:.2f}%</div>
                    <div class="description">Unlevered, operating only</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <h3><i class="fas fa-home"></i> Purchase Price</h3>
                    <div class="value">{format_currency(results['purchase_price'])}</div>
                    <div class="description">Total property value</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <h3><i class="fas fa-chart-line"></i> Gross Rental Income</h3>
                    <div class="value">{format_currency(results['gross_rental_income'])}</div>
                    <div class="description">Annual rental revenue</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <h3><i class="fas fa-coins"></i> Net Operating Income</h3>
                    <div class="value">{format_currency(results['net_operating_income'])}</div>
                    <div class="description">After operating expenses</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <h3><i class="fas fa-wallet"></i> Cash Flow After Debt</h3>
                    <div class="value {('positive' if results['cash_flow_after_debt_service'] >= 0 else 'negative')}">{format_currency(results['cash_flow_after_debt_service'])}</div>
                    <div class="description">Annual cash flow</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <h3><i class="fas fa-user"></i> Cash Flow per Owner</h3>
                    <div class="value {('positive' if results['cash_flow_per_owner'] >= 0 else 'negative')}">{format_currency(results['cash_flow_per_owner'])}</div>
                    <div class="description">Per owner per year</div>
                </div>
                
                <div class="kpi-card scroll-reveal" style="border-left: 4px solid var(--info);">
                    <h3><i class="fas fa-calendar-alt"></i> Monthly Cash per Owner</h3>
                    <div class="value {('positive' if results['cash_flow_per_owner'] >= 0 else 'negative')}">{format_currency(results['cash_flow_per_owner'] / 12)}</div>
                    <div class="description">Per owner per month</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <h3><i class="fas fa-percent"></i> Cap Rate</h3>
                    <div class="value">{format_percent(results['cap_rate_pct'])}</div>
                    <div class="description">NOI / Property Value</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <h3><i class="fas fa-shield-alt"></i> Debt Coverage Ratio</h3>
                    <div class="value">{results['debt_coverage_ratio']:.2f}</div>
                    <div class="description">NOI / Debt Service</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <h3><i class="fas fa-building"></i> Final Property Value</h3>
                    <div class="value">{format_currency(irr_results['final_property_value'])}</div>
                    <div class="description">After 15 years (2% appreciation)</div>
                </div>
                
                <div class="kpi-card scroll-reveal">
                    <h3><i class="fas fa-key"></i> Equity per Owner</h3>
                    <div class="value">{format_currency(results['equity_per_owner'])}</div>
                    <div class="description">Initial investment</div>
                </div>
            </div>
            
            <!-- Key Finding Box -->
            <div class="info-box {'warning' if results['cash_flow_after_debt_service'] < 0 else 'success'} scroll-reveal">
                <h3 style="margin-bottom: 15px; color: var(--primary);">
                    <i class="fas fa-lightbulb"></i> Key Finding
                </h3>
                <p style="font-size: 1.1em; line-height: 1.8;">
                    The base case scenario shows an annual cash flow of 
                    <strong class="{('negative' if results['cash_flow_after_debt_service'] < 0 else 'positive')}">{format_currency(results['cash_flow_after_debt_service'])}</strong> 
                    after debt service, which translates to 
                    <strong class="{('negative' if results['cash_flow_per_owner'] < 0 else 'positive')}">{format_currency(results['cash_flow_per_owner'])}</strong> per owner per year.
                    {'This negative cash flow means owners will need to contribute additional funds annually. However, this should be evaluated in the context of personal use value (5 nights per owner), potential property appreciation, and tax benefits.' if results['cash_flow_after_debt_service'] < 0 else 'This positive cash flow provides a return on investment while maintaining personal use of the property.'}
                </p>
            </div>
        </div>
        
        <!-- Charts Section -->
        <div class="section">
            <h2><i class="fas fa-chart-bar"></i> Financial Visualizations</h2>
            <div class="charts-grid">
                {charts_html}
            </div>
        </div>
        
        <div class="content">
            <!-- Executive Summary -->
            <div class="section">
                <h2><i class="fas fa-file-alt"></i> Executive Summary</h2>
                <div style="background: #f8f9fa; padding: 25px; border-radius: 8px; margin-bottom: 20px; line-height: 1.8;">
                    <p style="font-size: 1.1em; margin-bottom: 15px;">
                        This analysis evaluates a <strong>CHF {format_currency(config.financing.purchase_price)}</strong> property purchase in <strong>Engelberg, Switzerland</strong>, 
                        a picturesque mountain village at the foot of Mount Titlis. The investment is structured as a <strong>co-ownership arrangement</strong> 
                        among <strong>{config.financing.num_owners} friends</strong>, combining personal use with rental income generation.
                    </p>
                    <p style="font-size: 1.1em; margin-bottom: 15px;">
                        Each owner will enjoy <strong>{config.rental.owner_nights_per_person} nights per year</strong> of personal use, while the remaining 
                        <strong>{results['rentable_nights']:.0f} nights</strong> are available for rental. With an assumed <strong>{config.rental.occupancy_rate*100:.0f}% occupancy rate</strong> 
                        and an average daily rate of <strong>{format_currency(config.rental.average_daily_rate)}</strong>, the property is projected to generate 
                        <strong>{format_currency(results['gross_rental_income'])}</strong> in annual rental income.
                    </p>
                    <div style="background: {'#fff3cd' if results['cash_flow_after_debt_service'] < 0 else '#d1ecf1'}; padding: 20px; border-left: 4px solid {'#ffc107' if results['cash_flow_after_debt_service'] < 0 else '#0dcaf0'}; margin-top: 20px;">
                        <p style="font-size: 1.05em; margin: 0;">
                            <strong>Key Finding:</strong> The base case scenario shows an annual cash flow of 
                            <strong class="{('negative' if results['cash_flow_after_debt_service'] < 0 else 'positive')}">{format_currency(results['cash_flow_after_debt_service'])}</strong> 
                            after debt service, which translates to <strong class="{('negative' if results['cash_flow_per_owner'] < 0 else 'positive')}">{format_currency(results['cash_flow_per_owner'])}</strong> per owner per year. 
                            {'This negative cash flow means owners will need to contribute additional funds annually to cover operating costs and debt service. However, this should be evaluated in the context of personal use value, potential property appreciation, and tax benefits.' if results['cash_flow_after_debt_service'] < 0 else 'This positive cash flow provides a return on investment while maintaining personal use of the property.'}
                        </p>
                    </div>
                </div>
            </div>
            
            <!-- Financial Summary -->
            <div class="section">
                <h2><i class="fas fa-file-invoice-dollar"></i> Financial Summary</h2>
                <table class="summary-table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Amount (CHF)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Revenue</strong></td>
                            <td></td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Gross Rental Income</td>
                            <td>{format_currency(results['gross_rental_income'])}</td>
                        </tr>
                        <tr>
                            <td><strong>Operating Expenses</strong></td>
                            <td></td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Property Management (includes Cleaning)</td>
                            <td>{format_currency(results['property_management_cost'])}</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Tourist Tax</td>
                            <td>{format_currency(results['tourist_tax'])}</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Insurance</td>
                            <td>{format_currency(results['insurance'])}</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Utilities</td>
                            <td>{format_currency(results['utilities'])}</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Maintenance Reserve</td>
                            <td>{format_currency(results['maintenance_reserve'])}</td>
                        </tr>
                        <tr>
                            <td><strong>Total Operating Expenses</strong></td>
                            <td><strong>{format_currency(results['total_operating_expenses'])}</strong></td>
                        </tr>
                        <tr>
                            <td><strong>Net Operating Income</strong></td>
                            <td><strong>{format_currency(results['net_operating_income'])}</strong></td>
                        </tr>
                        <tr>
                            <td><strong>Debt Service</strong></td>
                            <td></td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Interest Payment</td>
                            <td>{format_currency(results['interest_payment'])}</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Amortization Payment</td>
                            <td>{format_currency(results['amortization_payment'])}</td>
                        </tr>
                        <tr>
                            <td><strong>Total Debt Service</strong></td>
                            <td><strong>{format_currency(results['debt_service'])}</strong></td>
                        </tr>
                        <tr>
                            <td><strong>Cash Flow After Debt Service</strong></td>
                            <td><strong class="{('positive' if results['cash_flow_after_debt_service'] >= 0 else 'negative')}">{format_currency(results['cash_flow_after_debt_service'])}</strong></td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <!-- Rental Performance Details -->
            <div class="section">
                <h2><i class="fas fa-bed"></i> Rental Performance Analysis</h2>
                <div style="background: #f8f9fa; padding: 25px; border-radius: 8px; margin-bottom: 20px;">
                    <p style="font-size: 1.05em; line-height: 1.8; margin-bottom: 15px;">
                        The property offers <strong>{results['rentable_nights']:.0f} rentable nights</strong> per year after accounting for 
                        <strong>{results['total_owner_nights']:.0f} owner nights</strong> (5 nights × {config.financing.num_owners} owners). 
                        With an <strong>overall occupancy rate of {results.get('overall_occupancy_rate', config.rental.occupancy_rate)*100:.1f}%</strong>, the property is expected to be rented for 
                        <strong>{results['rented_nights']:.0f} nights</strong> annually.
                    </p>
                    <p style="font-size: 1.05em; line-height: 1.8;">
                        At a weighted average daily rate of <strong>{format_currency(results.get('average_daily_rate', config.rental.average_daily_rate))}</strong> and an average stay length of 
                        <strong>{config.expenses.average_length_of_stay:.0f} nights</strong>, this translates to approximately 
                        <strong>{results['rented_nights']/config.expenses.average_length_of_stay:.0f} guest stays</strong> per year, generating 
                        <strong>{format_currency(results['gross_rental_income'])}</strong> in gross rental income.
                    </p>
                </div>
                
                <!-- Seasonal Breakdown -->
                {generate_seasonal_breakdown_html(results, format_currency)}
            </div>
            
            <!-- 15-Year Projection -->
            <div class="section">
                <h2><i class="fas fa-calendar-alt"></i> 15-Year Financial Projection</h2>
                <div style="background: #f8f9fa; padding: 25px; border-radius: 8px; margin-bottom: 20px;">
                    <p style="font-size: 1.05em; line-height: 1.8; margin-bottom: 15px;">
                        The following projection shows the financial performance over 15 years starting from <strong>January {projection_15yr[0]['year']}</strong>. 
                        The analysis assumes the property is purchased in <strong>{projection_15yr[0]['year']}</strong> and tracks how the loan balance decreases 
                        over time due to amortization, while interest payments decrease accordingly.
                    </p>
                    <p style="font-size: 1.05em; line-height: 1.8;">
                        <strong>Key Assumptions:</strong>
                    </p>
                    <ul style="font-size: 1.05em; line-height: 1.8; margin-left: 20px;">
                        <li><strong>Inflation:</strong> 2% per year applied to revenue and operating expenses</li>
                        <li><strong>Property Appreciation:</strong> 2% per year (optimistic estimate)</li>
                        <li>Occupancy rate and average daily rate remain constant</li>
                        <li>Loan balance decreases by annual amortization amount each year</li>
                    </ul>
                </div>
                <table class="summary-table">
                    <thead>
                        <tr>
                            <th>Year</th>
                            <th>Gross Rental Income</th>
                            <th>Operating Expenses</th>
                            <th>Net Operating Income</th>
                            <th>Debt Service</th>
                            <th>Cash Flow After Debt</th>
                            <th>Cash Flow per Owner</th>
                            <th>Remaining Loan Balance</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f'''
                        <tr>
                            <td><strong>{y['year']}</strong></td>
                            <td>{format_currency(y['gross_rental_income'])}</td>
                            <td>{format_currency(y['total_operating_expenses'])}</td>
                            <td>{format_currency(y['net_operating_income'])}</td>
                            <td>{format_currency(y['debt_service'])}</td>
                            <td class="{('positive' if y['cash_flow_after_debt_service'] >= 0 else 'negative')}">{format_currency(y['cash_flow_after_debt_service'])}</td>
                            <td class="{('positive' if y['cash_flow_per_owner'] >= 0 else 'negative')}">{format_currency(y['cash_flow_per_owner'])}</td>
                            <td>{format_currency(y['remaining_loan_balance'])}</td>
                        </tr>
                        ''' for y in projection_15yr])}
                    </tbody>
                </table>
            </div>
            
            <!-- IRR Analysis -->
            <div class="section">
                <h2><i class="fas fa-calculator"></i> Internal Rate of Return (IRR) Analysis</h2>
                <div class="info-box">
                    <p style="font-size: 1.05em; line-height: 1.8; margin-bottom: 15px;">
                        The Internal Rate of Return (IRR) measures the annualized return on the initial equity investment over the 15-year period. 
                        Two scenarios are calculated:
                    </p>
                    <ul style="font-size: 1.05em; line-height: 1.8; margin-left: 20px; margin-bottom: 15px;">
                        <li><strong>IRR with Sale:</strong> Includes annual cash flows plus proceeds from selling the property at the end of year 15</li>
                        <li><strong>IRR without Sale:</strong> Considers only annual cash flows, assuming the property is held indefinitely</li>
                    </ul>
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
                            <td><strong>Initial Equity Investment per Owner</strong></td>
                            <td>{format_currency(results['equity_per_owner'])}</td>
                        </tr>
                        <tr>
                            <td><strong>Final Property Value (Year 15)</strong></td>
                            <td>{format_currency(irr_results['final_property_value'])}</td>
                        </tr>
                        <tr>
                            <td><strong>Final Loan Balance (Year 15)</strong></td>
                            <td>{format_currency(irr_results['final_loan_balance'])}</td>
                        </tr>
                        <tr>
                            <td><strong>Net Sale Proceeds per Owner</strong></td>
                            <td>{format_currency(irr_results['sale_proceeds_per_owner'])}</td>
                        </tr>
                        <tr>
                            <td><strong>IRR (with Sale at Year 15)</strong></td>
                            <td><strong style="font-size: 1.2em; color: #2ecc71;">{irr_results['irr_with_sale_pct']:.2f}%</strong></td>
                        </tr>
                        <tr>
                            <td><strong>IRR (without Sale)</strong></td>
                            <td><strong style="font-size: 1.2em; color: #3498db;">{irr_results['irr_without_sale_pct']:.2f}%</strong></td>
                        </tr>
                    </tbody>
                </table>
                <div class="info-box" style="margin-top: 20px;">
                    <p style="font-size: 1.05em; line-height: 1.8; margin: 0;">
                        <strong>Note:</strong> The IRR calculations include inflation (2% per year) and property appreciation (1% per year). 
                        The IRR with sale scenario assumes the property is sold at the end of year 15 at the appreciated value, 
                        with proceeds distributed after paying off the remaining loan balance.
                    </p>
                </div>
            </div>
            
            <!-- Investment Insights -->
            <div class="section">
                <h2><i class="fas fa-lightbulb"></i> Investment Insights & Considerations</h2>
                <div style="background: #f8f9fa; padding: 25px; border-radius: 8px;">
                    <h3 style="color: #667eea; margin-bottom: 15px; font-size: 1.3em;">Financial Metrics</h3>
                    <ul style="line-height: 2; font-size: 1.05em; margin-bottom: 25px;">
                        <li><strong>Cap Rate:</strong> {format_percent(results['cap_rate_pct'])} - This represents the return on the total property value based on net operating income.</li>
                        <li><strong>Cash-on-Cash Return:</strong> {format_percent(results['cash_on_cash_return_pct'])} - This shows the return on the equity investment ({format_currency(results['equity_per_owner'])} per owner).</li>
                        <li><strong>Debt Coverage Ratio:</strong> {results['debt_coverage_ratio']:.2f} - This ratio indicates {'that net operating income does not fully cover debt service, requiring additional owner contributions.' if results['debt_coverage_ratio'] < 1.0 else 'the ability to cover debt payments from rental income.'}</li>
                        <li><strong>Operating Expense Ratio:</strong> {format_percent(results['operating_expense_ratio_pct'])} - Operating expenses represent this percentage of gross rental income.</li>
                    </ul>
                    
                    <h3 style="color: #667eea; margin-bottom: 15px; font-size: 1.3em; margin-top: 30px;">Key Considerations</h3>
                    <ul style="line-height: 2; font-size: 1.05em;">
                        <li><strong>Personal Use Value:</strong> Each owner receives 5 nights per year of personal use, which should be valued when evaluating the total return on investment.</li>
                        <li><strong>Property Appreciation:</strong> Swiss mountain properties have historically shown strong appreciation potential, which is not captured in this cash flow analysis.</li>
                        <li><strong>Tax Benefits:</strong> Property ownership in Switzerland may offer tax deductions for interest payments and depreciation that could improve the after-tax return.</li>
                        <li><strong>Occupancy Sensitivity:</strong> The {config.rental.occupancy_rate*100:.0f}% occupancy rate is a key assumption. Higher occupancy could significantly improve cash flow.</li>
                        <li><strong>Co-ownership Structure:</strong> The arrangement allows for shared costs and responsibilities while maintaining personal access to the property.</li>
                    </ul>
                </div>
            </div>
            
            <!-- Assumptions -->
            <div class="section">
                <h2><i class="fas fa-cog"></i> Key Assumptions</h2>
                <table class="summary-table">
                    <thead>
                        <tr>
                            <th>Parameter</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Financing</strong></td>
                            <td></td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Loan-to-Value Ratio</td>
                            <td>{config.financing.ltv*100:.1f}%</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Interest Rate</td>
                            <td>{config.financing.interest_rate*100:.2f}%</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Amortization Rate</td>
                            <td>{config.financing.amortization_rate*100:.1f}%</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Number of Owners</td>
                            <td>{config.financing.num_owners}</td>
                        </tr>
                        <tr>
                            <td><strong>Rental</strong></td>
                            <td></td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Owner Nights per Person</td>
                            <td>{config.rental.owner_nights_per_person}</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Occupancy Rate</td>
                            <td>{config.rental.occupancy_rate*100:.1f}%</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Average Daily Rate</td>
                            <td>{format_currency(config.rental.average_daily_rate)}</td>
                        </tr>
                        <tr>
                            <td><strong>Expenses</strong></td>
                            <td></td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Property Management Fee Rate (includes Cleaning)</td>
                            <td>{config.expenses.property_management_fee_rate*100:.1f}%</td>
                        </tr>
                        <tr>
                            <td style="padding-left: 30px;">Average Length of Stay</td>
                            <td>{config.expenses.average_length_of_stay:.1f} nights</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p style="font-size: 1.1em; margin-bottom: 10px;">Engelberg Property Investment Analysis</p>
            <p style="opacity: 0.8;">This report was generated automatically by the Engelberg Property Investment Simulation</p>
        </div>
    </div>
    
    <script>
        // Advanced JavaScript for interactivity and animations
        (function() {{
            // Scroll reveal animation
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
            
            // Observe all scroll-reveal elements
            document.querySelectorAll('.scroll-reveal').forEach(el => {{
                observer.observe(el);
            }});
            
            // Smooth scroll for anchor links
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
                anchor.addEventListener('click', function (e) {{
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {{
                        target.scrollIntoView({{
                            behavior: 'smooth',
                            block: 'start'
                        }});
                    }}
                }});
            }});
        }})();
    </script>
</body>
</html>
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"[+] HTML report generated: {output_path}")


def main():
    """Main function to run the base case simulation."""
    print("=" * 70)
    print("Engelberg Property Investment - Base Case Analysis")
    print("=" * 70)
    print()
    print("Analyzing co-ownership investment opportunity in Engelberg, Switzerland")
    print("Property: CHF 1,300,000 | Owners: 4 friends | Personal Use: 5 nights/owner")
    print()
    
    # Create base case configuration
    # IMPORTANT: This is the SINGLE SOURCE OF TRUTH for all analyses
    # All other scripts (sensitivity, Monte Carlo) must reference this base case
    print("[*] Creating base case configuration...")
    config = create_base_case_config()
    
    # Compute results
    print("[*] Computing annual cash flows...")
    results = compute_annual_cash_flows(config)
    
    # Compute 15-year projection with inflation and appreciation
    print("[*] Computing 15-year projection (starting January 2026)...")
    print("     Inflation: 2% per year | Property Appreciation: 2% per year")
    projection_15yr = compute_15_year_projection(config, start_year=2026, inflation_rate=0.02, property_appreciation_rate=0.02)
    
    # Calculate IRRs (Equity IRR and Project/Unlevered IRR)
    print("[*] Calculating IRRs (Equity IRR and Project/Unlevered IRR)...")
    final_property_value = projection_15yr[-1]['property_value']
    final_loan_balance = projection_15yr[-1]['remaining_loan_balance']
    initial_equity = results['equity_per_owner']
    
    irr_results = calculate_irrs_from_projection(
        projection_15yr,
        initial_equity,
        final_property_value,
        final_loan_balance,
        config.financing.num_owners,
        purchase_price=config.financing.purchase_price
    )
    
    # Calculate Levered Cash-on-Cash Return (annual)
    # This is already calculated in results as cash_on_cash_return_pct, but let's make it explicit
    levered_cash_on_cash_return = results['cash_on_cash_return_pct']
    
    # Display key results
    print("\n" + "=" * 70)
    print("KEY FINANCIAL RESULTS")
    print("=" * 70)
    print(f"\nREVENUE")
    print(f"  Gross Rental Income:        {results['gross_rental_income']:>15,.0f} CHF")
    print(f"  Rented Nights:              {results['rented_nights']:>15,.0f} nights")
    print(f"  (Rentable Nights:            {results['rentable_nights']:>15,.0f} nights)")
    
    print(f"\nOPERATING EXPENSES")
    print(f"  Total Operating Expenses:    {results['total_operating_expenses']:>15,.0f} CHF")
    print(f"    - Property Management (incl. Cleaning): {results['property_management_cost']:>15,.0f} CHF")
    print(f"    - Tourist Tax:            {results['tourist_tax']:>15,.0f} CHF")
    print(f"    - Insurance:              {results['insurance']:>15,.0f} CHF")
    print(f"    - Utilities:              {results['utilities']:>15,.0f} CHF")
    print(f"    - Maintenance Reserve:    {results['maintenance_reserve']:>15,.0f} CHF")
    
    print(f"\nNET OPERATING INCOME")
    print(f"  NOI:                        {results['net_operating_income']:>15,.0f} CHF")
    
    print(f"\nDEBT SERVICE")
    print(f"  Interest Payment:           {results['interest_payment']:>15,.0f} CHF")
    print(f"  Amortization Payment:        {results['amortization_payment']:>15,.0f} CHF")
    print(f"  Total Debt Service:         {results['debt_service']:>15,.0f} CHF")
    
    print(f"\nCASH FLOW")
    cash_flow_sign = "[!] " if results['cash_flow_after_debt_service'] < 0 else "[+] "
    print(f"  Cash Flow After Debt:       {cash_flow_sign}{results['cash_flow_after_debt_service']:>15,.0f} CHF")
    print(f"  Cash Flow per Owner:        {cash_flow_sign}{results['cash_flow_per_owner']:>15,.0f} CHF/year")
    
    print(f"\nKEY PERFORMANCE INDICATORS")
    print(f"  Cap Rate:                   {results['cap_rate_pct']:>15.2f}%")
    print(f"  Cash-on-Cash Return:        {results['cash_on_cash_return_pct']:>15.2f}%")
    print(f"  Debt Coverage Ratio:        {results['debt_coverage_ratio']:>15.2f}")
    print(f"  Operating Expense Ratio:    {results['operating_expense_ratio_pct']:>15.2f}%")
    
    print(f"\n15-YEAR PROJECTION METRICS")
    print(f"  Final Property Value:       {final_property_value:>15,.0f} CHF")
    print(f"  Final Loan Balance:          {final_loan_balance:>15,.0f} CHF")
    print(f"  Sale Proceeds per Owner:    {irr_results['sale_proceeds_per_owner']:>15,.0f} CHF")
    
    print(f"\nIRR METRICS")
    print(f"  Equity IRR (with sale):     {irr_results.get('equity_irr_with_sale_pct', irr_results.get('irr_with_sale_pct', 0)):>15.2f}%")
    print(f"  Equity IRR (without sale):  {irr_results.get('equity_irr_without_sale_pct', irr_results.get('irr_without_sale_pct', 0)):>15.2f}%")
    print(f"  Project IRR (unlevered, with sale):    {irr_results.get('project_irr_with_sale_pct', 0):>15.2f}%")
    print(f"  Project IRR (unlevered, without sale): {irr_results.get('project_irr_without_sale_pct', 0):>15.2f}%")
    
    print(f"\nCASH-ON-CASH RETURN")
    print(f"  Levered Cash-on-Cash Return: {results['cash_on_cash_return_pct']:>15.2f}%")
    
    if results['cash_flow_after_debt_service'] < 0:
        print(f"\n[!] NOTE: Negative cash flow means each owner contributes {abs(results['cash_flow_per_owner']):,.0f} CHF/year")
        print(f"   However, this includes 5 nights of personal use + potential appreciation + tax benefits")
    
    print("=" * 70)
    print()
    
    # Excel export disabled - user only uses HTML reports
    # print("\n[*] Exporting results to Excel...")
    # export_to_excel(results, config, projection_15yr, irr_results)
    
    # Ensure output directory exists
    import os
    os.makedirs("output", exist_ok=True)
    
    # Generate charts
    print("[*] Generating charts...")
    charts = create_charts(results, config, projection_15yr)
    
    # Generate HTML report
    print("[*] Generating HTML report...")
    generate_html_report(results, config, charts, projection_15yr, irr_results)
    
    print("\n" + "=" * 70)
    print("[+] Analysis complete!")
    print("=" * 70)
    # print(f"[+] Excel file: base_case_results.xlsx")  # Excel export disabled
    print(f"[+] HTML report: output/base_case_report.html")
    print("=" * 70)


if __name__ == "__main__":
    main()

