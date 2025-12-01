**TL;DR**
- Mapping file: Frontend hooks & services → Backend routers (based on `audit/06_backend_routers.md`).
- Purpose: show where frontend calls map to backend routers, and highlight mismatches (paths, params, payload/response expectations, missing docs, auth/headers/timeouts).

Scope & method
- Scanned: `frontend/src/hooks/*`, `frontend/src/services/*`. Extracted all `api.*(...)` usages and FormData/POST endpoints; reviewed `audit/06_backend_routers.md` for router responsibilities and notes.
- This file links each frontend service/hook to the backend router(s) that should implement the route and flags potential mismatches.

Summary mapping (frontend → backend router)
- Accounts
  - Frontend services/hooks: `accountService` (`/accounts`, `/accounts/{id}`), `useAccountStore`, `useTransactions` (account-scoped), `useSummary`.
  - Backend router: `accounts.py` (documented in `audit/06_backend_routers.md`).
  - Mismatch notes: none major; ensure delete semantics (frontend treats 404 on delete as success — backend should return 404 when already deleted). Link: `audit/06_backend_routers.md` → `accounts.py`.

- Categories & Mappings
  - Frontend services/hooks: `categoryService` (`/categories`, `/categories/{id}`, `/accounts/{id}/categories-data`, `/categories/recategorize`, pattern-check endpoints), `categoryStore.fetchMappings` calls `categoryService.getMappings`.
  - Backend router: `categories.py` (documented). See `audit/06_backend_routers.md` → `categories.py`.
  - Mismatch notes:
    - Frontend expects `/accounts/{id}/categories-data` and `/accounts/{id}/categories/{categoryId}/transactions` paths. Backend audit references aggregated endpoints but doesn't list exact path strings verbatim — add explicit path list to router MD.
    - Pattern conflict endpoint uses URL-encoded pattern in path: backend must match `GET /categories/check-pattern-conflict/{pattern}` (ensure encoding/decoding consistent and route accepts large patterns).

- Budgets
  - Frontend: `budgetService` (`/budgets`, `/budgets/progress`, `/budgets/summary`, `/budgets/{id}/progress`), `useBudgetStore`.
  - Backend router: `budgets.py` / grouped analytics (documented). See `audit/06_backend_routers.md` grouped section.
  - Mismatch notes: none blocking. Backend should support `active_only`, `category_id`, `account_id` query params as used by the frontend (snake_case vs camelCase — frontend uses snake_case query keys; ensure backend accepts them). Verify documented param names in router MD.

