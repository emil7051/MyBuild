# Implementation Plan: Payload Penalty Integration

## Overview
Payload penalty represents the economic cost of reduced cargo capacity in BEVs compared to equivalent diesel vehicles. Using actual freight rates per tonne-kilometre, we can accurately calculate the opportunity cost of carrying less freight per trip.

## Key Insight
The freight rates (17c/tonne-km for rigid, 26c/tonne-km for articulated) represent the market value of freight transport. When a BEV carries less payload than its diesel equivalent, the operator loses this revenue on every kilometre driven, requiring additional trips or vehicles to move the same total freight.

## Implementation Strategy

### 1. Add Constants
**File: `data/constants.py`**

Add the following constants:
```python
# Payload Penalty - Based on freight rates
FREIGHT_RATE_RIGID = 0.17  # $/tonne-km (market rate for rigid truck freight transport)
FREIGHT_RATE_ARTICULATED = 0.26  # $/tonne-km (market rate for articulated truck freight transport)
# Source: Industry freight rate data
# These represent the market value of freight transport capacity. When a vehicle
# has reduced payload, it generates less revenue per kilometre travelled.
```

### 2. Create Payload Penalty Calculator
**File: `calculations/operating.py`**

Add a new calculator class following the existing pattern:
```python
# Add import at top of file if not already present
import data.constants as const

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
        from data.vehicles import BY_ID
        if self.vehicle.comparison_pair not in BY_ID:
            return 0.0
            
        comparison_vehicle = BY_ID[self.vehicle.comparison_pair]
        
        # Calculate payload difference (positive means this vehicle has less payload)
        payload_difference = comparison_vehicle.payload - self.vehicle.payload
        
        # Only apply penalty if this vehicle has less payload
        if payload_difference <= 0:
            return 0.0
            
        # Get freight rate based on vehicle class
        if self.vehicle.weight_class == 'Articulated':
            freight_rate = const.FREIGHT_RATE_ARTICULATED
        else:  # Light Rigid or Medium Rigid
            freight_rate = const.FREIGHT_RATE_RIGID
            
        # Annual cost = payload difference × freight rate × annual kilometres
        # This represents the lost revenue from being unable to carry as much freight
        return payload_difference * freight_rate * self.vehicle.annual_kms
```

Don't forget to add to `__all__`:
```python
__all__ = [
    # ... existing exports ...
    'PayloadPenaltyCalculator',
]
```

### 3. Integrate into VehicleInputs
**File: `calculations/inputs.py`**

Add to the VehicleInputs dataclass:
```python
# In field definitions:
annual_payload_penalty: float = field(init=False)
_payload_calculator: PayloadPenaltyCalculator = field(init=False, repr=False)

# In __post_init__ method, after other calculators:
self._payload_calculator = PayloadPenaltyCalculator(self.vehicle)

# After other operating costs:
self.annual_payload_penalty = self._payload_calculator.calculate_annual_payload_penalty()

# Add method for year-specific costs:
def get_payload_penalty_year(self, year: int) -> float:
    """Get payload penalty for a specific year."""
    # Could be enhanced with scenario-based adjustments
    # For example, freight rates might increase with inflation
    return self.annual_payload_penalty
```

### Future Enhancement Consideration
To make this more sophisticated, you could add a utilisation factor in constants:
```python
PAYLOAD_UTILISATION_FACTOR = 0.85  # Assume trucks run at 85% payload capacity on average
```
Then multiply the penalty by this factor, as trucks rarely run at 100% capacity.

### 4. Add to TCO Calculation
**File: `calculations/calculations.py`**

Update `calculate_tco_from_inputs`:
```python
# Add accumulator with other totals:
total_payload_penalty = 0.0

# In the annual costs loop:
payload_penalty = vehicle_inputs.get_payload_penalty_year(year)
total_payload_penalty += discount_to_present(payload_penalty, year)

# In total_cost calculation, add:
+ total_payload_penalty

# Update TCOResult dataclass to include:
payload_penalty_cost: float = 0.0

# In the return statement, add:
payload_penalty_cost=total_payload_penalty,
```

### 5. Update Exports
**File: `calculations/__init__.py`**

Add to imports and exports:
```python
from .operating import (
    # ... existing imports ...
    PayloadPenaltyCalculator,
)

__all__ = [
    # ... existing exports ...
    'PayloadPenaltyCalculator',
]
```

## Calculation Example

For a BEV articulated truck with 42t payload vs diesel with 50t payload:
- Payload difference: 8 tonnes
- Freight rate: $0.26/tonne-km
- Annual distance: 84,000 km
- Annual payload penalty: 8 × 0.26 × 84,000 = $174,720/year

This represents the revenue lost from needing additional trips or vehicles to transport the same total freight volume.

## Benefits
- Captures real operational cost of reduced payload capacity using market freight rates
- Accurately reflects the economic impact: lost revenue × distance travelled
- Uses existing calculator pattern for consistency
- Automatically applies only when comparing vehicles with different payloads
- NPV calculation ensures proper time value of money treatment
- Integrates cleanly with existing TCO calculation flow

## Testing Considerations
- Verify BEVs show appropriate payload penalty based on actual freight rates
- Check that diesel vehicles typically show zero penalty
- Ensure comparison pairs are correctly matched
- Validate calculations:
  - Rigid trucks: penalty = payload_diff × 0.17 × 23,000 km/year
  - Articulated trucks: penalty = payload_diff × 0.26 × 84,000 km/year
- Consider that this penalty represents a real operational constraint that fleet operators face