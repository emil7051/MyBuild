# API Documentation

The TCO Web Platform provides a RESTful API for calculating Total Cost of Ownership, managing sessions, and accessing analytics.

## Base URL

- **Development**: `http://localhost:8000/api/v1`
- **Production**: `https://your-domain.com/api/v1`

## Authentication

### Session Access

Session endpoints do not require authentication. Clients can create, fetch, and update sessions using the `sessionId` returned on creation.

### Analytics API Key

The `/analytics/summary` endpoint requires an API key:

- Set the `ANALYTICS_API_KEY` environment variable to enable access
- Requests must include the `X-Analytics-Key` header
- If not configured, the endpoint is disabled

## Endpoints

### System

#### Health Check

```http
GET /api/v1/health
```

Check if the API is running and retrieve environment information.

**Response:**
```json
{
  "status": "ok",
  "environment": "production"
}
```

---

### Vehicles

#### List All Vehicles

```http
GET /api/v1/vehicles
```

Retrieve a list of all available vehicles with summary information.

**Response:**
```json
[
  {
    "vehicle_id": "BEV001",
    "model_name": "Jac N75",
    "drivetrain_type": "BEV",
    "weight_class": "Light Rigid",
    "comparison_pair": "DSL001"
  },
  {
    "vehicle_id": "DSL001",
    "model_name": "Hino 300",
    "drivetrain_type": "Diesel",
    "weight_class": "Light Rigid",
    "comparison_pair": "BEV001"
  }
]
```

#### Get Vehicle Details

```http
GET /api/v1/vehicles/{vehicle_id}
```

Retrieve detailed specifications for a specific vehicle.

**Parameters:**
- `vehicle_id` (path): Vehicle identifier (e.g., "BEV001")

**Response:**
```json
{
  "vehicle_id": "BEV001",
  "model_name": "Jac N75",
  "drivetrain_type": "BEV",
  "weight_class": "Light Rigid",
  "comparison_pair": "DSL001",
  "payload": 2650.0,
  "msrp": 145000.0,
  "range_km": 300.0,
  "battery_capacity_kwh": 89.0,
  "kwh_per_km": 0.6,
  "litres_per_km": 0.0,
  "maintenance_cost_per_km": 0.18,
  "annual_registration": 800.0,
  "annual_kms": 50000.0
}
```

**Error Responses:**
- `404 Not Found` - Vehicle ID does not exist

---

> Note: TCO calculations now execute in the shared TypeScript engine on the frontend. Backend endpoints currently cover vehicles, sessions, and analytics only.

### Sessions

Session endpoints allow you to persist calculation sessions for later retrieval.

#### Create Session

```http
POST /api/v1/sessions
```

Create a new calculation session with inputs and results.

**Request Body:**
```json
{
  "wizardData": {
    "currentVehicle": "BEV001",
    "comparisonVehicles": ["DSL001"],
    "scenario": "baseline",
    "purchaseMethod": "financed",
    "dutyCycle": {
      "urban": 60,
      "regional": 30,
      "longHaul": 10
    },
    "overrides": {
      "annual_kms_variation": 5000,
      "fuel_price_variation": 1.05
    },
    "vehicleParamOverrides": {
      "BEV001": {
        "msrp_override": 180000
      }
    }
  },
  "results": [
    {
      "vehicle_id": "BEV001",
      "scenario_name": "baseline",
      "total_cost": 523750.25,
      "annual_cost": 34916.68,
      "cost_per_km": 0.62,
      "breakdown": {
        "purchase_cost": 176500,
        "fuel_cost": 0,
        "maintenance_cost": 11250,
        "insurance_cost": 9260,
        "registration_cost": 4200,
        "battery_replacement_cost": 0,
        "financing_cost": 14600,
        "carbon_cost": 0,
        "charging_labour_cost": 0,
        "payload_penalty_cost": 0,
        "residual_value": 45000,
        "depreciation": 120000,
        "taxes_and_fees": 6000
      }
    }
  ],
  "operatorProfile": {
    "operatorType": "owner_driver",
    "fleetSize": "1",
    "contactEmail": "operator@example.com",
    "consentToContact": true,
    "notes": "Prefers email follow-up"
  },
  "feedback": {
    "rating": 4,
    "comment": "Useful comparison."
  }
}
```

