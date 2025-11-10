# TCO Web Platform Transformation – Master Execution Plan

This single source of truth replaces the prior transition documents. It captures the vision, architecture, scope, constraints, phased delivery plan, and success criteria required to transform the Python Total Cost of Ownership (TCO) engine into the Transport Workers Union (TWU) web platform.

## 0. Executive Summary & Live Context

The program modernises the proven Python calculation engine into a React + FastAPI platform so TWU members get five-minute TCO insights while analysts continue to trust the existing datasets. This master plan now rolls up everything that previously lived in `Step_one.md` and `TCO_WEB_IMPLEMENTATION_PLAN.md`; the execution log records the detailed chronology. Refer to `Transition Docs/Old_Architecture_Documentation.md` when you need to understand how the legacy engine works under the hood.

### Live Implementation Snapshot (Updated 2025-11-10 18:45 UTC)

| Step | Scope | Status | Evidence |
| --- | --- | --- | --- |
| Step 1 | Repo structure, FastAPI bootstrap, frontend scaffold, Docker + lint/type tooling. | ✅ Complete. | Execution log items 0‑5, repo tree in §4. |
| Step 2 | Shared data + TypeScript engine foundations (scripts, SDK, parity harness). | ✅ Complete – shared generator now emits constants/policies/scenarios, the TS calculator in `shared/calculator` matches the Python engine, and the Vitest harness enforces ±1 % drift across vehicles/scenarios. | Execution log items 2, 7‑9; `scripts/generate_vehicle_catalog_ts.py`, `scripts/export_tco_snapshot.py`. |
| Step 3 | React wizard experience incl. validation, caching, telemetry, starter charts. | ✅ Complete – client now runs the shared TS calculator locally with optimistic UX, comparison highlights, and Recharts insights cached for offline review. | Execution log items 3, 5, 6, 10. |
| Step 4 | Session persistence + analytics layer (PostgreSQL/Redis, session APIs, telemetry summaries). | 🟡 In progress – SQLAlchemy models, Redis caching, `/sessions` + `/analytics/summary` endpoints, and frontend autosave/insights are live; CSV/export automation and operator profile UX remain. | Execution log items 11‑13; `backend/app/services/sessions.py`; `frontend/src/components/results/AnalyticsSummaryCard.tsx`. |

### Immediate Priorities
- Finish the export/query surface: add CSV/HTML regeneration + archival endpoints that reuse the new session store so analysts can ingest runs without the React client.
- Expose operator profile + feedback capture inside the wizard/results flow and persist the structured metadata through the `/sessions` API to hit the 30 % opt-in target.
- Codify the runbooks (docker compose/.env scaffolding, CI gates, parity workflows) in this plan + README and thread the analytics parity checks into CI so future phases start from a reproducible, measurable baseline.

---

## 1. Vision, Value Proposition & Stakeholders

- **Purpose**: Give truck operators and TWU advocates instant clarity on the economics of switching from diesel to battery-electric vehicles (BEV) while collecting anonymized operating data for policy influence.
- **Primary Users**: Owner-drivers and fleet managers running heavy commercial trucks across light/medium/articulated weight classes.
- **Secondary Users**: TWU policy team, analysts, and campaign staff who ingest aggregated outputs for advocacy, funding proposals, and negotiations.
- **Value Proposition**:
  - Personalized 15-year TCO comparisons (diesel vs BEV vs custom options) in under five minutes.
  - Scenario exploration (baseline, technology breakthrough, oil crisis) and sensitivity levers.
  - Evidence capture: voluntarily shared operating profiles become an anonymized dataset for TWU.
- **Guiding Principles**: Progressive disclosure, smart defaults, accuracy before aesthetics, mobile-first responsiveness, accessibility (WCAG 2.1 AA), privacy-by-default.

---

## 2. Product Objectives & Success Metrics

| Category | Target |
| --- | --- |
| **User Impact** | ≥80 % of test operators complete the wizard unaided; average completion time < 5 min. |
| **Business Outcomes** | ≥67 % of comparisons show BEV advantage (validating TWU narrative); data export supports quarterly policy briefs. |
| **Calculation Accuracy** | React/TypeScript outputs match the Python engine within ±1 % across all 16 vehicles × 3 scenarios; regression suite blocks drift >0.5 %. |
| **Performance** | Initial load < 3 s, wizard navigation < 100 ms, single calculation < 500 ms, memory footprint < 50 MB, PWA offline-ready. |
| **Quality Gates** | TypeScript strict mode clean, ESLint/Prettier zero warnings, ≥80 % calculator test coverage, Docker compose up, CI (lint/type/tests) green on every PR. |
| **Data & Analytics** | Anonymous session logging on 100 % of calculations, opt-in operator metadata capture rate ≥30 %, analytics dashboard refresh < 5 s. |
| **Security & Compliance** | OWASP top 10 mitigations verified, secrets managed via environment files, rate limiting + input sanitization enforced, Sentry monitoring live. |

---

## 3. Core Product Capabilities

### 3.1 Operator Experience
- **Wizard Flow** (three core steps, expandable later):
  1. **Vehicle Selection** – Choose current truck, prospective BEV/diesel comparators, or define a custom vehicle using payload, range, class, drivetrain, while prefetching `/vehicles/{id}` metadata (payload, range, MSRP, storage) so spec cards and comparison tables stay in sync even when offline.
  2. **Operating Profile** – Annual distance, duty-cycle mix (urban/regional/long haul), daily pattern (return to base vs multi-day), working days, with React Hook Form + Zod enforcing the same ranges as `VehicleInputs` (e.g., 5 000–250 000 annual kms, 0.5–1.5× multipliers) and surfacing inline validation messages. Scenario presets display curated descriptions so operators understand the underlying diesel/electricity trajectories before running calculations.
  3. **Cost Inputs** – Fuel/electricity prices, charging mix, maintenance, financing terms; collapsible “advanced” options keep UI clean.
