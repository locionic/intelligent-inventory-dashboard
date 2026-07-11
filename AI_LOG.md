# AI Log - Intelligent Inventory Dashboard

## Chunk 1: Models (Dealership, Vehicle, AgingAction)

### Prompt/Goal
Implement Django models (`Dealership`, `Vehicle`, `AgingAction`) exactly as specified in `spec.md`, with nothing else (no views or serializers). Show generated code before running migrations.

### What Was Generated
- Django project (`inventory_project`) and app (`inventory`).
- Settings updated in `inventory_project/settings.py` to register `rest_framework` and `inventory`.
- `inventory/models.py` with:
  - `Dealership`: `name`, `location`
  - `Vehicle`: `dealership` (FK), `vin` (unique, standard max_length=17), `make`, `model`, `year`, `intake_date`, `price`, `status` (choices: `in_stock`, `sold`, `reserved`, default `in_stock`)
  - `AgingAction`: `vehicle` (FK), `action_type` (choices: `price_reduction_planned`, `promotion_planned`, `transfer_planned`, `no_action`), `notes` (optional text), `created_by` (optional string), `created_at` (auto timestamp)

### Test Written First and Results
No business logic tests written for Chunk 1, as only raw model fields were implemented. (Business logic and tests will be in Chunk 2).
Models verified by running migrations and performing end-to-end database operations via the Django shell.

### Bugs Found & Fixes
None. No model instantiation or schema mapping issues encountered.

### Decisions & Assumptions
- Standard max lengths used for CharFields (e.g., 255 for names/locations/created_by, 17 for VIN).
- SQLite used as default database configuration.
- App registered in `INSTALLED_APPS`.

### Review-driven Additions (Follow-up)
A follow-up review before Chunk 2 introduced the following index and field type updates:
- Added `db_index=True` to `Vehicle.make`, `model`, `status`, and `intake_date` fields.
- Added composite index on `(dealership, status, intake_date)` in `Vehicle.Meta.indexes`.
- Changed `Vehicle.year` to `PositiveIntegerField`.
These were review-driven optimization and type-safety additions, not part of the original generated output.

## Chunk 2: Aging-Stock Query Logic

### Prompt/Goal
Write boundary tests first (89/90/91 days, sold-vehicle exclusion, zero-day) before implementing anything. Then implement using a DB-level `annotate()`, not a Python loop. Threshold is strictly >90 days. Run the tests and show the output.

### What Was Generated
- Boundary tests in [tests.py](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py) covering 0, 89, 90, and 91 days, as well as `sold` and `reserved` vehicles at 91 days.
- [queries.py](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/queries.py) containing `get_annotated_vehicles()` which adds `days_in_stock` (using `RawSQL` on SQLite for integer day subtraction and `ExtractDay` on PostgreSQL/others) and `is_aging` (using conditional `Case`/`When` logic).

### Test Written First and Results
- Tests were written first in [tests.py](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py).
- Initial test run failed as expected with `ModuleNotFoundError: No module named 'inventory.queries'` because the queries logic was not yet implemented.
- After implementing `get_annotated_vehicles`, the test run passed successfully.
- Split the monolithic test into 6 separate test methods (`test_89_days_not_aging`, `test_90_days_not_aging`, `test_91_days_is_aging`, `test_zero_days_not_aging`, `test_sold_vehicle_excluded`, `test_reserved_vehicle_excluded`) to isolate test failures.
- Conducted simulated off-by-one bug test using `intake_date__lte` instead of `intake_date__lt`.

### Bugs Found & Fixes
- **SQLite ExtractDay limitation**: Initially attempted to use Django's database-agnostic `ExtractDay` on standard date difference inside SQLite. This failed with `ValueError: Extract requires native DurationField database support`. Fixed by adding connection vendor detection in [queries.py](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/queries.py) to use `RawSQL` for integer Julian day calculations on SQLite, while keeping `ExtractDay` for PostgreSQL and other production databases.
- **Simulated off-by-one error**: Successfully caught during injection when `test_90_days_not_aging` failed with `AssertionError: True is not false` on `self.assertFalse(annotated_v.is_aging)`. Reverting back to `intake_date__lt` successfully restored the test suite, producing `6/6` passing tests.


