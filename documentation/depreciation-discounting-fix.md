# Implementation Plan: Fix Depreciation Discounting

## Issue
Currently, depreciation is subtracted from total cost without discounting, which is financially incorrect. Depreciation represents future value losses that should be discounted to present value.

## Current Implementation
In `calculations/calculations.py`, the `calculate_tco_from_inputs` function:
```python
# Calculate depreciation over vehicle life
total_depreciation = 0.0
for year in range(1, const.VEHICLE_LIFE + 1):
    total_depreciation += vehicle_inputs.get_depreciation_year(year)
```

## Required Changes

### File: `calculations/calculations.py`

1. **Update depreciation calculation to use discounting**:
   - Replace the current depreciation calculation loop with:
   ```python
   # Calculate depreciation over vehicle life with discounting
   total_depreciation = 0.0
   for year in range(1, const.VEHICLE_LIFE + 1):
       annual_depreciation = vehicle_inputs.get_depreciation_year(year)
       total_depreciation += discount_to_present(annual_depreciation, year)
   ```

2. **Update the TCOResult to clarify reporting**:
   - The `depreciation_cost` field in TCOResult should represent the NPV of depreciation
   - Update the comment in the return statement to clarify this

## Benefits
- Financially accurate NPV calculation
- Consistent treatment of all future cash flows
- Better comparison between purchase methods

## Testing Considerations
- Verify that TCO values increase slightly (as depreciation offset is now lower)
- Ensure BEV vs diesel comparisons remain valid
- Check that financing vs outright purchase comparisons are still meaningful