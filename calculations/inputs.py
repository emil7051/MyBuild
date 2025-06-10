"""
Input calculations and vehicle data management for TCO analysis.
1. Universal access to vehicle data with pre-calculated subcomponents
2. Transparent calculation definitions
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal

from data.vehicles import VehicleModel, BY_ID, ALL_MODELS
from data.scenarios import EconomicScenario, get_active_scenario

# Import modular calculators
from .financial import (
    calculate_stamp_duty, 
    calculate_rebate, 
    calculate_initial_cost,
    FinancingCalculator,
    DepreciationCalculator
)
from .operating import (
    FuelCostCalculator,
    MaintenanceCostCalculator,
    InsuranceCostCalculator,
    BatteryReplacementCalculator,
    calculate_carbon_cost_year,
    ChargingTimeCostCalculator,
    PayloadPenaltyCalculator
)
from .utils import calculate_present_value, discount_to_present


@dataclass
class VehicleInputs:
    """Pre-calculated subcomponents for vehicle calculations."""

    # Base vehicle data
    vehicle: VehicleModel
    
    # Economic scenario
    scenario: EconomicScenario = field(default_factory=get_active_scenario)
    
    # Purchase method
    purchase_method: Literal['outright', 'financed'] = 'financed'
    
    # Purchase-related calculations
    stamp_duty: float = field(init=False)
    rebate: float = field(init=False)
    initial_cost: float = field(init=False)
    
    # Financing calculations
    down_payment: float = field(init=False)
    loan_amount: float = field(init=False)
    monthly_payment: float = field(init=False)
    total_financing_cost: float = field(init=False)
    
    # Annual operating costs
    annual_fuel_cost_base: float = field(init=False)
    annual_maintenance_cost: float = field(init=False)
    annual_insurance_cost: float = field(init=False)
    annual_vehicle_insurance: float = field(init=False)
    
    # Battery-related (BEV only)
    battery_replacement_cost_year8: float = field(init=False)
    
    # Charging labour cost (BEV only)
    annual_charging_labour_cost: float = field(init=False)
    
    # Payload penalty
    annual_payload_penalty: float = field(init=False)
    
    # Depreciation
    first_year_depreciation: float = field(init=False)
    annual_depreciation_rate: float = field(init=False)
    
    # Calculator instances (private)
    _fuel_calculator: FuelCostCalculator = field(init=False, repr=False)
    _maintenance_calculator: MaintenanceCostCalculator = field(init=False, repr=False)
    _insurance_calculator: InsuranceCostCalculator = field(init=False, repr=False)
    _battery_calculator: BatteryReplacementCalculator = field(init=False, repr=False)
    _depreciation_calculator: DepreciationCalculator = field(init=False, repr=False)
    _financing_calculator: FinancingCalculator = field(init=False, repr=False)
    _charging_calculator: ChargingTimeCostCalculator = field(init=False, repr=False)
    _payload_calculator: PayloadPenaltyCalculator = field(init=False, repr=False)
    
    def __post_init__(self):
        """Calculations of derived values listed above."""
        
        # Initialise calculators
        self._fuel_calculator = FuelCostCalculator(self.vehicle, self.scenario)
        self._maintenance_calculator = MaintenanceCostCalculator(self.vehicle, self.scenario)
        self._insurance_calculator = InsuranceCostCalculator(self.vehicle)
        self._battery_calculator = BatteryReplacementCalculator(self.vehicle, self.scenario)
        self._financing_calculator = FinancingCalculator()
        self._charging_calculator = ChargingTimeCostCalculator(self.vehicle)
        self._payload_calculator = PayloadPenaltyCalculator(self.vehicle)
        
        # Purchase calculations
        self.stamp_duty = calculate_stamp_duty(self.vehicle.msrp, self.vehicle.drivetrain_type == 'BEV')
        self.rebate = calculate_rebate(self.vehicle.msrp, self.vehicle.drivetrain_type)
        self.initial_cost = calculate_initial_cost(self.vehicle.msrp, self.vehicle.drivetrain_type)
        
        # Depreciation calculator (needs initial cost)
        self._depreciation_calculator = DepreciationCalculator(self.initial_cost, self.scenario)
        self.first_year_depreciation = self._depreciation_calculator.first_year_depreciation
        self.annual_depreciation_rate = self._depreciation_calculator.annual_depreciation_rate
        
        # Financing calculations (only if financed)
        if self.purchase_method == 'financed':
            self.down_payment = self._financing_calculator.calculate_down_payment(self.initial_cost)
            self.loan_amount = self._financing_calculator.calculate_loan_amount(self.initial_cost, self.down_payment)
            
            interest_rate = self._financing_calculator.calculate_interest_rate(self.vehicle.drivetrain_type)
            self.monthly_payment = self._financing_calculator.calculate_monthly_payment(self.loan_amount, interest_rate)
            self.total_financing_cost = self._financing_calculator.calculate_total_financing_cost(self.monthly_payment, self.loan_amount)
        else:
            # Outright purchase - no financing
            self.down_payment = 0.0
            self.loan_amount = 0.0
            self.monthly_payment = 0.0
            self.total_financing_cost = 0.0
        
        # Operating costs
        self.annual_fuel_cost_base = self._fuel_calculator.get_annual_base_cost()
        self.annual_maintenance_cost = self._maintenance_calculator.get_annual_base_cost()
        self.annual_vehicle_insurance = self._insurance_calculator.get_vehicle_insurance()
        self.annual_insurance_cost = self._insurance_calculator.get_total_insurance()
        
        # Battery replacement cost (year 8 for BEVs)
        self.battery_replacement_cost_year8 = self._battery_calculator.get_replacement_cost_year8()
        
        # Charging labour cost (BEV only)
        self.annual_charging_labour_cost = self._charging_calculator.calculate_annual_charging_labour_cost()
        
        # Payload penalty
        self.annual_payload_penalty = self._payload_calculator.calculate_annual_payload_penalty()
    
    def get_fuel_cost_year(self, year: int) -> float:
        """Get fuel cost for a specific year with price escalation and efficiency improvements."""
        return self._fuel_calculator.get_fuel_cost_year(year)
    
    def get_battery_replacement_year(self, year: int) -> float:
        """Get battery replacement cost for a specific year (only year 8 for BEVs)."""
        return self._battery_calculator.get_battery_replacement_year(year)
    
    def get_depreciation_year(self, year: int) -> float:
        """Get depreciation for a specific year."""
        return self._depreciation_calculator.get_depreciation_year(year, self.vehicle.drivetrain_type)
    
    def get_residual_value(self, year: int) -> float:
        """Get residual value at the end of a specific year."""
        return self._depreciation_calculator.get_residual_value(year, self.vehicle.drivetrain_type)
    
    def get_policy_adjusted_rebate(self, year: int = 1) -> float:
        """Get rebate amount considering policy phase-out from scenario."""
        if not self.scenario.policy_active(year):
            return 0.0
        return self.rebate
    
    def get_carbon_cost_year(self, year: int) -> float:
        """Calculate carbon cost for a specific year (diesel only)."""
        return calculate_carbon_cost_year(self.vehicle, year, self.scenario)
    
    def get_maintenance_cost_year(self, year: int) -> float:
        """Get maintenance cost for a specific year with age-based escalation."""
        return self._maintenance_calculator.get_maintenance_cost_year(year)
    
    def get_charging_labour_cost_year(self, year: int) -> float:
        """Get charging labour cost for a specific year."""
        # For now, return constant annual cost
        # Could be enhanced with scenario-based adjustments
        return self.annual_charging_labour_cost
    
    def get_payload_penalty_year(self, year: int) -> float:
        """Get payload penalty for a specific year."""
        # Could be enhanced with scenario-based adjustments
        # For example, freight rates might increase with inflation
        return self.annual_payload_penalty

class VehicleData:
    """Universal access point for vehicle data with pre-calculated inputs."""
    
    def __init__(self, scenario: Optional[EconomicScenario] = None, purchase_method: Literal['outright', 'financed'] = 'financed'):
        self._default_scenario = scenario or get_active_scenario()
        self._default_purchase_method = purchase_method
        self._inputs_cache: Dict[str, VehicleInputs] = {}
        self._initialise_all_vehicles()
    
    def _initialise_all_vehicles(self):
        """Pre-calculate inputs for all vehicles with default scenario."""
        for vehicle_id, vehicle in BY_ID.items():
            self._inputs_cache[vehicle_id] = VehicleInputs(vehicle, self._default_scenario, self._default_purchase_method)
    
    def get_vehicle(self, vehicle_id: str, scenario: Optional[EconomicScenario] = None, purchase_method: Optional[Literal['outright', 'financed']] = None) -> VehicleInputs:
        """Get vehicle with pre-calculated inputs, optionally with a specific scenario and purchase method."""
        if vehicle_id not in BY_ID:
            raise ValueError(f"Vehicle ID '{vehicle_id}' not found")
        
        # If no scenario or purchase method specified, use cached version with defaults
        if scenario is None and purchase_method is None:
            return self._inputs_cache[vehicle_id]
        
        # Otherwise create new VehicleInputs with specified parameters
        use_scenario = scenario or self._default_scenario
        use_purchase_method = purchase_method or self._default_purchase_method
        return VehicleInputs(BY_ID[vehicle_id], use_scenario, use_purchase_method)
    
    def get_all_vehicles(self, scenario: Optional[EconomicScenario] = None, purchase_method: Optional[Literal['outright', 'financed']] = None) -> Dict[str, VehicleInputs]:
        """Get all vehicles with pre-calculated inputs."""
        if scenario is None and purchase_method is None:
            return self._inputs_cache.copy()
        
        # Create new inputs with specified parameters
        use_scenario = scenario or self._default_scenario
        use_purchase_method = purchase_method or self._default_purchase_method
        return {
            vehicle_id: VehicleInputs(vehicle, use_scenario, use_purchase_method)
            for vehicle_id, vehicle in BY_ID.items()
        }
    
    def get_vehicle_pairs(self, scenario: Optional[EconomicScenario] = None, purchase_method: Optional[Literal['outright', 'financed']] = None) -> List[tuple[VehicleInputs, VehicleInputs]]:
        """Get BEV-Diesel comparison pairs."""
        all_vehicles = self.get_all_vehicles(scenario, purchase_method)
        pairs = []
        
        for vehicle_id, vehicle_inputs in all_vehicles.items():
            if (vehicle_inputs.vehicle.drivetrain_type == 'BEV' and 
                vehicle_inputs.vehicle.comparison_pair in all_vehicles):
                bev = vehicle_inputs
                diesel = all_vehicles[vehicle_inputs.vehicle.comparison_pair]
                pairs.append((bev, diesel))
        return pairs

# Global instance for easy access
vehicle_data = VehicleData()
