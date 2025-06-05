# Implementation Plan: Include Charging Labour Costs

## Issue
`ChargingTimeCostCalculator` exists in `operating.py` but is not integrated into the TCO calculation. This represents a significant operational cost for BEVs that should be included.

## Current Implementation
- `ChargingTimeCostCalculator` class exists in `operating.py` with `calculate_annual_charging_labour_cost()` method
- Not referenced in `VehicleInputs` or `calculate_tco_from_inputs`

## Required Changes

### File: `calculations/inputs.py`

1. **Add charging calculator to VehicleInputs**:
   ```python
   # In VehicleInputs dataclass, add:
   annual_charging_labour_cost: float = field(init=False)
   _charging_calculator: ChargingTimeCostCalculator = field(init=False, repr=False)
   ```

2. **Update `__post_init__` method**:
   ```python
   # After initialising other calculators:
   self._charging_calculator = ChargingTimeCostCalculator(self.vehicle)
   
   # After other operating costs:
   self.annual_charging_labour_cost = self._charging_calculator.calculate_annual_charging_labour_cost()
   ```

3. **Add year-specific method**:
   ```python
   def get_charging_labour_cost_year(self, year: int) -> float:
       """Get charging labour cost for a specific year."""
       # For now, return constant annual cost
       # Could be enhanced with scenario-based adjustments
       return self.annual_charging_labour_cost
   ```

### File: `calculations/operating.py`

1. **Import ChargingTimeCostCalculator in the `__all__` list**:
   ```python
   __all__ = [
       # ... existing exports ...
       'ChargingTimeCostCalculator',
   ]
   ```

### File: `calculations/calculations.py`

1. **Add charging labour cost to TCO calculation**:
   ```python
   # In calculate_tco_from_inputs, add new accumulator:
   total_charging_labour_cost = 0.0
   
   # In the annual costs loop:
   charging_labour_cost = vehicle_inputs.get_charging_labour_cost_year(year)
   total_charging_labour_cost += discount_to_present(charging_labour_cost, year)
   
   # In total_cost calculation, add:
   + total_charging_labour_cost
   ```

2. **Update TCOResult dataclass**:
   ```python
   # Add field to TCOResult:
   charging_labour_cost: float = 0.0
   
   # Include in the return statement with appropriate value
   ```

### File: `calculations/__init__.py`

1. **Export ChargingTimeCostCalculator**:
   ```python
   from .operating import (
       # ... existing imports ...
       ChargingTimeCostCalculator,
   )
   ```

## Benefits
- More accurate BEV operational costs
- Better comparison with diesel vehicles (which have minimal refuelling time)
- Accounts for productivity loss during charging

## Testing Considerations
- Verify BEV TCO increases appropriately
- Check that diesel vehicles show zero charging labour cost
- Validate assumptions about charging frequency and duration