- **Results Dashboard**:
  - Cost-per-km summary cards (current diesel vs electric option vs latest diesel).
  - Payback timeline and cumulative cashflow waterfall.
  - Sensitivity sliders for fuel price, electricity price, maintenance cost, annual kms, residual value.
  - Download/Share and “Save for later” (localStorage + optional email).
- **Experience Enhancements**: Zustand-powered persistence, autosave, tooltips, inline education, loading skeletons, optimistic calculations using client-side engine, cached vehicle spec summaries (payload, range, batteries, registration, maintenance) rendered via the wizard’s selection summary panel, toast-based feedback for calculation errors/success, routing guards that bounce users back to the wizard if they hit results without a completed run, and an offline-ready vehicle dataset generated directly from the Python source (`scripts/generate_vehicle_catalog_ts.py` → `shared/data/vehicleCatalog.ts`) so the UI never blocks on spec fetches.

### 3.2 Calculation & Scenario Engine
- **Vehicle Dataset**: 16 predefined vehicles (8 BEV, 8 diesel) covering light, medium, and articulated classes with immutable comparison pairs (e.g., BEV001 Jac N75 ↔ DSL001 Hino 300).
- **Financial Invariants**: 15-year vehicle life, 5-year financing with 20 % down payment, 5 % discount rate, 6 % interest rate, battery replacement in year 8, 255 working days/year.
- **Cost Components (14 total)**: Purchase (MSRP + stamp duty – rebates + financing), fuel or electricity, maintenance (with age-based multipliers), insurance, registration, battery replacement, carbon, charging labor, payload penalty, residual value (discounted).
- **Scenario Mechanism**: Baseline, Technology Breakthrough, Oil Crisis trajectories for diesel price, electricity price, battery cost, efficiency improvements, maintenance multipliers. Lists auto-extend to 15 years; overrides support Monte Carlo/sensitivity hooks (fuel price variation, annual kms overrides, etc.).
- **Testing Strategy**: Parity harness running the Python engine vs TypeScript port for every vehicle/scenario, Jest unit tests for each calculator, snapshot tests for results objects, Playwright smoke tests for wizard flows.

### 3.3 Data, Analytics & Admin
- **Anonymous Session Logging**: Input sets, scenario choices, calculation outputs stored in PostgreSQL; Redis caches active sessions for speed and throttling.
- **Optional Metadata Capture**: Operator type, fleet size, industry segment, contact for follow-up; gated behind incentive messaging.
- **Internal Analytics Dashboard**: Real-time counters (active sessions, daily calculations, data points collected), top comparisons, aggregated findings (BEV win rate, average payback).
- **Exports & Reporting**: CSV/JSON exports for TWU analysts, automated weekly digest, PDF report generation (post-MVP).

### 3.4 Analytical Extensions & Research Workbench
- **Reference Analytics Suite (`analysis/`)**: `analysis/analysis.py` already produces `PaybackAnalysis`, `PolicyImpactAnalysis`, and `FleetTransitionAnalysis` objects that policy teams rely on; the web platform must expose these calculations (or their summaries) so we do not regress on the insights presently generated by the Python notebooks/scripts.
- **Scenario Research Scripts**: `analysis/generate_tco_analysis.py` and `analysis/purchase_year_analysis.py` generate longitudinal CSV/JSON exports by looping over purchase years and scenarios. The new backend should provide equivalent endpoints or scheduled jobs so these reports can be reproduced without shell access.
- **Uncertainty Tooling (`calculations/simulation.py`)**: `MonteCarloSimulation` and `SensitivityAnalysis` classes already support overrides such as `fuel_price_variation`, `annual_kms_variation`, and `battery_life_variation`. The transformation plan must keep these override keys intact so that the TypeScript engine, FastAPI endpoints, and UX sliders remain aligned with the existing distributions.
- **Output Packaging (`output/charts.py`, `output/generate_html_report.py`)**: Plotly HTML, CSV exports, and the `main.py → output/charts` pipeline are authoritative artefacts that TWU uses today. Phase 4 deliverables need to guarantee that the same datasets and visuals can be produced (automatically or via “export” actions) from the new stack.
- **Data Guardrails**: Tests in `tests/test_comprehensive.py` currently cover financing, depreciation, fuel/maintenance, charging labour, policy levers, and validator hooks. Any new feature should reuse these fixtures (e.g., BY_ID vehicle map, EconomicScenario constants) to avoid accidental drift between research tooling and the product experience.

---

## 4. System Architecture & Technology Stack

```
┌──────────────────────── Frontend (React/Vite) ─────────────────────────┐
│  Wizard UI  │  Calculator Engine (TypeScript) │  Visualization Layer   │
└─────────────┴─────────────────────────────────┴────────────────────────┘
                               │
                        HTTPS / REST
                               │
┌────────────────────── FastAPI Backend ───────────────────────┐
│  /api/vehicles  /api/calculate/tco  /api/calculate/comparison │
│  /api/sessions  /api/analytics                               │
└──────────────────────┬────────────────────────┬──────────────┘
                       │                        │
          ┌────────────▼────────────┐  ┌────────▼────────┐
          │ PostgreSQL (user data,  │  │ Redis (sessions │
          │ inputs, results, audit) │  │ & caching)      │
          └─────────────────────────┘  └─────────────────┘
```

