# Duty Cycle Form Validation Bug - Root Cause Analysis

**Date:** 2026-01-19
**Status:** FIXED - forwardRef added to Field component

## Problem
When users enter values (50, 25, 25) in the duty cycle percentage fields:
- All three fields show "Required" validation errors
- The "Total: 0%" indicator shows values aren't being summed
- Values are visibly present in the input fields

## TRUE Root Cause: Missing forwardRef in Field Component

**File:** `frontend/src/components/shared/Field.tsx`

The Field component was NOT using `React.forwardRef`, which meant the `ref` callback from React Hook Form's `register()` function was silently dropped.

### Why This Caused the Bug

1. `register('dutyCycle.urban')` returns `{ ref, name, onChange, onBlur }`
2. When spread via `{...register(...)}`, React treats `ref` as a special prop
3. Without `forwardRef`, the `ref` was silently dropped by React
4. The `<input>` never connected to RHF's internal state tracker

### Consequences Without Ref
- `onChange` still worked (captured as regular prop), so typing updated RHF state initially
- BUT `reset()` could not update DOM values (needs ref to set `input.value`)
- BUT `defaultValues` didn't populate inputs on mount (needs ref)
- After any `reset()` call, DOM showed stale values while RHF state had new values
- This caused: DOM shows 50, 25, 25 but RHF validation sees `undefined`

## The Fix (2026-01-19)

```tsx
// BEFORE (broken)
const Field = ({ label, hint, error, className, ...props }: FieldProps) => (
  <label>
    <input {...props} />   {/* ref NOT forwarded! */}
  </label>
);

// AFTER (fixed)
const Field = forwardRef<HTMLInputElement, FieldProps>(
  ({ label, hint, error, className, ...props }, ref) => (
    <label>
      <input ref={ref} {...props} />   {/* ref properly forwarded */}
    </label>
  )
);
Field.displayName = 'Field';
```

## Contributing Factors (May Still Need Attention)

### 1. setValueAs Not Called During reset()
- `setValueAs` is ONLY called during onChange/onBlur events
- NOT called during `reset()` or `defaultValues` initialization
- May cause type issues if values need transformation

### 2. Bidirectional Sync Race Condition
- Two useEffects in WizardPage.tsx create bidirectional sync
- `isUpdatingFromForm` ref attempts to prevent loops but has timing issues
- Consider switching to unidirectional data flow using `values` prop

### 3. Store Normalization During User Input
- `validateDutyCycle` in tcoStore.ts normalizes values that don't sum to 100
- This can cause feedback loops during active typing
- Consider only validating (not normalizing) user input

## Files Modified
- `frontend/src/components/shared/Field.tsx` - Added forwardRef

## Testing
- TypeScript: `bun run typecheck` passes
- Unit tests: 137 tests pass
- Manual verification needed: Enter duty cycle values and confirm validation works
