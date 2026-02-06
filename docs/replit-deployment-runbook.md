# Replit Deployment Runbook

This runbook is the operational guide for deploying and rolling back the TCO Web Platform on Replit.

## 1. Scope and Source of Truth

- Deployment target: Replit autoscale deployment.
- Build/run configuration source of truth: `.replit` `[deployment]` section.
- Backend entrypoint: `backend.app.main:app` (Uvicorn).
- Frontend build output: `frontend/dist` (served by FastAPI static routes in `backend/app/main.py`).

Current deployment config in `.replit`:
- build: `cd frontend && bun install --frozen-lockfile && bun run build`
- run: `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`

## 2. Required Environment Variables

Set these in Replit Secrets for production deployments:

| Variable | Required | Notes |
|---|---|---|
| `ENVIRONMENT` | Yes | Set to `production`. |
| `DATABASE_URL` | Yes | PostgreSQL URL. `postgres://` / `postgresql://` are normalized to async driver automatically. |
| `REDIS_URL` | Yes | Redis URL for session cache. |
| `BACKEND_CORS_ORIGINS` | Usually | Comma-separated origins. Must not include `*`. |
| `RUN_MIGRATIONS` | Recommended | Set `false` for controlled/manual migration flow. |
| `ANALYTICS_API_KEY` | Optional | Required only if `/api/v1/analytics/summary` should be enabled. |
| `RATE_LIMIT_REDIS_URL` | Optional | Dedicated Redis for rate limits; defaults to `REDIS_URL` outside development. |
| `OBSERVABILITY_TRACING_ENABLED` | Optional | Defaults to `true`. Set `false` to disable tracing completely. |
| `OBSERVABILITY_TRACING_SAMPLE_RATE` | Optional | Defaults to `0.1` (10%). Use lower values for cost/noise control. |
| `OBSERVABILITY_TRACING_SERVICE_NAME` | Optional | Defaults to `tco-web-platform-api`. |
| `OBSERVABILITY_TRACING_OTLP_ENDPOINT` | Optional | OTLP/HTTP endpoint for exported spans. If omitted, spans are logged to stdout. |
| `OBSERVABILITY_TRACING_OTLP_HEADERS` | Optional | Comma-separated OTLP headers (`key=value,key2=value2`). |
| `OBSERVABILITY_ALERT_MIN_REQUESTS` | Optional | Defaults to `20`. Minimum requests in a metrics window before alerts trigger. |
| `OBSERVABILITY_ALERT_ERROR_RATE_THRESHOLD` | Optional | Defaults to `0.2` (20% 5xx rate threshold). |
| `OBSERVABILITY_ALERT_AVG_DURATION_MS_THRESHOLD` | Optional | Defaults to `1500` ms average request latency threshold. |
| `OBSERVABILITY_ALERT_COOLDOWN_SECONDS` | Optional | Defaults to `300` seconds between repeated alerts. |
| `OBSERVABILITY_ALERT_WEBHOOK_URL` | Optional | Webhook for forwarding alert payloads (e.g. Slack/Teams/Pager bridge). |
| `OBSERVABILITY_ALERT_WEBHOOK_TIMEOUT_SECONDS` | Optional | Defaults to `2.0` seconds. |

Notes:
- `SESSION_SECRET_COOKIE_SECURE` defaults to secure in non-development environments.
- Frontend `VITE_API_URL` is optional in production because backend serves the SPA and API on the same host (`/api/v1` default).

## 3. Pre-Deploy Checklist

From repo root:

```bash
# Backend quality gates
python -m pytest tests --cov
python -m mypy backend/app/core backend/app/api backend/app/main.py

# Frontend quality gates
cd frontend
bun run test
bun run typecheck
bun run lint
# Optional but recommended smoke check (installs browser if needed)
bunx playwright install chromium
bun run test:e2e
bun run build
cd ..
```

If Python data files changed (`data/*.py` or generation script changes):

```bash
python scripts/generate_vehicle_catalog_ts.py
python scripts/validation.py
git diff -- shared/data
```

## 4. Database Migration Flow (Production)

Use a controlled migration step before deployment rollout.

From repo root:

```bash
pip install -r requirements.lock.txt
cd backend
alembic current
alembic upgrade head
alembic current
cd ..
```

Guidance:
- Prefer manual migration execution with `RUN_MIGRATIONS=false` in production.
- Do not modify previously applied migration files.

## 5. Deployment Steps on Replit

1. Confirm all required secrets are set.
2. Confirm migrations are at `head`.
3. Trigger deployment from the main branch in Replit Deployments.
4. Wait for build and process startup to complete.
5. Proceed with post-deploy checks below.

## 6. Post-Deploy Operational Checks

Replace `<deployment-url>` with the live Replit deployment URL.

```bash
# Health endpoint
curl -fsS https://<deployment-url>/api/v1/health

# Vehicle catalog endpoint
curl -fsS https://<deployment-url>/api/v1/vehicles
```

Expected health response includes:
- `status: "ok"`

Additional checks:
- Open the web app and run a comparison end-to-end.
- Confirm session autosave works (session ID appears in UI).
- If analytics is enabled, verify endpoint with `X-Analytics-Key`.
- Inspect logs for repeated 5xx errors or connection failures.
- Confirm `tracing.configured` appears at startup with expected `sample_rate` and `exporter`.
- Confirm API responses include `x-request-id`; sampled requests also include `x-trace-id`.
- If alert webhook is configured, verify a test alert is delivered after threshold breach.

## 7. Tracing and Alerting Workflow (OBS-02)

Use this default Replit-compatible workflow:

1. Start with `OBSERVABILITY_TRACING_SAMPLE_RATE=0.05` in production.
2. Leave `OBSERVABILITY_TRACING_OTLP_ENDPOINT` unset to emit sampled spans to logs, or set it to your OTLP collector.
3. Route JSON logs for `event=http.alert` to your notification target.
4. Optionally set `OBSERVABILITY_ALERT_WEBHOOK_URL` for direct alert forwarding.
5. Tune alert thresholds after one day of traffic using observed error-rate and latency baselines.

## 8. Rollback Procedure

### Application rollback (fastest path)

1. In Replit Deployments, redeploy/promote the previous known-good release.
2. Re-run post-deploy checks.

### Database rollback (when required)

Only perform if schema changes are incompatible and a normal app rollback is insufficient.

```bash
cd backend
alembic history
alembic downgrade -1
# or: alembic downgrade <revision_id>
cd ..
```

Then redeploy the matching previous app version.

If a destructive migration was applied, restore from database backup/snapshot and redeploy the matching code version.

## 9. Incident Notes

- If `/api/v1/health` fails: check `DATABASE_URL`, database availability, and backend logs first.
- If session writes fail: check `REDIS_URL`, API logs, and rate-limit settings.
- If frontend loads but API calls fail: check CORS origins and `/api/v1` routing.

## 10. Related Files

- `.replit`
- `backend/app/core/config.py`
- `backend/app/db/session.py`
- `backend/alembic/`
- `backend/app/main.py`
