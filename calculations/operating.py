"""
Operating cost calculations for vehicle TCO analysis.
Handles fuel, maintenance, insurance, and battery replacement costs.
"""

from typing import Optional, Dict

import data.constants as const
from data.scenarios import EconomicScenario
from data.vehicles import VehicleModel, BY_ID


__all__ = [
    'FuelCostCalculator',
    'ChargingTimeCostCalculator',
    'MaintenanceCostCalculator',
    'InsuranceCostCalculator',
    'BatteryReplacementCalculator',
    'PayloadPenaltyCalculator',
    'calculate_carbon_cost_year',
]


class FuelCostCalculator:
    """Handles fuel cost calculations for both BEV and diesel vehicles."""
    
    def __init__(self, vehicle: VehicleModel, scenario: Optional[EconomicScenario] = None):
        self.vehicle = vehicle
        self.scenario = scenario
    
    def calculate_bev_base_cost(self) -> float:
        """Calculate base annual electricity cost for BEV."""
        # Account for efficiency improvements from scenario (year 1)
        efficiency_multiplier = 1.0
        if self.scenario and self.scenario.bev_efficiency_improvement:
            efficiency_multiplier = self.scenario.bev_efficiency_improvement[0]
        
        adjusted_kwh_per_km = self.vehicle.kwh_per_km * efficiency_multiplier
        
        # Get charging proportions from the new dictionary structure
        proportions = const.CHARGING_MIX_PROPORTIONS['BEV'][self.vehicle.weight_class]
        
        return adjusted_kwh_per_km * self.vehicle.annual_kms * (
            proportions['retail'] * const.RETAIL_CHARGING_PRICE +
            proportions['offpeak'] * const.OFFPEAK_CHARGING_PRICE +
            proportions['solar'] * const.SOLAR_CHARGING_PRICE +
            proportions['public'] * const.PUBLIC_CHARGING_PRICE
        )
    
    def calculate_diesel_base_cost(self) -> float:
        """Calculate base annual diesel cost."""
        # Account for efficiency improvements from scenario (year 1)
        efficiency_multiplier = 1.0
        if self.scenario and self.scenario.diesel_efficiency_improvement:
            efficiency_multiplier = self.scenario.diesel_efficiency_improvement[0]
        
        adjusted_litres_per_km = self.vehicle.litres_per_km * efficiency_multiplier
        
        return adjusted_litres_per_km * self.vehicle.annual_kms * const.DIESEL_PRICE
    
    def get_annual_base_cost(self) -> float:
        """Get base annual fuel cost for the vehicle type."""
        if self.vehicle.drivetrain_type == 'BEV':
            return self.calculate_bev_base_cost()
        return self.calculate_diesel_base_cost()
    
    def get_fuel_cost_year(self, year: int, overrides: Optional[Dict[str, float]] = None) -> float:
        """Get fuel cost for a specific year with price escalation and efficiency improvements."""
        if self.vehicle.drivetrain_type == 'BEV':
            # Get price and efficiency multipliers from scenario
            price_multiplier = self.scenario.get_electricity_price_multiplier(year) if self.scenario else 1.0
            
            # Apply electricity price variation from overrides
            if overrides and 'electricity_price_variation' in overrides:
                price_multiplier *= overrides['electricity_price_variation']
                
            efficiency_multiplier = 1.0
            if (self.scenario and 
                self.scenario.bev_efficiency_improvement and 
                year <= len(self.scenario.bev_efficiency_improvement)):
                efficiency_multiplier = self.scenario.bev_efficiency_improvement[year - 1]
            
            # Apply charging efficiency variation from overrides
            if overrides and 'charging_efficiency_variation' in overrides:
                efficiency_multiplier *= overrides['charging_efficiency_variation']
            
            # Get charging proportions from the new dictionary structure
            proportions = const.CHARGING_MIX_PROPORTIONS['BEV'][self.vehicle.weight_class]
            
            # Recalculate base cost with year-specific efficiency
            adjusted_kwh_per_km = self.vehicle.kwh_per_km * efficiency_multiplier
            base_cost = adjusted_kwh_per_km * self.vehicle.annual_kms * (
                proportions['retail'] * const.RETAIL_CHARGING_PRICE +
                proportions['offpeak'] * const.OFFPEAK_CHARGING_PRICE +
                proportions['solar'] * const.SOLAR_CHARGING_PRICE +
                proportions['public'] * const.PUBLIC_CHARGING_PRICE
            )
        else:
            # Diesel vehicle
            price_multiplier = self.scenario.get_diesel_price_multiplier(year) if self.scenario else 1.0
            
            # Apply fuel price variation from overrides
            if overrides and 'fuel_price_variation' in overrides:
                price_multiplier *= overrides['fuel_price_variation']
                
            efficiency_multiplier = 1.0
            if (self.scenario and 
                self.scenario.diesel_efficiency_improvement and 
                year <= len(self.scenario.diesel_efficiency_improvement)):
                efficiency_multiplier = self.scenario.diesel_efficiency_improvement[year - 1]
            
            # Recalculate base cost with year-specific efficiency
            adjusted_litres_per_km = self.vehicle.litres_per_km * efficiency_multiplier
            base_cost = adjusted_litres_per_km * self.vehicle.annual_kms * const.DIESEL_PRICE
        
        return base_cost * price_multiplier

