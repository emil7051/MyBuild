"""
Monte Carlo simulation and uncertainty analysis for TCO calculations.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

from .inputs import VehicleInputs
from data import constants as const
from data.scenarios import EconomicScenario

# Type checking imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .calculations import TCOResult


@dataclass
class UncertaintyParameter:
    """Define uncertain parameter with probability distribution."""
    name: str  # The human-readable name of the parameter
    override_key: str  # The key this parameter maps to in the overrides dictionary
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
                override_key='fuel_price_variation',
                distribution='normal',
                base_value=1.0,
                std_dev=0.15  # 15% standard deviation
            ),
            'electricity_price_variation': UncertaintyParameter(
                name='electricity_price_variation',
                override_key='electricity_price_variation',
                distribution='triangular',
                base_value=1.0,
                min_value=0.7,   # 30% below base
                mode_value=1.0,  # Most likely at base
                max_value=1.5    # 50% above base
            ),
            'maintenance_cost_variation': UncertaintyParameter(
                name='maintenance_cost_variation',
                override_key='maintenance_cost_variation',
                distribution='normal',
                base_value=1.0,
                std_dev=0.10  # 10% standard deviation
            ),
            'annual_kms_variation': UncertaintyParameter(
                name='annual_kms_variation',
                override_key='annual_kms_variation',
                distribution='normal',
                base_value=vehicle.annual_kms,
                std_dev=vehicle.annual_kms * 0.1  # 10% variation
            ),
            'residual_value_variation': UncertaintyParameter(
                name='residual_value_variation',
                override_key='residual_value_variation',
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
                override_key='battery_life_variation',
                distribution='triangular',
                base_value=1.0,
                min_value=0.7,   # Battery might fail earlier
                mode_value=1.0,  # Expected life
                max_value=1.3    # Battery might last longer
            )
            uncertainties['charging_efficiency_variation'] = UncertaintyParameter(
                name='charging_efficiency_variation',
                override_key='charging_efficiency_variation',
                distribution='normal',
                base_value=1.0,
                std_dev=0.05  # 5% variation in charging losses
            )
            
        return uncertainties
    
    def add_custom_uncertainty(self, param: UncertaintyParameter):
        """Add or override an uncertainty parameter."""
        self.parameters[param.name] = param
    
    def run(self, iterations: int = 10000, seed: Optional[int] = None) -> SimulationResults:
        """Run Monte Carlo simulation."""
        if seed is not None:
            np.random.seed(seed)
            
        tco_results = []
        
        for i in range(iterations):
            # 1. Create the overrides dictionary from sampled parameters
            sample_overrides = {
                param.override_key: param.sample()
                for param in self.parameters.values()
            }
            
            # 2. Calculate TCO directly, passing the base inputs and the new overrides
            from .calculations import calculate_tco_from_inputs
            tco = calculate_tco_from_inputs(self.base_inputs, overrides=sample_overrides)
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
        from .calculations import calculate_tco_from_inputs
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
            # Create overrides dictionary based on parameter name and type
            overrides = {}
            
            if parameter_type == 'multiplier':
                if parameter_name == 'diesel_price':
                    overrides['fuel_price_variation'] = value
                elif parameter_name == 'electricity_price':
                    overrides['electricity_price_variation'] = value
                elif parameter_name == 'maintenance_cost':
                    overrides['maintenance_cost_variation'] = value
                elif parameter_name == 'battery_life':
                    overrides['battery_life_variation'] = value
                elif parameter_name == 'residual_value':
                    overrides['residual_value_variation'] = value
            elif parameter_type == 'absolute':
                if parameter_name == 'annual_kms':
                    overrides['annual_kms_variation'] = value
                    
            # Calculate TCO with overrides
            from .calculations import calculate_tco_from_inputs
            new_tco = calculate_tco_from_inputs(self.base_inputs, overrides=overrides)
            
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