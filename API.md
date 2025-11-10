# API Documentation

The TCO Web Platform provides a RESTful API for calculating Total Cost of Ownership, managing sessions, and accessing analytics.

## Base URL

- **Development**: `http://localhost:8000/api/v1`
- **Production**: `https://your-domain.com/api/v1`

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

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
    "id": "BEV001",
    "name": "Jac N75",
    "weight_class": "Light Rigid",
    "drivetrain": "BEV",
    "payload_kg": 2650,
    "range_km": 300,
    "msrp": 145000,
    "comparison_pair": "DSL001"
  },
  {
    "id": "DSL001",
    "name": "Hino 300",
    "weight_class": "Light Rigid",
    "drivetrain": "DSL",
    "payload_kg": 3000,
    "range_km": 800,
    "msrp": 85000,
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
  "id": "BEV001",
  "name": "Jac N75",
  "weight_class": "Light Rigid",
  "drivetrain": "BEV",
  "payload_kg": 2650,
  "range_km": 300,
  "msrp": 145000,
  "battery_kwh": 89.0,
  "consumption_kwh_100km": 60.0,
  "maintenance_cost_per_km": 0.18,
  "registration_cost": 800,
  "default_annual_kms": 50000,
  "comparison_pair": "DSL001"
}
```

**Error Responses:**
- `404 Not Found` - Vehicle ID does not exist

---

### Calculations

#### Calculate Single Vehicle TCO

```http
POST /api/v1/calculations
```

Calculate Total Cost of Ownership for a single vehicle.

**Request Body:**
```json
{
  "vehicle_id": "BEV001",
  "scenario": "baseline",
  "purchase_method": "financed",
  "annual_kms": 50000,
  "duty_cycle": {
    "urban": 0.6,
    "regional": 0.3,
    "long_haul": 0.1
  },
  "overrides": {
    "fuel_price_variation": 1.0,
    "electricity_price_variation": 1.0,
    "annual_kms_variation": 1.0,
    "residual_value_variation": 1.0,
    "maintenance_cost_variation": 1.0,
    "battery_life_variation": 1.0,
    "charging_efficiency_variation": 1.0
  }
}
```

**Request Schema:**
- `vehicle_id` (string, required): Vehicle identifier
- `scenario` (string, required): Economic scenario - "baseline", "tech_breakthrough", or "oil_crisis"
- `purchase_method` (string, required): "outright" or "financed"
- `annual_kms` (number, optional): Annual kilometers driven (default: vehicle's default)
- `duty_cycle` (object, optional): Distribution across duty types (must sum to 1.0)
  - `urban` (number): 0.0-1.0
  - `regional` (number): 0.0-1.0
  - `long_haul` (number): 0.0-1.0
- `overrides` (object, optional): Multipliers for sensitivity analysis (all default to 1.0)

**Response:**
```json
{
  "vehicle_id": "BEV001",
  "vehicle_name": "Jac N75",
  "scenario": "baseline",
  "purchase_method": "financed",
  "total_cost_npv": 523750.25,
  "cost_per_km": 0.62,
  "annual_cost": 31000.50,
  "breakdown": {
    "purchase_cost": 145000,
    "financing_cost": 18500,
    "depreciation": 87000,
    "taxes_and_fees": 5800,
    "fuel_cost": 0,
    "electricity_cost": 78450,
    "maintenance_cost": 67500,
    "insurance_cost": 48750,
    "registration_cost": 12000,
    "battery_replacement_cost": 32500,
    "carbon_cost": 0,
    "charging_labour_cost": 15250,
    "payload_penalty_cost": 8500,
    "residual_value": -43500
  },
  "metadata": {
    "vehicle_life_years": 15,
    "discount_rate": 0.05,
    "annual_kms": 50000
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Vehicle ID does not exist

#### Compare Multiple Vehicles

```http
POST /api/v1/calculations/compare
```

Calculate and compare TCO for multiple vehicles with the same operating profile.

**Request Body:**
```json
{
  "vehicle_ids": ["BEV001", "DSL001", "BEV002"],
  "scenario": "baseline",
  "purchase_method": "financed",
  "annual_kms": 50000,
  "duty_cycle": {
    "urban": 0.6,
    "regional": 0.3,
    "long_haul": 0.1
  },
  "overrides": {}
}
```

**Request Schema:**
- `vehicle_ids` (array, required): Array of vehicle identifiers (2-8 vehicles)
- Other fields same as single calculation

**Response:**
```json
[
  {
    "vehicle_id": "BEV001",
    "total_cost_npv": 523750.25,
    "cost_per_km": 0.62,
    ...
  },
  {
    "vehicle_id": "DSL001",
    "total_cost_npv": 612300.75,
    "cost_per_km": 0.73,
    ...
  }
]
```

**Error Responses:**
- `400 Bad Request` - Invalid parameters or too many vehicles
- `404 Not Found` - One or more vehicle IDs do not exist

---

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
  "wizard_data": {
    "selected_vehicles": ["BEV001", "DSL001"],
    "scenario": "baseline",
    "purchase_method": "financed",
    "annual_kms": 50000,
    "duty_cycle": {
      "urban": 0.6,
      "regional": 0.3,
      "long_haul": 0.1
    },
    "overrides": {}
  },
  "results": [
    {
      "vehicle_id": "BEV001",
      "total_cost_npv": 523750.25,
      "cost_per_km": 0.62,
      "breakdown": {...}
    }
  ],
  "operator_profile": {
    "operator_type": "owner_driver",
    "fleet_size": 1,
    "industry": "construction"
  }
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "wizard_data": {...},
  "results": [...],
  "operator_profile": {...},
  "created_at": "2025-11-10T21:30:00Z",
  "updated_at": "2025-11-10T21:30:00Z"
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
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "wizard_data": {...},
  "results": [...],
  "operator_profile": {...},
  "created_at": "2025-11-10T21:30:00Z",
  "updated_at": "2025-11-10T21:30:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Session ID does not exist

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
  "wizard_data": {...},
  "results": [...],
  "operator_profile": {...}
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "wizard_data": {...},
  "results": [...],
  "operator_profile": {...},
  "created_at": "2025-11-10T21:30:00Z",
  "updated_at": "2025-11-10T21:45:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Session ID does not exist

---

### Analytics

#### Get Analytics Summary

```http
GET /api/v1/analytics/summary
```

Retrieve aggregated analytics across all sessions.

**Response:**
```json
{
  "total_sessions": 1250,
  "total_calculations": 3875,
  "bev_win_rate": 0.68,
  "average_payback_years": 4.2,
  "top_vehicles": [
    {
      "vehicle_id": "BEV001",
      "count": 450
    },
    {
      "vehicle_id": "BEV003",
      "count": 380
    }
  ],
  "scenario_distribution": {
    "baseline": 0.65,
    "tech_breakthrough": 0.25,
    "oil_crisis": 0.10
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
- `500 Internal Server Error` - Server error

---

## Rate Limiting

Currently, there is no rate limiting implemented. For production deployments, consider implementing rate limiting at the infrastructure level.

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
response = requests.get(f"{BASE_URL}/vehicles")
vehicles = response.json()

# Calculate TCO
payload = {
    "vehicle_id": "BEV001",
    "scenario": "baseline",
    "purchase_method": "financed",
    "annual_kms": 50000
}
response = requests.post(f"{BASE_URL}/calculations", json=payload)
result = response.json()

print(f"Total Cost: ${result['total_cost_npv']:,.2f}")
print(f"Cost per km: ${result['cost_per_km']:.2f}")
```

### JavaScript Example

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

// Compare vehicles
async function compareVehicles() {
  const response = await fetch(`${BASE_URL}/calculations/compare`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      vehicle_ids: ['BEV001', 'DSL001'],
      scenario: 'baseline',
      purchase_method: 'financed',
      annual_kms: 50000,
    }),
  });
  
  const results = await response.json();
  
  results.forEach(result => {
    console.log(`${result.vehicle_name}: $${result.cost_per_km}/km`);
  });
}
```

---

## Interactive API Documentation

When the backend server is running, you can access interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These provide interactive documentation where you can test endpoints directly in the browser.