class ChargingTimeCostCalculator:
    """Calculate labour cost impact of charging time for BEVs."""
    
    def __init__(self, vehicle: VehicleModel):
        self.vehicle = vehicle
        
    def calculate_annual_charging_labour_cost(self) -> float:
        """Calculate annual labour cost during charging stops."""
        if self.vehicle.drivetrain_type != 'BEV':
            return 0.0
            
        # Calculate daily driving needs
        daily_kms = self.vehicle.annual_kms / const.DAYS_IN_YEAR
        
        # Calculate charging sessions needed
        # Account for not fully depleting battery (typically charge at 20% remaining)
        usable_range = self.vehicle.range_km * 0.8
        daily_charging_sessions = daily_kms / usable_range
        
        # Charging time varies by weight class and charging type
        if self.vehicle.weight_class == 'Articulated':
            # More public fast charging needed
            avg_charging_hours = 1.0  # 60 minutes for articulated
        elif self.vehicle.weight_class == 'Medium Rigid':
            avg_charging_hours = 0.75  # 45 minutes
        else:  # Light Rigid
            avg_charging_hours = 0.5  # 30 minutes
            
        # Calculate annual charging hours
        # Assume working days only (not all 365 days)
        working_days = const.DAYS_IN_YEAR * 0.7  # ~250 working days
        annual_charging_hours = daily_charging_sessions * avg_charging_hours * working_days
        
        # Return labour cost
        return annual_charging_hours * const.HOURLY_WAGE

class MaintenanceCostCalculator:
    """Handles maintenance cost calculations."""
    
    def __init__(self, vehicle: VehicleModel, scenario: Optional[EconomicScenario] = None):
        self.vehicle = vehicle
        self.scenario = scenario
    
    def get_annual_base_cost(self) -> float:
        """Calculate annual maintenance cost based on vehicle type."""
        cost_per_km = const.MAINTENANCE_COST_PER_KM[self.vehicle.drivetrain_type][self.vehicle.weight_class]
        return self.vehicle.annual_kms * cost_per_km
    
    def get_maintenance_cost_year(self, year: int, overrides: Optional[Dict[str, float]] = None) -> float:
        """Get maintenance cost for a specific year with age-based escalation."""
        base_cost = self.get_annual_base_cost()
        
        # Get the standard multiplier from the scenario
        multiplier = self.scenario.get_maintenance_cost_multiplier(year) if self.scenario else 1.0
        
        # Apply the override if it exists
        if overrides and 'maintenance_cost_variation' in overrides:
            multiplier *= overrides['maintenance_cost_variation']
            
        return base_cost * multiplier