### Current Python Assets & Migration Targets
- **`calculations/` modules**: `financial.py`, `operating.py`, `inputs.py`, `simulation.py`, and `calculations.py` already encode financing rules, maintenance curves, payload penalties, Monte Carlo hooks, and the `calculate_tco_from_inputs` contract. These are the canonical behaviours the TypeScript “shared SDK” and FastAPI endpoints must reproduce.
- **`data/` layer**: `constants.py`, `policies.py`, `scenarios.py`, and `vehicles.py` (plus `vehicle_models.csv`) define every invariant the platform depends on. Treat the Python dataclasses (e.g., `VehicleModel`, `EconomicScenario`, `PolicyIncentive`) as the schema source when generating TS/Pydantic types or seed data in PostgreSQL.
- **`analysis/` + `output/`**: Advanced analytics (payback, fleet transition, purchase-year deltas) and the Plotly/CSV exporters (`output/charts.py`, `output/generate_html_report.py`, `main.py`) underpin TWU reporting today. The new platform needs feature flags or batch jobs so stakeholders can regenerate these artefacts without hacking scripts.
- **Testing & QA**: `tests/test_comprehensive.py` is an exhaustive suite covering finance, operating, scenario, and (referenced) validation logic. Use it as the regression net when refactoring Python services and as the acceptance dataset for the TS parity harness.
- **Tooling Reality Check**: `frontend/src` currently contains empty scaffolding directories—Phase 2 must include bootstrapping (Vite/React, ESLint/Prettier, Vitest, Playwright) before any wizard work. Conversely, the Python side already has `requirements.txt`, so DevOps must preserve virtualenv workflows alongside Node workspaces.
- **Documentation Sources**: `TCO - Tech Specification 150725.md` documents the same modules listed above; this master plan should remain in lock-step with that spec so engineers are never reconciling conflicting requirements.

### Technology Choices
- **Frontend**: React 18 + TypeScript, Vite bundler, TailwindCSS + shadcn/ui, React Router, Zustand, React Hook Form + Zod, TanStack Query, Axios, Recharts/Plotly, Vitest/Jest + Testing Library, Playwright.
- **Shared**: `shared/` workspace for TypeScript types, constants, calculator engine; consumed by frontend and (optionally) backend via ts-node or transpiled package.
- **Backend**: FastAPI (Python 3.11), Pydantic models aligned with shared types, SQLAlchemy ORM, asyncpg, Redis for session/cache, Uvicorn/Gunicorn, pytest for API tests.
- **Infrastructure**: Docker/Docker Compose for local parity, GitHub Actions CI (frontend + backend jobs), Nginx reverse proxy, Let’s Encrypt SSL, Sentry for monitoring, AWS/Azure/DigitalOcean for hosting.
- **API Contracts**:
  - `GET /api/vehicles` – list vehicles with filters/search.
  - `POST /api/vehicles/custom` – validate & persist custom vehicle.
  - `POST /api/calculate/tco` – returns `TCOResult` (14 components + metadata).
  - `POST /api/calculate/comparison` – multi-vehicle comparisons.
  - `POST /api/sessions` – persist wizard progress for resume links.
  - `GET /api/analytics/summary` – aggregated KPIs for dashboard.

### Repository Layout & Bootstrap Runbook
```
MyBuild/
├── frontend/           # React/Vite app (src, public, config, Dockerfile)
├── backend/            # FastAPI service (app/, requirements, Dockerfile)
├── shared/             # TypeScript SDK (types, generated vehicle catalog)
├── scripts/            # Generators such as generate_vehicle_catalog_ts.py
├── docker-compose.yml  # Frontend + backend + Postgres + Redis
├── .github/workflows/ci.yml
└── Transition Docs/    # Master plan, execution log, old architecture doc
```
- Align new modules with this tree; `frontend/src` and `backend/app` already contain scaffolds, so Phase 0 mainly hardens tooling instead of inventing structure.
- The shared directory is the contract source for both React and FastAPI; keep generators in `scripts/` and rerun them in CI when Python data changes.

### Tooling & Dependency Baseline
- **Frontend runtime dependencies**: React 18.2, React Router 6.20, Zustand 4.4, React Hook Form 7.48, Zod 3.22, TanStack Query 5.12, Axios 1.6, Recharts 2.10, clsx/tailwind-merge, toast + telemetry helpers. Dev tooling: Vite 5, TypeScript 5.3, ESLint 8.55 + `@typescript-eslint`, Prettier 3, Vitest + Testing Library, Playwright smoke tests.
- **Backend requirements**: FastAPI 0.108, Uvicorn 0.25, Pydantic 2.5, SQLAlchemy 2.0, asyncpg, Redis 5, python-dotenv, numpy/pandas/scipy for parity with the engine. Keep the Python virtualenv lightweight; heavy analytics still run via the existing `analysis/` scripts outside the FastAPI container.
- **Shared SDK**: `shared/types/tco.types.ts` defines vehicles, operating profiles, overrides, and results; the TS calculator lives alongside the generated catalog so the wizard, FastAPI, and parity harness consume the same shapes.