### Decisions & Assumptions
- Confirmed that "aging" is defined as strictly greater than 90 days. Day 90 is not aging, day 91 is aging.
- Confirmed that only `in_stock` vehicles can show as aging (sold/reserved status exclusions).
- Determined that for SQLite, `RawSQL("CAST(julianday(%s) - julianday(intake_date) AS INTEGER)", [str(today)])` is the most robust way to calculate pure integer days in stock at the database level.
- Added `db_index=True` on filtered/sorted fields (`make`, `model`, `status`, `intake_date`) to optimize standard and aging query lookups.
- Added composite database index `Meta.indexes` on `(dealership, status, intake_date)` to highly optimize multi-field filters on the aging stock query.
- Converted `Vehicle.year` to `PositiveIntegerField` to enforce positive values for calendar years.

## Chunk 3: Serializers and Views

### Prompt/Goal
Implement serializers and views matching `spec.md` while defaulting to narrow endpoints (no `ModelViewSet`/full CRUD). Create `VehicleSerializer` with `days_in_stock`, `is_aging`, and `latest_action`. Build read-only list/detail views with specific filters, and a single POST endpoint to log actions on `in_stock` vehicles. Write tests for API write-endpoint validation rules before implementing, and run all tests.

### What Was Generated
- [serializers.py](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/serializers.py) containing serializers for `Dealership`, `Vehicle`, `AgingAction` (regular, history, and create with `validate` check for `in_stock` status).
- [views.py](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/views.py) defining:
  - `DealershipListView` (unpaginated list of dealerships populated alphabetically)
  - `VehicleListView` (paginated list of vehicles with custom query filters and sorted by `-intake_date`, `id`)
  - `AgingVehicleListView` (paginated list pre-filtered to `is_aging=True` and sorted by `days_in_stock` desc)
  - `VehicleDetailView` (single vehicle retrieval including full history of actions)
  - `AgingActionCreateView` (endpoint for creating action records)
- [urls.py](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/urls.py) and main URL routing setup in [urls.py](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory_project/urls.py).
- Added list, filtering, detail, and dropdown test cases to `VehicleAPITestCase` in [tests.py](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py).
- Added `test_vehicle_detail_write_methods_not_allowed` in [tests.py](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py) to assert PUT/PATCH/DELETE return 405 Method Not Allowed.
- Added `test_vehicle_list_n_plus_one_queries` using `CaptureQueriesContext` to verify query count is constant (exactly 3 queries) regardless of the number of vehicles and actions.

### Test Written First and Results
- API tests written first in [tests.py](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/tests.py).
- Run against the unimplemented endpoints, the tests failed as expected with 404 response codes (e.g. `AssertionError: 404 != 400` on validation tests, and `AssertionError: 404 != 201` on success test).
- After implementing serializers, views, and routing, all 17 tests passed cleanly:
  - Confirmed `POST /api/vehicles/99999/actions/` returns `404 Not Found` for non-existent vehicle.
  - Confirmed PUT/PATCH/DELETE on `/api/vehicles/{id}/` returns `405 Method Not Allowed`.
  - Confirmed query count is exactly 3 queries (constant regardless of scale) for `/api/vehicles/` using `CaptureQueriesContext`.

### Bugs Found & Fixes
- **Serializer validation error mapping**: Initially validation for missing vehicles returned a `400 Bad Request` from the serializer instead of `404 Not Found` when requesting `POST /api/vehicles/{id}/actions/`. Fixed by calling `get_object_or_404(Vehicle, pk=...)` in the view's `create()` method prior to calling `serializer.is_valid()`, ensuring a standard 404 is returned if the vehicle does not exist.
- **Unordered pagination warning**: Ran into `UnorderedObjectListWarning` from Django REST Framework because the vehicle queryset was not explicitly ordered in the list view. Resolved by adding `order_by('-intake_date', 'id')` on the list view's queryset.