class InsuranceCostCalculator:
    """Handles insurance cost calculations."""
    
    def __init__(self, vehicle: VehicleModel):
        self.vehicle = vehicle
    
    def get_vehicle_insurance(self) -> float:
        """Calculate annual vehicle insurance (excluding other insurance)."""
        if self.vehicle.drivetrain_type == 'BEV':
            return self.vehicle.msrp * const.INSURANCE_RATE_BEV
        return self.vehicle.msrp * const.INSURANCE_RATE_DSL
    
    def get_total_insurance(self) -> float:
        """Calculate total annual insurance cost including other insurance."""
        return self.get_vehicle_insurance() + const.OTHER_INSURANCE


class BatteryReplacementCalculator:
    """Handles battery replacement cost calculations for BEVs."""
    
    def __init__(self, vehicle: VehicleModel, scenario: Optional[EconomicScenario] = None):
        self.vehicle = vehicle
        self.scenario = scenario
    
    def get_replacement_cost_year8(self) -> float:
        """Calculate battery replacement cost for year 8."""
        if self.vehicle.drivetrain_type != 'BEV' or self.vehicle.battery_capacity_kwh == 0:
            return 0.0
        
        # Use scenario battery price trajectory
        battery_price_year8 = const.BATTERY_REPLACEMENT_COST
        if self.scenario:
            battery_price_year8 *= self.scenario.get_battery_price_multiplier(8)
        
        net_cost_per_kwh = battery_price_year8 - const.BATTERY_RECYCLE_VALUE
        
        return self.vehicle.battery_capacity_kwh * net_cost_per_kwh
    
    def get_battery_replacement_year(self, year: int, overrides: Optional[Dict[str, float]] = None) -> float:
        """Get battery replacement cost for a specific year (only year 8 for BEVs)."""
        if year == 8 and self.vehicle.drivetrain_type == 'BEV':
            base_cost = self.get_replacement_cost_year8()
            
            # Apply battery life variation if present
            if overrides and 'battery_life_variation' in overrides:
                # Shorter battery life increases replacement cost, longer life reduces it
                multiplier = 2.0 - overrides['battery_life_variation']  # If life is 0.7x, cost is 1.3x
                base_cost *= multiplier
                
            return base_cost
        return 0.0


def calculate_carbon_cost_year(vehicle: VehicleModel, year: int, scenario: Optional[EconomicScenario] = None, overrides: Optional[Dict[str, float]] = None) -> float:
    """Calculate carbon cost for a specific year (diesel only)."""
    if vehicle.drivetrain_type == 'BEV':
        return 0.0
    
    # Get carbon price from scenario
    carbon_price = scenario.get_carbon_price(year) if scenario else 0.0
    if carbon_price == 0:
        return 0.0
    
    # Calculate emissions (tonnes CO2e)
    annual_emissions = vehicle.litres_per_km * vehicle.annual_kms * const.DIESEL_EMISSIONS / 1000
    
    return annual_emissions * carbon_price

# Payload Penalty Calculator
class PayloadPenaltyCalculator:
    """Calculate economic penalty for reduced payload capacity based on freight rates."""
    
    def __init__(self, vehicle: VehicleModel):
        self.vehicle = vehicle
        
    def calculate_annual_payload_penalty(self) -> float:
        """
        Calculate annual cost penalty for reduced payload capacity.
        Based on freight rates per tonne-kilometre.
        Only applies to vehicles with comparison pairs.
        """
        if not self.vehicle.comparison_pair:
            return 0.0
            
        # Get the comparison vehicle
        if self.vehicle.comparison_pair not in BY_ID:
            return 0.0
            
        comparison_vehicle = BY_ID[self.vehicle.comparison_pair]
        
        # Calculate payload difference (positive means this vehicle has less payload)
        payload_difference = comparison_vehicle.payload - self.vehicle.payload
        
        # Only apply penalty if this vehicle has less payload
        if payload_difference <= 0:
            return 0.0
            
        # Get freight rate based on vehicle class
        freight_rate = const.FREIGHT_RATE_PER_TONNE_KM[self.vehicle.weight_class]
            
        # Annual cost = payload difference × freight rate × annual kilometres × utilisation factor
        # This represents the lost revenue from being unable to carry as much freight
        # Apply utilisation factor as trucks rarely run at 100% capacity
        return payload_difference * freight_rate * self.vehicle.annual_kms * const.PAYLOAD_UTILISATION_FACTOR