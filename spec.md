Spec: Intelligent Inventory Dashboard (Scenario B, Backend)
Data Model
Dealership

id (PK)
name
location

Vehicle

id (PK)
dealership_id (FK → Dealership)
vin (unique, string)
make
model
year
intake_date (date — when it arrived in inventory)
price
status (enum: in_stock, sold, reserved) — default in_stock

AgingAction (audit log, not overwrite-in-place — lets you show history, more defensible design choice)

id (PK)
vehicle_id (FK → Vehicle)
action_type (enum: price_reduction_planned, promotion_planned, transfer_planned, no_action)
notes (text, optional)
created_by (string, optional — no auth in scope, just a name field)
created_at (auto timestamp)

Aging rule (business logic, isolate this):
is_aging = (today - vehicle.intake_date).days > 90
Edge case to test: exactly 90 days → NOT aging (inclusive threshold means day 91 is aging). Decide > not >= and document why — that's your ambiguity-documented-as-assumption point for the design doc.
Only in_stock vehicles count toward aging (sold/reserved shouldn't show as "aging stock" — a real assumption worth stating explicitly).
API Contract
GET /api/vehicles/
  Query params: dealership_id, make, model, min_age_days, status
  Returns: paginated list of vehicles with computed `days_in_stock` and `is_aging` fields

GET /api/vehicles/aging/
  Same filters, pre-filtered to is_aging=true, sorted by days_in_stock desc
  Returns: vehicles + their latest AgingAction if any

GET /api/vehicles/{id}/
  Returns: single vehicle detail + full AgingAction history

POST /api/vehicles/{id}/actions/
  Body: { action_type, notes, created_by }
  Returns: created AgingAction record
  Validation: action_type must be valid enum, vehicle must exist and be in_stock

GET /api/dealerships/
  Returns: list, for filter dropdown population
Response shape example
json{
  "id": 42,
  "vin": "1HGCM82633A123456",
  "make": "Toyota",
  "model": "Camry",
  "year": 2023,
  "intake_date": "2026-03-15",
  "price": "24999.00",
  "status": "in_stock",
  "days_in_stock": 117,
  "is_aging": true,
  "latest_action": {
    "action_type": "price_reduction_planned",
    "notes": "Reduce by $1000",
    "created_at": "2026-07-01T10:00:00Z"
  }
}
Deliberate assumptions to write in your design doc

Aging threshold is >90 days, exclusive at day 90, inclusive from day 91 — chose strict > per literal requirement wording.
Only in_stock vehicles are eligible for aging status.
AgingAction is append-only history, not a single mutable field — supports audit trail, more realistic for a dealership ops tool.
No auth layer in scope — created_by is a free-text field, noted as a gap for production.