### Environment & CI Expectations
- **Docker Compose**: Services for frontend (`VITE_API_URL`), backend (`DATABASE_URL`, `REDIS_URL`), Postgres 15, Redis 7. Bind mounts keep developer workflows hot-reload friendly; Postgres data uses a named volume.
- **GitHub Actions**: `frontend-tests` job (Node 20, `npm ci`, lint, type-check, unit tests). `backend-tests` job (Python 3.11, pip install, pytest). Extend later with Playwright + API integration stages but keep the two-lane pipeline until parity work stabilises.
- **Local verification**: `npm run dev`, `uvicorn backend.app.main:app --reload`, `docker compose up`, and `pytest`/`npm run test` should all succeed before shipping.

### Step 1 Success Criteria (Completed)
- Monorepo folder structure + scaffolds created and committed.
- Frontend runs at `http://localhost:3000` (Vite dev server) without runtime errors.
- Backend health check available at `http://localhost:8000/api/health`.
- `docker-compose up` brings up frontend, backend, Postgres, and Redis successfully.
- GitHub Actions pipeline (frontend/backend jobs) green.
- Frontend can call the backend health endpoint (proves proxy + CORS baselines).

### Step 4 Snapshot (In Progress)
- Introduced SQLAlchemy models (`SessionRecord`, `UserInputRecord`, `CalculationResultRecord`, `OperatorProfileRecord`, `FeedbackRecord`) plus async engine bootstrap so FastAPI can persist sessions to Postgres by default (SQLite fallback for local tests).
- Added Redis-backed caching and `/api/v1/sessions` + `/api/v1/analytics/summary` endpoints powered by `SessionService`, enabling autosave, resume, and aggregated KPIs (BEV win rate, payback heuristics, top vehicles) straight from the session store.
- React now persists wizard runs via those APIs (Zustand stores the session ID) and surfaces the new analytics summary on the results dashboard; the remaining Step 4 work tracks CSV/export endpoints, operator-profile capture, and CI wiring.

---

## 5. User Journey & UX Principles

```
Landing → Vehicle Selection → Operating Profile → Cost Inputs → Results → (Optional) Data Share & Follow-up
```

- **Landing Page**: Explain value proposition, trust badges, start button.
- **Vehicle Selection**: Dropdown for make/model, quick class buttons (Light Rigid <8t, Medium 8‑16t, Articulated >16t), toggle for electric equivalent vs latest diesel vs custom specification. Show pairings to set expectations.
- **Operating Profile**: Annual distance slider (validated 1 000–500 000 km), route profile sliders summing to 100 %, daily pattern radio buttons, working days per year. Provide contextual hints (e.g., “Most medium rigid fleets run 23 000 km/year”).
- **Cost Inputs**: Primary inputs (diesel price, electricity price) plus collapsible advanced settings (charging mix by location, maintenance rate, finance rate). Inline visuals show defaults vs user adjustments.
- **Results Dashboard**: Summary cards, charts (waterfall, payback), textual insights (“BEV cheaper after 3.8 years”), sensitivity controls, download/share buttons.
- **Data Share Step**: Optional form for operator type, fleet size, contact email, consent to follow-up; reassure about anonymity.
- **UX Tenets**: Progressive disclosure, smart defaults, immediate feedback, error states that explain how to fix, responsive layouts, keyboard navigation, ARIA tagging.

### Component Implementation Strategy
- **Phase 1 – Core Calculator (Weeks 1‑3)**: Port the TypeScript TCO engine (`TCOCalculator`) using the shared types, wire the generated vehicle catalog, and stand up the multi-step wizard with validation, autosave, and localStorage backup. Deliver Vitest coverage plus parity snapshots vs Python.
- **Phase 2 – Advanced UX (Weeks 4‑5)**: Layer interactive visualisations (comparison cards, waterfall, payback timeline), scenario manager (baseline/technology/oil crisis/custom), and advanced inputs (charging mix calculator, route builder, maintenance overrides). Introduce scenario comparison mode and the first tranche of sensitivity sliders.
- **Phase 3 – Polish & Optimisation (Week 6)**: Ship PWA/offline mode, push notifications for saved comparisons, mobile-specific performance tweaks (code splitting, lazy charts, optimised assets), and tighten accessibility + analytics hooks before launch.

---

## 6. Functional Scope & Definition of Done

### 6.1 Functional Requirements
- Working prototype accepts all specified inputs for diesel and BEV options.
- 5‑15 year projections displayed; cost per km, annual cost, cumulative cost.
- Fuel savings, maintenance differentials, upfront cost gap, financing impacts surfaced.
- Scenario selection (baseline/tech/oil crisis) and custom overrides.
- Sensitivity sliders for core economic levers.
- Results downloadable (CSV/PDF roadmap) and sharable link.
- Wizard completion time < 5 minutes with clear progress indicator.

### 6.2 Data Collection
- Anonymous session tracking with UUID linkage.
- Storage of user inputs + calculation results for analytics.
- Optional operator profile capture with consent.
- Export capability for TWU analysts (CSV/JSON).

### 6.3 Technical Requirements
- Web-based, no install; mobile-friendly responsive layouts.
- Accessibility: WCAG 2.1 AA compliance, ARIA labels, keyboard navigation.
- Load time < 3 s on 4G, asset budgets enforced.
- Works on Chrome, Firefox, Safari, Edge (latest two versions).
- Docker containers for frontend, backend, DB; staging/prod parity.

### 6.4 Analytics & Stakeholder Approval
- Analytics dashboard presenting active sessions, calculation counts, BEV win rate, payback averages.
- Funding gap quantification, cohort barrier identification, geographic variation tracking (using captured data).
- TWU leadership sign-off, operator usability testing (≥20 participants), security audit, performance benchmarks, documentation complete.

