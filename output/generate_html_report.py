#!/usr/bin/env python3
"""
Comprehensive HTML Report Generator for TCO Analysis.

This script generates a complete HTML report with charts and analysis
from the simulation module and report generators.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from typing import Dict, List, Tuple
import json
import argparse

# Import MyBuild modules
from calculations.inputs import vehicle_data
from calculations.calculations import compare_vehicle_pairs, calculate_tco_from_inputs
from data.scenarios import SCENARIOS
from data.vehicles import BY_ID
from app.simulation import MonteCarloSimulation, SensitivityAnalysis
from output.generators import (
    generate_executive_summary, 
    generate_fleet_report,
    generate_policy_recommendations
)
from output.analysis import (
    calculate_payback_analysis,
    analyse_policy_combinations,
    PolicyImpactAnalysis
)
from output.visualisations import TCOVisualiser


def generate_monte_carlo_chart(sim_results, title="Monte Carlo TCO Distribution"):
    """Generate Monte Carlo simulation results chart."""
    fig = go.Figure()
    
    # Histogram of TCO values
    fig.add_trace(go.Histogram(
        x=sim_results.tco_values,
        nbinsx=50,
        name='TCO Distribution',
        marker_color='lightblue',
        hovertemplate='TCO Range: $%{x}<br>Count: %{y}<extra></extra>'
    ))
    
    # Add vertical lines for key statistics
    fig.add_vline(x=sim_results.mean, line_dash="dash", line_color="red",
                  annotation_text=f"Mean: ${sim_results.mean:,.0f}")
    fig.add_vline(x=sim_results.percentiles[50], line_dash="dash", line_color="green",
                  annotation_text=f"Median: ${sim_results.percentiles[50]:,.0f}")
    
    fig.update_layout(
        title=title,
        xaxis_title="Total Cost of Ownership ($)",
        yaxis_title="Frequency",
        showlegend=False,
        template='plotly_white'
    )
    
    return fig


def generate_class_comparison_chart(comparisons: List[Tuple], scenario_name: str):
    """Generate comparison chart by vehicle class."""
    # Organize by class
    class_data = {}
    for bev_tco, diesel_tco, diff in comparisons:
        vehicle = BY_ID[bev_tco.vehicle_id]
        if vehicle.weight_class not in class_data:
            class_data[vehicle.weight_class] = []
        class_data[vehicle.weight_class].append({
            'model': vehicle.model_name,
            'bev_tco': bev_tco.total_cost,
            'diesel_tco': diesel_tco.total_cost,
            'difference': diff,
            'savings_pct': -diff / diesel_tco.total_cost * 100 if diesel_tco.total_cost > 0 else 0
        })
    
    # Create subplot for each class
    n_classes = len(class_data)
    fig = make_subplots(
        rows=n_classes, cols=1,
        subplot_titles=list(class_data.keys()),
        row_heights=[300] * n_classes
    )
    
    for idx, (weight_class, vehicles) in enumerate(class_data.items(), 1):
        df = pd.DataFrame(vehicles)
        df = df.sort_values('savings_pct', ascending=False)
        
        # Add bars for savings percentage
        fig.add_trace(
            go.Bar(
                x=df['model'],
                y=df['savings_pct'],
                name=weight_class,
                marker_color=['green' if x > 0 else 'red' for x in df['savings_pct']],
                text=[f"{x:.1f}%" for x in df['savings_pct']],
                textposition='outside',
                showlegend=False
            ),
            row=idx, col=1
        )
        
        # Add zero line
        fig.add_hline(y=0, line_dash="solid", line_color="black", row=idx, col=1)
    
    fig.update_layout(
        title=f"BEV vs Diesel Savings by Vehicle Class - {scenario_name}",
        height=300 * n_classes,
        template='plotly_white'
    )
    
    fig.update_yaxes(title_text="Savings (%)", row=n_classes, col=1)
    
    return fig


def generate_fleet_transition_chart(fleet_data: pd.DataFrame):
    """Generate fleet transition impact visualization."""
    if fleet_data.empty:
        return None
        
    # Filter out total row - ensure we get a DataFrame
    filtered_data = fleet_data[fleet_data['vehicle_model'] != 'TOTAL']
    # Ensure it's a DataFrame (not Series) and create a copy
    fleet_data = pd.DataFrame(filtered_data).copy()
    
    # Create bubble chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=fleet_data['payback_years'],
        y=fleet_data['fleet_annual_savings'],
        mode='markers+text',
        marker=dict(
            size=fleet_data['quantity'] * 10,
            color=fleet_data['fleet_emissions_reduction'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Annual Emissions<br>Reduction (tCO2)")
        ),
        text=fleet_data['vehicle_model'],
        textposition="top center",
        hovertemplate=(
            '<b>%{text}</b><br>' +
            'Payback: %{x:.1f} years<br>' +
            'Annual Savings: $%{y:,.0f}<br>' +
            'Fleet Size: %{marker.size}<extra></extra>'
        )
    ))
    
    fig.update_layout(
        title="Fleet Transition Analysis",
        xaxis_title="Payback Period (years)",
        yaxis_title="Fleet Annual Savings ($)",
        template='plotly_white'
    )
    
    return fig


def generate_monte_carlo_differentials(vehicle_pairs, scenario):
    """Generate Monte Carlo TCO differentials for all vehicle pairs."""
    from app.simulation import MonteCarloSimulation
    
    monte_carlo_results = []
    weight_class_results = {}
    
    print("Running Monte Carlo simulations for all vehicle pairs...")
    for i, (bev_tco, diesel_tco, cost_diff) in enumerate(vehicle_pairs):
        # Get vehicle inputs for Monte Carlo simulation
        bev_inputs = vehicle_data.get_vehicle(bev_tco.vehicle_id, scenario)
        diesel_inputs = vehicle_data.get_vehicle(diesel_tco.vehicle_id, scenario)
        
        print(f"  Simulating {bev_inputs.vehicle.model_name} vs {diesel_inputs.vehicle.model_name}...")
        
        # Run Monte Carlo for BEV
        mc_bev = MonteCarloSimulation(bev_inputs)
        bev_results = mc_bev.run(iterations=1000)
        
        # Run Monte Carlo for Diesel
        mc_diesel = MonteCarloSimulation(diesel_inputs)
        diesel_results = mc_diesel.run(iterations=1000)
        
        # Calculate differentials
        tco_differential = diesel_results.mean - bev_results.mean
        tco_differential_std = (bev_results.std_dev**2 + diesel_results.std_dev**2)**0.5
        
        result = {
            'weight_class': bev_inputs.vehicle.weight_class,
            'bev_model': bev_inputs.vehicle.model_name,
            'diesel_model': diesel_inputs.vehicle.model_name,
            'bev_mean_tco': bev_results.mean,
            'diesel_mean_tco': diesel_results.mean,
            'tco_differential': tco_differential,
            'tco_differential_std': tco_differential_std,
            'confidence_interval_low': tco_differential - 1.96 * tco_differential_std,
            'confidence_interval_high': tco_differential + 1.96 * tco_differential_std,
            'probability_bev_cheaper': sum(1 for b, d in zip(bev_results.tco_values, 
                                                            diesel_results.tco_values) 
                                         if b < d) / len(bev_results.tco_values)
        }
        monte_carlo_results.append(result)
        
        # Group by weight class
        if bev_inputs.vehicle.weight_class not in weight_class_results:
            weight_class_results[bev_inputs.vehicle.weight_class] = []
        weight_class_results[bev_inputs.vehicle.weight_class].append(result)
    
    # Calculate weight class averages
    weight_class_averages = {}
    for weight_class, results in weight_class_results.items():
        avg_differential = sum(r['tco_differential'] for r in results) / len(results)
        avg_probability = sum(r['probability_bev_cheaper'] for r in results) / len(results)
        weight_class_averages[weight_class] = {
            'avg_tco_differential': avg_differential,
            'avg_probability_bev_cheaper': avg_probability,
            'num_comparisons': len(results)
        }
    
    return monte_carlo_results, weight_class_averages


def create_monte_carlo_differentials_chart(monte_carlo_results, weight_class_averages):
    """Create a chart showing Monte Carlo TCO differentials."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    # Create subplots: 1 for individual comparisons, 1 for weight class averages
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.7, 0.3],
        subplot_titles=("TCO Differentials by Vehicle Pair (Diesel TCO - BEV TCO)", 
                       "Average TCO Differential by Weight Class"),
        vertical_spacing=0.15
    )
    
    # Sort results by weight class and differential
    sorted_results = sorted(monte_carlo_results, 
                          key=lambda x: (x['weight_class'], x['tco_differential']), 
                          reverse=True)
    
    # Plot individual vehicle pairs
    vehicle_labels = [f"{r['bev_model']} vs {r['diesel_model']}" for r in sorted_results]
    differentials = [r['tco_differential'] for r in sorted_results]
    error_bars = [r['tco_differential_std'] * 1.96 for r in sorted_results]  # 95% CI
    colors = ['green' if d > 0 else 'red' for d in differentials]
    
    fig.add_trace(
        go.Bar(
            x=differentials,
            y=vehicle_labels,
            orientation='h',
            error_x=dict(type='data', array=error_bars),
            marker_color=colors,
            text=[f"${d:,.0f}" for d in differentials],
            textposition='outside',
            name='TCO Differential',
            hovertemplate='%{y}<br>Differential: $%{x:,.0f}<br>±$%{error_x.array:,.0f} (95% CI)<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Plot weight class averages
    weight_classes = list(weight_class_averages.keys())
    avg_differentials = [weight_class_averages[wc]['avg_tco_differential'] for wc in weight_classes]
    avg_colors = ['green' if d > 0 else 'red' for d in avg_differentials]
    
    fig.add_trace(
        go.Bar(
            x=avg_differentials,
            y=weight_classes,
            orientation='h',
            marker_color=avg_colors,
            text=[f"${d:,.0f}" for d in avg_differentials],
            textposition='outside',
            name='Average Differential',
            hovertemplate='%{y}<br>Average Differential: $%{x:,.0f}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_xaxes(title_text="TCO Differential ($)", row=1, col=1)
    fig.update_xaxes(title_text="Average TCO Differential ($)", row=2, col=1)
    fig.update_yaxes(tickfont_size=10)
    
    fig.update_layout(
        height=800,
        showlegend=False,
        template='plotly_white',
        title=dict(
            text="Monte Carlo Simulation: TCO Differentials<br><sub>Positive values indicate BEV advantage</sub>",
            x=0.5,
            xanchor='center'
        )
    )
    
    # Add vertical line at x=0
    fig.add_vline(x=0, line_dash="dash", line_color="gray", row=1, col=1)
    fig.add_vline(x=0, line_dash="dash", line_color="gray", row=2, col=1)
    
    return fig


def generate_comprehensive_report(scenario_name: str = "Current", 
                                output_file: str = "tco_report.html"):
    """Generate comprehensive HTML report with all analyses."""
    
    print(f"Generating comprehensive TCO report for {scenario_name} scenario...")
    
    # Get scenario
    scenario = SCENARIOS.get(scenario_name, SCENARIOS["baseline"])
    
    # Run vehicle comparisons
    print("Running vehicle comparisons...")
    comparisons = compare_vehicle_pairs(scenario)
    
    # Generate executive summary
    print("Generating executive summary...")
    exec_summary = generate_executive_summary(comparisons, scenario_name)
    
    # Sample fleet composition for demonstration
    fleet_composition = {
        'light_rigid_bev': 5,
        'medium_rigid_bev': 3,
        'articulated_bev': 2
    }
    
    # Generate fleet report
    print("Generating fleet analysis...")
    fleet_report = generate_fleet_report(fleet_composition, scenario_name)
    
    # Run Monte Carlo simulation for a sample vehicle
    print("Running Monte Carlo simulation...")
    sample_vehicle = vehicle_data.get_vehicle('BEV001', scenario)
    mc_sim = MonteCarloSimulation(sample_vehicle)
    mc_results = mc_sim.run(iterations=5000)
    
    # Run sensitivity analysis
    print("Running sensitivity analysis...")
    sensitivity = SensitivityAnalysis(sample_vehicle)
    tornado_params = {
        'diesel_price': (0.8, 1.2),
        'electricity_price': (0.7, 1.3),
        'maintenance_cost': (0.8, 1.2),
        'interest_rate': (0.04, 0.08)
    }
    
    # Generate payback analysis for best performing pair
    print("Analyzing payback periods...")
    best_pair = min(comparisons, key=lambda x: x[2])
    if best_pair[2] < 0:
        bev_inputs = vehicle_data.get_vehicle(best_pair[0].vehicle_id, scenario)
        diesel_inputs = vehicle_data.get_vehicle(best_pair[1].vehicle_id, scenario)
        payback_analysis = calculate_payback_analysis(bev_inputs, diesel_inputs)
    else:
        payback_analysis = None
    
    # Generate Monte Carlo TCO differentials
    print("Generating Monte Carlo TCO differentials...")
    monte_carlo_differentials, weight_class_averages = generate_monte_carlo_differentials(comparisons, scenario)
    
    # Create all visualizations
    print("Creating visualizations...")
    charts = {}
    
    # 1. Executive Summary Chart
    fig_summary = go.Figure()
    fig_summary.add_trace(go.Indicator(
        mode="number+delta",
        value=exec_summary['overview']['percentage_competitive'],
        title={"text": "BEV Models Cost Competitive (%)"},
        delta={'reference': 50, 'relative': False},
        domain={'x': [0, 0.5], 'y': [0.5, 1]}
    ))
    fig_summary.add_trace(go.Indicator(
        mode="number",
        value=exec_summary['overview']['average_savings'],
        title={"text": "Average BEV Savings ($)"},
        number={'prefix': "$", 'valueformat': ",.0f"},
        domain={'x': [0.5, 1], 'y': [0.5, 1]}
    ))
    fig_summary.add_trace(go.Indicator(
        mode="number",
        value=exec_summary['overview']['best_case_savings'],
        title={"text": "Best Case Savings ($)"},
        number={'prefix': "$", 'valueformat': ",.0f"},
        domain={'x': [0, 0.5], 'y': [0, 0.5]}
    ))
    fig_summary.add_trace(go.Indicator(
        mode="number",
        value=len(comparisons),
        title={"text": "Vehicle Pairs Analyzed"},
        domain={'x': [0.5, 1], 'y': [0, 0.5]}
    ))
    fig_summary.update_layout(title="Executive Summary Dashboard", height=400)
    charts['summary'] = fig_summary
    
    # 2. Class comparison chart
    charts['class_comparison'] = generate_class_comparison_chart(comparisons, scenario_name)
    
    # 3. Monte Carlo results
    charts['monte_carlo'] = generate_monte_carlo_chart(mc_results, 
        f"Monte Carlo Simulation: {sample_vehicle.vehicle.model_name}")
    
    # 4. Sensitivity analysis tornado chart
    charts['sensitivity'] = TCOVisualiser.create_tornado_chart(
        {param: sensitivity.analyse_parameter(param, [low, 1.0, high], 'multiplier')
         for param, (low, high) in tornado_params.items()},
        sensitivity.base_tco.total_cost
    )
    
    # 5. Payback chart (if applicable)
    if payback_analysis:
        charts['payback'] = TCOVisualiser.create_payback_chart(payback_analysis)
    
    # 6. Fleet transition chart
    if not fleet_report.empty:
        charts['fleet'] = generate_fleet_transition_chart(fleet_report)
    
    # 7. Monte Carlo TCO differentials chart
    charts['monte_carlo_differentials'] = create_monte_carlo_differentials_chart(monte_carlo_differentials, weight_class_averages)
    
    # Generate HTML report
    print(f"Generating HTML report: {output_file}")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>TCO Analysis Report - {scenario_name} Scenario</title>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #333;
                text-align: center;
                margin-bottom: 10px;
            }}
            h2 {{
                color: #555;
                margin-top: 40px;
                border-bottom: 2px solid #eee;
                padding-bottom: 10px;
            }}
            .metadata {{
                text-align: center;
                color: #666;
                margin-bottom: 30px;
            }}
            .section {{
                margin: 30px 0;
            }}
            .key-findings {{
                background-color: #f0f8ff;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .key-findings ul {{
                margin: 10px 0;
                padding-left: 20px;
            }}
            .chart-container {{
                margin: 20px 0;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #f8f9fa;
                font-weight: 600;
            }}
            tr.positive-savings {{
                background-color: #e8f5e9;
            }}
            tr.negative-savings {{
                background-color: #ffebee;
            }}
            .footer {{
                margin-top: 50px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                text-align: center;
                color: #666;
                font-size: 0.9em;
            }}
        </style>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>
    <body>
        <div class="container">
            <h1>Total Cost of Ownership Analysis Report</h1>
            <div class="metadata">
                <p>Scenario: <strong>{scenario_name}</strong> | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            </div>
            
            <div class="section">
                <h2>Executive Summary</h2>
                <div id="summary-chart" class="chart-container"></div>
                
                <div class="key-findings">
                    <h3>Key Findings</h3>
                    <ul>
    """
    
    # Add key findings
    for finding in exec_summary.get('key_findings', []):
        html_content += f"                        <li>{finding}</li>\n"
    
    html_content += """
                    </ul>
                </div>
            </div>
            
            <div class="section">
                <h2>Vehicle Class Comparison</h2>
                <div id="class-comparison-chart" class="chart-container"></div>
            </div>
            
            <div class="section">
                <h2>Detailed Model-by-Model TCO Comparison</h2>
                <p>Individual vehicle pair comparisons showing total cost of ownership over 15 years</p>
                <table>
                    <thead>
                        <tr>
                            <th>BEV Model</th>
                            <th>Diesel Model</th>
                            <th>Weight Class</th>
                            <th>BEV TCO</th>
                            <th>Diesel TCO</th>
                            <th>TCO Savings</th>
                            <th>Savings %</th>
                            <th>Payback Years</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    # Add detailed comparison rows
    for bev_tco, diesel_tco, cost_diff in comparisons:
        bev_vehicle = vehicle_data.get_vehicle(bev_tco.vehicle_id, scenario).vehicle
        diesel_vehicle = vehicle_data.get_vehicle(diesel_tco.vehicle_id, scenario).vehicle
        
        savings_pct = (cost_diff / diesel_tco.total_cost) * -100
        
        # Calculate payback for this pair
        bev_inputs = vehicle_data.get_vehicle(bev_tco.vehicle_id, scenario)
        diesel_inputs = vehicle_data.get_vehicle(diesel_tco.vehicle_id, scenario)
        payback_result = calculate_payback_analysis(bev_inputs, diesel_inputs)
        
        # Format payback years for display
        if payback_result.breakeven_achieved:
            if payback_result.payback_years < 0:
                payback_display = "No payback needed"
            else:
                payback_display = f"{payback_result.payback_years:.1f}"
        else:
            # If no breakeven but BEV saves money, something's wrong
            if cost_diff < 0:  # BEV is cheaper overall
                # BEV saves money but payback is beyond 15 years due to high initial cost
                payback_display = ">15 years"
            else:
                payback_display = "Never"
        
        # Determine row color based on savings
        row_class = "positive-savings" if cost_diff < 0 else "negative-savings" if cost_diff > 0 else ""
        
        html_content += f"""
                        <tr class="{row_class}">
                            <td>{bev_vehicle.model_name}</td>
                            <td>{diesel_vehicle.model_name}</td>
                            <td>{bev_vehicle.weight_class}</td>
                            <td>${bev_tco.total_cost:,.0f}</td>
                            <td>${diesel_tco.total_cost:,.0f}</td>
                            <td>${-cost_diff:,.0f}</td>
                            <td>{savings_pct:.1f}%</td>
                            <td>{payback_display}</td>
                        </tr>
        """
    
    html_content += """
                    </tbody>
                </table>
            </div>
    """
    
    # Add best performers by class table
    if exec_summary.get('by_class'):
        html_content += """
            <div class="section">
                <h2>Best Performing Models by Class</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Weight Class</th>
                            <th>BEV Model</th>
                            <th>Diesel Model</th>
                            <th>TCO Savings</th>
                            <th>Payback Years</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for weight_class, data in exec_summary['by_class'].items():
            if data.get('best_performing_pair'):
                pair = data['best_performing_pair']
                payback_years = pair.get('payback_years')
                if payback_years is None:
                    payback_display = "N/A"
                elif payback_years < 0:
                    payback_display = "No payback needed"
                elif payback_years > 15:
                    payback_display = ">15 years"
                else:
                    payback_display = f"{payback_years:.1f}"
                html_content += f"""
                        <tr>
                            <td>{weight_class}</td>
                            <td>{pair.get('bev_model', 'N/A')}</td>
                            <td>{pair.get('diesel_model', 'N/A')}</td>
                            <td>${pair.get('tco_savings', 0):,.0f}</td>
                            <td>{payback_display}</td>
                        </tr>
                """
        
        html_content += """
                    </tbody>
                </table>
            </div>
        """
    
    # Add Monte Carlo section
    html_content += f"""
            <div class="section">
                <h2>Uncertainty Analysis</h2>
                <p>Monte Carlo simulation with {mc_results.iterations:,} iterations for {sample_vehicle.vehicle.model_name}</p>
                <div id="monte-carlo-chart" class="chart-container"></div>
                
                <table>
                    <thead>
                        <tr>
                            <th>Statistic</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>Mean TCO</td><td>${mc_results.mean:,.0f}</td></tr>
                        <tr><td>Standard Deviation</td><td>${mc_results.std_dev:,.0f}</td></tr>
                        <tr><td>95% Confidence Interval</td><td>${mc_results.confidence_interval_95[0]:,.0f} - ${mc_results.confidence_interval_95[1]:,.0f}</td></tr>
                        <tr><td>Minimum</td><td>${mc_results.min_value:,.0f}</td></tr>
                        <tr><td>Maximum</td><td>${mc_results.max_value:,.0f}</td></tr>
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>Sensitivity Analysis</h2>
                <p>Impact of ±20% parameter changes on Total Cost of Ownership</p>
                <div id="sensitivity-chart" class="chart-container"></div>
            </div>
            
            <div class="section">
                <h2>Monte Carlo TCO Differentials</h2>
                <p>TCO differentials between BEV and diesel models for all vehicle pairs</p>
                <div id="monte-carlo-differentials-chart" class="chart-container"></div>
            </div>
    """
    
    # Add payback analysis if available
    if payback_analysis:
        html_content += """
            <div class="section">
                <h2>Payback Analysis</h2>
                <div id="payback-chart" class="chart-container"></div>
            </div>
        """
    
    # Add fleet transition analysis
    if not fleet_report.empty:
        total_row = fleet_report[fleet_report['vehicle_model'] == 'TOTAL'].iloc[0]
        html_content += f"""
            <div class="section">
                <h2>Fleet Transition Analysis</h2>
                <div class="key-findings">
                    <h3>Fleet Summary</h3>
                    <ul>
                        <li>Total vehicles: {int(total_row['quantity'])}</li>
                        <li>Total capital premium: ${total_row['fleet_capex_premium']:,.0f}</li>
                        <li>Annual fleet savings: ${total_row['fleet_annual_savings']:,.0f}</li>
                        <li>Average payback: {total_row['payback_years']:.1f} years</li>
                        <li>15-year NPV savings: ${total_row['15yr_npv_savings']:,.0f}</li>
                    </ul>
                </div>
                <div id="fleet-chart" class="chart-container"></div>
            </div>
        """
    
    # Add footer
    html_content += """
            <div class="footer">
                <p>Generated by MyBuild TCO Analysis System</p>
            </div>
        </div>
        
        <script>
    """
    
    # Add JavaScript to render charts
    for chart_id, fig in charts.items():
        if fig:
            html_content += f"""
            Plotly.newPlot('{chart_id}-chart', {pio.to_json(fig)});
            """
    
    html_content += """
        </script>
    </body>
    </html>
    """
    
    # Write HTML file
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"Report generated successfully: {output_file}")
    return output_file


def main():
    parser = argparse.ArgumentParser(description='Generate comprehensive TCO HTML report')
    parser.add_argument('--scenario', default='baseline', 
                       choices=list(SCENARIOS.keys()),
                       help='Scenario to analyze')
    parser.add_argument('--output', default='tco_report.html',
                       help='Output HTML file name')
    
    args = parser.parse_args()
    
    generate_comprehensive_report(args.scenario, args.output)


if __name__ == "__main__":
    import signal
    import sys
    
    def signal_handler(sig, frame):
        print(f'\nReceived signal {sig}. Cleaning up...')
        sys.exit(0)
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
