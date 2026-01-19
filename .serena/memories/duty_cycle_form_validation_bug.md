# Duty Cycle Form Validation Bug - Investigation Log

**Date:** 2026-01-19
**Status:** PARTIALLY FIXED - "Required" errors persist despite 4-phase refactor

## Problem
When users enter values in the duty cycle percentage fields:
- All three fields show "Required" validation errors
- The "Total: 0%" indicator shows values aren't being summed
- Values are visibly present in the input fields
- **Errors persist even after all 4 phases of fixes**

## Fixes Implemented (Phases 1-4)

### Phase 1: Field Component forwardRef
**File:** `frontend/src/components/shared/Field.tsx`
- Added `forwardRef` to properly forward ref from RHF's `register()`

### Phase 2: Unidirectional Data Flow
**File:** `frontend/src/pages/WizardPage.tsx`
- Replaced bidirectional sync with `values` prop
- Single debounced `watch` effect for form → store sync
- Removed complex `isUpdatingFromForm` flag

### Phase 3: Explicit useWatch Defaults
**File:** `frontend/src/components/wizard/WizardOperatingStep.tsx`
- Individual `useWatch` calls with explicit `defaultValue` for each field

### Phase 4: Remove Store Normalization
**File:** `frontend/src/state/tcoStore.ts`
- `validateDutyCycle` no longer normalizes sums

## Persisting Issue Analysis

The "Required" error appearing despite visible values indicates a fundamental disconnect between:
1. What the DOM displays (values visible in inputs)
2. What Zod validation receives (undefined)

### Hypothesis: Field Registration Timing

**Key observation:** The duty cycle fields are inside `WizardOperatingStep`, which only renders when `stepIndex === 2` (step 3). 

**Potential sequence:**
1. User navigates to step 3
2. `WizardOperatingStep` starts mounting
3. Form validation runs (triggered by something)
4. At this moment, fields haven't registered yet via `register()`
5. Zod sees `undefined` for `dutyCycle.urban`, etc.
6. "Required" errors are set
7. Fields then register and display values
8. But error state persists

**Evidence supporting this:**
- "Required" is Zod's default error for undefined on a non-optional field
- The `values` prop sets form state, but field registration is separate
- RHF might validate before fields in child components register

### Hypothesis: `values` Prop Behavior

The `values` prop in React Hook Form might not work as expected with nested fields that haven't registered yet. RHF's documentation states:
> "The `values` prop will react to changes and update the form values, which is useful when your form needs to be updated by external state or server data."

But it's unclear how this interacts with:
- Fields that don't exist yet (not rendered)
- Nested object paths like `dutyCycle.urban`
- The Zod resolver trying to validate before registration

### Hypothesis: Validation Mode

Current config: `mode: 'onTouched'`

This should only validate after a field is touched. But if something calls `trigger()` explicitly or if `values` prop change triggers validation, errors would appear immediately.

## Potential Next Steps

### Option A: Delay Rendering Until Fields Ready
Wait for store hydration before rendering the form:
```tsx
const hasHydrated = useTCOStore((s) => s._hasHydrated);
if (!hasHydrated) return <Loading />;
```

### Option B: Use `defaultValues` Instead of `values`
The `values` prop is for reactive external state, but might have validation timing issues. Try `defaultValues` with manual reset:
```tsx
useForm({
  defaultValues: formValues,  // Not reactive
});
// Then manually reset when store changes
```

### Option C: Suppress Initial Validation Errors
Use `shouldUnregister: false` and check if field is registered before showing errors:
```tsx
error={formState.dirtyFields['dutyCycle.urban'] ? errors.dutyCycle?.urban?.message : undefined}
```

### Option D: Change Zod Schema to Optional with Transform
Make fields optional but transform undefined to defaults:
```tsx
urban: z.number().optional().default(60)
```

### Option E: Investigate Why Validation Runs on Mount
Add console logs to trace when validation is triggered:
- In the Zod schema (add `.refine()` with logging)
- In the form mode callbacks
- On `trigger()` calls

## Files Modified So Far
- `frontend/src/components/shared/Field.tsx` - forwardRef
- `frontend/src/pages/WizardPage.tsx` - values prop, debounced sync
- `frontend/src/components/wizard/WizardOperatingStep.tsx` - useWatch defaults
- `frontend/src/state/tcoStore.ts` - removed normalization
- `frontend/src/test/state-management.test.ts` - updated test

## Key Learnings

1. **React Hook Form's `values` prop might not prevent validation timing issues** with nested fields in conditionally rendered components.

2. **Field registration is separate from form state** - RHF can have values in state but no registered fields to display them.

3. **Zod validation can run before fields register** - especially when components mount asynchronously.

4. **The "Required" error is the smoking gun** - it specifically means Zod received `undefined`, not a type mismatch or range error.
