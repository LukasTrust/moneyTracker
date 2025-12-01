## API Endpoint Reference (frontend → backend)

This file lists the canonical API paths the frontend calls, the expected HTTP method, common query parameters or payload fields, the typical response shape (what the frontend expects), and a short backend note describing where to find the router/service and any mismatch risks identified during the audit.

| Path | Method | Query params / Payload | Response shape (frontend expects) | Backend note / mismatch risk |
|---|---:|---|---|---|
| `/accounts` | GET | `limit`, `offset` | `{ items: [...], total: N }` or `data` | Router: `accounts.py` — documented in `audit/06_backend_routers.md`. Ensure list shape consistent. |
| `/accounts/{id}` | GET | — | `{ account: {...} }` or direct object | Router: `accounts.py`. |
| `/accounts` | POST | JSON `{ name, currency, type }` | `{ account: {...} }` | Router: `accounts.py`. Handle 400/422 shapes consistently. |
| `/accounts/{id}` | PUT, DELETE | JSON for PUT | `{ account: {...} }` / 204 for DELETE | Router: `accounts.py`. Frontend treats 404 on delete as success — confirm behaviour. |
| `/categories` | GET, POST | GET: pagination; POST: `{ name, color }` | `{ categories: [...] }` or array | Router: `categories.py`. Patterns & recategorize endpoints described in audit but exact path params should be listed here. |
| `/categories/{id}` | GET, PUT, DELETE | — | `{ category: {...} }` | Router: `categories.py`. |
| `/accounts/{id}/categories-data` | GET | `from_date,to_date,category_ids,limit` | aggregated category results array | Router: `categories.py` / `data.py` interplay. Ensure path exists and param names match frontend. |
| `/accounts/{id}/categories/{categoryId}/transactions` | GET | `from_date,to_date,limit,offset` | `{ transactions: [...], total }` | Router: `categories.py` (category-specific transactions) - backend audit references aggregated endpoints but not exact path literal. |
| `/categories/recategorize` | POST | `account_id` optional | `{ job_id }` or `{ processed: N }` | Router: `categories.py`. Audit recommends background job for large runs. |
| `/categories/check-pattern-conflict/{pattern}` | GET | query `current_category_id` optional | `{ conflict: true/false, matches: [...] }` | Router: `categories.py`. Ensure URL encoding for `pattern`. |
| `/budgets` | GET, POST | GET: `active_only,category_id`; POST: budget payload | list / `{ budget: {...} }` | Router: `budgets.py`. Supports progress endpoints. |
| `/budgets/progress`, `/budgets/summary` | GET | `account_id,active_only` | aggregated progress/summary object | Router: `budgets.py` / `BudgetTracker` service. |
| `/accounts/{accountId}/transactions` | GET | `limit,offset,from_date,to_date,category_ids,min_amount,max_amount,recipient,purpose,transaction_type` | `{ transactions: [...], total }` | Router: `data.py`. Confirm param snake_case. Frontend expects comma-separated `category_ids`. |
| `/accounts/{accountId}/transactions/summary` | GET | same filters | summary object `{ income, expense, balance }` | Router: `data.py`. |
| `/accounts/{accountId}/transactions/statistics` | GET | `group_by=day|month|year` + filters | `[ { period: '2025-11', total: ... }, ... ]` | Router: `data.py` / `DataAggregator`. |
| `/accounts/{accountId}/transactions/recipients` | GET | filters + `limit` | `[ { recipient, total_amount, transaction_count, category_id } ]` | Router: `data.py` / recipients aggregation. |
| `/csv-import/preview` | POST (multipart/form-data) | `file` | `{ headers: [...], sample_rows: [...], delimiter }` | Router: `csv_import.py`. Must enforce file-size/row limits to avoid OOM. |
| `/csv-import/suggest-mapping` | POST (multipart/form-data) | `file` | `{ suggestions: [...] }` | Router: `csv_import.py`. |
| `/csv-import/import` | POST (multipart/form-data) | `account_id, mapping_json, file` | `{ import_id, stats }` or `{ job_id }` (if async) | Router: `csv_import.py`. IMPORTANT: frontend currently expects synchronous results; audit recommends async for large imports — coordinate contract. |
| `/import-history/history` | GET | `account_id, limit, offset` | `{ items: [...], total }` | Router: `import_history.py`. Audit mentions history & rollback. |
| `/import-history/history/{id}` | GET | — | `{ import: {...}, stats }` | Router: `import_history.py`. |
| `/import-history/rollback` | POST | `{ import_id, confirm }` | `{ success: true }` | Router: `import_history.py`. Ensure transactional rollback behavior. |
| `/transfers` | GET, POST | `limit,offset` | list / `{ transfer: {...} }` | Router: `transfers.py`. Audit warns about N+1 and float casting. |
| `/transfers/{id}` | GET, PUT, DELETE | — | `{ transfer: {...} }` | Router: `transfers.py`. |
| `/transfers/detect` | POST | detection params | `{ candidates: [...] }` or `{ job_id }` | Router: `transfers.py` / `TransferMatcher`. |
| `/transfers/stats` | GET | filters | aggregated stats | Router: `transfers.py`. |
| `/accounts/{id}/recurring-transactions` | GET, POST | — | list / `{ recurring: {...} }` | Router: `recurring.py`. Audit recommends background detection and Decimal math. |
| `/accounts/recurring-transactions/detect-all` | POST | — | `{ job_id }` | Router: `recurring.py`. Prefer job-based flow for full-run. |

> Note: The backend audit files (`audit/06_backend_routers.md`, `audit/05_backend_services.md`) document behavior and risks for many of these routers but do not always enumerate every path literal or exact query parameter name. The table above consolidates the canonical paths the frontend uses — update the backend implementation or docs if any path/param differs.
