# API Documentation

The TCO Web Platform exposes a REST API for vehicle catalog access, session persistence, and analytics.

## Base URL

- Development: `http://localhost:8000/api/v1`
- Production: `https://<your-domain>/api/v1`

## Authentication and Access Control

### Session endpoints

- `POST /sessions` does not require an existing session cookie.
- `GET /sessions/{session_id}` and `PUT /sessions/{session_id}` require the HttpOnly session-secret cookie that is issued when the session is created.
- Session secrets are stored server-side as SHA-256 hashes and are never returned in JSON responses.

Expected failures on protected session routes:
- `401 Unauthorized`: session secret cookie is missing.
- `403 Forbidden`: session secret cookie is present but invalid.

### Analytics endpoint

`GET /analytics/summary` requires `X-Analytics-Key`.

- If `ANALYTICS_API_KEY` is not configured, the endpoint is disabled (`403`).
- If configured but missing/invalid in the request, the endpoint returns `401`.

## Response Headers

- `x-request-id`: Included on API responses for request correlation.
- `x-trace-id`: Included when tracing is enabled and the request is sampled.

## Endpoints

### System

#### Health Check

```http
GET /api/v1/health
```

Response:

```json
{
  "status": "ok",
  "environment": "production"
}
```

### Vehicles

#### List Vehicles

```http
GET /api/v1/vehicles
```

Response (example):

```json
[
  {
    "vehicle_id": "BEV001",
    "model_name": "Jac N75",
    "drivetrain_type": "BEV",
    "weight_class": "Light Rigid",
    "comparison_pair": "DSL001"
  }
]
```

#### Get Vehicle Detail

```http
GET /api/v1/vehicles/{vehicle_id}
```

Response (example):

```json
{
  "vehicle_id": "BEV001",
  "model_name": "Jac N75",
  "drivetrain_type": "BEV",
  "weight_class": "Light Rigid",
  "comparison_pair": "DSL001",
  "payload": 4.0,
  "msrp": 176500.0,
  "range_km": 220.0,
  "battery_capacity_kwh": 100.0,
  "kwh_per_km": 0.48,
  "litres_per_km": 0.0,
  "annual_registration": 653.0,
  "annual_kms": 23000.0
}
```

Errors:
- `404 Not Found`: unknown vehicle ID.

### Sessions

Session payloads use frontend-style camelCase field names.

#### Create Session

```http
POST /api/v1/sessions
```

Request body (example):

```json
{
  "wizardData": {
    "currentVehicle": "DSL001",
    "comparisonVehicles": ["BEV001"],
    "scenario": "baseline",
    "purchaseMethod": "financed",
    "dutyCycle": {
      "urban": 60,
      "regional": 25,
      "longHaul": 15
    },
    "overrides": {
      "annual_kms_variation": 50000,
      "fuel_price_variation": 1.05,
      "apply_road_user_charge_bev": true
    },
    "vehicleParamOverrides": {
      "BEV001": {
        "msrp_override": 185000
      }
    }
  },
  "results": [
    {
      "vehicle_id": "BEV001",
      "scenario_name": "baseline",
      "total_cost": 500000.0,
      "annual_cost": 33333.33,
      "cost_per_km": 1.45,
      "breakdown": {
        "npv_costs": {
          "fuel_cost": 0,
          "maintenance_cost": 15000,
          "battery_replacement_cost": 10000,
          "carbon_cost": 0,
          "charging_labour_cost": 12000,
          "payload_penalty_cost": 30000,
          "residual_value": 45000
        },
        "nominal_costs": {
          "insurance_cost": 12000,
          "registration_cost": 9795,
          "financing_cost": 28000,
          "depreciation": 130000
        },
        "upfront_costs": {
          "purchase_cost": 176500,
          "taxes_and_fees": 5295
        }
      }
    }
  ]
}
```

Response:
- `201 Created`
- Sets an HttpOnly session-secret cookie.
- Returns a session payload (without session secret in JSON).

#### Get Session

```http
GET /api/v1/sessions/{session_id}
```

Requires valid session-secret cookie.

Errors:
- `401 Unauthorized`: missing session cookie.
- `403 Forbidden`: invalid session cookie.
- `404 Not Found`: unknown session ID.
- `422 Unprocessable Entity`: invalid UUID format.

#### Update Session

```http
PUT /api/v1/sessions/{session_id}
```

Requires valid session-secret cookie.

Body fields are optional (`wizardData`, `results`, `operatorProfile`, `feedback`).

Errors:
- `401 Unauthorized`: missing session cookie.
- `403 Forbidden`: invalid session cookie.
- `404 Not Found`: unknown session ID.
- `422 Unprocessable Entity`: invalid UUID or payload validation error.

### Analytics

#### Analytics Summary

```http
GET /api/v1/analytics/summary
```

Headers:
- `X-Analytics-Key: <configured-key>`

Response (example):

```json
{
  "totalSessions": 1250,
  "completedSessions": 980,
  "calculationsLast24h": 42,
  "bevWinRate": 0.68,
  "averagePaybackYears": 4.2,
  "averageCostDelta": 18500.5,
  "topVehicles": {
    "BEV001": 450,
    "BEV003": 380
  }
}
```

## Error Format

All errors follow:

```json
{
  "detail": "Error message"
}
```

## Status Codes

- `200 OK`
- `201 Created`
- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`
- `413 Content Too Large` (request body exceeds configured maximum)
- `422 Unprocessable Entity`
- `429 Too Many Requests`
- `500 Internal Server Error`

## Rate Limiting

Rate limits are enforced per client IP:

| Endpoint Group | Default | Environment Variable |
|---|---:|---|
| Sessions | `30/minute` | `RATE_LIMIT_SESSIONS_PER_MINUTE` |
| Vehicles | `60/minute` | `RATE_LIMIT_VEHICLES_PER_MINUTE` |
| Analytics | `10/minute` | `RATE_LIMIT_ANALYTICS_PER_MINUTE` |

Trusted proxy forwarding behavior is controlled with `TRUSTED_PROXIES`.

## Notes

- The authoritative calculation engine is `shared/calculator` (TypeScript).
- The backend does not expose a public calculation endpoint in this API surface.
