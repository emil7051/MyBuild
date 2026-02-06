# Security and API Requirements

This document is the canonical reference for backend security and request-handling
requirements. It replaces inline audit reference codes in source comments and
docstrings.

## Request Validation

- Session route IDs must be valid UUIDv4 values before service lookups.
- Session payloads must be validated server-side with shared bounds for:
  - cost overrides
  - vehicle parameter overrides
  - scenario identifiers
  - duty-cycle totals
  - freeform field lengths and email format
- Vehicle IDs in payloads must exist in the canonical catalog.

Primary implementation:
- `backend/app/api/router.py`
- `backend/app/models/calculation.py`
- `backend/app/models/session.py`

## Session Authorization

- Session read/update access is protected by an HttpOnly session-secret cookie.
- Secrets are generated cryptographically, stored as SHA-256 hashes, and verified
  with constant-time comparison.

Primary implementation:
- `backend/app/core/security.py`
- `backend/app/api/router.py`
- `backend/app/services/sessions.py`

## Analytics Endpoint Protection

- Analytics summary access requires `X-Analytics-Key`.
- If no analytics key is configured, the endpoint is disabled.

Primary implementation:
- `backend/app/core/security.py`
- `backend/app/api/router.py`

## Traffic and Abuse Controls

- Request bodies are capped by middleware using both:
  - `Content-Length` pre-check
  - streaming byte-count enforcement for chunked/forged requests
- Session, vehicle-catalog, and analytics routes are rate-limited.
- `X-Forwarded-For` is trusted only when requests come through configured trusted
  proxy CIDRs.

Primary implementation:
- `backend/app/core/middleware.py`
- `backend/app/core/security.py`
- `backend/app/main.py`
- `backend/app/core/config.py`

## Observability and Alerting Controls

- API responses include `x-request-id` for request correlation.
- Sampled traced requests include `x-trace-id` when tracing is enabled.
- Route-grouped request metrics are emitted as structured logs.
- Threshold breaches emit structured `http.alert` events, with optional webhook forwarding.

Primary implementation:
- `backend/app/core/observability.py`
- `backend/app/core/config.py`
- `backend/app/main.py`

## Persistence and Analytics Consistency

- Wizard overrides are normalized into a stable structure before storage:
  `{"cost": {...}, "vehicle": {...}}`.
- Analytics summaries are computed through SQL aggregation to avoid per-session
  query loops and inconsistent rollups.

Primary implementation:
- `backend/app/services/sessions.py`
