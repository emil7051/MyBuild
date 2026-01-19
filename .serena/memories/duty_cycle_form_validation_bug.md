# Duty Cycle Form Validation Bug - Root Cause Analysis

**Date:** 2026-01-19
**Status:** Fixed and verified

## Problem
When users enter values (50, 25, 25) in the duty cycle percentage fields:
- All three fields show "Required" validation errors
- The "Total: 0%" indicator shows values aren't being summed
- Values are visibly present in the input fields

## Root Cause Analysis

### Primary Issue: Watch Subscription Timing
The `formMethods.watch()` subscription in WizardPage.tsx fires during form initialization, BEFORE nested fields (`dutyCycle.urban`, etc.) are fully registered.

**Sequence:**
1. Form initializes with `defaultValues: { dutyCycle: { urban: 60, ... } }`
2. Watch subscription is created in useEffect
3. React Hook Form fires callback with current state
4. At this point, nested fields may not be registered yet
5. `values.dutyCycle` is `{ urban: undefined, regional: undefined, longHaul: undefined }`
6. Store gets updated with undefined values (the `??` fallback doesn't help because the object exists, just with undefined properties)
7. Reset effect fires, but the cycle continues

### Secondary Issue: setValueAs Type Handling
```typescript
const numberOrUndefined = (value: string) =>
  value === '' ? undefined : Number(value);
```

The function is typed for strings but receives:
- Strings from user input (onChange events)
- Numbers from `defaultValues` or `reset()` (though `setValueAs` isn't called for these)

### Contributing Factor: Nested Object Watch
`useWatch({ control, name: 'dutyCycle' })` returns undefined or partial objects when nested fields aren't registered.

## Recommended Fix

### Option A: Skip Initial Watch Callback (Recommended)
```typescript
useEffect(() => {
  let isInitialMount = true;
  const subscription = formMethods.watch((values) => {
    if (isInitialMount) {
      isInitialMount = false;
      return;
    }
    // ... rest of logic
  });
  return () => subscription.unsubscribe();
}, [formMethods, updateWizard]);
```

### Option B: Watch Specific Fields with Defaults
```typescript
const [urban, regional, longHaul] = useWatch({
  control,
  name: ['dutyCycle.urban', 'dutyCycle.regional', 'dutyCycle.longHaul'],
  defaultValue: [60, 25, 15],
});
```

### Option C: Validate Before Store Update
```typescript
const subscription = formMethods.watch((values) => {
  const dutyCycle = values.dutyCycle;
  // Skip if any value is undefined
  if (!dutyCycle || 
      dutyCycle.urban === undefined || 
      dutyCycle.regional === undefined || 
      dutyCycle.longHaul === undefined) {
    return;
  }
  // ... proceed with store update
});
```

### Additional Fix: Type-Safe setValueAs
```typescript
const numberOrUndefined = (value: unknown): number | undefined => {
  if (value === '' || value === undefined || value === null) return undefined;
  const num = Number(value);
  return Number.isNaN(num) ? undefined : num;
};
```

## Files Affected
- `frontend/src/pages/WizardPage.tsx` - Main fix location
- `frontend/src/components/wizard/WizardOperatingStep.tsx` - Secondary validation
- `frontend/src/forms/wizardForm.ts` - Zod schema (consider adding required_error)

## Testing
After fix, verify:
1. Default values (60, 25, 15) display correctly on page load
2. No validation errors appear until user clears a field
3. Total percentage updates in real-time when values change
4. Form correctly syncs with Zustand store