- Transactions / Data / Summary / Stats / Recipients
  - Frontend: `dataService` uses `/accounts/{accountId}/transactions`, `/accounts/{accountId}/transactions/summary`, `/transactions/statistics`, `/transactions/recipients`, and category-specific transactions endpoints.
  - Backend router: `data.py` and `accounts`-scoped transaction routes (documented at router/service level). See `audit/06_backend_routers.md` (DataAggregator notes).
  - Mismatch notes:
    - Frontend uses query params like `category_ids` (comma-separated), `min_amount`, `max_amount`, `purpose` — confirm backend parameter names match these (audit notes filters but doesn't list exact param names). Add param list to router MD.
    - Frontend expects `response.data` to contain `{ data, total }` or `{ transactions, total }` in different places. Backend should standardize list endpoints to return consistent shape (e.g., `{ items, total }`). Where backend audit mentions heavy aggregations, confirm response shape in backend code or add schema docs to `audit/04_backend_schemas.md`.

- CSV Import & Import History
  - Frontend: `csvImportApi` `/csv-import/preview`, `/csv-import/suggest-mapping`, `/csv-import/import` (multipart/form-data). `importHistoryService` uses `/import-history/history`, `/import-history/history/{id}`, `/import-history/rollback`.
  - Backend router: `csv_import.py` and `import_history.py` discussed in `audit/06_backend_routers.md` and `audit/05_backend_services.md` (high-priority). Router MD strongly warns about streaming and background jobs.
  - Mismatch / Risk notes (important):
    - Frontend sends multipart POST to `/csv-import/import` and expects synchronous import results. Backend audit recommends moving heavy imports to background jobs and returning job IDs for large imports. Frontend and backend must agree on this contract. If backend enqueues jobs, frontend should expect `{ job_id }` and poll `import-history` endpoints, not immediate `import result` payload.
    - `csvImportApi.previewCsv` expects immediate parsing of the uploaded file and returns sample rows; backend must enforce file-size limits and safe parsing to avoid OOM. Add explicit accepted file-size header/behavior in router MD.
    - `importHistoryService.rollbackImport` uses `POST /import-history/rollback` with body `{ import_id, confirm }` — backend router must support that shape (audit mentions rollback but not payload shape explicitly).

- Transfers
  - Frontend: `transferService` (`/transfers`, `/transfers/detect`, `/transfers/stats`, `/transactions/{id}/transfer`).
  - Backend: `transfers.py` (documented). Audit warns about N+1 and float casting.
  - Mismatch notes: Ensure `/transactions/{id}/transfer` exists and returns correct fields; frontend expects `transactions/{id}/transfer` path (singular `transaction` vs `transactions`) — confirm backend path matches exactly.

- Recurring
  - Frontend: `recurringService` uses `/accounts/{id}/recurring-transactions`, `/accounts/recurring-transactions`, `/accounts/recurring-transactions/detect-all`, etc.
  - Backend: `recurring.py` (documented). Audit notes float→Decimal migration and background jobs.
  - Mismatch notes: confirm detection endpoints (`detect`, `detect-all`) behavior and return shapes (job id vs result) match frontend expectations.

Cross-cutting mismatches & risks (concrete)
- Path literal differences and implicit assumptions
  - Example: frontend calls `/transactions/{id}/transfer` (singular `transactionS` in other places). Search the backend router source or MD for exact path string before shipping. Recommendation: add an explicit path table to `audit/06_backend_routers.md`.

- Response shape inconsistencies
  - Several frontend consumers tolerate either `response.data.transactions` or `response.data.data` or `response.data` — prefer a single canonical list response shape. Backend audit should include expected response schemas for list endpoints in `audit/04_backend_schemas.md`.

- Query param naming
  - Frontend sends snake_case query keys (`from_date`, `to_date`, `category_ids`). Ensure backend expects snake_case and does not require camelCase. Add param lists in router MD to avoid confusion.

- CSV import sync vs async contract
  - Frontend currently calls import endpoints synchronously. Backend audit recommends async for large imports. Coordinate API contract: either frontend should limit uploads (small) or backend returns `{ job_id }` and frontend polls import history.

- Authorization / Auth header behavior
  - Frontend attaches `Authorization: Bearer <token>` if present in localStorage (in `api.js`). Backend audit should confirm endpoints use the same auth scheme; if some routers are public (health, metrics) and others are protected, list which need auth in router MD.

- Error normalization
  - Frontend `api` expects normalized error shapes and displays `error.response.data.message`. Backend audit recommends `error` shapes `{ success: false, error: { status, code, message, details } }`. Ensure backend returns compatible shape or update interceptor mapping accordingly.

Integration & Cross-References
- **Related files:** `/audit/08_frontend_overview.md`, `/audit/09_frontend_src.md`, `/audit/11_frontend_pages.md`, `/audit/12_frontend_components.md`.
- **Error & response normalization:**
  - Frontend expects a consistent error shape (e.g., `{ error: { status, code, message } }`). If backend uses a different shape, add an adapter in `frontend/src/services/api.js` to normalize before components consume it.
  - Centralize list response normalization in `frontend/src/services/api.js` so hooks and services can rely on `{ items, total }`.
- **Next practical steps:**
  1. Create `audit/backend_api_endpoints.md` listing canonical paths and the expected request/response samples for the high-usage endpoints identified here.
  2. Add a small `api-normalizer` in `frontend/src/services/api.js` (or extend the axios interceptors) to normalize `{ data } | { transactions } | [...]` into `{ items, total }` and to normalize error objects.
  3. Coordinate CSV import contract (sync vs async) in the new backend endpoints document and update frontend import logic accordingly.

Files referenced / links
- Frontend: `frontend/src/hooks/useApi.js`, `frontend/src/services/*.js`, `frontend/src/store/*.js`
- Backend audit: `audit/06_backend_routers.md`, `audit/05_backend_services.md`, `audit/04_backend_schemas.md`

Next steps I can take (pick one)
- A: Apply a small patch that appends an `API endpoints` table to `audit/06_backend_routers.md` listing the canonical paths used by the frontend and expected params (quick, non-invasive documentation patch). 
- B: Update `frontend/src/services/api.js` to normalize list response shapes (`items`/`total`) centrally and adjust callers accordingly (requires small code changes and basic tests).

I will now mark this new audit file as complete in the TODO list.
