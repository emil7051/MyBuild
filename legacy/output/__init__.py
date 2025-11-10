"""
Reporting module for TCO analysis.
Provides analysis, visualisation and report generation capabilities.
"""
import sys
import os

# Ensure the project root is on the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis.analysis import (
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