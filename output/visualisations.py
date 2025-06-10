"""
Visualisation functions for TCO analysis reports.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Optional

from .analysis import PaybackAnalysis, PolicyImpactAnalysis
from calculations.calculations import TCOResult
from calculations.simulation import SensitivityAnalysis
from data import constants as const
from data.scenarios import EconomicScenario

class TCOVisualiser:
    """Central visualisation class for TCO reports."""
    
    @staticmethod
    def create_payback_chart(analysis: PaybackAnalysis) -> go.Figure:
        """Create interactive payback period visualisation."""
        fig = go.Figure()
        
        # Create years array including year 0
        years = list(range(const.VEHICLE_LIFE + 1))
        
        # Add initial costs at year 0
        bev_costs = [analysis.cumulative_bev_costs[0] if analysis.cumulative_bev_costs else 0]
        bev_costs.extend(analysis.cumulative_bev_costs)
        
        diesel_costs = [analysis.cumulative_diesel_costs[0] if analysis.cumulative_diesel_costs else 0]
        diesel_costs.extend(analysis.cumulative_diesel_costs)
        
        # BEV cumulative cost line
        fig.add_trace(go.Scatter(
            x=years,
            y=bev_costs[:len(years)],
            mode='lines+markers',
            name=f'BEV ({analysis.bev_id})',
            line=dict(color='green', width=3),
            hovertemplate='Year: %{x}<br>Cumulative Cost: $%{y:,.0f}<extra></extra>'
        ))
        
        # Diesel cumulative cost line
        fig.add_trace(go.Scatter(
            x=years,
            y=diesel_costs[:len(years)],
            mode='lines+markers',
            name=f'Diesel ({analysis.diesel_id})',
            line=dict(color='grey', width=3),
            hovertemplate='Year: %{x}<br>Cumulative Cost: $%{y:,.0f}<extra></extra>'
        ))
        
        # Add savings area
        fig.add_trace(go.Scatter(
            x=years[1:],
            y=analysis.annual_savings,
            mode='lines',
            name='Annual Savings',
            line=dict(color='blue', width=2, dash='dot'),
            yaxis='y2',
            hovertemplate='Year: %{x}<br>Annual Saving: $%{y:,.0f}<extra></extra>'
        ))
        
        # Add breakeven point
        if analysis.breakeven_achieved:
            fig.add_vline(
                x=analysis.payback_years,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Payback: {analysis.payback_years:.1f} years",
                annotation_position="top left"
            )
        
        # Update layout
        fig.update_layout(
            title={
                'text': f"Payback Analysis: {analysis.bev_id} vs {analysis.diesel_id}",
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis=dict(
                title="Years from Purchase",
                gridcolor='lightgray'
            ),
            yaxis=dict(
                title="Cumulative Cost ($)",
                gridcolor='lightgray',
                rangemode='tozero'
            ),
            yaxis2=dict(
                title="Annual Savings ($)",
                overlaying='y',
                side='right',
                showgrid=False
            ),
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            template='plotly_white'
        )
        
        # Add annotations for key metrics
        fig.add_annotation(
            text=f"Total 15-year savings: ${analysis.total_savings_15yr:,.0f}",
            xref="paper", yref="paper",
            x=0.02, y=0.95,
            showarrow=False,
            bgcolor="white",
            bordercolor="black",
            borderwidth=1
        )
        
        return fig
    
    @staticmethod
    def create_tornado_chart(
        sensitivity_results: Dict[str, List[tuple]],
        base_tco: float
    ) -> go.Figure:
        """Create tornado diagram from sensitivity analysis results."""
        
        # Process results to get impact ranges
        tornado_data = []
        
        for param, results in sensitivity_results.items():
            # Find results closest to ±20% change
            low_result = min(results, key=lambda x: abs(x[0] - 0.8))
            high_result = min(results, key=lambda x: abs(x[0] - 1.2))
            
            low_impact = (low_result[1] - base_tco) / base_tco * 100
            high_impact = (high_result[1] - base_tco) / base_tco * 100
            
            tornado_data.append({
                'parameter': param.replace('_', ' ').title(),
                'low_impact': low_impact,
                'high_impact': high_impact,
                'range': abs(high_impact - low_impact)
            })
        
        # Sort by impact range
        tornado_data.sort(key=lambda x: x['range'], reverse=True)
        df = pd.DataFrame(tornado_data)
        
        # Create figure
        fig = go.Figure()
        
        # Add bars
        fig.add_trace(go.Bar(
            name='Decrease (-20%)',
            y=df['parameter'],
            x=df['low_impact'],
            orientation='h',
            marker_color='lightblue',
            hovertemplate='%{y}<br>Impact: %{x:.1f}%<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            name='Increase (+20%)',
            y=df['parameter'],
            x=df['high_impact'],
            orientation='h',
            marker_color='lightcoral',
            hovertemplate='%{y}<br>Impact: %{x:.1f}%<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title='Sensitivity Analysis: Impact on Total Cost of Ownership',
            xaxis=dict(
                title='Change in TCO (%)',
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='black'
            ),
            yaxis=dict(
                title='Parameter',
                categoryorder='total ascending'
            ),
            barmode='overlay',
            template='plotly_white',
            height=400 + len(tornado_data) * 30  # Dynamic height
        )
        
        return fig
    
    @staticmethod
    def create_policy_impact_dashboard(
        policy_results: List[PolicyImpactAnalysis],
        top_n: int = 20
    ) -> go.Figure:
        """Create comprehensive policy impact visualisation."""
        
        # Convert to DataFrame for easier manipulation
        data = []
        for result in policy_results[:top_n]:
            data.append({
                'rebate': result.policy_combination['purchase_rebate'],
                'stamp_duty': result.policy_combination['stamp_duty_exemption'],
                'loan_subsidy': result.policy_combination['green_loan_subsidy'],
                'carbon_price': result.policy_combination['carbon_price'],
                'avg_tco_diff': result.avg_tco_difference,
                'viable_vehicles': result.vehicles_becoming_viable,
                'policy_cost': result.total_policy_cost,
                'cost_effectiveness': result.cost_effectiveness
            })
        
        df = pd.DataFrame(data)
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Policy Cost vs TCO Impact',
                'Cost Effectiveness by Policy Mix',
                'Vehicles Becoming Viable',
                'Policy Parameter Heatmap'
            ),
            specs=[
                [{'type': 'scatter'}, {'type': 'bar'}],
                [{'type': 'bar'}, {'type': 'scatter'}]
            ]
        )
        
        # 1. Scatter: Policy Cost vs TCO Impact
        fig.add_trace(
            go.Scatter(
                x=df['policy_cost'],
                y=-df['avg_tco_diff'],  # Negative so positive = BEV cheaper
                mode='markers',
                marker=dict(
                    size=df['viable_vehicles'] * 3,
                    color=df['cost_effectiveness'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Cost<br>Effectiveness")
                ),
                text=[f"Rebate: ${r:,}<br>Carbon: ${c}" 
                      for r, c in zip(df['rebate'], df['carbon_price'])],
                hovertemplate='Policy Cost: $%{x:,.0f}<br>' +
                              'TCO Reduction: $%{y:,.0f}<br>' +
                              '%{text}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # 2. Bar: Cost Effectiveness
        top_5 = df.nsmallest(5, 'cost_effectiveness')
        fig.add_trace(
            go.Bar(
                x=top_5.index,
                y=top_5['cost_effectiveness'],
                text=[f"R:${r/1000:.0f}k<br>S:{s:.0%}<br>L:{l:.1%}<br>C:${c}" 
                      for r,s,l,c in zip(top_5['rebate'], top_5['stamp_duty'], 
                                         top_5['loan_subsidy']*100, top_5['carbon_price'])],
                textposition='outside',
                marker_color='lightgreen'
            ),
            row=1, col=2
        )
        
        # 3. Bar: Vehicles Becoming Viable
        fig.add_trace(
            go.Bar(
                x=['Light Rigid', 'Medium Rigid', 'Articulated'],
                y=[3, 2, 3],  # This should be calculated from actual data
                marker_color=['lightblue', 'lightcoral', 'lightgreen']
            ),
            row=2, col=1
        )
        
        # 4. 3D Scatter: Multi-dimensional view
        fig.add_trace(
            go.Scatter(
                x=df['rebate'],
                y=df['carbon_price'],
                mode='markers',
                marker=dict(
                    size=10,
                    color=-df['avg_tco_diff'],
                    colorscale='RdYlGn',
                    showscale=False
                ),
                hovertemplate='Rebate: $%{x:,}<br>' +
                              'Carbon Price: $%{y}<br>' +
                              'TCO Diff: $%{marker.color:,.0f}<extra></extra>'
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_xaxes(title_text="Annual Policy Cost ($)", row=1, col=1)
        fig.update_yaxes(title_text="Average TCO Reduction ($)", row=1, col=1)
        
        fig.update_xaxes(title_text="Policy Mix #", row=1, col=2)
        fig.update_yaxes(title_text="$ Policy per $ TCO Reduction", row=1, col=2)
        
        fig.update_xaxes(title_text="Vehicle Class", row=2, col=1)
        fig.update_yaxes(title_text="Number of Viable Models", row=2, col=1)
        
        fig.update_xaxes(title_text="Purchase Rebate ($)", row=2, col=2)
        fig.update_yaxes(title_text="Carbon Price ($/tonne)", row=2, col=2)
        
        fig.update_layout(
            height=800,
            showlegend=False,
            title_text="Policy Impact Analysis Dashboard",
            title_x=0.5
        )
        
        return fig


# Standalone convenience functions
def create_payback_chart(payback_analysis: PaybackAnalysis) -> go.Figure:
    """Convenience function to create payback chart."""
    return TCOVisualiser.create_payback_chart(payback_analysis)


def create_tornado_chart(
    sensitivity_analysis: SensitivityAnalysis,
    parameters: Optional[Dict[str, tuple]] = None
) -> go.Figure:
    """Convenience function to create tornado chart from sensitivity analysis."""
    if parameters is None:
        parameters = {
            'diesel_price': (0.8, 1.2),
            'electricity_price': (0.8, 1.2),
            'maintenance_cost': (0.8, 1.2),
            'battery_price': (0.8, 1.2),
            'interest_rate': (0.8, 1.2)
        }
    
    # Run sensitivity analysis for each parameter
    results = {}
    for param, (low, high) in parameters.items():
        results[param] = sensitivity_analysis.analyse_parameter(
            param, [low, 1.0, high], 'multiplier'
        )
    
    return TCOVisualiser.create_tornado_chart(results, sensitivity_analysis.base_tco.total_cost)


def create_policy_impact_dashboard(
    scenario: Optional[EconomicScenario] = None,
    purchase_method: str = 'financed'
) -> go.Figure:
    """Convenience function to create policy impact dashboard."""
    from .analysis import analyse_policy_combinations
    policy_results = analyse_policy_combinations(scenario, purchase_method)
    return TCOVisualiser.create_policy_impact_dashboard(policy_results)