### 6.5 Engine, Data & Reporting Deliverables
- **Parity Artifacts**: The React/TS calculator must emit the same shape as `calculations.calculations.TCOResult` (14 cost components + metadata) so FastAPI can persist results and legacy scripts (`output/charts.py`, `analysis/analysis.py`) can consume them without translation glue.
- **Scenario/Policy Surface Area**: Ensure the UI can toggle every override that `EconomicScenario`, `POLICIES`, and `MonteCarloSimulation` support today (diesel/electricity price multipliers, maintenance multipliers, policy toggles, annual kms overrides, residual value scalars). Anything not exposed in the MVP must still be reachable via backend APIs so analysts are not blocked.
- **Data Validation Hooks**: `scripts/validation.py` now ships the `DataValidator` consumed by `tests/test_comprehensive.py`; keep those rules mirrored in PostgreSQL constraints + FastAPI validation so our “single source of truth” continues to block malformed datasets before they reach analysts.
- **Export Guarantees**: Maintain the current `generate_all_charts()`/`generate_all_csv()` capabilities. Whether through scheduled FastAPI jobs, a CLI wrapper around `main.py`, or a “Download TWU Pack” action, analysts need button-click access to the exact CSV/Plotly formats they use today.
- **Documentation & Runbooks**: Converge `README.md`, this master plan, and `TCO - Tech Specification 150725.md` so developers know where to update constants, vehicles, policies, and analytics outputs. Every new data table or endpoint should call out its upstream/downstream dependencies.

---

## 7. Constraints, Invariants & Business Rules

### 7.1 Financial & Operational Assumptions
1. Vehicle life fixed at 15 years.
2. Battery replacement occurs in year 8 for BEVs with capacity >0.
3. Financing term 5 years, 20 % down payment, monthly compounding.
4. Discount rate 5 % annually; interest rate 6 %.
5. Working days fixed at 255/year (≈70 % utilization).

### 7.2 Calculation Rules
1. BEV charging labor cost triggers only when daily driving exceeds 60 % of usable range.
2. Payload penalties apply only when comparison pair defined.
3. Diesel vehicles incur carbon costs; BEVs do not.
4. Battery replacement costs apply only to BEVs with non-zero battery capacity.
5. All future cashflows discounted using 5 % annual rate.
6. Scenario trajectories auto-extend to 15 years; empty lists default to multiplier 1.0.

### 7.3 Data Validation
- Vehicle specs sourced from canonical CSV/JSON; validated on load.
- Scenario lists validated for length and numeric values.
- Constants centralized; any change goes through review with parity rerun.

### 7.4 Security & Privacy
- Anonymous by default; PII optional and stored with consent flags.
- Input sanitization, rate limiting, CSRF protections, HTTPS everywhere.
- Error tracking via Sentry; logs scrubbed of PII.

---

## 8. Phase Plan Overview

| Phase | Timeline | Goal | Key Deliverable |
| --- | --- | --- | --- |
| **0. Alignment & Tooling** | Week 0 | Freeze scope, create repo/workspace, confirm CI + Docker + env parity. | Mono-repo skeleton running locally and in CI. |
| **1. Shared Data & TS Engine** | Week 1 | Port constants, vehicles, scenarios, calculators with parity tests. | Shared TypeScript SDK validated vs Python. |
| **2. Wizard MVP & Client Experience** | Week 2 | Build 3-step wizard, client-side calculations, persistence, responsive UI. | MVP meeting Step 3 success criteria. |
| **3. Backend, Persistence & Beta** | Weeks 3‑4 | FastAPI services, PostgreSQL/Redis integration, advanced inputs, visualizations, staging deploy. | Beta-ready platform for TWU review. |
| **4. Analytics, Polish & Launch** | Weeks 5‑6 | Data capture, analytics dashboard, performance/security polish, documentation, launch prep. | Production deployment satisfying definition-of-done. |

---

## 9. Detailed Phase Playbooks

### Phase 0 – Alignment & Tooling (Week 0)
- Confirm architecture, scope boundaries, and stakeholder success measures, then map every requirement back to `TCO - Tech Specification 150725.md` and the sections of this master plan so we never maintain parallel specs.
- Apply the Step 1 runbook: instantiate the monorepo structure (`frontend/`, `backend/`, `shared/`, `scripts/`, `docker-compose.yml`, `.github/workflows/ci.yml`, `.env.example`), drop in the Vite + FastAPI scaffolds, and wire the shared workspace that will host the TS SDK.
- Bootstrap tooling per §4 (React/Tailwind/Zod stack, FastAPI + SQLAlchemy dependencies, lint/type/test scripts) so `npm run dev`, `npm run lint`, `npm run typecheck`, `pytest`, and `uvicorn` are all defined before feature work.
- Run baseline commands on the legacy Python code (`pip install -r requirements.txt`, `pytest -q`, `python main.py`, `analysis/generate_tco_analysis.py`) to surface any missing modules (e.g., `scripts/validation`) and log remediation tasks.
- Exit Criteria: local frontend on `http://localhost:3000`, backend `/api/health` responding, Docker compose (frontend/backend/Postgres/Redis) up, GitHub Actions pipeline green, and this document cross-referencing all canonical data sources.

