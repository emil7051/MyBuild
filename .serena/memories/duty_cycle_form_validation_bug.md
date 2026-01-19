# Duty Cycle Form Validation Bug - Investigation Log

**Date:** 2026-01-19
**Status:** UNDER INVESTIGATION - 4-phase refactor complete but issue persists

## Current Symptom (Clarified)

The "Required" validation error behavior:
1. **Page loads → NO errors** - Values display correctly (60, 25, 15), Total shows 100%
2. **User interacts (types/deletes) → Errors appear** - "Required" on all three fields
3. **Errors persist** - No matter what value is entered or removed, errors stay

**This is NOT a registration timing issue** - the form works initially. Something happens during user interaction that corrupts the form state.

## Fixes Already Implemented (Phases 1-4)

### Phase 1: Field Component forwardRef ✅
**File:** `frontend/src/components/shared/Field.tsx`
```tsx
const Field = forwardRef<HTMLInputElement, FieldProps>(
  ({ label, hint, error, className, ...props }, ref) => (
    <label>
      <input ref={ref} {...props} />
    </label>
  )
);
```

### Phase 2: Unidirectional Data Flow ✅
**File:** `frontend/src/pages/WizardPage.tsx`
- Replaced bidirectional sync with `values` prop for store → form
- Single debounced `watch` effect for form → store
- Removed complex `isUpdatingFromForm` flag

### Phase 3: Explicit useWatch Defaults ✅
**File:** `frontend/src/components/wizard/WizardOperatingStep.tsx`
```tsx
const urban = useWatch({ control, name: 'dutyCycle.urban', defaultValue: 60 });
const regional = useWatch({ control, name: 'dutyCycle.regional', defaultValue: 25 });
const longHaul = useWatch({ control, name: 'dutyCycle.longHaul', defaultValue: 15 });
```

### Phase 4: Remove Store Normalization ✅
**File:** `frontend/src/state/tcoStore.ts`
- `validateDutyCycle` no longer normalizes sums to 100
- Only rejects clearly invalid data (NaN, negative, >100)

## Current Hypothesis: Form-Store-Form Sync Loop Corruption

The `values` prop creates a reactive sync from store to form. Combined with the watch subscription that syncs form to store, there's a potential circular update:

```
User types → Form onChange → setValueAs transforms → Form state updates
    ↓
Watch subscription fires → syncToStore (debounced 150ms)
    ↓
Store updates wizardData.dutyCycle
    ↓
formValues useMemo recalculates (new object reference)
    ↓
values prop changes → RHF receives new values
    ↓
??? Something here may corrupt field state or trigger validation incorrectly ???
```

### Why "Required" Specifically?

"Required" is Zod's default error when a non-optional field receives `undefined`. This means after user interaction, Zod validation is receiving `undefined` for `dutyCycle.urban`, etc., even though:
- The DOM shows values
- useWatch returns values
- The store has values

The disconnect must be in RHF's internal form state that gets passed to the Zod resolver.

### Suspect: `values` Prop + `keepDirtyValues`

Current config:
```tsx
useForm({
  values: formValues,
  resetOptions: { keepDirtyValues: true },
});
```

When user types:
1. Field becomes "dirty"
2. `keepDirtyValues: true` should preserve the dirty field's value
3. But when `values` prop changes, RHF might be doing something unexpected with the parent object `dutyCycle`
4. Perhaps `dutyCycle` object gets reset while trying to preserve dirty children, causing corruption

### Suspect: useMemo Dependency on Object Reference

```tsx
const formValues = useMemo<WizardFormValues>(
  () => ({
    scenario: wizardData.scenario,
    purchaseMethod: wizardData.purchaseMethod,
    dutyCycle: wizardData.dutyCycle,  // Object reference
    overrides: wizardData.overrides ?? {},
  }),
  [wizardData.scenario, wizardData.purchaseMethod, wizardData.dutyCycle, wizardData.overrides]
);
```

`wizardData.dutyCycle` is an object. Every store update creates a new object reference, causing useMemo to recalculate, causing `values` prop to change, potentially triggering unwanted RHF behavior.

## Diagnostic Logging Added

**File:** `frontend/src/pages/WizardPage.tsx`
```tsx
const subscription = formMethods.watch((values, { name, type }) => {
  console.log('[Form Watch]', { name, type, dutyCycle: values.dutyCycle });
  // ... rest of handler
});
```

**File:** `frontend/src/components/wizard/WizardOperatingStep.tsx`
```tsx
console.log('[WizardOperatingStep]', {
  watchedValues: { urban, regional, longHaul },
  errors: errors.dutyCycle,
  formValues: control._formValues,
});
```

## Next Steps to Try

### Option A: Remove the Sync Loop Entirely
Temporarily disable form-to-store sync to confirm it's the cause:
```tsx
// Comment out the watch subscription
// If form works without errors, the loop is the problem
```

### Option B: Use defaultValues Instead of values
Don't reactively sync store to form. Let form be independent:
```tsx
useForm({
  defaultValues: initialFormValues,  // Set once
  // Remove values prop entirely
});
```

### Option C: Stabilize formValues Reference
Spread dutyCycle values individually to prevent object reference changes:
```tsx
const formValues = useMemo(() => ({
  // ...
  dutyCycle: {
    urban: wizardData.dutyCycle.urban,
    regional: wizardData.dutyCycle.regional,
    longHaul: wizardData.dutyCycle.longHaul,
  },
}), [
  wizardData.dutyCycle.urban,
  wizardData.dutyCycle.regional,
  wizardData.dutyCycle.longHaul,
  // ...
]);
```

### Option D: Check RHF's getValues() vs Validation State
Add logging to see what Zod actually receives:
```tsx
// In Zod schema, add refine with logging
.refine((val) => { console.log('Zod sees:', val); return true; })
```

## Files Modified
- `frontend/src/components/shared/Field.tsx` - forwardRef
- `frontend/src/pages/WizardPage.tsx` - values prop, debounced sync, debug logging
- `frontend/src/components/wizard/WizardOperatingStep.tsx` - useWatch defaults, debug logging
- `frontend/src/state/tcoStore.ts` - removed normalization
- `frontend/src/test/state-management.test.ts` - updated test expectations

## Key Insight

The fact that the form works on initial load but breaks after interaction strongly suggests the **form-to-store-to-form sync loop** is corrupting state. The `values` prop receiving a new object reference after each keystroke (due to store update) may be causing RHF to reset or corrupt the nested `dutyCycle` field registrations.
