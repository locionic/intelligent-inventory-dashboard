# Intelligent Inventory Dashboard Backend

This project implements the backend API layer for the Intelligent Inventory Dashboard as specified in [spec.md](file:///home/hongloc/Desktop/hobbies/keyloop2/spec.md). It provides tracking of aging vehicles, computed days in stock, and auditing capability via action logging.

---

## Setup Instructions

These instructions assume a fresh clone of the repository.

### 1. Set Up the Virtual Environment and Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install django djangorestframework
```

### 2. Generate and Apply Database Migrations
```bash
python manage.py makemigrations
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

## API Overview

The API endpoints are detailed in the OpenAPI 3.0 specification contract and illustrated with examples:
- **API Specification Contract**: [openapi.yaml](file:///home/hongloc/Desktop/hobbies/keyloop2/openapi.yaml)
- **cURL Examples with Mock Payloads**: [curl_examples.md](file:///home/hongloc/Desktop/hobbies/keyloop2/curl_examples.md)

---

## AI Collaboration Narrative

This project was built following a strict chunk-by-chunk collaborative loop. Below is a factual timeline of the strategy, verification steps, and architectural choices.

### Chunk-by-Chunk Development Strategy
We divided development into isolated milestones:
1. **Core Database Models**: Created the [Dealership](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/models.py#L3), [Vehicle](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/models.py#L11), and [AgingAction](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/models.py#L37) entities. Review-driven optimization updates added indexes (`db_index=True`) on make, model, status, and intake date, set a composite index on `(dealership, status, intake_date)` to speed up aging filter aggregation, and converted year to a `PositiveIntegerField`.
2. **Aging Stock Queries**: Isolated calculations to database-level `annotate()` calls (using Julian date arithmetic on SQLite, and native `ExtractDay` on production SQL vendors) to compute stock duration.
3. **Serializers & Views**: Structured REST-compliant paginated and filtered list views. Excluded write methods (PUT/PATCH/DELETE) on detail views, and added standard validation constraints.

### Aging Stock Boundary Verification
During the implementation of the aging rule (vehicles count as aging if they are `in_stock` and in inventory for strictly greater than 90 days), we verified the logic by injecting a simulated off-by-one bug where `intake_date__lte` was used instead of `intake_date__lt`.

This simulated bug was immediately caught by `test_90_days_not_aging` with the following trace:
```text
FAIL: test_90_days_not_aging (inventory.tests.AgingStockQueryTestCase)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py", line 64, in test_90_days_not_aging
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

---

## Test Coverage and Execution

Execute all 17 tests:
```bash
python manage.py test
```

### Tests Grouped by Chunk

#### Chunk 2: Aging-Stock Query Logic
- [test_zero_days_not_aging](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py#L14)
- [test_89_days_not_aging](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py#L29)
- [test_90_days_not_aging](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py#L44)
- [test_91_days_is_aging](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py#L59)
- [test_sold_vehicle_excluded](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py#L74)
- [test_reserved_vehicle_excluded](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py#L89)

#### Chunk 3: Serializers, Views, and Validation
- [test_create_action_success](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py#L162)
- [test_create_action_invalid_action_type](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py#L173)
- [test_create_action_missing_vehicle](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py#L184)
- [test_create_action_sold_vehicle_rejected](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py#L194)
- [test_create_action_reserved_vehicle_rejected](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py#L204)
- [test_vehicle_list_filtering](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py#L214)
- [test_aging_vehicle_list](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py#L249)
- [test_vehicle_detail](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py#L268)
- [test_dealership_dropdown_list](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py#L289)
- [test_vehicle_detail_write_methods_not_allowed](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py#L297)
- [test_vehicle_list_n_plus_one_queries](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py#L312)