### Phase 1 – Shared Data & TS Engine (Week 1)
- Extend `shared/types/tco.types.ts` to capture every entity defined in Step 2 (vehicles, operating profiles, charging mix, financing, annual cost breakdown, comparison/savings analysis) and regenerate `shared/data/vehicleCatalog.ts` via `scripts/generate_vehicle_catalog_ts.py` whenever Python data changes.
- Port calculators in dependency order: TS utilities → financial pieces (`calculateStampDuty`, `calculateRebate`, financing helpers) → operating costs (fuel, maintenance, insurance, charging labour, payload penalties, battery replacement) → `VehicleInputs` equivalent → `calculateTcoFromInputs`, keeping names aligned with `calculations/calculations.py`.
- Build the Jest/Vitest parity harness referenced in Step 2 (`frontend/src/services/calculator/__tests__/TCOEngine.test.ts`) so every vehicle × scenario × override combination shells out to the Python engine (or reads golden fixtures) and enforces ±1 % tolerance; include Monte Carlo override coverage for fuel/electricity price multipliers, annual kms, residual multipliers, and battery life scalars.
- Deliverable: shared SDK published from `shared/`, automated scripts + docs explaining how to keep TS + Python in sync, parity test reports attached to CI, and a remediation plan for the missing `scripts.validation.DataValidator`.
- **Status — 2025-11-10**: `scripts/generate_vehicle_catalog_ts.py` now emits the vehicle catalog, constants, scenarios, and policy payloads consumed by `shared/calculator`, the TypeScript TCO engine mirrors `calculations/calculations.py` field-for-field, and `frontend/src/services/calculator/__tests__/TCOEngine.test.ts` runs against live Python outputs from `scripts/export_tco_snapshot.py` to enforce the ±1 % tolerance per vehicle, scenario, purchase method, and override combination.

### Phase 2 – Wizard MVP & Client Experience (Week 2)
- Implement wizard components (`WizardContainer`, `VehicleSelection`, `OperatingProfile`, `CostInputs`, `WizardProgress`) on top of a fresh Vite/React codebase that already consumes the shared SDK directly from the monorepo (no mocked JSON copies).
- Wire React Hook Form + Zod schemas so that every constraint baked into `VehicleInputs` is reflected in the UI: route profile sums to 100 %, diesel/electricity price bounds line up with the override multipliers, custom vehicles reuse the `VehicleModel` shape exported from the Python layer.
- Integrate the TS calculator for instant results and render miniature versions of today’s Plotly assets (cost-per-km, waterfall, payback callouts) so stakeholders can compare against the HTML exported from `output/charts.py`.
- Ensure persistence (Zustand + localStorage) plus telemetry events that mirror what the backend will store (inputs, overrides, scenario choice, timestamp). Include ARIA-compliant components, keyboard flows, loading/error states, and Playwright smoke tests for the “baseline diesel vs BEV” happy path.
- Exit Criteria: navigation + validation solid, parity snapshots captured for at least one vehicle pair (Jac N75 vs Hino 300), data persists, mobile-ready, calculations trigger with user feedback, meets Step 3 checklist.
- **Status — 2025-11-10**: Wizard steps now rely on React Hook Form + Zod for scenario/override validation, vehicle specs hydrate instantly from the generated shared catalog (`shared/data/vehicleCatalog.ts`) rather than repeated `/api/v1/vehicles/{id}` calls, a Selected Vehicles Summary card surfaces the cached payload/range/MSRP data alongside persisted Zustand state and comparison results, and the operating profile step captures duty-cycle splits + scenario presets while toast notifications + routing guards handle failed or premature navigation to the results view. The calculation path now executes locally through `shared/calculator` (with FastAPI fallback) and the results experience layers in comparison highlights plus Recharts cost-per-km and cost-breakdown charts so demos show live insights without waiting on Python responses.

### Phase 3 – Backend, Persistence & Beta Hardening (Weeks 3‑4)
- Build FastAPI routes with Pydantic schemas generated from the shared SDK so that `/api/calculate/tco` literally calls the existing Python `calculate_tco_from_inputs` (until the TS port is production-ready) and `/api/calculate/comparison` reuses `compare_vehicle_pairs`, `calculate_breakeven_analysis`, and `PaybackAnalysis`.
- Design PostgreSQL schema (tables: `sessions`, `user_inputs`, `calculation_results`, `operator_profiles`, `feedback`, plus materialized view `tco_statistics`) and Redis caching strategy, seeding relational data from `data/vehicle_models.csv`, `data/constants.py`, and policy defaults to avoid drift. ✅ Schema + caching are now live via `backend/app/db/models.py` and `SessionService`; materialised views/exports remain.
- Add advanced inputs (charging mix calculator, route builder, maintenance customizer) alongside scenario management UI that exposes every override already supported by `EconomicScenario` and `POLICIES`.
- Implement interactive visualizations (cost comparison cards, payback chart, waterfall, tornado/sensitivity) using a shared config that reproduces the structure in `output/visualisations.py`.
- Containerize services, deploy to staging (Docker + Nginx + SSL), switch frontend to server-backed calculations for persistent logging, and expose an authenticated endpoint that regenerates the same CSV/HTML artefacts as `main.py`.
- Exit Criteria: vehicle DB complete, advanced inputs & charts live, API + DB stable, end-to-end parity tests green, staging environment ready for TWU beta with reproducible data exports.

