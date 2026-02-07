# Agent 1: Foundation & Design System

## Context
You are one of three Opus 4.5 sub-agents working in parallel on a UI/UX redesign of the MyBuild TCO Calculator. This is a React/TypeScript app using Tailwind CSS and Recharts.

**Your focus**: Config files, CSS, and shared UI components (the visual foundation)
**Other agents (DO NOT TOUCH THEIR FILES):**
- Agent 2: Charts & data visualization
- Agent 3: Copy/content changes in wizard steps

## Brand Guidelines
- **Nova Yellow #FFC700**: Primary accent (use creatively, not as harsh backgrounds)
- **Black #000000**: Primary text
- **Neutral #F4F4F3**: Page background
- **White #FFFFFF**: Card surfaces
- **Typography**:
  - Noto Serif Condensed (H1/H2) - Regular weight only
  - Noto Serif (H3+) - Regular/Italic
  - Noto Sans (body) - All weights

## CRITICAL: Do NOT Modify
- Any files in `frontend/src/state/`
- Any files in `frontend/src/hooks/`
- Any files in `frontend/src/services/calculator/`
- `frontend/src/utils/payload.ts`
- `frontend/src/forms/wizardForm.ts` (validation logic)

---

## Your Files to Modify

### 1. frontend/tailwind.config.js
Add extended theme tokens:
```js
// Add to theme.extend
borderRadius: {
  DEFAULT: '0.5rem',  // 8px - cards, inputs
  lg: '0.75rem',      // 12px - buttons, chips
},
boxShadow: {
  'card': '0 1px 3px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.04)',
  'card-hover': '0 4px 12px rgba(0,0,0,0.1)',
  'button': '0 2px 4px rgba(255,199,0,0.3)',
},
fontFamily: {
  'heading-major': ['Noto Serif Condensed', 'serif'],
  'heading-minor': ['Noto Serif', 'serif'],
  'body': ['Noto Sans', 'sans-serif'],
},
// Add light/dark variants to brand colors
colors: {
  brand: {
    // Keep existing...
    'blue-light': '#B9C2FF',
    'blue-dark': '#3040B9',
    'aqua-light': '#C5FFF3',
    'aqua-dark': '#005A46',
    'orange-light': '#F2AE95',
    'orange-dark': '#844A34',
  }
}
```

### 2. frontend/index.html
Add Noto Serif (non-condensed) font if not already present:
```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;500;600;700&family=Noto+Serif:ital,wght@0,400;1,400&family=Noto+Serif+Condensed:wght@400&display=swap" rel="stylesheet">
```

### 3. frontend/src/index.css
Fix typography hierarchy:
```css
h1, h2 {
  font-family: 'Noto Serif Condensed', serif;
  font-weight: 400;  /* Brand guide says Regular, not bold */
  line-height: 1.1;
}
h3, h4, h5, h6 {
  font-family: 'Noto Serif', serif;
  font-weight: 400;
}
.micro-heading {
  font-family: 'Noto Sans', sans-serif;
  font-weight: 500;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
}
```

### 4. frontend/src/components/shared/Card.tsx
**Current issues**: No border-radius (square/boxy), no shadow depth, no yellow accent
**Changes:**
- Add `rounded-lg` for softer edges
- Add `shadow-card` and `hover:shadow-card-hover` for depth
- Add `border-l-4 border-brand-primary` for yellow accent on left edge
- Change padding to responsive: `p-4 sm:p-6 md:p-8`
- Change title font-weight to `font-normal` (not bold)
- Add `transition-shadow` for smooth hover

### 5. frontend/src/components/shared/Button.tsx
**Changes:**
- Add `shadow-button` to primary variant (subtle yellow glow)
- Change `rounded-md` to `rounded-lg` for consistency
- Add `active:scale-[0.98]` for tactile click feedback
- Ensure focus ring uses brand-primary color

### 6. frontend/src/components/shared/Field.tsx
**Changes:**
- Add `rounded-lg` to input (consistency)
- Use `.micro-heading` pattern for labels (uppercase, small, muted)
- Improve focus ring: `focus:ring-2 focus:ring-brand-primary/25`
- Keep error states (rose/red) as-is

### 7. frontend/src/components/shared/Select.tsx
**Changes:**
- Mirror Field.tsx styling updates
- Increase padding to `py-3.5` for better touch targets (44px min)
- Ensure consistent rounded corners and focus states

### 8. frontend/src/components/layout/AppShell.tsx
**Changes to header (keep white background, add creative yellow accents):**
- Keep `bg-white` but enhance `border-b-4 border-brand-primary`
- Nav active state: `bg-brand-primary text-black font-bold` (yellow pill)
- Nav hover: `hover:bg-brand-primary/20` (subtle yellow tint)
- Consider adding animated underline effect on hover
- Change "Wizard" nav link text to "Compare"
- Consider shortening title to "Truck Cost Calculator"

**Main container:**
- Responsive padding: `px-4 sm:px-6 py-8 md:py-12`

### 9. frontend/src/components/wizard/WizardStepper.tsx
**Changes:**
- Active step: Add `bg-brand-primary/10` background (light yellow tint)
- Add `rounded-r-lg` to step items for softer appearance
- Increase padding for better touch targets: `min-h-[48px]`
- Keep existing border-left color logic (yellow for active)

---

## Testing Checklist
After making changes:
1. Visual review in browser - does it look polished, not boxy?
2. Run `bun test` to ensure no regressions
3. Check mobile viewport (responsive padding working?)
4. Verify yellow is prominent but not overwhelming
5. Test hover/focus states on buttons and inputs
