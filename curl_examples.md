# cURL Examples

This document lists realistic sample cURL requests and responses for the API endpoints.

Assume the server is running on `http://127.0.0.1:8000`.

### 1. List Dealerships
Used to populate dropdown filters.

**Request:**
```bash
curl -X GET http://127.0.0.1:8000/api/dealerships/ \
  -H "Accept: application/json"
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Toyota of Seattle",
    "location": "Seattle, WA"
  },
  {
    "id": 2,
    "name": "Honda of Bellevue",
    "location": "Bellevue, WA"
  }
]
```

### 2. List Vehicles (with pagination and filtering)

**Request:**
```bash
curl -X GET "http://127.0.0.1:8000/api/vehicles/?dealership_id=1&status=in_stock" \
  -H "Accept: application/json"
```

**Response (200 OK):**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "vin": "1HGCM82633A123456",
      "make": "Toyota",
      "model": "Camry",
      "year": 2023,
      "intake_date": "2026-03-15",
      "price": "24999.00",
      "status": "in_stock",
      "days_in_stock": 118,
      "is_aging": true,
      "latest_action": {
        "action_type": "price_reduction_planned",
        "notes": "Reduce price by $1000 due to aging stock",
        "created_at": "2026-07-11T11:09:15.320118Z"
      }
    }
  ]
}
```

### 3. List Aging Vehicles (pre-filtered to `is_aging=true`, sorted desc by `days_in_stock`)

**Request:**
```bash
curl -X GET "http://127.0.0.1:8000/api/vehicles/aging/?make=Toyota" \
  -H "Accept: application/json"
```

**Response (200 OK):**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "vin": "1HGCM82633A123456",
      "make": "Toyota",
      "model": "Camry",
      "year": 2023,
      "intake_date": "2026-03-15",
      "price": "24999.00",
      "status": "in_stock",
      "days_in_stock": 118,
      "is_aging": true,
      "latest_action": {
        "action_type": "price_reduction_planned",
        "notes": "Reduce price by $1000 due to aging stock",
        "created_at": "2026-07-11T11:09:15.320118Z"
      }
    }
  ]
}
```

### 4. Get Vehicle Detail (including full action history)

**Request:**
```bash
curl -X GET http://127.0.0.1:8000/api/vehicles/1/ \
  -H "Accept: application/json"
```

**Response (200 OK):**
```json
{
  "id": 1,
  "vin": "1HGCM82633A123456",
  "make": "Toyota",
  "model": "Camry",
  "year": 2023,
  "intake_date": "2026-03-15",
  "price": "24999.00",
  "status": "in_stock",
  "days_in_stock": 118,
  "is_aging": true,
  "latest_action": {
    "action_type": "price_reduction_planned",
    "notes": "Reduce price by $1000 due to aging stock",
    "created_at": "2026-07-11T11:09:15.320118Z"
  },
  "history": [
    {
      "id": 1,
      "action_type": "price_reduction_planned",
      "notes": "Reduce price by $1000 due to aging stock",
      "created_by": "John Doe",
      "created_at": "2026-07-11T11:09:15.320118Z"
    }
  ]
}
```

**Request (PUT - Rejected as 405 Method Not Allowed):**
```bash
curl -X PUT http://127.0.0.1:8000/api/vehicles/1/ \
  -H "Content-Type: application/json" \
  -d '{"make": "Modified"}'
```

**Response (405 Method Not Allowed):**
```json
{
  "detail": "Method \"PUT\" not allowed."
}
```

### 5. Log Aging Action on a Vehicle

**Request (Successful POST on an in-stock vehicle):**
```bash
curl -X POST http://127.0.0.1:8000/api/vehicles/1/actions/ \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "promotion_planned",
    "notes": "Feature on the homepage banner",
    "created_by": "Jane Smith"
  }'
```

**Response (201 Created):**
```json
{
  "id": 2,
  "action_type": "promotion_planned",
  "notes": "Feature on the homepage banner",
  "created_by": "Jane Smith",
  "created_at": "2026-07-11T12:20:45.123456Z"
}
```

**Request (Failed POST on a sold vehicle - returns 400 Bad Request):**
```bash
curl -X POST http://127.0.0.1:8000/api/vehicles/2/actions/ \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "promotion_planned",
    "notes": "Feature on homepage",
    "created_by": "Jane Smith"
  }'
```

**Response (400 Bad Request):**
```json
{
  "non_field_errors": [
    "Actions can only be logged on in_stock vehicles."
  ]
}
```

**Request (Failed POST for a non-existent vehicle ID - returns 404 Not Found):**
```bash
curl -X POST http://127.0.0.1:8000/api/vehicles/99999/actions/ \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "no_action",
    "notes": "Check status",
    "created_by": "System"
  }'
```

**Response (404 Not Found):**
```json
{
  "detail": "Not found."
}
```