### Phase 4 – Analytics, Polish & Launch (Weeks 5‑6)
- Implement anonymous data collection pipeline, exports, optional email capture, feedback loop, analytics dashboard, and verify analytics queries reproduce the same KPIs calculated today via `analysis/analysis.py` (payback years, BEV win rate, emission deltas).
- Add PWA capabilities, code splitting, lazy loading, skeleton states, and offline caching for the wizard plus “export pack” downloads so a field operator can still access saved comparisons without connectivity.
- Run performance profiling, accessibility audit, security review, load tests; finalize TWU branding and documentation (runbook, API docs, user guide) and explicitly document how to run `python main.py`, `analysis/generate_tco_analysis.py`, and the new FastAPI jobs side-by-side.
- Execute launch checklist (DNS, SSL, backups, monitoring alerts, rollback plan) and provide TWU analysts with staged CSV/HTML outputs that match the historical ones byte-for-byte (or document deltas).
- Exit Criteria: definition-of-done satisfied, TWU leadership approval, production deployment complete, reproducible research exports validated.

### Timeline Detail (Weeks 1‑6)

| Week | Focus | Milestones |
| --- | --- | --- |
| 1‑2 | Foundation | Day 1‑2 project setup + CI; Day 3‑5 TS engine port; Day 6‑8 wizard skeleton; Day 9‑10 initial API hooks. |
| 3‑4 | Core Dev | Day 11‑13 complete UI components; Day 14‑16 visualisations; Day 17‑19 backend endpoints + DB; Day 20 integration test. |
| 5 | Data & Analytics | Day 21‑22 schema hardening; Day 23‑24 data collection + analytics dashboard; Day 25 export tooling. |
| 6 | Launch Prep | Day 26‑27 performance/security polish; Day 28 audit; Day 29 documentation; Day 30 production deploy + monitoring handover. |

---

## 10. Cross-Cutting Workstreams

| Track | Responsibilities |
| --- | --- |
| **Calculation Integrity** | Maintain dual-run harness, nightly regression suite per scenario, guardrail alerts when drift >0.5 %, manual review of high-value vehicle pairs. |
| **Quality & Testing** | Vitest/Testing Library coverage for components, Jest parity harness, Playwright end-to-end wizard flow, pytest + FastAPI integration tests, Locust load tests (1 000 concurrent users), Lighthouse + WebPageTest performance gates, user testing rounds (alpha/beta/UAT) as outlined in §5. |
| **UX & Accessibility** | Usability testing every phase, ARIA + keyboard support, Lighthouse & axe scans, copy review for tooltips/help text. |
| **DevOps & Monitoring** | CI/CD automation, artifact versioning, container security scans, Sentry & structured logging, environment parity, backup/restore drills. |
| **Documentation & Knowledge Sharing** | Keep this master plan and README updated, maintain API docs/OpenAPI, publish runbooks for deployment/support. |

---

## 11. Risk Register & Mitigations

| Risk | Impact | Mitigation | Owner |
| --- | --- | --- | --- |
| Calculation divergence between Python and TS | Misleading business insights & loss of trust | Automated parity tests per commit, manual spot checks, alerting on >0.5 % drift. | Calculation lead |
| Mobile performance regressions | Users abandon flow in field conditions | Early profiling, Web Workers or WebAssembly for heavy math, bundle splitting, asset budgets. | Frontend lead |
| Data loss during wizard flow | Incomplete datasets, frustration | Autosave (Zustand + localStorage), Redis session backups, offline PWA safeguards. | Full-stack lead |
| Browser incompatibility | Support burden | Polyfills, Playwright cross-browser CI, progressive enhancement. | Frontend QA |
| Security/privacy breach | Compliance failure | Input sanitization, rate limiting, dependency scanning, security review before launch, Sentry monitoring. | Backend lead |
| Scope creep | Delays & missed deadlines | Phase gates with readiness reviews, clear backlog triage, stakeholder sign-off for changes. | Project manager |
| Missing validation module (`scripts.validation.DataValidator`) | Undetected data issues + failing parity tests | ✅ `scripts/validation.py` now implements the validator consumed by `tests/test_comprehensive.py`; keep the same constraints mirrored in FastAPI/Pydantic + PostgreSQL so CI catches regressions before analysts do. | Tech lead |

---

## 12. Execution Cadence & Governance

- **Daily**: Stand-up with workstream leads; track blockers on Kanban/roadmap.
- **Twice Weekly**: Calculation parity + UX review.
- **Weekly**: Demo/Show-and-tell with TWU stakeholders; update burndown.
- **Phase Gates**: Formal readiness review using exit criteria before progressing.
- **Metrics Dashboard**: Display build health (CI status), accuracy drift, performance metrics, session counts, BEV win-rate, average payback.
- **Change Control**: Any adjustment to assumptions, calculators, or architecture must be recorded in this document and acknowledged by project lead + TWU contact.

---

## 13. Key Data Tables & Constants (Authoritative Values)

### 13.1 Vehicle Classes & Sample Pairs
- **Light Rigid (<8 t)**: BEV001 Jac N75 ↔ DSL001 Hino 300; BEV002 Hyundai Mighty Electric ↔ DSL002 Hyundai Mighty; BEV003 Jac N90 ↔ DSL003 Hino 500.
- **Medium Rigid (8‑16 t)**: BEV004 Volvo FL ↔ DSL004 Volvo FE; BEV005 MB eActros 300 ↔ DSL005 MB Actros.
- **Articulated (>16 t)**: BEV006 MB eActros 600 ↔ DSL006 MB Actros; BEV007 Volvo FH ↔ DSL007 Volvo FH Diesel; BEV008 Scania 45R ↔ DSL008 Scania R560.