### Decisions & Assumptions
- Defaulted to narrow generic API views (`ListAPIView`, `RetrieveAPIView`, `CreateAPIView`) to restrict HTTP methods to only GET and POST as required by spec, rather than exposing full CRUD operations via `ModelViewSet`.
- Excluded pagination on the dealerships list endpoint to make dropdown data fetching simpler and more logical for frontend components.
- Proactively added N+1 query prevention using `Prefetch('actions', queryset=AgingAction.objects.order_by('-created_at'), to_attr='prefetched_actions')` to optimize list view serialization and eliminate database query loops (constant 3 queries total).

## Chunk 4: OpenAPI Contract & Documentation

### Prompt/Goal
Generate an OpenAPI 3.0 specification (`openapi.yaml`) and cURL examples (`curl_examples.md`) documenting all implemented endpoints, request/response schemas, and example response status codes (200, 201, 400, 404, 405). Write a complete `README.md` detailing the project, setup commands, API links, AI Collaboration Narrative, and test coverage mapping.

### What Was Generated
- [openapi.yaml](file:///home/hongloc/Desktop/hobbies/keyloop2/openapi.yaml): OpenAPI 3.0.3 specification file describing query parameters, request schemas, and responses for `/api/dealerships/`, `/api/vehicles/`, `/api/vehicles/aging/`, `/api/vehicles/{id}/`, and `/api/vehicles/{id}/actions/`.
- [curl_examples.md](file:///home/hongloc/Desktop/hobbies/keyloop2/curl_examples.md): Detailed cURL usage examples with mock json payloads showing success and error states.
- [README.md](file:///home/hongloc/Desktop/hobbies/keyloop2/README.md): Comprehensive project guide containing Overview, Setup, API Links, AI Collaboration Narrative (summarizing model indexing choices, mutation testing results, view set constraints, and the N+1 proof), and full test method mapping.

### Test Written First and Results
No new tests written for this documentation chunk. All documentation points to the verified passing test suite.

### Bugs Found & Fixes
None. Documentation matched the code exactly.

### Decisions & Assumptions
- Pull details directly from views and serializers, ensuring that all query parameters (`min_age_days`, etc.) and response structures are perfectly matching.

## Chunk 5: Demo Frontend Client

### Prompt/Goal
Enable CORS on the Django backend using `django-cors-headers` for local demo purposes. Build a single-page demo client in a `/frontend` folder using plain HTML, vanilla JS, and fetch to display standard/aging vehicles, display vehicle details with full history in a side drawer, and log new actions (rejection validation shown inline). Write a short `frontend/README.md` and test the system end-to-end.

### What Was Generated
- Django backend configuration: Installed `django-cors-headers`, registered app and `CorsMiddleware` in [settings.py](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory_project/settings.py), and set `CORS_ALLOW_ALL_ORIGINS = True` (flagged as development-only).
- [index.html](file:///home/hongloc/Desktop/hobbies/keyloop2/frontend/index.html): HTML/JS interface featuring responsive cards, glassmorphic layout, two tab states (Inventory Directory vs. Aging Stock Insights), filter inputs, detail drawer panel, form submission, and error handling.
- [README.md](file:///home/hongloc/Desktop/hobbies/keyloop2/frontend/README.md): Simple static-serving instructions noting the frontend is for video walkthrough demo only.

### Test Written First and Results
No new tests written for this frontend chunk. Backend test suite remains at 17 passing tests.

### Bugs Found & Fixes
- **CORS blockages**: Attempted fetch requests from port 3000 to port 8000. Fixed by registering `django-cors-headers` middleware and defining `CORS_ALLOW_ALL_ORIGINS = True` on the Django side.
- **Dealership view queryset assignment**: Fixed typo in `DealershipListView` queryset property in [views.py](file:///home/hongloc/Desktop/hobbies/keyloop2/inventory/views.py) that arose during the cleanup, ensuring the unpaginated dropdown values fetch correctly.

### Decisions & Assumptions
- Used plain HTML/JS/Fetch instead of standard frameworks (like React/Vite) to keep the demo client zero-install, lightweight, and easy to run with python's built-in HTTP server.
- Excluded any create/edit/delete functionality on vehicles or dealerships, preserving the strict read-only nature of the data models.






