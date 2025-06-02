"""
Monte Carlo simulation and uncertainty analysis for TCO calculations.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import copy

from calculations.inputs import VehicleInputs
from calculations.calculations import calculate_tco_from_inputs, TCOResult
from data import constants as const
from data.scenarios import EconomicScenario


@dataclass
class UncertaintyParameter:
    """Define uncertain parameter with probability distribution."""
    name: str
    distribution: str  # 'normal', 'uniform', 'triangular'
    base_value: float
    # For normal distribution
    std_dev: Optional[float] = None
    # For uniform and triangular
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    # For triangular only
    mode_value: Optional[float] = None
    
    def sample(self) -> float:
        """Sample a value from the distribution."""
        if self.distribution == 'normal':
            return max(0, np.random.normal(self.base_value, self.std_dev))
        elif self.distribution == 'uniform':
            return np.random.uniform(self.min_value, self.max_value)
        elif self.distribution == 'triangular':
            return np.random.triangular(self.min_value, self.mode_value, self.max_value)
        else:
            return self.base_value


@dataclass
class SimulationResults:
    """Results from Monte Carlo simulation."""
    iterations: int
    tco_values: np.ndarray
    percentiles: Dict[int, float] = field(default_factory=dict)
    mean: float = 0.0
    std_dev: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0
    confidence_interval_95: Tuple[float, float] = (0.0, 0.0)
    
    def __post_init__(self):
        """Calculate summary statistics."""
        self.mean = np.mean(self.tco_values)
        self.std_dev = np.std(self.tco_values)
        self.min_value = np.min(self.tco_values)
        self.max_value = np.max(self.tco_values)
        
        # Calculate percentiles
        for p in [5, 10, 25, 50, 75, 90, 95]:
            self.percentiles[p] = np.percentile(self.tco_values, p)
            
        self.confidence_interval_95 = (self.percentiles[5], self.percentiles[95])


class MonteCarloSimulation:
    """Perform Monte Carlo simulation for TCO uncertainty analysis."""
    
    def __init__(self, base_inputs: VehicleInputs):
        self.base_inputs = base_inputs
        self.parameters = self._define_default_uncertainties()
        
    def _define_default_uncertainties(self) -> Dict[str, UncertaintyParameter]:
        """Define default uncertainty distributions for key parameters."""
        vehicle = self.base_inputs.vehicle
        
        uncertainties = {
            'fuel_price_variation': UncertaintyParameter(
                name='fuel_price_variation',
                distribution='normal',
                base_value=1.0,
                std_dev=0.15  # 15% standard deviation
            ),
            'electricity_price_variation': UncertaintyParameter(
                name='electricity_price_variation',
                distribution='triangular',
                base_value=1.0,
                min_value=0.7,   # 30% below base
                mode_value=1.0,  # Most likely at base
                max_value=1.5    # 50% above base
            ),
            'maintenance_cost_variation': UncertaintyParameter(
                name='maintenance_cost_variation',
                distribution='normal',
                base_value=1.0,
                std_dev=0.10  # 10% standard deviation
            ),
            'annual_kms_variation': UncertaintyParameter(
                name='annual_kms_variation',
                distribution='normal',
                base_value=vehicle.annual_kms,
                std_dev=vehicle.annual_kms * 0.1  # 10% variation
            ),
            'residual_value_variation': UncertaintyParameter(
                name='residual_value_variation',
                distribution='uniform',
                base_value=1.0,
                min_value=0.8,  # 20% below expected
                max_value=1.2   # 20% above expected
            )
        }
        
        # Add battery-specific uncertainties for BEVs
        if vehicle.drivetrain_type == 'BEV':
            uncertainties['battery_life_variation'] = UncertaintyParameter(
                name='battery_life_variation',
                distribution='triangular',
                base_value=1.0,
                min_value=0.7,   # Battery might fail earlier
                mode_value=1.0,  # Expected life
                max_value=1.3    # Battery might last longer
            )
            uncertainties['charging_efficiency_variation'] = UncertaintyParameter(
                name='charging_efficiency_variation',
                distribution='normal',
                base_value=1.0,
                std_dev=0.05  # 5% variation in charging losses
            )
            
        return uncertainties
    
    def add_custom_uncertainty(self, param: UncertaintyParameter):
        """Add or override an uncertainty parameter."""
        self.parameters[param.name] = param
        
    def _apply_uncertainties(self, sample_values: Dict[str, float]) -> VehicleInputs:
        """Create modified inputs with sampled uncertainty values."""
        # Deep copy to avoid modifying original
        modified_inputs = copy.deepcopy(self.base_inputs)
        
        # Apply fuel/electricity price variations
        if 'fuel_price_variation' in sample_values:
            # Modify fuel cost calculator's base prices
            if modified_inputs.vehicle.drivetrain_type == 'Diesel':
                # Apply to diesel price in scenario
                multiplier = sample_values['fuel_price_variation']
                modified_scenario = copy.deepcopy(modified_inputs.scenario)
                modified_scenario.diesel_price_trajectory = [
                    p * multiplier for p in modified_scenario.diesel_price_trajectory
                ]
                modified_inputs.scenario = modified_scenario
                
        if 'electricity_price_variation' in sample_values:
            if modified_inputs.vehicle.drivetrain_type == 'BEV':
                multiplier = sample_values['electricity_price_variation']
                modified_scenario = copy.deepcopy(modified_inputs.scenario)
                modified_scenario.electricity_price_trajectory = [
                    p * multiplier for p in modified_scenario.electricity_price_trajectory
                ]
                modified_inputs.scenario = modified_scenario
                
        # Apply maintenance cost variation
        if 'maintenance_cost_variation' in sample_values:
            multiplier = sample_values['maintenance_cost_variation']
            modified_inputs.annual_maintenance_cost *= multiplier
            
        # Apply annual kms variation
        if 'annual_kms_variation' in sample_values:
            # Create new vehicle with modified annual kms
            modified_vehicle = copy.deepcopy(modified_inputs.vehicle)
            object.__setattr__(modified_vehicle, 'annual_kms', sample_values['annual_kms_variation'])
            modified_inputs.vehicle = modified_vehicle
            
        # Reinitialise calculators with modified inputs
        modified_inputs.__post_init__()
        
        return modified_inputs
    
    def run(self, iterations: int = 10000, seed: Optional[int] = None) -> SimulationResults:
        """Run Monte Carlo simulation."""
        if seed is not None:
            np.random.seed(seed)
            
        tco_results = []
        
        for i in range(iterations):
            # Sample from all uncertainty distributions
            sample_values = {
                name: param.sample() 
                for name, param in self.parameters.items()
            }
            
            # Apply uncertainties to create modified inputs
            modified_inputs = self._apply_uncertainties(sample_values)
            
            # Calculate TCO with modified inputs
            tco = calculate_tco_from_inputs(modified_inputs)
            tco_results.append(tco.total_cost)
            
        return SimulationResults(
            iterations=iterations,
            tco_values=np.array(tco_results)
        )
    
    def compare_uncertainty(
        self, 
        other_inputs: VehicleInputs, 
        iterations: int = 10000
    ) -> Tuple[SimulationResults, SimulationResults, np.ndarray]:
        """Compare uncertainty between two vehicles (e.g., BEV vs Diesel)."""
        # Run simulation for this vehicle
        results1 = self.run(iterations)
        
        # Run simulation for other vehicle
        other_sim = MonteCarloSimulation(other_inputs)
        # Use same uncertainty parameters where applicable
        for name, param in self.parameters.items():
            if name not in ['battery_life_variation', 'charging_efficiency_variation']:
                other_sim.parameters[name] = param
                
        results2 = other_sim.run(iterations)
        
        # Calculate differences
        differences = results1.tco_values - results2.tco_values
        
        return results1, results2, differences


class SensitivityAnalysis:
    """Perform deterministic sensitivity analysis."""
    
    def __init__(self, base_inputs: VehicleInputs):
        self.base_inputs = base_inputs
        self.base_tco = calculate_tco_from_inputs(base_inputs)
        
    def analyse_parameter(
        self,
        parameter_name: str,
        values: List[float],
        parameter_type: str = 'multiplier'
    ) -> List[Tuple[float, float, float]]:
        """
        Analyse sensitivity to a parameter.
        
        Returns: List of (parameter_value, total_cost, percent_change)
        """
        results = []
        
        for value in values:
            modified_inputs = copy.deepcopy(self.base_inputs)
            
            # Apply parameter change based on type
            if parameter_type == 'multiplier':
                if parameter_name == 'diesel_price':
                    modified_scenario = copy.deepcopy(modified_inputs.scenario)
                    modified_scenario.diesel_price_trajectory = [
                        p * value for p in modified_scenario.diesel_price_trajectory
                    ]
                    modified_inputs.scenario = modified_scenario
                elif parameter_name == 'electricity_price':
                    modified_scenario = copy.deepcopy(modified_inputs.scenario)
                    modified_scenario.electricity_price_trajectory = [
                        p * value for p in modified_scenario.electricity_price_trajectory
                    ]
                    modified_inputs.scenario = modified_scenario
                elif parameter_name == 'maintenance_cost':
                    modified_inputs.annual_maintenance_cost *= value
                elif parameter_name == 'interest_rate':
                    # Modify interest rate and recalculate financing
                    modified_inputs.__post_init__()
                    
            # Recalculate TCO
            modified_inputs.__post_init__()  # Reinitialise calculators
            new_tco = calculate_tco_from_inputs(modified_inputs)
            
            # Calculate percent change
            percent_change = (new_tco.total_cost - self.base_tco.total_cost) / self.base_tco.total_cost * 100
            
            results.append((value, new_tco.total_cost, percent_change))
            
        return results
    
    def tornado_analysis(
        self,
        parameters: Dict[str, Tuple[float, float]]
    ) -> List[Tuple[str, float, float, float]]:
        """
        Perform tornado diagram analysis.
        
        Args:
            parameters: Dict of parameter_name -> (low_value, high_value)
            
        Returns:
            List of (parameter_name, low_impact, high_impact, range)
            sorted by impact range
        """
        results = []
        
        for param_name, (low, high) in parameters.items():
            # Calculate impact at low and high values
            low_results = self.analyse_parameter(param_name, [low])
            high_results = self.analyse_parameter(param_name, [high])
            
            low_impact = low_results[0][2]  # Percent change
            high_impact = high_results[0][2]  # Percent change
            impact_range = abs(high_impact - low_impact)
            
            results.append((param_name, low_impact, high_impact, impact_range))
            
        # Sort by impact range (largest first)
        return sorted(results, key=lambda x: x[3], reverse=True)