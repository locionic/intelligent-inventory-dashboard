# Intelligent Inventory Dashboard Backend

This project implements the backend API layer for the Intelligent Inventory Dashboard as specified in [spec.md](spec.md). It provides tracking of aging vehicles, computed days in stock, and auditing capability via action logging.

---

## Prerequisites

- **Python 3.10 or higher** (tested on 3.11). Django 5.x requires Python ≥3.10;
  installing on an older Python will fail at the `pip install` step with a
  version resolution error.

## Setup Instructions

These instructions assume a fresh clone of the repository.

### 1. Set Up the Virtual Environment and Install Dependencies
```bash
python3 --version    # confirm 3.10+
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Generate and Apply Database Migrations
```bash
python manage.py migrate
```

### 3. Run the Development Server
```bash
python manage.py runserver
```
The server will start running at `http://127.0.0.1:8000/`.

### 4. Run the Test Suite
```bash
python manage.py test
```

---

## Demo Frontend (optional, not the graded service layer)

A minimal single-page demo client lives in [`frontend/`](frontend/) — it exists purely
for visual walkthroughs and calls the real API above (no mocked data). The backend
is the fully-implemented, graded service layer per the assessment; the frontend is
a bonus for the video demo.

CORS is enabled in `inventory_project/settings.py` via `django-cors-headers`
(`CORS_ALLOW_ALL_ORIGINS = True`) so the frontend, served from a different port,
can call the API. This setting is **development-only** — a production deployment
should restrict allowed origins explicitly.

To run the frontend, with the backend already running on port 8000:
```bash
cd frontend
python3 -m http.server 3000
```
Then open `http://localhost:3000`. See [`frontend/README.md`](frontend/README.md) for details.

---

## API Overview

The API endpoints are detailed in the OpenAPI 3.0 specification contract and illustrated with examples:
- **API Specification Contract**: [openapi.yaml](openapi.yaml)
- **cURL Examples with Mock Payloads**: [curl_examples.md](curl_examples.md)

---

## AI Collaboration Narrative

This project was built following a strict chunk-by-chunk collaborative loop. Below is a factual timeline of the strategy, verification steps, and architectural choices.

### Chunk-by-Chunk Development Strategy
We divided development into isolated milestones:
1. **Core Database Models**: Created the `Dealership`, `Vehicle`, and `AgingAction` entities. Review-driven optimization updates added indexes (`db_index=True`) on make, model, status, and intake date, set a composite index on `(dealership, status, intake_date)` to speed up aging filter aggregation, and converted year to a `PositiveIntegerField`.
2. **Aging Stock Queries**: Isolated calculations to database-level `annotate()` calls (using Julian date arithmetic on SQLite, and native `ExtractDay` on production SQL vendors) to compute stock duration.
3. **Serializers & Views**: Structured REST-compliant paginated and filtered list views. Excluded write methods (PUT/PATCH/DELETE) on detail views, and added standard validation constraints.
4. **Documentation**: OpenAPI contract, cURL examples, and this README.
5. **Demo Frontend**: A minimal, non-graded UI for video walkthroughs, calling the real API.

### Aging Stock Boundary Verification
During the implementation of the aging rule (vehicles count as aging if they are `in_stock` and in inventory for strictly greater than 90 days), we verified the logic by injecting a simulated off-by-one bug where `intake_date__lte` was used instead of `intake_date__lt`.

This simulated bug was immediately caught by `test_90_days_not_aging` with the following trace:
```text
FAIL: test_90_days_not_aging (inventory.tests.AgingStockQueryTestCase)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "inventory/tests.py", line 64, in test_90_days_not_aging
    self.assertFalse(annotated_v.is_aging)
AssertionError: True is not false
```
Reverting to the strict inequality operator (`intake_date__lt`) returned all tests to a passing state.

### Rejecting Broad Endpoints
To uphold the "default to narrow, not broad" guideline, we rejected standard Django REST Framework `ModelViewSet` routers because they automatically generate full CRUD routes. Because the specifications only call for read-only listings and one audit action logger, we instead constructed explicit generic views:
- `ListAPIView` for dealerships, vehicles, and aging vehicles
- `RetrieveAPIView` for vehicle details
- `CreateAPIView` for aging actions

This strictly rejects PUT, PATCH, and DELETE operations, yielding a `405 Method Not Allowed` response.

### Proactive N+1 Query Prevention & Proof
To prevent serializing child objects in loops, we proactively configured the list view to prefetch vehicle actions in reverse-chronological order:
```python
queryset = queryset.prefetch_related(
    Prefetch(
        'actions',
        queryset=AgingAction.objects.order_by('-created_at'),
        to_attr='prefetched_actions'
    )
)
```
We proved N+1 prevention with `CaptureQueriesContext` in `test_vehicle_list_n_plus_one_queries`. The test runs a query on a single vehicle, creates 4 additional vehicles (with associated actions), and asserts that the query count remains constant at exactly **3 queries** regardless of dataset size:
1. `SELECT COUNT(*)` (pagination count)
2. `SELECT vehicle` (paginated results)
3. `SELECT agingaction WHERE vehicle_id IN (...)` (prefetch actions)

### Repo Hygiene Note
`manage.py`, the `inventory_project/` settings module, and `requirements.txt`
were initially generated locally but not committed in an early pass, which
made the repo unrunnable from a fresh clone. Caught by explicitly testing a
fresh `git clone` + setup walkthrough before submission, rather than
assuming the committed repo matched the local working copy. Fixed by
committing the missing files and regenerating `requirements.txt` from the
correct project virtual environment.

---

## Test Coverage and Execution

Execute all 17 tests:
```bash
python manage.py test
```

### Tests Grouped by Chunk

#### Chunk 2: Aging-Stock Query Logic
- test_zero_days_not_aging
- test_89_days_not_aging
- test_90_days_not_aging
- test_91_days_is_aging
- test_sold_vehicle_excluded
- test_reserved_vehicle_excluded

#### Chunk 3: Serializers, Views, and Validation
- test_create_action_success
- test_create_action_invalid_action_type
- test_create_action_missing_vehicle
- test_create_action_sold_vehicle_rejected
- test_create_action_reserved_vehicle_rejected
- test_vehicle_list_filtering
- test_aging_vehicle_list
- test_vehicle_detail
- test_dealership_dropdown_list
- test_vehicle_detail_write_methods_not_allowed
- test_vehicle_list_n_plus_one_queries
