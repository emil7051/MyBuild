"""
Example usage of the reporting capabilities.
"""

from calculations.calculations import vehicle_data, compare_vehicle_pairs
from data.scenarios import SCENARIOS
from reports import (
    calculate_payback_analysis,
    create_payback_chart,
    generate_executive_summary,
    analyse_policy_combinations
)

# Example 1: Generate payback analysis for a specific pair
bev_inputs = vehicle_data.get_vehicle('BEV006')  # eActros 600
diesel_inputs = vehicle_data.get_vehicle('DSL006')  # MB Actros

payback = calculate_payback_analysis(bev_inputs, diesel_inputs)
chart = create_payback_chart(payback)
chart.write_html('payback_analysis.html')

# Example 2: Generate executive summary
comparisons = compare_vehicle_pairs(SCENARIOS['baseline'])
summary = generate_executive_summary(comparisons, 'Baseline Scenario')
print(summary)

# Example 3: Analyse policy combinations
policy_results = analyse_policy_combinations()
print(f"Most cost-effective policy: {policy_results[0].policy_combination}")
