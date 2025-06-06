"""
Reporting module for TCO analysis.
Provides analysis, visualisation and report generation capabilities.
"""

from .analysis import (
    PaybackAnalysis,
    PolicyImpactAnalysis,
    FleetTransitionAnalysis,
    calculate_payback_analysis,
    analyse_policy_combinations,
    analyse_purchase_timing
)

from .visualisations import (
    TCOVisualiser,
    create_payback_chart,
    create_tornado_chart,
    create_policy_impact_dashboard
)

from .generators import (
    generate_executive_summary,
    generate_fleet_report,
    generate_policy_recommendations
)

__all__ = [
    # Analysis classes
    'PaybackAnalysis',
    'PolicyImpactAnalysis', 
    'FleetTransitionAnalysis',
    
    # Analysis functions
    'calculate_payback_analysis',
    'analyse_policy_combinations',
    'analyse_purchase_timing',
    
    # Visualisation
    'TCOVisualiser',
    'create_payback_chart',
    'create_tornado_chart',
    'create_policy_impact_dashboard',
    
    # Report generation
    'generate_executive_summary',
    'generate_fleet_report',
    'generate_policy_recommendations'
]