Duty cycle values are percentages (0-100) and must sum to ~100.

**Response:**
```json
{
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "wizardData": {...},
  "results": [...],
  "operatorProfile": {...},
  "feedback": {...},
  "updatedAt": "2025-11-10T21:30:00Z",
  "lastCalculatedAt": "2025-11-10T21:30:00Z"
}
```

**Status Code:** `201 Created`

#### Get Session

```http
GET /api/v1/sessions/{session_id}
```

Retrieve a saved session by ID.

**Parameters:**
- `session_id` (path): UUID of the session

**Response:**
```json
{
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "wizardData": {...},
  "results": [...],
  "operatorProfile": {...},
  "feedback": {...},
  "updatedAt": "2025-11-10T21:30:00Z",
  "lastCalculatedAt": "2025-11-10T21:30:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Session ID does not exist
- `422 Unprocessable Entity` - Invalid UUID format

#### Update Session

```http
PUT /api/v1/sessions/{session_id}
```

Update an existing session with new data.

**Parameters:**
- `session_id` (path): UUID of the session

**Request Body:**
```json
{
  "wizardData": {...},
  "results": [...],
  "operatorProfile": {...},
  "feedback": {...}
}
```

**Response:**
```json
{
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "wizardData": {...},
  "results": [...],
  "operatorProfile": {...},
  "feedback": {...},
  "updatedAt": "2025-11-10T21:45:00Z",
  "lastCalculatedAt": "2025-11-10T21:45:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Session ID does not exist
- `422 Unprocessable Entity` - Invalid UUID format or validation error

---

### Analytics

#### Get Analytics Summary

```http
GET /api/v1/analytics/summary
```

Retrieve aggregated analytics across all sessions.

**Headers:**
- `X-Analytics-Key` (required): The configured analytics API key

If `ANALYTICS_API_KEY` is not configured, the endpoint is disabled and returns `403`.

**Response:**
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

---

## Error Handling

All errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `413 Request Entity Too Large` - Request body exceeds 1MB limit
- `422 Unprocessable Entity` - Validation error (invalid UUID format, invalid vehicle ID, invalid scenario, etc.)
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

---

## Rate Limiting

Rate limiting is implemented via [slowapi](https://github.com/laurentS/slowapi) with configurable limits per endpoint type:

| Endpoint Type | Default Limit | Environment Variable |
|---------------|---------------|---------------------|
| Sessions | 30/minute | `RATE_LIMIT_SESSIONS_PER_MINUTE` |
| Analytics | 10/minute | `RATE_LIMIT_ANALYTICS_PER_MINUTE` |
| Vehicles | 60/minute | `RATE_LIMIT_VEHICLES_PER_MINUTE` |

When rate limited, the API returns `429 Too Many Requests` with a `Retry-After` header.

### Request Size Limits

A maximum request body size of 1MB is enforced. Requests exceeding this limit receive `413 Request Entity Too Large`.

---

## CORS

The API supports CORS for browser-based clients. Allowed origins can be configured via the `BACKEND_CORS_ORIGINS` environment variable.

Default development origins:
- `http://localhost:5000`
- `http://127.0.0.1:5000`

---

## Examples

### Python Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Get all vehicles
vehicles = requests.get(f"{BASE_URL}/vehicles").json()
print(f"Loaded {len(vehicles)} vehicles")

```

### JavaScript Example

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

async function loadCatalog() {
  const vehiclesRes = await fetch(`${BASE_URL}/vehicles`);
  const vehicles = await vehiclesRes.json();

  console.log(`Loaded ${vehicles.length} vehicles`);
}
```

---

## Interactive API Documentation

When the backend server is running, you can access interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These provide interactive documentation where you can test endpoints directly in the browser.