### 13.2 Key Constants (AUD unless noted)
- Electricity prices: retail 0.30/kWh, off-peak 0.15/kWh, public fast 0.50/kWh, solar 0.04/kWh.
- Diesel price: 2.05/litre; labour (charging) 47/hour.
- Maintenance (per km): BEV light/medium 0.10, BEV articulated 0.12, diesel light 0.20, diesel medium 0.25, diesel articulated 0.30.
- Battery replacement: 130/kWh replacement, 13/kWh recycle (net 117/kWh) at year 8.
- Depreciation: 20 % initial year, then 10 % of remaining value annually.
- Annual kms defaults: light/medium 23 000, articulated 84 000.

### 13.3 Scenario Trajectories
- **Baseline**: Diesel +3 %/yr, electricity +2 %/yr, battery cost ‑7 %/yr, maintenance multiplier 0.85→1.25 over life.
- **Technology Breakthrough**: Same fuel trends, faster battery decline (75 % reduction by year 15), BEV efficiency improvements > baseline.
- **Oil Crisis**: Diesel spike +55 % in year 3, electricity +3 %/yr, faster diesel efficiency improvements, diesel 2.22× by year 15.

---

## 14. Maintenance of This Document

- Treat this plan as the definitive playbook. Update it whenever scope, architecture, or success criteria change.
- Remove obsolete references immediately; every new decision or artifact should be summarized here to keep the single-document mandate intact.
- Before deleting source materials (legacy transition docs), ensure their critical content has been merged into the relevant sections above.

---

## 15. Traceability & Source Materials

- **Python Engine Assets**: `calculations/financial.py`, `calculations/operating.py`, `calculations/inputs.py`, `calculations/calculations.py`, and `calculations/simulation.py` define every invariant referenced in Sections 3, 6, and 13; keep change logs synchronized here whenever formulas shift.
- **Data Tables**: `data/vehicle_models.csv`, `data/vehicles.py`, `data/constants.py`, `data/policies.py`, and `data/scenarios.py` back Sections 7 and 13. When analysts update any CSV/constant, run `scripts/generate_vehicle_catalog_ts.py` to refresh `shared/data/vehicleCatalog.ts`, `shared/data/constants.ts`, `shared/data/scenarios.ts`, and `shared/data/policies.ts`, mirror the change in this plan, and commit the regenerated payloads so React and FastAPI stay aligned with Python.
- **Analytics & Reporting**: `analysis/analysis.py`, `analysis/generate_tco_analysis.py`, `analysis/purchase_year_analysis.py`, `output/charts.py`, `output/generate_html_report.py`, and `main.py` provide the exports noted in Sections 3.4, 6.5, and 10. Document any new job or API that supersedes these scripts.
- **Quality & Validation**: `tests/test_comprehensive.py` (and the soon-to-be `scripts/validation.py`) are the regression nets referenced in Sections 6.5 and 11; CI must keep them green before shipping any platform change. The Vitest parity harness (`frontend/src/services/calculator/__tests__/TCOEngine.test.ts`) and its `scripts/export_tco_snapshot.py` fixture keep the TypeScript calculator aligned with the Python engine within ±1 %.
- **Specs & Narrative**: `TCO - Tech Specification 150725.md` plus this master plan are the only approved sources of truth. Whenever requirements evolve, update both and link the relevant Pull Request so future contributors can trace the decision.

---

## 16. Team & Resource Plan

- **Frontend Developer (1 FTE)** – React/TypeScript expert with data visualisation + mobile-first experience; owns wizard, charts, state store, and PWA polish.
- **Backend Developer (0.5 FTE)** – FastAPI + PostgreSQL specialist who wraps the Python engine, implements APIs, persistence, Redis caching, and analytics exports.
- **UI/UX Designer (0.5 FTE)** – Conducts operator research, produces journey maps, mockups, and usability tests; ensures accessibility + copy clarity.
- **DevOps Engineer (0.25 FTE)** – Sets up CI/CD, container orchestration, monitoring/alerting, SSL/DNS, and manages environment parity.
- **Support Crew**: Project manager (TWU liaison), data analyst (interprets captured data + policy outputs), technical writer (documentation/runbooks).

---

## 17. Budget & Ongoing Costs

- **Development (6 weeks)**: $60 k engineering, $10 k design, $8 k project management, $5 k QA — total $83 k.
- **Infrastructure (annualised)**: ~$500/mo hosting, $200/mo database, $100/mo CDN/storage, $200/mo monitoring — total ~$12 k/yr.
- **Operational Run Rate**: 20 % maintenance reserve ($16.6 k/yr), ~$20 k/yr for feature updates, ~$10 k/yr support & community engagement.
- Track actuals against these guardrails each phase gate; if costs deviate, update §17 and annotate the execution log entry that triggered the change.

---

## 18. Post-Launch Enhancements Backlog

- **Fleet & Planning Tools**: Multi-vehicle comparison, bulk upload, fleet transition sequencing.
- **Advanced Analytics**: AI-assisted recommendations, predictive TCO modeling, route optimisation overlays.
- **Integrations**: Telematics data ingest, accounting/ERP connectors, automated policy incentive lookups.
- **Community Features**: Anonymous benchmarking, discussion hub, knowledge base, notification feeds.
- **Native Mobile**: Consider dedicated iOS/Android shells for offline workflows and push notifications once the PWA usage data justifies it.

---

**Next Steps**
1. Assign owners/dates to each phase and record them in the delivery tracker.
2. Kick off Phase 0 readiness: confirm tooling, environments, and stakeholder buy-in.
