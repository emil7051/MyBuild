# Duty Cycle Calculation - RESOLVED

**Date:** 2026-01-19
**Status:** Complete

## Changes Made

### 1. Navigation UX Improvements
| File | Change |
|------|--------|
| `AppShell.tsx` | "Compare" → "Configure" NavLink |
| `AppShell.tsx` | Added "Run comparison" button in header (highlighted, between Configure/Results) |
| `ResultsPage.tsx` | "Return to wizard" → "Return to Configuration" |
| `WizardPage.tsx` | Removed duplicate "Run comparison" from bottom nav |
| `ui-redesign.spec.ts` | Updated E2E test expectations |

### 2. Auto-Calculation Fix (WizardCompareStep.tsx)
**Problem:** Form↔store bidirectional sync caused debounce cascade - 15 watch events per update reset timers before calculation fired.

**Solution:** Stable memoized debounce via `lodash-es`:
```tsx
const debouncedCalculate = useMemo(
  () => debounce((p: ComparisonRequestPayload) => {
    // calculation logic
  }, 600),
  [getNextRequestId, setIsCalculating, setResults]
);

useEffect(() => {
  return () => debouncedCalculate.cancel();
}, [debouncedCalculate]);

useEffect(() => {
  if (payload) debouncedCalculate(payload);
}, [payload, debouncedCalculate]);
```

**Key improvements:**
- `lodash-es` debounce survives React re-renders (unlike setTimeout)
- Debounce increased from 350ms to 600ms for stability
- Proper cleanup on unmount

### 3. Dependencies Added
```bash
bun add lodash-es
bun add -d @types/lodash-es
```

## Architecture Summary

**Calculation triggers:**
1. **Auto-calc:** WizardCompareStep auto-calculates 600ms after form changes (debounced)
2. **Manual calc:** Header "Run comparison" button for immediate calculation

**Data flow:**
```
Form → (150ms debounce) → Store → WizardCompareStep payload → (600ms debounce) → Calculator
                                         ↑
Header button clicks here directly ──────┘
```

## Verification
- TypeScript: ✓ passes
- ESLint: ✓ passes
- Unit tests: 137/137 pass
